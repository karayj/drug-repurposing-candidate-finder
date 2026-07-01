import asyncio
from typing import List, Dict, Any, Optional
from app.services.api_clients.open_targets import OpenTargetsClient
from app.services.api_clients.chembl import ChEMBLClient
from app.services.api_clients.uniprot import UniProtClient
from app.services.api_clients.omim import OMIMClient
from app.services.api_clients.string_db import StringDBClient
# Expression data now comes from Open Targets, no separate client needed
from app.services.api_clients.reactome import ReactomeClient
from app.services.scoring import EvidenceScorer
from app.services.cache_service import CacheService


class SearchOrchestrator:
    """
    Orchestrates drug repurposing searches across multiple biological databases.

    Coordinates parallel API calls, handles failures gracefully, calculates evidence scores,
    and returns ranked drug candidates.
    """

    def __init__(self, cache: CacheService):
        self.cache = cache

        # Existing clients
        self.open_targets = OpenTargetsClient()
        self.chembl = ChEMBLClient()
        self.uniprot = UniProtClient()  # Keep for backward compat but don't use
        self.omim = OMIMClient()

        # NEW clients
        self.string_db = StringDBClient()
        self.reactome = ReactomeClient()

        self.scorer = EvidenceScorer()

    async def search_drug_candidates(
        self,
        disease_name: str,
        weights: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for drug repurposing candidates.

        Args:
            disease_name: Name of the disease to search
            weights: Optional custom scoring weights. If None, uses defaults.

        Returns:
            List of drug candidates sorted by total_score (descending)
        """
        # Cache key includes weights to avoid mixing results
        cache_key = self.cache.generate_key("search", disease_name, str(weights) if weights else "default")

        cached_results = await self.cache.get(cache_key)
        if cached_results:
            print(f"Orchestrator: Returning cached results for {disease_name}")
            return cached_results

        try:
            targets_data = await self.open_targets.get_disease_targets(disease_name)
        except Exception as e:
            print(f"Open Targets API error: {e}")
            targets_data = []

        if not targets_data:
            return []

        # NEW: Extract top disease-associated genes for network/pathway queries
        # Limit to top 8 targets (user decision: reduce if latency issue)
        disease_genes = [t["gene_symbol"] for t in targets_data[:8]]
        print(f"Orchestrator: Processing {len(disease_genes)} disease genes for {disease_name}")

        all_candidates = []

        for target_data in targets_data[:8]:  # Reduced from 10 to 8
            try:
                candidates = await self._process_target(
                    target_data,
                    disease_genes,  # NEW parameter
                    disease_name,   # NEW parameter
                    weights         # NEW parameter
                )
                all_candidates.extend(candidates)
            except Exception as e:
                print(f"Error processing target {target_data.get('target_id')}: {e}")
                continue

        all_candidates.sort(key=lambda x: x["total_score"], reverse=True)
        top_candidates = all_candidates[:50]

        await self.cache.set(cache_key, top_candidates)

        return top_candidates

    async def _process_target(
        self,
        target_data: Dict,
        disease_genes: List[str],  # NEW
        disease_name: str,          # NEW
        weights: Optional[Dict[str, float]] = None  # NEW
    ) -> List[Dict[str, Any]]:
        """
        Process a single target gene: query for drugs and enrich with evidence.

        Args:
            target_data: Target gene data from Open Targets
            disease_genes: List of all disease-associated genes (for network/pathway analysis)
            disease_name: Disease name (for expression queries)
            weights: Optional custom scoring weights

        Returns:
            List of drug candidates for this target
        """
        gene_symbol = target_data["gene_symbol"]

        try:
            drugs_data = await self.chembl.get_drugs_for_target(gene_symbol)
        except Exception as e:
            print(f"ChEMBL error for {gene_symbol}: {e}")
            return []

        if not drugs_data:
            return []

        # Parallel async calls to all enrichment APIs
        omim_task = asyncio.create_task(
            self._safe_api_call(self.omim.get_gene_disease_associations, gene_symbol)
        )

        # NEW async calls
        string_task = asyncio.create_task(
            self._safe_api_call(
                self.string_db.get_protein_interactions,
                gene_symbol,
                disease_genes
            )
        )
        reactome_task = asyncio.create_task(
            self._safe_api_call(
                self.reactome.get_pathway_overlap,
                gene_symbol,
                disease_genes
            )
        )

        # Gather all results (removed uniprot_task, expression_task)
        omim_data, string_data, reactome_data = await asyncio.gather(
            omim_task,
            string_task,
            reactome_task
        )

        # Extract expression data from Open Targets (already fetched)
        expression_info = self.open_targets.get_disease_relevant_expression(
            target_data.get("expressions", []),
            disease_name
        ) if "expressions" in target_data else {}

        candidates = []
        for drug_data in drugs_data:
            # Prepare expression data with drug action type for alignment scoring
            expression_data_with_action = None
            if expression_info:
                expression_data_with_action = {
                    **expression_info,
                    "drug_action_type": drug_data.get("action_type", "UNKNOWN")
                }

            scores = self.scorer.calculate_total_score(
                open_targets_data=target_data,
                chembl_data=drug_data,
                uniprot_data=None,  # Deprecated
                omim_data=omim_data,
                string_data=string_data,
                expression_data=expression_data_with_action,
                reactome_data=reactome_data,
                weights=weights  # NEW: Pass through custom weights
            )

            candidate = {
                "drug_name": drug_data["drug_name"],
                "chembl_id": drug_data["chembl_id"],
                "target_gene": gene_symbol,
                "target_id": target_data["target_id"],
                "mechanism": drug_data.get("mechanism", "Unknown"),
                "action_type": drug_data.get("action_type", "UNKNOWN"),  # NEW
                **scores,
                "omim_associations": len(omim_data) if omim_data else 0,
                # NEW metadata
                "string_interactions": string_data.get("direct_interactions", 0) if string_data else 0,
                "network_distance": string_data.get("network_distance", 999) if string_data else 999,
                "expression_level": expression_info.get("expression_level", "unknown") if expression_info else "unknown",
                "expression_fold_change": expression_info.get("fold_change", None) if expression_info else None,
                "shared_pathways": reactome_data.get("shared_pathways", []) if reactome_data else [],
                "pathway_similarity": reactome_data.get("pathway_similarity", 0.0) if reactome_data else 0.0
            }

            candidates.append(candidate)

        return candidates

    async def _safe_api_call(self, func, *args, **kwargs) -> Optional[Any]:
        """Wrap API calls with exception handling for graceful degradation."""
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            print(f"API call error for {func.__name__}: {e}")
            return None

    async def cleanup(self):
        """Close all HTTP connections."""
        await self.open_targets.close()
        await self.chembl.close()
        await self.uniprot.close()
        await self.omim.close()
        await self.string_db.close()
        await self.reactome.close()
