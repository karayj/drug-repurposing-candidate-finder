from typing import Dict, Any, Optional, List
from .base_client import BaseAPIClient
from .circuit_breaker import CircuitBreaker


class UniProtClient(BaseAPIClient):
    def __init__(self):
        super().__init__("https://rest.uniprot.org")
        self.circuit_breaker = CircuitBreaker()

    async def get_protein_info(self, gene_symbol: str) -> Optional[Dict[str, Any]]:
        async def _execute():
            response = await self.get(
                "uniprotkb/search",
                params={
                    "query": f"gene:{gene_symbol} AND organism_id:9606",
                    "format": "json",
                    "size": 1
                }
            )

            results = response.get("results", [])
            if not results:
                return None

            protein = results[0]

            return {
                "uniprot_id": protein.get("primaryAccession"),
                "protein_name": self._extract_protein_name(protein),
                "functions": self._extract_functions(protein),
                "pathways": self._extract_pathways(protein)
            }

        try:
            return await self.circuit_breaker.call(_execute)
        except Exception:
            return None

    def _extract_protein_name(self, protein: Dict) -> str:
        desc = protein.get("proteinDescription", {})
        rec_name = desc.get("recommendedName", {})
        full_name = rec_name.get("fullName", {})
        return full_name.get("value", "Unknown")

    def _extract_functions(self, protein: Dict) -> str:
        comments = protein.get("comments", [])
        for comment in comments:
            if comment.get("commentType") == "FUNCTION":
                texts = comment.get("texts", [])
                if texts:
                    return texts[0].get("value", "")
        return ""

    def _extract_pathways(self, protein: Dict) -> List[str]:
        pathways = []
        comments = protein.get("comments", [])
        for comment in comments:
            if comment.get("commentType") == "PATHWAY":
                texts = comment.get("texts", [])
                pathways.extend([t.get("value", "") for t in texts])
        return pathways[:3]
