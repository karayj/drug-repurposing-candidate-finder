"""Unit tests for Open Targets API client."""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.api_clients.open_targets import OpenTargetsClient


class TestOpenTargetsClient:
    """Test suite for OpenTargetsClient class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = OpenTargetsClient()

    @pytest.mark.asyncio
    @patch('app.services.api_clients.open_targets.OpenTargetsClient.post')
    async def test_get_disease_targets_success(self, mock_post):
        """Test successful retrieval of disease targets."""
        # Mock disease search response
        mock_post.return_value = {
            "data": {
                "search": {
                    "hits": [{"id": "EFO_0000400", "name": "diabetes mellitus"}]
                }
            }
        }

        # Mock with side_effect to return different responses
        async def mock_post_side_effect(url, data):
            if "search" in data.get("query", ""):
                return {
                    "data": {
                        "search": {
                            "hits": [{"id": "EFO_0000400", "name": "diabetes mellitus"}]
                        }
                    }
                }
            else:  # associatedTargets query
                return {
                    "data": {
                        "disease": {
                            "associatedTargets": {
                                "rows": [
                                    {
                                        "target": {
                                            "id": "ENSG00000171105",
                                            "approvedSymbol": "INSR",
                                            "expressions": [
                                                {
                                                    "tissue": {"id": "UBERON_0001264", "label": "pancreas"},
                                                    "rna": {"value": 5703, "level": 4},
                                                    "protein": {"level": 3}
                                                }
                                            ]
                                        },
                                        "score": 0.9
                                    }
                                ]
                            }
                        }
                    }
                }

        mock_post.side_effect = mock_post_side_effect

        result = await self.client.get_disease_targets("diabetes")

        assert len(result) == 1
        assert result[0]["target_id"] == "ENSG00000171105"
        assert result[0]["gene_symbol"] == "INSR"
        assert result[0]["association_score"] == 0.9
        assert "expressions" in result[0]
        assert len(result[0]["expressions"]) == 1

    def test_get_disease_relevant_expression_pancreas_diabetes(self):
        """Test expression extraction for diabetes-relevant tissue."""
        expressions = [
            {
                "tissue": {"id": "UBERON_0001264", "label": "pancreas"},
                "rna": {"value": 5703, "level": 4}
            },
            {
                "tissue": {"id": "UBERON_0002107", "label": "liver"},
                "rna": {"value": 2000, "level": 2}
            }
        ]

        result = self.client.get_disease_relevant_expression(expressions, "diabetes")

        assert result["expression_level"] == "high"
        assert result["relevant_tissue"] == "pancreas"
        assert result["rna_value"] == 5703
        assert result["tissue_specificity"] is True  # Pancreas is relevant to diabetes

    def test_get_disease_relevant_expression_brain_alzheimers(self):
        """Test expression extraction for Alzheimer's disease."""
        expressions = [
            {
                "tissue": {"id": "UBERON_0000955", "label": "brain"},
                "rna": {"value": 1234, "level": 3}
            },
            {
                "tissue": {"id": "UBERON_0002107", "label": "liver"},
                "rna": {"value": 500, "level": 1}
            }
        ]

        result = self.client.get_disease_relevant_expression(expressions, "alzheimer's disease")

        assert result["expression_level"] == "high"
        assert result["relevant_tissue"] == "brain"
        assert result["tissue_specificity"] is True

    def test_get_disease_relevant_expression_fallback_to_any_tissue(self):
        """Test fallback when no disease-relevant tissue found."""
        expressions = [
            {
                "tissue": {"id": "UBERON_0001630", "label": "muscle"},
                "rna": {"value": 800, "level": 2}
            }
        ]

        result = self.client.get_disease_relevant_expression(expressions, "diabetes")

        # Should fallback to muscle (non-relevant tissue)
        assert result["expression_level"] == "medium"
        assert result["relevant_tissue"] == "muscle"
        assert result["rna_value"] == 800
        assert result["tissue_specificity"] is False

    def test_get_disease_relevant_expression_no_data(self):
        """Test handling of empty expression data."""
        result = self.client.get_disease_relevant_expression([], "diabetes")
        assert result == {}

    def test_level_to_category(self):
        """Test expression level categorization."""
        assert self.client._level_to_category(-1) == "not_detected"
        assert self.client._level_to_category(0) == "low"
        assert self.client._level_to_category(1) == "medium"
        assert self.client._level_to_category(2) == "medium"
        assert self.client._level_to_category(3) == "high"
        assert self.client._level_to_category(4) == "high"

    def test_disease_tissue_mapping(self):
        """Test that disease-to-tissue mapping works correctly."""
        # Test diabetes mapping
        expressions_diabetes = [
            {"tissue": {"label": "pancreatic islet"}, "rna": {"level": 3}},
            {"tissue": {"label": "brain"}, "rna": {"level": 2}}
        ]
        result = self.client.get_disease_relevant_expression(expressions_diabetes, "diabetes mellitus")
        assert "pancreatic" in result["relevant_tissue"].lower() or "islet" in result["relevant_tissue"].lower()

        # Test cardiovascular mapping
        expressions_cardio = [
            {"tissue": {"label": "heart"}, "rna": {"level": 3}},
            {"tissue": {"label": "liver"}, "rna": {"level": 2}}
        ]
        result = self.client.get_disease_relevant_expression(expressions_cardio, "cardiovascular disease")
        assert result["relevant_tissue"].lower() == "heart"

        # Test cancer (generic - should work with any tissue)
        expressions_cancer = [
            {"tissue": {"label": "tumor"}, "rna": {"level": 3}},
            {"tissue": {"label": "normal tissue"}, "rna": {"level": 1}}
        ]
        result = self.client.get_disease_relevant_expression(expressions_cancer, "cancer")
        assert result["relevant_tissue"].lower() == "tumor"

    @pytest.mark.asyncio
    @patch('app.services.api_clients.open_targets.OpenTargetsClient.post')
    async def test_get_disease_targets_no_results(self, mock_post):
        """Test handling when no disease found."""
        mock_post.return_value = {
            "data": {
                "search": {
                    "hits": []
                }
            }
        }

        result = await self.client.get_disease_targets("unknown_disease_xyz")

        assert result == []

    @pytest.mark.asyncio
    @patch('app.services.api_clients.open_targets.OpenTargetsClient.post')
    async def test_get_disease_targets_graphql_error(self, mock_post):
        """Test handling of GraphQL errors."""
        mock_post.return_value = {
            "errors": [{"message": "Invalid query"}]
        }

        result = await self.client.get_disease_targets("test")

        assert result == []
