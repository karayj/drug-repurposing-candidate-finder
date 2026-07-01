"""Unit tests for OMIM API client."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.api_clients.omim import OMIMClient


class TestOMIMClient:
    """Test suite for OMIMClient class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = OMIMClient()

    @pytest.mark.asyncio
    @patch('app.services.api_clients.omim.OMIMClient.get')
    async def test_get_gene_disease_associations_success(self, mock_get):
        """Test successful retrieval of gene-disease associations."""
        mock_response = {
            "omim": {
                "searchResponse": {
                    "entryList": [
                        {
                            "entry": {
                                "mimNumber": 147670,
                                "geneMap": {
                                    "geneSymbol": "INSR",
                                    "phenotypes": "Diabetes mellitus, type 2",
                                    "inheritance": "Autosomal dominant"
                                }
                            }
                        },
                        {
                            "entry": {
                                "mimNumber": 147671,
                                "geneMap": {
                                    "geneSymbol": "INSR",
                                    "phenotypes": "Insulin resistance",
                                    "inheritance": "Autosomal recessive"
                                }
                            }
                        }
                    ]
                }
            }
        }
        mock_get.return_value = mock_response

        result = await self.client.get_gene_disease_associations("INSR")

        assert len(result) == 2
        assert result[0]["omim_id"] == "147670"
        assert result[0]["gene_symbol"] == "INSR"
        assert result[0]["phenotype"] == "Diabetes mellitus, type 2"
        assert result[0]["inheritance"] == "Autosomal dominant"

    @pytest.mark.asyncio
    @patch('app.services.api_clients.omim.OMIMClient.get')
    async def test_get_gene_disease_associations_no_limit(self, mock_get):
        """Test that all associations are returned (no hardcoded limit)."""
        # Create 10 mock entries
        entries = [
            {
                "entry": {
                    "mimNumber": 147670 + i,
                    "geneMap": {
                        "geneSymbol": "TEST",
                        "phenotypes": f"Disease {i}",
                        "inheritance": "Autosomal dominant"
                    }
                }
            }
            for i in range(10)
        ]

        mock_response = {
            "omim": {
                "searchResponse": {
                    "entryList": entries
                }
            }
        }
        mock_get.return_value = mock_response

        result = await self.client.get_gene_disease_associations("TEST")

        # Should return all 10, not limited to 3
        assert len(result) == 10

    @pytest.mark.asyncio
    @patch('app.services.api_clients.omim.OMIMClient.get')
    async def test_get_gene_disease_associations_empty(self, mock_get):
        """Test handling of no associations found."""
        mock_response = {
            "omim": {
                "searchResponse": {
                    "entryList": []
                }
            }
        }
        mock_get.return_value = mock_response

        result = await self.client.get_gene_disease_associations("UNKNOWN")

        assert result == []

    @pytest.mark.asyncio
    @patch('app.services.api_clients.omim.OMIMClient.get')
    async def test_get_gene_disease_associations_malformed_response(self, mock_get):
        """Test handling of malformed API response."""
        mock_get.return_value = {}

        result = await self.client.get_gene_disease_associations("TEST")

        assert result == []

    @pytest.mark.asyncio
    @patch('app.services.api_clients.omim.OMIMClient.get')
    async def test_get_gene_disease_associations_api_error(self, mock_get):
        """Test handling of API errors."""
        mock_get.side_effect = Exception("API timeout")

        result = await self.client.get_gene_disease_associations("TEST")

        # Should return empty list on error (graceful degradation)
        assert result == []

    @pytest.mark.asyncio
    async def test_api_endpoint_called_correctly(self):
        """Test that correct API endpoint is called with parameters."""
        with patch.object(self.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "omim": {"searchResponse": {"entryList": []}}
            }

            await self.client.get_gene_disease_associations("BRCA1")

            # Verify API was called with correct path and params
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[0][0] == "search"  # Endpoint path
            assert call_args[1]["params"]["search"] == "BRCA1"
            assert call_args[1]["params"]["format"] == "json"
            assert call_args[1]["params"]["include"] == "geneMap"
