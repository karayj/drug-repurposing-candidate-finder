from typing import List, Dict, Any
from .base_client import BaseAPIClient
from .circuit_breaker import CircuitBreaker


class StringDBClient(BaseAPIClient):
    """
    Client for STRING protein-protein interaction database.
    Queries network proximity between drug targets and disease proteins.
    """

    def __init__(self):
        super().__init__("https://string-db.org/api")
        self.circuit_breaker = CircuitBreaker()

    async def get_protein_interactions(
        self,
        target_gene: str,
        disease_genes: List[str]
    ) -> Dict[str, Any]:
        """
        Get protein-protein interaction network proximity.

        Args:
            target_gene: Drug target gene symbol (e.g., "ACHE")
            disease_genes: List of disease-associated gene symbols (e.g., ["APP", "PSEN1"])

        Returns:
            {
                "direct_interactions": int,  # Count of direct interactions with disease proteins
                "network_distance": float,    # Shortest path length (0=direct, 1=1-hop, 2=2-hop, 999=no connection)
                "interaction_score": float,   # STRING combined confidence score (0.4-1.0)
                "interacting_genes": List[str] # Disease genes that interact
            }
        """
        async def _execute():
            print(f"STRING: Querying network for target={target_gene}, disease_genes={disease_genes[:3]}...")

            # Combine target and disease genes for network query
            all_genes = [target_gene] + disease_genes
            identifiers = "%0d".join(all_genes)  # STRING uses %0d as separator

            try:
                # Query STRING network endpoint
                response = await self.get(
                    "json/network",
                    params={
                        "identifiers": identifiers,
                        "species": 9606,  # Homo sapiens
                        "required_score": 400,  # Medium confidence (0-1000 scale)
                        "limit": 500  # Max interactions to return
                    }
                )

                if not response:
                    print(f"STRING: No network data returned for {target_gene}")
                    return {}

                # Parse interactions to find connections between target and disease genes
                direct_interactions = []
                all_interactions = {}

                for interaction in response:
                    gene_a = interaction.get("preferredName_A", "")
                    gene_b = interaction.get("preferredName_B", "")
                    score = interaction.get("score", 0.0)

                    # Build adjacency list for network distance calculation
                    if gene_a not in all_interactions:
                        all_interactions[gene_a] = []
                    if gene_b not in all_interactions:
                        all_interactions[gene_b] = []
                    all_interactions[gene_a].append((gene_b, score))
                    all_interactions[gene_b].append((gene_a, score))

                    # Check for direct interactions between target and disease genes
                    if (gene_a == target_gene and gene_b in disease_genes) or \
                       (gene_b == target_gene and gene_a in disease_genes):
                        disease_gene = gene_b if gene_a == target_gene else gene_a
                        direct_interactions.append({
                            "gene": disease_gene,
                            "score": score
                        })

                # Calculate network distance using BFS
                network_distance = self._calculate_network_distance(
                    target_gene,
                    disease_genes,
                    all_interactions
                )

                # Calculate average interaction score
                avg_score = 0.0
                if direct_interactions:
                    avg_score = sum(i["score"] for i in direct_interactions) / len(direct_interactions)

                result = {
                    "direct_interactions": len(direct_interactions),
                    "network_distance": network_distance,
                    "interaction_score": avg_score,
                    "interacting_genes": [i["gene"] for i in direct_interactions]
                }

                print(f"STRING: Found {len(direct_interactions)} direct interactions, distance={network_distance}")
                return result

            except Exception as e:
                print(f"STRING: Error querying network: {e}")
                return {}

        try:
            return await self.circuit_breaker.call(_execute)
        except Exception as e:
            print(f"STRING: Circuit breaker error: {e}")
            return {}

    def _calculate_network_distance(
        self,
        target: str,
        disease_genes: List[str],
        adjacency: Dict[str, List[tuple]]
    ) -> float:
        """
        Calculate shortest path distance from target to any disease gene using BFS.

        Returns:
            0 = direct interaction
            1 = 1-hop distance (shared partner)
            2 = 2-hop distance
            999 = no connection within 2 hops
        """
        if target not in adjacency:
            return 999

        # Check for direct connections (distance 0)
        direct_neighbors = [neighbor for neighbor, score in adjacency[target]]
        for disease_gene in disease_genes:
            if disease_gene in direct_neighbors:
                return 0

        # BFS for distance 1 (shared partner) and distance 2
        visited = {target}
        queue = [(target, 0)]  # (gene, distance)

        while queue:
            current_gene, distance = queue.pop(0)

            if distance >= 2:  # Only search up to 2-hop
                continue

            if current_gene not in adjacency:
                continue

            for neighbor, score in adjacency[current_gene]:
                if neighbor in visited:
                    continue

                visited.add(neighbor)

                # Check if this neighbor is a disease gene
                if neighbor in disease_genes:
                    return distance + 1

                # Add to queue for further exploration
                if distance + 1 < 2:
                    queue.append((neighbor, distance + 1))

        return 999  # No connection within 2 hops
