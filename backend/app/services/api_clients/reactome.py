from typing import List, Dict, Any
from .base_client import BaseAPIClient
from .circuit_breaker import CircuitBreaker


class ReactomeClient(BaseAPIClient):
    """
    Client for Reactome pathway database.
    Queries pathway overlap between drug targets and disease genes.
    """

    def __init__(self):
        super().__init__("https://reactome.org/ContentService")
        self.circuit_breaker = CircuitBreaker()

    async def get_pathway_overlap(
        self,
        target_gene: str,
        disease_genes: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate pathway overlap between target gene and disease genes.

        Args:
            target_gene: Drug target gene symbol (e.g., "ACHE")
            disease_genes: List of disease-associated genes (e.g., ["APP", "PSEN1"])

        Returns:
            {
                "shared_pathways": List[str],     # Pathway IDs/names shared
                "pathway_similarity": float,       # Jaccard index (0-1)
                "enriched_processes": List[str],   # Key biological processes
                "target_pathway_count": int,       # Total pathways for target
                "disease_pathway_count": int       # Total pathways for disease genes
            }
        """
        async def _execute():
            print(f"Reactome: Querying pathways for target={target_gene}, disease_genes={disease_genes[:3]}...")

            try:
                # Get pathways for target gene
                target_pathways = await self._get_gene_pathways(target_gene)

                if not target_pathways:
                    print(f"Reactome: No pathways found for {target_gene}")
                    return {}

                # Get pathways for disease genes (combine all)
                disease_pathways = set()
                for disease_gene in disease_genes:
                    gene_pathways = await self._get_gene_pathways(disease_gene)
                    disease_pathways.update(gene_pathways)

                if not disease_pathways:
                    print(f"Reactome: No pathways found for disease genes")
                    return {}

                # Calculate Jaccard similarity: |intersection| / |union|
                target_set = set(target_pathways)
                disease_set = disease_pathways

                intersection = target_set & disease_set
                union = target_set | disease_set

                jaccard_similarity = len(intersection) / len(union) if union else 0.0

                # Extract shared pathway names
                shared_pathway_names = list(intersection)

                # Get enriched processes (top-level pathway categories)
                enriched_processes = self._extract_enriched_processes(shared_pathway_names)

                result = {
                    "shared_pathways": shared_pathway_names,
                    "pathway_similarity": jaccard_similarity,
                    "enriched_processes": enriched_processes,
                    "target_pathway_count": len(target_set),
                    "disease_pathway_count": len(disease_set)
                }

                print(f"Reactome: Found {len(intersection)} shared pathways (Jaccard={jaccard_similarity:.2f})")
                return result

            except Exception as e:
                print(f"Reactome: Error querying pathways: {e}")
                return {}

        try:
            return await self.circuit_breaker.call(_execute)
        except Exception as e:
            print(f"Reactome: Circuit breaker error: {e}")
            return {}

    async def _search_gene_entities(self, gene_symbol: str) -> List[str]:
        """
        Search Reactome for entity IDs matching a gene symbol.

        Args:
            gene_symbol: Gene symbol (e.g., "INSR")

        Returns:
            List of Reactome entity IDs (e.g., ["R-HSA-74668", "R-HSA-141718"])
        """
        try:
            response = await self.get(
                "search/query",
                params={
                    "query": gene_symbol,
                    "species": "Homo sapiens",
                    "types": "ReferenceEntity"
                }
            )

            if not response or "results" not in response:
                return []

            # Extract entity IDs from search results
            entity_ids = []
            for result_group in response.get("results", []):
                for entry in result_group.get("entries", []):
                    # Get the stId which is the stable identifier
                    entity_id = entry.get("stId") or entry.get("id")
                    if entity_id and entity_id.startswith("R-HSA-"):
                        entity_ids.append(entity_id)

            return entity_ids

        except Exception as e:
            if "404" not in str(e):
                print(f"Reactome: Error searching for {gene_symbol}: {e}")
            return []

    async def _get_gene_pathways(self, gene_symbol: str) -> List[str]:
        """
        Get all pathways containing a gene.

        Returns list of pathway identifiers/names.
        """
        try:
            # Step 1: Search for entity IDs
            entity_ids = await self._search_gene_entities(gene_symbol)

            if not entity_ids:
                return []

            # Step 2: Get pathways for first entity (usually sufficient)
            entity_id = entity_ids[0]

            response = await self.get(
                f"data/pathways/low/entity/{entity_id}"
            )

            if not response:
                return []

            # Parse pathway identifiers
            pathways = []
            if isinstance(response, list):
                for pathway in response:
                    # Extract pathway name or ID
                    pathway_name = pathway.get("displayName") or pathway.get("stId") or pathway.get("name")
                    if pathway_name:
                        pathways.append(pathway_name)
            elif isinstance(response, dict):
                # Single pathway returned
                pathway_name = response.get("displayName") or response.get("stId") or response.get("name")
                if pathway_name:
                    pathways.append(pathway_name)

            return pathways

        except Exception as e:
            # Reactome has limited gene coverage - gracefully return empty
            # Only log non-404 errors
            if "404" not in str(e):
                print(f"Reactome: Error fetching pathways for {gene_symbol}: {e}")
            return []

    def _extract_enriched_processes(self, pathway_names: List[str]) -> List[str]:
        """
        Extract high-level biological processes from pathway names.

        Reactome pathways are hierarchical. Extract top-level categories.
        """
        # Common top-level processes in Reactome
        process_keywords = {
            "Signal Transduction": ["signal", "signaling", "signalling"],
            "Metabolism": ["metabol", "glycolysis", "citric acid", "oxidative phosphorylation"],
            "Immune System": ["immune", "interferon", "cytokine", "complement"],
            "Cell Cycle": ["cell cycle", "mitosis", "meiosis", "DNA replication"],
            "Gene Expression": ["transcription", "translation", "RNA", "gene expression"],
            "Apoptosis": ["apoptosis", "programmed cell death"],
            "DNA Repair": ["DNA repair", "DNA damage"],
            "Protein Degradation": ["ubiquitin", "proteasome", "autophagy"],
            "Vesicle Transport": ["vesicle", "transport", "endocytosis", "exocytosis"],
            "Developmental Biology": ["development", "differentiation"]
        }

        enriched = set()

        for pathway_name in pathway_names:
            pathway_lower = pathway_name.lower()
            for process, keywords in process_keywords.items():
                if any(keyword in pathway_lower for keyword in keywords):
                    enriched.add(process)

        return list(enriched)
