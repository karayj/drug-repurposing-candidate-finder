from typing import Dict, List, Optional
from app.config import get_settings


class EvidenceScorer:
    """
    Evidence-based scorer for drug repurposing candidates.

    Supports user-configurable weights with intelligent redistribution
    when data sources are unavailable.
    """

    def __init__(self):
        self.settings = get_settings()

    def calculate_total_score(
        self,
        open_targets_data: Optional[Dict] = None,
        chembl_data: Optional[Dict] = None,
        uniprot_data: Optional[Dict] = None,  # DEPRECATED: Will be set to 0
        omim_data: Optional[List[Dict]] = None,
        string_data: Optional[Dict] = None,
        expression_data: Optional[Dict] = None,
        reactome_data: Optional[Dict] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float|str]:
        """
        Calculate evidence-based score from multiple API sources.

        Args:
            weights: Optional dict with keys 'open_targets', 'chembl', 'string',
                     'expression', 'reactome', 'omim'. If None, uses default weights.

        Default weights (sum to 100):
        - Open Targets: 30 pts
        - ChEMBL: 25 pts
        - STRING: 15 pts
        - Expression: 15 pts
        - Reactome: 10 pts
        - OMIM: 5 pts
        """
        # Load weights (defaults if not provided)
        if weights is None:
            weights = {
                'open_targets': 30.0,
                'chembl': 25.0,
                'string': 15.0,
                'expression': 15.0,
                'reactome': 10.0,
                'omim': 5.0
            }

        # Validate weights sum to 100
        total_weight = sum(weights.values())
        if abs(total_weight - 100.0) > 0.01:
            raise ValueError(f"Weights must sum to 100, got {total_weight}")

        # Calculate normalized scores (0-1 scale) from each source
        source_results = {
            'open_targets': (self._score_open_targets(open_targets_data) if open_targets_data else None, weights['open_targets']),
            'chembl': (self._score_chembl(chembl_data) if chembl_data else None, weights['chembl']),
            'string': (self._score_string(string_data) if string_data else None, weights['string']),
            'expression': (self._score_expression(expression_data) if expression_data else None, weights['expression']),
            'reactome': (self._score_reactome(reactome_data) if reactome_data else None, weights['reactome']),
            'omim': (self._score_omim(omim_data) if omim_data else None, weights['omim'])
        }

        # WEIGHT REDISTRIBUTION: If sources unavailable, redistribute weights to available sources
        available_sources = {k: v for k, v in source_results.items() if v[0] is not None}
        unavailable_sources = {k: v for k, v in source_results.items() if v[0] is None}

        # Calculate total weight to redistribute
        weight_to_redistribute = sum(v[1] for v in unavailable_sources.values())

        # Redistribute proportionally to available sources
        if weight_to_redistribute > 0 and len(available_sources) > 0:
            total_available_weight = sum(v[1] for v in available_sources.values())

            # Calculate adjusted weights (proportional redistribution)
            adjusted_weights = {}
            for source, (score, original_weight) in available_sources.items():
                proportion = original_weight / total_available_weight
                redistribution = weight_to_redistribute * proportion
                adjusted_weights[source] = original_weight + redistribution

            # Apply adjusted weights to available sources
            ot_score = (available_sources['open_targets'][0] * adjusted_weights['open_targets']) if 'open_targets' in available_sources else 0.0
            chembl_score = (available_sources['chembl'][0] * adjusted_weights['chembl']) if 'chembl' in available_sources else 0.0
            string_score = (available_sources['string'][0] * adjusted_weights['string']) if 'string' in available_sources else 0.0
            expression_score = (available_sources['expression'][0] * adjusted_weights['expression']) if 'expression' in available_sources else 0.0
            reactome_score = (available_sources['reactome'][0] * adjusted_weights['reactome']) if 'reactome' in available_sources else 0.0
            omim_score = (available_sources['omim'][0] * adjusted_weights['omim']) if 'omim' in available_sources else 0.0

            # Store adjusted weights for return (fill in 0 for unavailable sources)
            actual_weights_used = {
                'open_targets': adjusted_weights.get('open_targets', 0.0),
                'chembl': adjusted_weights.get('chembl', 0.0),
                'string': adjusted_weights.get('string', 0.0),
                'expression': adjusted_weights.get('expression', 0.0),
                'reactome': adjusted_weights.get('reactome', 0.0),
                'omim': adjusted_weights.get('omim', 0.0)
            }
        else:
            # No redistribution needed (all sources available or all failed)
            ot_score = source_results['open_targets'][0] * weights['open_targets'] if source_results['open_targets'][0] is not None else 0.0
            chembl_score = source_results['chembl'][0] * weights['chembl'] if source_results['chembl'][0] is not None else 0.0
            string_score = source_results['string'][0] * weights['string'] if source_results['string'][0] is not None else 0.0
            expression_score = source_results['expression'][0] * weights['expression'] if source_results['expression'][0] is not None else 0.0
            reactome_score = source_results['reactome'][0] * weights['reactome'] if source_results['reactome'][0] is not None else 0.0
            omim_score = source_results['omim'][0] * weights['omim'] if source_results['omim'][0] is not None else 0.0

            # Use original weights (no redistribution)
            actual_weights_used = weights.copy()

        # UniProt deprecated - set to 0
        uniprot_score = 0.0

        total = ot_score + chembl_score + string_score + expression_score + reactome_score + omim_score

        # Calculate data completeness
        apis_succeeded = len(available_sources)
        data_completeness = apis_succeeded / 6.0

        # NOTE: With weight redistribution, total_score can still reach 100 even with missing sources
        # Confidence still considers completeness to flag cases with limited evidence
        confidence = self._determine_confidence(total, data_completeness)

        return {
            "open_targets_score": round(ot_score, 2),
            "chembl_score": round(chembl_score, 2),
            "uniprot_score": round(uniprot_score, 2),  # Always 0 now
            "omim_score": round(omim_score, 2),
            "string_score": round(string_score, 2),
            "expression_score": round(expression_score, 2),
            "reactome_score": round(reactome_score, 2),
            "total_score": round(total, 2),
            "data_completeness": round(data_completeness, 2),
            "confidence_level": confidence,
            "actual_weights_used": {
                "open_targets": round(actual_weights_used['open_targets'], 2),
                "chembl": round(actual_weights_used['chembl'], 2),
                "string": round(actual_weights_used['string'], 2),
                "expression": round(actual_weights_used['expression'], 2),
                "reactome": round(actual_weights_used['reactome'], 2),
                "omim": round(actual_weights_used['omim'], 2)
            }
        }

    def _score_open_targets(self, data: Dict) -> float:
        """
        Score Open Targets association (normalized 0-1 scale).
        Returns association_score directly (already 0-1).
        """
        association_score = data.get("association_score", 0.0)  # 0.0-1.0
        return association_score

    def _score_chembl(self, data: Dict) -> float:
        """
        Score ChEMBL approval status (normalized 0-1 scale).
        Phase 4 (approved) = 1.0, Phase 3 = 0.7, Phase 2 = 0.4, Phase 1 = 0.2
        """
        max_phase = data.get("max_phase", 0)
        if max_phase == 4:
            return 1.0
        elif max_phase == 3:
            return 0.7
        elif max_phase == 2:
            return 0.4
        elif max_phase == 1:
            return 0.2
        return 0.0

    def _score_omim(self, data: List[Dict]) -> float:
        """
        Score OMIM associations (normalized 0-1 scale).
        Caps at 2 associations = 1.0 (more gives diminishing returns).
        """
        if not data:
            return 0.0
        count = len(data)
        return min(count / 2.0, 1.0)

    def _score_string(self, data: Dict) -> float:
        """
        Score STRING PPI network proximity (normalized 0-1 scale).

        Scoring:
        - Direct interaction: 1.0
        - 1-hop distance: 0.67
        - 2-hop distance: 0.33
        - No connection: 0.0
        """
        if not data:
            return 0.0

        direct_interactions = data.get("direct_interactions", 0)
        network_distance = data.get("network_distance", 999)

        if direct_interactions > 0:
            return 1.0
        elif network_distance == 1:
            return 0.67
        elif network_distance == 2:
            return 0.33
        return 0.0

    def _score_expression(self, data: Dict) -> float:
        """
        Score expression alignment (normalized 0-1 scale).

        Now uses Open Targets expression data instead of Expression Atlas.
        Scoring based on:
        - Expression level in disease-relevant tissue
        - Alignment with drug mechanism (inhibitor/activator)
        """
        if not data:
            return 0.33  # Conservative neutral score when unknown

        expression_level = data.get("expression_level", "not_detected")
        drug_action_type = data.get("drug_action_type", "UNKNOWN").upper()
        tissue_specificity = data.get("tissue_specificity", False)

        # Calculate alignment score based on expression + mechanism
        alignment_score = self._calculate_expression_alignment(
            expression_level,
            drug_action_type
        )

        # Bonus for tissue specificity
        if tissue_specificity:
            alignment_score = min(alignment_score * 1.2, 1.0)

        return round(alignment_score, 2)

    def _calculate_expression_alignment(
        self,
        expression_level: str,
        drug_action_type: str
    ) -> float:
        """
        Calculate alignment between expression level and drug mechanism.

        Logic:
        - High expression + INHIBITOR = 1.0 (good: suppress overexpressed target)
        - Low/not_detected + ACTIVATOR = 1.0 (good: boost underexpressed target)
        - High + ACTIVATOR = 0.2 (bad: further activate overexpressed)
        - Low + INHIBITOR = 0.2 (bad: further suppress underexpressed)
        - Medium expression = 0.6 (somewhat favorable)
        - Unknown mechanism = 0.5 (neutral)
        """
        # Normalize action type
        inhibitory_actions = {"INHIBITOR", "ANTAGONIST", "BLOCKER", "INHIBITION", "NEGATIVE MODULATOR"}
        activating_actions = {"ACTIVATOR", "AGONIST", "OPENER", "ACTIVATION", "POSITIVE MODULATOR"}

        is_inhibitor = any(action in drug_action_type for action in inhibitory_actions)
        is_activator = any(action in drug_action_type for action in activating_actions)

        # Unknown mechanism
        if not is_inhibitor and not is_activator:
            return 0.5

        # High expression levels
        if expression_level == "high":
            if is_inhibitor:
                return 1.0  # Perfect: inhibit overexpressed target
            elif is_activator:
                return 0.2  # Misalignment: activate already high target

        # Low/not detected expression
        elif expression_level in ["low", "not_detected"]:
            if is_activator:
                return 1.0  # Perfect: activate underexpressed target
            elif is_inhibitor:
                return 0.2  # Misalignment: inhibit already low target

        # Medium expression - generally neutral/favorable
        elif expression_level == "medium":
            if is_inhibitor or is_activator:
                return 0.6  # Somewhat favorable

        return 0.5  # Default neutral

    def _score_reactome(self, data: Dict) -> float:
        """
        Score pathway overlap (normalized 0-1 scale).

        Uses Jaccard similarity of pathway sets:
        J = |intersection| / |union|

        Maps Jaccard to 0-1:
        - J > 0.5 → 1.0
        - J > 0.3 → 0.7
        - J > 0.1 → 0.4
        - J ≤ 0.1 → 0.0
        """
        if not data:
            return 0.0

        pathway_similarity = data.get("pathway_similarity", 0.0)  # Jaccard index 0.0-1.0

        if pathway_similarity > 0.5:
            return 1.0
        elif pathway_similarity > 0.3:
            return 0.7
        elif pathway_similarity > 0.1:
            return 0.4
        return 0.0

    def _determine_confidence(self, total_score: float, data_completeness: float) -> str:
        """Determine confidence level (updated thresholds for 100-point scale)"""
        if total_score >= 70 and data_completeness >= 0.67:
            return "HIGH"
        elif total_score >= 40 and data_completeness >= 0.50:
            return "MEDIUM"
        else:
            return "LOW"
