"""Integration tests for full search flow."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.orchestrator import SearchOrchestrator
from app.services.cache_service import CacheService


class TestSearchFlow:
    """Integration tests for complete search workflow."""

    @pytest.fixture
    async def orchestrator(self):
        """Create orchestrator with mocked cache."""
        cache = MagicMock(spec=CacheService)
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.generate_key = MagicMock(return_value="test_key")
        return SearchOrchestrator(cache)

    @pytest.mark.asyncio
    async def test_search_drug_candidates_diabetes_full_flow(self, orchestrator):
        """Test complete search flow for diabetes."""
        # Mock Open Targets response
        mock_ot_targets = [
            {
                "target_id": "ENSG00000171105",
                "gene_symbol": "INSR",
                "association_score": 0.9,
                "data_sources": [],
                "expressions": [
                    {
                        "tissue": {"id": "UBERON_0001264", "label": "pancreas"},
                        "rna": {"value": 5703, "level": 4}
                    }
                ]
            }
        ]

        # Mock ChEMBL response
        mock_chembl_drugs = [
            {
                "drug_name": "INSULIN HUMAN",
                "chembl_id": "CHEMBL1201631",
                "max_phase": 4,
                "molecule_type": "Protein",
                "mechanism": "Insulin receptor agonist",
                "action_type": "AGONIST"
            }
        ]

        # Mock OMIM response
        mock_omim_data = [
            {"omim_id": "147670", "gene_symbol": "INSR", "phenotype": "Diabetes"},
            {"omim_id": "147671", "gene_symbol": "INSR", "phenotype": "Insulin resistance"}
        ]

        # Mock STRING response
        mock_string_data = {
            "direct_interactions": 4,
            "network_distance": 0
        }

        # Mock Reactome response
        mock_reactome_data = {
            "shared_pathways": ["Insulin signaling", "Glucose metabolism"],
            "pathway_similarity": 0.4,
            "enriched_processes": ["Metabolism"],
            "target_pathway_count": 10,
            "disease_pathway_count": 12
        }

        with patch.object(orchestrator.open_targets, 'get_disease_targets',
                         return_value=mock_ot_targets), \
             patch.object(orchestrator.chembl, 'get_drugs_for_target',
                         return_value=mock_chembl_drugs), \
             patch.object(orchestrator.omim, 'get_gene_disease_associations',
                         return_value=mock_omim_data), \
             patch.object(orchestrator.string_db, 'get_protein_interactions',
                         return_value=mock_string_data), \
             patch.object(orchestrator.reactome, 'get_pathway_overlap',
                         return_value=mock_reactome_data):

            results = await orchestrator.search_drug_candidates("diabetes")

            # Verify results structure
            assert len(results) > 0
            candidate = results[0]

            # Verify all required fields present
            assert "drug_name" in candidate
            assert "chembl_id" in candidate
            assert "target_gene" in candidate
            assert "total_score" in candidate
            assert "confidence_level" in candidate
            assert "data_completeness" in candidate

            # Verify scoring
            assert 0 <= candidate["total_score"] <= 100
            assert candidate["data_completeness"] == 1.0  # All sources succeeded
            assert candidate["confidence_level"] in ["HIGH", "MEDIUM", "LOW"]

            # Verify metadata
            assert candidate["omim_associations"] == 2
            assert candidate["string_interactions"] == 4
            assert candidate["expression_level"] == "high"
            assert len(candidate["shared_pathways"]) == 2

    @pytest.mark.asyncio
    async def test_search_with_custom_weights(self, orchestrator):
        """Test search with custom scoring weights."""
        mock_ot_targets = [
            {
                "target_id": "ENSG00000171105",
                "gene_symbol": "INSR",
                "association_score": 0.8,
                "data_sources": [],
                "expressions": []
            }
        ]

        mock_chembl_drugs = [
            {
                "drug_name": "TEST_DRUG",
                "chembl_id": "CHEMBL123",
                "max_phase": 4,
                "molecule_type": "Small molecule",
                "mechanism": "Test mechanism",
                "action_type": "INHIBITOR"
            }
        ]

        clinical_weights = {
            "open_targets": 35,
            "chembl": 35,
            "string": 10,
            "expression": 10,
            "reactome": 5,
            "omim": 5
        }

        with patch.object(orchestrator.open_targets, 'get_disease_targets',
                         return_value=mock_ot_targets), \
             patch.object(orchestrator.chembl, 'get_drugs_for_target',
                         return_value=mock_chembl_drugs), \
             patch.object(orchestrator.omim, 'get_gene_disease_associations',
                         return_value=[]), \
             patch.object(orchestrator.string_db, 'get_protein_interactions',
                         return_value=None), \
             patch.object(orchestrator.reactome, 'get_pathway_overlap',
                         return_value=None):

            results = await orchestrator.search_drug_candidates("test", weights=clinical_weights)

            assert len(results) > 0
            candidate = results[0]

            # Verify custom weights were used
            assert "actual_weights_used" in candidate
            actual = candidate["actual_weights_used"]

            # With missing sources, weights should be redistributed
            assert actual["open_targets"] > 35  # Should be boosted
            assert actual["chembl"] > 35  # Should be boosted

    @pytest.mark.asyncio
    async def test_graceful_degradation_with_api_failures(self, orchestrator):
        """Test system continues working when some APIs fail."""
        mock_ot_targets = [
            {
                "target_id": "ENSG00000171105",
                "gene_symbol": "INSR",
                "association_score": 0.9,
                "data_sources": [],
                "expressions": []
            }
        ]

        mock_chembl_drugs = [
            {
                "drug_name": "TEST_DRUG",
                "chembl_id": "CHEMBL123",
                "max_phase": 4,
                "molecule_type": "Small molecule",
                "mechanism": "Test",
                "action_type": "UNKNOWN"
            }
        ]

        with patch.object(orchestrator.open_targets, 'get_disease_targets',
                         return_value=mock_ot_targets), \
             patch.object(orchestrator.chembl, 'get_drugs_for_target',
                         return_value=mock_chembl_drugs), \
             patch.object(orchestrator.omim, 'get_gene_disease_associations',
                         side_effect=Exception("OMIM API down")), \
             patch.object(orchestrator.string_db, 'get_protein_interactions',
                         side_effect=Exception("STRING API down")), \
             patch.object(orchestrator.reactome, 'get_pathway_overlap',
                         side_effect=Exception("Reactome API down")):

            results = await orchestrator.search_drug_candidates("test")

            # Should still return results despite 3 API failures
            assert len(results) > 0
            candidate = results[0]

            # Verify graceful degradation
            assert candidate["data_completeness"] == 2/6  # Only 2 of 6 sources
            assert candidate["omim_associations"] == 0
            assert candidate["string_interactions"] == 0
            assert len(candidate["shared_pathways"]) == 0

            # Total score should still be calculated with weight redistribution
            assert 0 <= candidate["total_score"] <= 100

    @pytest.mark.asyncio
    async def test_no_approved_drugs_found(self, orchestrator):
        """Test handling when no approved drugs found for targets."""
        mock_ot_targets = [
            {
                "target_id": "ENSG00000000001",
                "gene_symbol": "RARE_GENE",
                "association_score": 0.8,
                "data_sources": [],
                "expressions": []
            }
        ]

        with patch.object(orchestrator.open_targets, 'get_disease_targets',
                         return_value=mock_ot_targets), \
             patch.object(orchestrator.chembl, 'get_drugs_for_target',
                         return_value=[]):  # No drugs found

            results = await orchestrator.search_drug_candidates("rare_disease")

            # Should return empty list
            assert results == []

    @pytest.mark.asyncio
    async def test_cache_hit(self, orchestrator):
        """Test that cached results are returned."""
        cached_data = [
            {
                "drug_name": "CACHED_DRUG",
                "total_score": 85.0,
                "confidence_level": "HIGH"
            }
        ]

        orchestrator.cache.get = AsyncMock(return_value=cached_data)

        results = await orchestrator.search_drug_candidates("diabetes")

        # Should return cached data without calling APIs
        assert results == cached_data
        orchestrator.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_results_sorted_by_score(self, orchestrator):
        """Test that results are sorted by total_score descending."""
        mock_ot_targets = [
            {
                "target_id": "ENSG1",
                "gene_symbol": "GENE1",
                "association_score": 0.5,
                "data_sources": [],
                "expressions": []
            },
            {
                "target_id": "ENSG2",
                "gene_symbol": "GENE2",
                "association_score": 0.9,
                "data_sources": [],
                "expressions": []
            }
        ]

        mock_chembl_drugs_gene1 = [
            {"drug_name": "DRUG1", "chembl_id": "C1", "max_phase": 2,
             "molecule_type": "Small molecule", "mechanism": "Test", "action_type": "UNKNOWN"}
        ]

        mock_chembl_drugs_gene2 = [
            {"drug_name": "DRUG2", "chembl_id": "C2", "max_phase": 4,
             "molecule_type": "Small molecule", "mechanism": "Test", "action_type": "UNKNOWN"}
        ]

        async def mock_get_drugs(gene_symbol):
            if gene_symbol == "GENE1":
                return mock_chembl_drugs_gene1
            else:
                return mock_chembl_drugs_gene2

        with patch.object(orchestrator.open_targets, 'get_disease_targets',
                         return_value=mock_ot_targets), \
             patch.object(orchestrator.chembl, 'get_drugs_for_target',
                         side_effect=mock_get_drugs), \
             patch.object(orchestrator.omim, 'get_gene_disease_associations',
                         return_value=[]), \
             patch.object(orchestrator.string_db, 'get_protein_interactions',
                         return_value=None), \
             patch.object(orchestrator.reactome, 'get_pathway_overlap',
                         return_value=None):

            results = await orchestrator.search_drug_candidates("test")

            # DRUG2 should rank higher (better association + phase 4)
            assert len(results) >= 2
            assert results[0]["total_score"] >= results[1]["total_score"]
