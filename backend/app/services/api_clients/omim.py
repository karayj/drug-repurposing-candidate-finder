from typing import List, Dict, Any
from .base_client import BaseAPIClient
from .circuit_breaker import CircuitBreaker
from app.config import get_settings


class OMIMClient(BaseAPIClient):
    def __init__(self):
        settings = get_settings()
        super().__init__("https://api.omim.org/api")
        self.api_key = settings.OMIM_API_KEY
        self.circuit_breaker = CircuitBreaker()

    async def get_gene_disease_associations(self, gene_symbol: str) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []

        async def _execute():
            response = await self.get(
                "entry/search",
                params={
                    "search": gene_symbol,
                    "format": "json",
                    "apiKey": self.api_key,
                    "include": "geneMap"
                }
            )

            entries = response.get("omim", {}).get("searchResponse", {}).get("entryList", [])

            associations = []
            for entry in entries:
                gene_map = entry.get("entry", {}).get("geneMap", {})
                associations.append({
                    "omim_id": str(entry.get("entry", {}).get("mimNumber", "")),
                    "gene_symbol": gene_map.get("geneSymbol", ""),
                    "phenotype": gene_map.get("phenotypes", ""),
                    "inheritance": gene_map.get("inheritance", "")
                })

            return associations

        try:
            return await self.circuit_breaker.call(_execute)
        except Exception:
            return []
