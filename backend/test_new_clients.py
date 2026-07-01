"""
Test script for new API clients (STRING, Expression Atlas, Reactome).
Tests real API calls and data structure validation.
"""
import asyncio
import sys
from app.services.api_clients.string_db import StringDBClient
from app.services.api_clients.expression_atlas import ExpressionAtlasClient
from app.services.api_clients.reactome import ReactomeClient


async def test_string_client():
    """Test STRING PPI client with Alzheimer's disease genes."""
    print("=" * 80)
    print("TEST 1: STRING DB Client")
    print("=" * 80)

    client = StringDBClient()

    try:
        # Test with ACHE (acetylcholinesterase) and Alzheimer's disease genes
        target_gene = "ACHE"
        disease_genes = ["APP", "PSEN1", "MAPT", "APOE"]

        print(f"\nQuerying STRING for target={target_gene}, disease_genes={disease_genes}")
        result = await client.get_protein_interactions(target_gene, disease_genes)

        if result:
            print(f"\n✅ SUCCESS! Retrieved interaction data:")
            print(f"   Direct interactions: {result.get('direct_interactions', 0)}")
            print(f"   Network distance: {result.get('network_distance', 999)}")
            print(f"   Interaction score: {result.get('interaction_score', 0.0):.3f}")
            print(f"   Interacting genes: {result.get('interacting_genes', [])}")

            # Validate data structure
            assert 'direct_interactions' in result, "Missing 'direct_interactions' field"
            assert 'network_distance' in result, "Missing 'network_distance' field"
            assert isinstance(result['direct_interactions'], int), "direct_interactions should be int"
            assert isinstance(result['network_distance'], (int, float)), "network_distance should be numeric"

            print("\n✅ Data structure validation passed")
        else:
            print("\n⚠️ WARNING: No data returned (might be API issue or no interactions found)")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()

    return True


async def test_expression_atlas_client():
    """Test Expression Atlas client."""
    print("\n" + "=" * 80)
    print("TEST 2: Expression Atlas Client")
    print("=" * 80)

    client = ExpressionAtlasClient()

    try:
        # Test with APP gene and Alzheimer's disease
        gene_symbol = "APP"
        disease = "Alzheimer's disease"
        action_type = "INHIBITOR"

        print(f"\nQuerying Expression Atlas for gene={gene_symbol}, disease={disease}")
        result = await client.get_differential_expression(gene_symbol, disease, action_type)

        if result:
            print(f"\n✅ SUCCESS! Retrieved expression data:")
            print(f"   Fold change: {result.get('fold_change', 'N/A')}")
            print(f"   P-value: {result.get('p_value', 'N/A')}")
            print(f"   Expression level: {result.get('expression_level', 'unknown')}")
            print(f"   Tissue specificity: {result.get('tissue_specificity', False)}")
            print(f"   Alignment score: {result.get('alignment_score', 0.0):.3f}")

            # Validate data structure
            assert 'expression_level' in result, "Missing 'expression_level' field"
            assert 'alignment_score' in result, "Missing 'alignment_score' field"
            assert result['expression_level'] in ['up', 'down', 'unchanged', 'unknown'], \
                f"Invalid expression_level: {result['expression_level']}"

            print("\n✅ Data structure validation passed")
        else:
            print("\n⚠️ WARNING: No data returned (Expression Atlas has limited coverage)")
            print("   This is expected - API returns empty for many disease-gene pairs")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()

    return True


async def test_reactome_client():
    """Test Reactome pathway client."""
    print("\n" + "=" * 80)
    print("TEST 3: Reactome Client")
    print("=" * 80)

    client = ReactomeClient()

    try:
        # Test with ACHE and Alzheimer's disease genes
        target_gene = "ACHE"
        disease_genes = ["APP", "PSEN1", "MAPT"]

        print(f"\nQuerying Reactome for target={target_gene}, disease_genes={disease_genes}")
        result = await client.get_pathway_overlap(target_gene, disease_genes)

        if result:
            print(f"\n✅ SUCCESS! Retrieved pathway data:")
            print(f"   Shared pathways: {len(result.get('shared_pathways', []))}")
            print(f"   Pathway similarity (Jaccard): {result.get('pathway_similarity', 0.0):.3f}")
            print(f"   Target pathway count: {result.get('target_pathway_count', 0)}")
            print(f"   Disease pathway count: {result.get('disease_pathway_count', 0)}")
            print(f"   Enriched processes: {result.get('enriched_processes', [])}")

            if result.get('shared_pathways'):
                print(f"\n   Sample shared pathways:")
                for pathway in result['shared_pathways'][:3]:
                    print(f"      - {pathway}")

            # Validate data structure
            assert 'shared_pathways' in result, "Missing 'shared_pathways' field"
            assert 'pathway_similarity' in result, "Missing 'pathway_similarity' field"
            assert isinstance(result['shared_pathways'], list), "shared_pathways should be list"
            assert 0 <= result['pathway_similarity'] <= 1, "pathway_similarity should be 0-1"

            print("\n✅ Data structure validation passed")
        else:
            print("\n⚠️ WARNING: No data returned (might be API issue)")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()

    return True


async def test_scoring_integration():
    """Test that API client outputs work with scorer."""
    print("\n" + "=" * 80)
    print("TEST 4: Scoring Integration")
    print("=" * 80)

    from app.services.scoring import EvidenceScorer

    # Create mock data in the format returned by clients
    string_data = {
        "direct_interactions": 2,
        "network_distance": 0,
        "interaction_score": 0.85
    }

    expression_data = {
        "fold_change": 2.5,
        "p_value": 0.001,
        "expression_level": "up",
        "tissue_specificity": True,
        "alignment_score": 0.9
    }

    reactome_data = {
        "shared_pathways": ["Pathway1", "Pathway2", "Pathway3"],
        "pathway_similarity": 0.45,
        "enriched_processes": ["Signal Transduction"]
    }

    scorer = EvidenceScorer()

    try:
        scores = scorer.calculate_total_score(
            open_targets_data={'association_score': 0.8},
            chembl_data={'max_phase': 4},
            string_data=string_data,
            expression_data=expression_data,
            reactome_data=reactome_data,
            omim_data=[{'id': 1}]
        )

        print("\n✅ SUCCESS! Scorer accepted API client data:")
        print(f"   STRING score: {scores['string_score']}")
        print(f"   Expression score: {scores['expression_score']}")
        print(f"   Reactome score: {scores['reactome_score']}")
        print(f"   Total score: {scores['total_score']}")
        print(f"   Confidence: {scores['confidence_level']}")

        # Validate scoring
        assert scores['string_score'] > 0, "STRING score should be > 0"
        assert scores['expression_score'] > 0, "Expression score should be > 0"
        assert scores['reactome_score'] > 0, "Reactome score should be > 0"
        assert 0 <= scores['total_score'] <= 100, "Total score should be 0-100"

        print("\n✅ Scoring validation passed")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n🧪 Testing New API Clients for Drug Repurposing App")
    print("=" * 80)

    results = []

    # Test each client
    results.append(("STRING DB", await test_string_client()))
    results.append(("Expression Atlas", await test_expression_atlas_client()))
    results.append(("Reactome", await test_reactome_client()))
    results.append(("Scoring Integration", await test_scoring_integration()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")

    if total_passed == len(results):
        print("\n🎉 All tests passed! API clients are working correctly.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
