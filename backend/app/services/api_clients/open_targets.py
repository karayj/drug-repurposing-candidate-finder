from typing import List, Dict, Any
from .base_client import BaseAPIClient
from .circuit_breaker import CircuitBreaker


class OpenTargetsClient(BaseAPIClient):
    def __init__(self):
        super().__init__("https://api.platform.opentargets.org/api/v4/graphql")
        self.circuit_breaker = CircuitBreaker()

    async def get_disease_targets(self, disease_name: str) -> List[Dict[str, Any]]:
        query = """
        query diseaseTargets($queryString: String!) {
          search(queryString: $queryString, entityNames: ["disease"]) {
            hits {
              id
              name
            }
          }
        }
        """

        async def _execute():
            try:
                response = await self.post("", {
                    "query": query,
                    "variables": {"queryString": disease_name}
                })

                if "errors" in response:
                    print(f"Open Targets GraphQL errors: {response['errors']}")
                    return []

                hits = response.get("data", {}).get("search", {}).get("hits", [])
                if not hits:
                    print(f"No disease hits found for: {disease_name}")
                    return []

                disease_id = hits[0]["id"]
                print(f"Found disease ID: {disease_id} for {disease_name}")
                return await self._get_associated_targets(disease_id)
            except Exception as e:
                print(f"Open Targets search error: {e}")
                return []

        return await self.circuit_breaker.call(_execute)

    async def _get_associated_targets(self, disease_id: str) -> List[Dict]:
        query = """
        query associatedTargets($diseaseId: String!) {
          disease(efoId: $diseaseId) {
            associatedTargets(page: {index: 0, size: 20}) {
              rows {
                target {
                  id
                  approvedSymbol
                  expressions {
                    tissue {
                      id
                      label
                    }
                    rna {
                      value
                      level
                    }
                    protein {
                      level
                    }
                  }
                }
                score
              }
            }
          }
        }
        """

        try:
            response = await self.post("", {
                "query": query,
                "variables": {"diseaseId": disease_id}
            })

            if "errors" in response:
                print(f"Open Targets associatedTargets errors: {response['errors']}")
                return []

            targets = response.get("data", {}).get("disease", {}).get("associatedTargets", {}).get("rows", [])
            print(f"Found {len(targets)} targets for disease {disease_id}")

            result = [
                {
                    "target_id": row["target"]["id"],
                    "gene_symbol": row["target"]["approvedSymbol"],
                    "association_score": row["score"],
                    "data_sources": [],
                    "expressions": row["target"].get("expressions", [])
                }
                for row in targets
            ]

            if result:
                print(f"First target: {result[0]['gene_symbol']}, expressions: {len(result[0].get('expressions', []))}")

            return result
        except Exception as e:
            print(f"Error getting associated targets: {e}")
            return []

    def get_disease_relevant_expression(
        self,
        expressions: List[Dict],
        disease_name: str
    ) -> Dict[str, Any]:
        """
        Extract expression data for disease-relevant tissues.

        Args:
            expressions: List of tissue expression data from Open Targets
            disease_name: Disease name to determine relevant tissues

        Returns:
            {
                "expression_level": str,  # "high", "medium", "low", "not_detected"
                "relevant_tissue": str,   # Tissue name
                "rna_value": float,       # TPM value
                "tissue_specificity": bool  # True if measured in disease-relevant tissue
            }
        """
        if not expressions:
            return {}

        # Map diseases to relevant tissues
        disease_tissue_map = {
            "alzheimer": ["brain", "cortex", "hippocampus", "frontal", "temporal"],
            "diabetes": ["pancreas", "islet", "liver", "adipose", "muscle"],
            "cancer": ["tumor"],
            "cardiovascular": ["heart", "cardiac", "vascular", "artery"],
            "arthritis": ["joint", "synovial", "cartilage"],
            "lung": ["lung", "bronch"],
            "kidney": ["kidney", "renal"],
            "liver": ["liver", "hepat"],
            "leukemia": ["blood", "bone marrow", "spleen"]
        }

        disease_lower = disease_name.lower()
        relevant_tissues = []

        # Find relevant tissue keywords
        for disease_key, tissues in disease_tissue_map.items():
            if disease_key in disease_lower:
                relevant_tissues = tissues
                break

        # Find highest expression in relevant tissues
        best_match = None
        highest_level = -1

        for expr in expressions:
            tissue_label = expr.get("tissue", {}).get("label", "").lower()
            rna_data = expr.get("rna", {})
            rna_level = rna_data.get("level", -1)
            rna_value = rna_data.get("value", 0)

            # Check if tissue is disease-relevant
            is_relevant = any(tissue_kw in tissue_label for tissue_kw in relevant_tissues) if relevant_tissues else False

            # Prioritize disease-relevant tissues
            if is_relevant and rna_level > highest_level:
                best_match = {
                    "expression_level": self._level_to_category(rna_level),
                    "relevant_tissue": expr["tissue"]["label"],
                    "rna_value": rna_value,
                    "tissue_specificity": True
                }
                highest_level = rna_level
            elif not best_match and rna_level > highest_level:
                # Fallback to any tissue if no relevant tissue found
                best_match = {
                    "expression_level": self._level_to_category(rna_level),
                    "relevant_tissue": expr["tissue"]["label"],
                    "rna_value": rna_value,
                    "tissue_specificity": False
                }
                highest_level = rna_level

        return best_match if best_match else {}

    def _level_to_category(self, level: int) -> str:
        """Convert numeric expression level to category."""
        if level == -1:
            return "not_detected"
        elif level == 0:
            return "low"
        elif level in [1, 2]:
            return "medium"
        else:  # 3, 4
            return "high"
