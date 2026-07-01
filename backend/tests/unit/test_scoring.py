"""Unit tests for scoring service."""
import pytest
from app.services.scoring import EvidenceScorer


class TestEvidenceScorer:
    """Test suite for EvidenceScorer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = EvidenceScorer()

    def test_calculate_total_score_all_sources(self):
        """Test scoring with all data sources available."""
        scores = self.scorer.calculate_total_score(
            open_targets_data={"association_score": 0.8},
            chembl_data={"max_phase": 4},
            uniprot_data=None,  # Deprecated
            omim_data=[{"id": 1}, {"id": 2}],
            string_data={"direct_interactions": 5, "network_distance": 0},
            expression_data={
                "expression_level": "high",
                "drug_action_type": "INHIBITOR",
                "tissue_specificity": True
            },
            reactome_data={"pathway_similarity": 0.6},
            weights=None  # Use defaults
        )

        # Verify all score components present
        assert "open_targets_score" in scores
        assert "chembl_score" in scores
        assert "string_score" in scores
        assert "expression_score" in scores
        assert "reactome_score" in scores
        assert "omim_score" in scores
        assert "total_score" in scores
        assert "confidence_level" in scores
        assert "data_completeness" in scores
        assert "actual_weights_used" in scores

        # Verify score ranges
        assert 0 <= scores["total_score"] <= 100
        assert scores["data_completeness"] == 1.0  # All 6 sources succeeded
        assert scores["confidence_level"] in ["HIGH", "MEDIUM", "LOW"]

        # Verify deprecated UniProt is 0
        assert scores["uniprot_score"] == 0.0

    def test_calculate_total_score_with_missing_sources(self):
        """Test scoring with some data sources unavailable."""
        scores = self.scorer.calculate_total_score(
            open_targets_data={"association_score": 0.9},
            chembl_data={"max_phase": 4},
            uniprot_data=None,
            omim_data=None,  # Missing
            string_data=None,  # Missing
            expression_data=None,  # Missing
            reactome_data=None,  # Missing
            weights=None
        )

        # Should still work with partial data
        assert 0 <= scores["total_score"] <= 100
        assert abs(scores["data_completeness"] - 2/6) < 0.01  # Only 2 of 6 sources
        assert scores["omim_score"] == 0.0
        assert scores["string_score"] == 0.0
        assert scores["expression_score"] == 0.0
        assert scores["reactome_score"] == 0.0

    def test_weight_redistribution_one_source_missing(self):
        """Test weights redistribute when one source unavailable."""
        scores = self.scorer.calculate_total_score(
            open_targets_data={"association_score": 1.0},  # Perfect
            chembl_data={"max_phase": 4},  # Perfect
            string_data={"direct_interactions": 5},  # Perfect
            expression_data=None,  # MISSING (15 pts)
            reactome_data={"pathway_similarity": 0.6},  # Perfect
            omim_data=[{"id": 1}, {"id": 2}],  # Perfect
            weights={"open_targets": 30, "chembl": 25, "string": 15,
                    "expression": 15, "reactome": 10, "omim": 5}
        )

        # With redistribution, should still reach 100
        assert scores["total_score"] == 100.0
        assert abs(scores["data_completeness"] - 5/6) < 0.01

        # Verify weights were redistributed
        actual_weights = scores["actual_weights_used"]
        assert actual_weights["expression"] == 0.0  # Missing source gets 0
        assert actual_weights["open_targets"] > 30  # Should be boosted
        assert actual_weights["chembl"] > 25  # Should be boosted

        # Total weights should sum to 100
        total_weight = sum(actual_weights.values())
        assert abs(total_weight - 100.0) < 0.01

    def test_weight_redistribution_multiple_sources_missing(self):
        """Test redistribution with multiple missing sources."""
        scores = self.scorer.calculate_total_score(
            open_targets_data={"association_score": 1.0},
            chembl_data={"max_phase": 4},
            string_data=None,  # MISSING (15)
            expression_data=None,  # MISSING (15)
            reactome_data=None,  # MISSING (10)
            omim_data=[{"id": 1}, {"id": 2}],
            weights={"open_targets": 30, "chembl": 25, "string": 15,
                    "expression": 15, "reactome": 10, "omim": 5}
        )

        # 40 points to redistribute among 3 sources
        assert scores["total_score"] == 100.0
        assert scores["data_completeness"] == 3/6

        actual_weights = scores["actual_weights_used"]
        # Missing sources get 0
        assert actual_weights["string"] == 0.0
        assert actual_weights["expression"] == 0.0
        assert actual_weights["reactome"] == 0.0

        # Available sources boosted significantly
        assert actual_weights["open_targets"] == 50.0  # 30 + (40 * 30/60)
        assert abs(actual_weights["chembl"] - 41.67) < 0.1  # 25 + (40 * 25/60)
        assert abs(actual_weights["omim"] - 8.33) < 0.1  # 5 + (40 * 5/60)

    def test_custom_weights_validation(self):
        """Test custom weights must sum to 100."""
        invalid_weights = {
            "open_targets": 50,
            "chembl": 30,
            "string": 10,
            "expression": 10,
            "reactome": 10,
            "omim": 5  # Sum = 115
        }

        with pytest.raises(ValueError, match="must sum to 100"):
            self.scorer.calculate_total_score(
                open_targets_data={"association_score": 0.5},
                weights=invalid_weights
            )

    def test_custom_weights_applied_correctly(self):
        """Test custom weights change final scores."""
        # Clinical focus profile (high weight on OT and ChEMBL)
        clinical_weights = {
            "open_targets": 35,
            "chembl": 35,
            "string": 10,
            "expression": 10,
            "reactome": 5,
            "omim": 5
        }

        scores = self.scorer.calculate_total_score(
            open_targets_data={"association_score": 0.8},  # 0.8 * 35 = 28
            chembl_data={"max_phase": 4},  # 1.0 * 35 = 35
            string_data={"direct_interactions": 5},  # 1.0 * 10 = 10
            expression_data={
                "expression_level": "high",
                "drug_action_type": "INHIBITOR",
                "tissue_specificity": False
            },  # 1.0 * 10 = 10
            reactome_data={"pathway_similarity": 0.6},  # 1.0 * 5 = 5
            omim_data=[{"id": 1}],  # 0.5 * 5 = 2.5
            weights=clinical_weights
        )

        # Open Targets and ChEMBL should dominate
        assert scores["open_targets_score"] == 28.0
        assert scores["chembl_score"] == 35.0
        assert scores["string_score"] == 10.0
        assert abs(scores["total_score"] - 90.5) < 0.5

    def test_score_open_targets(self):
        """Test Open Targets scoring (0-1 normalized)."""
        # Perfect association
        assert self.scorer._score_open_targets({"association_score": 1.0}) == 1.0

        # Medium association
        assert self.scorer._score_open_targets({"association_score": 0.5}) == 0.5

        # No association
        assert self.scorer._score_open_targets({"association_score": 0.0}) == 0.0

    def test_score_chembl(self):
        """Test ChEMBL approval status scoring."""
        # FDA approved (Phase 4)
        assert self.scorer._score_chembl({"max_phase": 4}) == 1.0

        # Phase 3
        assert self.scorer._score_chembl({"max_phase": 3}) == 0.7

        # Phase 2
        assert self.scorer._score_chembl({"max_phase": 2}) == 0.4

        # Phase 1
        assert self.scorer._score_chembl({"max_phase": 1}) == 0.2

        # No phase data
        assert self.scorer._score_chembl({"max_phase": 0}) == 0.0

    def test_score_omim(self):
        """Test OMIM associations scoring."""
        # No associations
        assert self.scorer._score_omim([]) == 0.0
        assert self.scorer._score_omim(None) == 0.0

        # 1 association
        assert self.scorer._score_omim([{"id": 1}]) == 0.5

        # 2 associations (max score)
        assert self.scorer._score_omim([{"id": 1}, {"id": 2}]) == 1.0

        # More than 2 (capped at 1.0)
        assert self.scorer._score_omim([{"id": 1}, {"id": 2}, {"id": 3}]) == 1.0

    def test_score_string(self):
        """Test STRING PPI network scoring."""
        # Direct interaction
        assert self.scorer._score_string({
            "direct_interactions": 5,
            "network_distance": 0
        }) == 1.0

        # 1-hop distance
        assert self.scorer._score_string({
            "direct_interactions": 0,
            "network_distance": 1
        }) == 0.67

        # 2-hop distance
        assert self.scorer._score_string({
            "direct_interactions": 0,
            "network_distance": 2
        }) == 0.33

        # No connection
        assert self.scorer._score_string({
            "direct_interactions": 0,
            "network_distance": 999
        }) == 0.0

        # No data
        assert self.scorer._score_string(None) == 0.0

    def test_score_expression_alignment(self):
        """Test expression-mechanism alignment scoring."""
        # Perfect alignment: high expression + inhibitor
        score = self.scorer._score_expression({
            "expression_level": "high",
            "drug_action_type": "INHIBITOR",
            "tissue_specificity": False
        })
        assert score == 1.0

        # Perfect alignment: low expression + activator
        score = self.scorer._score_expression({
            "expression_level": "low",
            "drug_action_type": "ACTIVATOR",
            "tissue_specificity": False
        })
        assert score == 1.0

        # Misalignment: high expression + activator
        score = self.scorer._score_expression({
            "expression_level": "high",
            "drug_action_type": "ACTIVATOR",
            "tissue_specificity": False
        })
        assert score == 0.2

        # Misalignment: low expression + inhibitor
        score = self.scorer._score_expression({
            "expression_level": "low",
            "drug_action_type": "INHIBITOR",
            "tissue_specificity": False
        })
        assert score == 0.2

        # Medium expression
        score = self.scorer._score_expression({
            "expression_level": "medium",
            "drug_action_type": "INHIBITOR",
            "tissue_specificity": False
        })
        assert score == 0.6

        # Unknown mechanism
        score = self.scorer._score_expression({
            "expression_level": "high",
            "drug_action_type": "UNKNOWN",
            "tissue_specificity": False
        })
        assert score == 0.5

    def test_score_expression_tissue_specificity_bonus(self):
        """Test tissue specificity bonus for expression."""
        # With tissue specificity (20% bonus)
        score_with_bonus = self.scorer._score_expression({
            "expression_level": "high",
            "drug_action_type": "INHIBITOR",
            "tissue_specificity": True
        })
        # 1.0 * 1.2 = 1.2, capped at 1.0
        assert score_with_bonus == 1.0

        # Lower base score with bonus
        score_with_bonus = self.scorer._score_expression({
            "expression_level": "medium",
            "drug_action_type": "INHIBITOR",
            "tissue_specificity": True
        })
        # 0.6 * 1.2 = 0.72
        assert score_with_bonus == 0.72

    def test_score_expression_no_data(self):
        """Test expression scoring with missing data."""
        score = self.scorer._score_expression(None)
        assert score == 0.33  # Conservative neutral score

    def test_score_reactome(self):
        """Test Reactome pathway overlap scoring."""
        # High overlap (Jaccard > 0.5)
        assert self.scorer._score_reactome({"pathway_similarity": 0.6}) == 1.0

        # Moderate overlap (0.3 < Jaccard <= 0.5)
        assert self.scorer._score_reactome({"pathway_similarity": 0.4}) == 0.7

        # Low overlap (0.1 < Jaccard <= 0.3)
        assert self.scorer._score_reactome({"pathway_similarity": 0.2}) == 0.4

        # Minimal overlap
        assert self.scorer._score_reactome({"pathway_similarity": 0.05}) == 0.0

        # No data
        assert self.scorer._score_reactome(None) == 0.0

    def test_confidence_levels(self):
        """Test confidence level determination."""
        # HIGH confidence
        scores_high = self.scorer.calculate_total_score(
            open_targets_data={"association_score": 0.9},
            chembl_data={"max_phase": 4},
            string_data={"direct_interactions": 5},
            expression_data={"expression_level": "high", "drug_action_type": "INHIBITOR"},
            reactome_data={"pathway_similarity": 0.6},
            omim_data=[{"id": 1}, {"id": 2}]
        )
        # Total ~95, completeness 1.0
        assert scores_high["confidence_level"] == "HIGH"

        # MEDIUM confidence (moderate score)
        scores_medium = self.scorer.calculate_total_score(
            open_targets_data={"association_score": 0.5},
            chembl_data={"max_phase": 2},
            string_data={"network_distance": 2},
            expression_data={"expression_level": "medium", "drug_action_type": "UNKNOWN"},
            reactome_data={"pathway_similarity": 0.2},
            omim_data=None
        )
        # Lower score but good completeness
        assert scores_medium["confidence_level"] in ["MEDIUM", "LOW"]

        # LOW confidence (low completeness)
        scores_low = self.scorer.calculate_total_score(
            open_targets_data={"association_score": 0.3},
            chembl_data={"max_phase": 1},
            string_data=None,
            expression_data=None,
            reactome_data=None,
            omim_data=None
        )
        assert scores_low["confidence_level"] == "LOW"

    def test_calculate_expression_alignment_action_types(self):
        """Test different drug action type mappings."""
        # Inhibitory actions
        for action in ["INHIBITOR", "ANTAGONIST", "BLOCKER", "NEGATIVE MODULATOR"]:
            score = self.scorer._calculate_expression_alignment("high", action)
            assert score == 1.0, f"Failed for {action}"

        # Activating actions
        for action in ["ACTIVATOR", "AGONIST", "OPENER", "POSITIVE MODULATOR"]:
            score = self.scorer._calculate_expression_alignment("low", action)
            assert score == 1.0, f"Failed for {action}"

        # Unknown/unmapped action
        score = self.scorer._calculate_expression_alignment("high", "MODULATOR")
        assert score == 0.5  # Neutral

    def test_not_detected_expression(self):
        """Test handling of not detected expression."""
        # Not detected + activator (good: boost underexpressed)
        score = self.scorer._score_expression({
            "expression_level": "not_detected",
            "drug_action_type": "ACTIVATOR",
            "tissue_specificity": False
        })
        assert score == 1.0

        # Not detected + inhibitor (bad: further suppress)
        score = self.scorer._score_expression({
            "expression_level": "not_detected",
            "drug_action_type": "INHIBITOR",
            "tissue_specificity": False
        })
        assert score == 0.2
