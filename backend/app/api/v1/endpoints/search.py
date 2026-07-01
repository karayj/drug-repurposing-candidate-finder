from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import SearchRequest, SearchResponse, DrugCandidate
from app.services.orchestrator import SearchOrchestrator
from app.services.cache_service import CacheService
from app.dependencies import get_cache

router = APIRouter()

# Preset weight profiles
WEIGHT_PROFILES = {
    'balanced': {
        'open_targets': 30.0,
        'chembl': 25.0,
        'string': 15.0,
        'expression': 15.0,
        'reactome': 10.0,
        'omim': 5.0
    },
    'clinical': {
        'open_targets': 35.0,
        'chembl': 35.0,
        'string': 10.0,
        'expression': 10.0,
        'reactome': 5.0,
        'omim': 5.0
    },
    'mechanistic': {
        'open_targets': 20.0,
        'chembl': 15.0,
        'string': 20.0,
        'expression': 25.0,
        'reactome': 15.0,
        'omim': 5.0
    },
    'expression': {
        'open_targets': 20.0,
        'chembl': 20.0,
        'string': 15.0,
        'expression': 30.0,
        'reactome': 10.0,
        'omim': 5.0
    },
}


@router.post("/search", response_model=SearchResponse)
async def search_drug_candidates(
    request: SearchRequest,
    cache: CacheService = Depends(get_cache)
):
    """
    Search for drug repurposing candidates with optional custom scoring weights.

    Can provide either:
    - `profile`: Use a preset weight profile ('balanced', 'clinical', 'mechanistic', 'expression')
    - `weights`: Specify exact weights (must sum to 100)
    - Neither: Uses default 'balanced' profile
    """
    if not request.disease_name or len(request.disease_name.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Disease name must be at least 3 characters"
        )

    # Determine which weights to use
    if request.weights:
        # User provided custom weights
        weights = request.weights.model_dump()
    elif request.profile:
        # User selected a preset profile
        weights = WEIGHT_PROFILES[request.profile]
    else:
        # Default to balanced profile
        weights = WEIGHT_PROFILES['balanced']

    orchestrator = SearchOrchestrator(cache)

    try:
        candidates = await orchestrator.search_drug_candidates(
            disease_name=request.disease_name,
            weights=weights
        )

        return SearchResponse(
            disease_name=request.disease_name,
            total_candidates=len(candidates),
            weights_used=weights,
            candidates=[DrugCandidate(**c) for c in candidates]
        )

    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing search: {str(e)}"
        )
    finally:
        await orchestrator.cleanup()
