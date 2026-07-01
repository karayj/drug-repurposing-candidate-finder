from typing import List, Dict, Any
from .base_client import BaseAPIClient
from .circuit_breaker import CircuitBreaker


class ChEMBLClient(BaseAPIClient):
    def __init__(self):
        super().__init__("https://www.ebi.ac.uk/chembl/api/data")
        self.circuit_breaker = CircuitBreaker()

    async def get_drugs_for_target(self, gene_symbol: str) -> List[Dict[str, Any]]:
        async def _execute():
            print(f"ChEMBL: Searching for target with gene symbol: {gene_symbol}")

            # Search for target
            target_search = await self.get(
                "target/search.json",
                params={"q": gene_symbol, "format": "json"}
            )

            targets = target_search.get("targets", [])
            if not targets:
                print(f"ChEMBL: No targets found for {gene_symbol}")
                return []

            chembl_target_id = targets[0]["target_chembl_id"]
            print(f"ChEMBL: Found target {chembl_target_id}")

            # Get mechanisms for this target (approved drugs)
            try:
                mechanisms = await self.get(
                    "mechanism.json",
                    params={
                        "target_chembl_id": chembl_target_id,
                        "limit": 100
                    }
                )

                drugs = []
                seen_molecules = set()

                for mech in mechanisms.get("mechanisms", []):
                    mol_chembl_id = mech.get("molecule_chembl_id")
                    max_phase = mech.get("max_phase")
                    action_type = mech.get("action_type", "UNKNOWN")  # NEW: Extract action type

                    if not mol_chembl_id or mol_chembl_id in seen_molecules:
                        continue

                    # Only include phase 4 (approved) drugs
                    if max_phase == 4:
                        seen_molecules.add(mol_chembl_id)

                        # Fetch molecule name
                        try:
                            mol_data = await self.get(f"molecule/{mol_chembl_id}.json")
                            drug_name = mol_data.get("pref_name", mol_chembl_id)

                            drugs.append({
                                "chembl_id": mol_chembl_id,
                                "drug_name": drug_name,
                                "max_phase": max_phase,
                                "molecule_type": mol_data.get("molecule_type", "Unknown"),
                                "mechanism": mech.get("mechanism_of_action", "Unknown"),
                                "action_type": action_type  # NEW: Include action type
                            })

                            if len(drugs) <= 3:
                                print(f"ChEMBL: Found approved drug {drug_name} ({action_type})")
                        except Exception as e:
                            print(f"ChEMBL: Error fetching name for {mol_chembl_id}: {e}")
                            # Still add it even without the name
                            drugs.append({
                                "chembl_id": mol_chembl_id,
                                "drug_name": mol_chembl_id,
                                "max_phase": max_phase,
                                "molecule_type": "Unknown",
                                "mechanism": mech.get("mechanism_of_action", "Unknown"),
                                "action_type": action_type  # NEW: Include action type
                            })

                print(f"ChEMBL: Found {len(drugs)} approved drugs for {gene_symbol}")
                return drugs

            except Exception as e:
                print(f"ChEMBL: Error fetching mechanisms: {e}")
                return []

        try:
            return await self.circuit_breaker.call(_execute)
        except Exception as e:
            print(f"ChEMBL: Circuit breaker error: {e}")
            return []
