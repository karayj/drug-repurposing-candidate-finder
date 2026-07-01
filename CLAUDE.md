# Drug Repurposing Candidate Finder - MVP Implementation Plan

## Context

This plan addresses the need to build a full-stack drug repurposing application from scratch. The user needs a system where researchers can input a disease name and discover FDA-approved drugs that could potentially be repurposed for new therapeutic applications. 

The system will query four bioinformatics APIs (Open Targets, ChEMBL, UniProt, OMIM), cross-reference the data, calculate evidence-based scores, and present ranked drug candidates. This addresses the real-world challenge that drug development is expensive and time-consuming, while drug repurposing can accelerate bringing treatments to patients.

**Why this approach:** We're building a complete system with all four APIs, PostgreSQL for persistence, Redis for caching, and Docker Compose for orchestration. This provides a production-ready foundation while maintaining rapid development velocity for the MVP.

## Architecture Overview

### Tech Stack
- **Backend:** FastAPI (Python 3.10+) with async/await for concurrent API calls
- **Frontend:** Next.js 14 + TypeScript + React + Tailwind CSS
- **Database:** PostgreSQL 14+ with normalized schema
- **Caching:** Redis for API response caching (12-24hr TTL)
- **Deployment:** Docker Compose with 4 services (postgres, redis, backend, frontend)

### Data Flow
1. User enters disease name in web form
2. Frontend sends POST request to backend `/api/v1/search`
3. Backend orchestrator:
   - Queries Open Targets for disease-associated genes/proteins (targets)
   - For each target, queries ChEMBL for FDA-approved drugs
   - Enriches data in parallel: UniProt (pathway info) + OMIM (gene-disease validation)
   - Calculates multi-factor evidence score (0-100)
   - Stores results in PostgreSQL
   - Caches in Redis
4. Returns ranked drug candidates to frontend
5. Frontend displays results with evidence breakdown

### Evidence Scoring Algorithm
**Total Score: 0-100 points**
- Open Targets association score: 40 points (0-1 scale → 0-40)
- ChEMBL approval status: 30 points (FDA approved=30, Phase 3=20, Phase 2=10, Phase 1=5)
- UniProt pathway relevance: 20 points (based on pathway count + function description)
- OMIM gene-disease validation: 10 points (based on association count)

**Confidence Levels:**
- HIGH: score ≥70 AND ≥75% APIs succeeded
- MEDIUM: score ≥40 AND ≥50% APIs succeeded  
- LOW: everything else

### Resilience Strategy
- **Circuit breaker pattern** for each API client (5 failures → open circuit for 60s)
- **Retry logic** with exponential backoff (3 attempts, 0.5s → 10s)
- **Graceful degradation**: Continue with partial data if APIs fail
- **Timeout management**: Individual API timeout 30s, total request 60s
- **Caching**: Reduce API load and provide fallback when APIs are down

## Project Structure

```
drug-repurposing-candidate-finder/
├── backend/
│   ├── app/
│   │   ├── main.py                          # FastAPI app entry
│   │   ├── config.py                        # Environment settings
│   │   ├── database.py                      # SQLAlchemy session
│   │   ├── dependencies.py                  # DI for DB/cache
│   │   ├── api/v1/endpoints/
│   │   │   ├── search.py                    # POST /search endpoint
│   │   │   └── health.py                    # GET /health endpoint
│   │   ├── models/
│   │   │   ├── domain.py                    # SQLAlchemy ORM models
│   │   │   └── schemas.py                   # Pydantic request/response
│   │   ├── services/
│   │   │   ├── orchestrator.py              # Main search orchestration
│   │   │   ├── scoring.py                   # Evidence scoring logic
│   │   │   ├── cache_service.py             # Redis caching wrapper
│   │   │   └── api_clients/
│   │   │       ├── base_client.py           # HTTP client with retry
│   │   │       ├── circuit_breaker.py       # Circuit breaker implementation
│   │   │       ├── open_targets.py          # Open Targets GraphQL client
│   │   │       ├── chembl.py                # ChEMBL REST client
│   │   │       ├── uniprot.py               # UniProt REST client
│   │   │       └── omim.py                  # OMIM REST client
│   │   ├── repositories/
│   │   │   ├── base.py                      # Generic CRUD repository
│   │   │   ├── disease.py                   # Disease data access
│   │   │   ├── target.py                    # Target data access
│   │   │   ├── drug.py                      # Drug data access
│   │   │   └── evidence.py                  # Evidence data access
│   │   └── migrations/versions/
│   │       └── 001_initial_schema.py        # Alembic migration
│   ├── tests/
│   │   ├── unit/                            # Unit tests
│   │   └── integration/                     # Integration tests
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                     # Main search page
│   │   │   └── layout.tsx                   # Root layout
│   │   ├── components/
│   │   │   ├── SearchForm.tsx               # Disease input form
│   │   │   ├── ResultsList.tsx              # Results container
│   │   │   ├── ResultCard.tsx               # Individual drug card
│   │   │   ├── EvidenceBreakdown.tsx        # Score visualization
│   │   │   ├── LoadingSpinner.tsx           # Loading state
│   │   │   └── ErrorMessage.tsx             # Error display
│   │   ├── lib/
│   │   │   ├── api.ts                       # Backend API client
│   │   │   ├── types.ts                     # TypeScript types
│   │   │   └── utils.ts                     # Helper functions
│   │   └── hooks/
│   │       └── useSearch.ts                 # Search state hook
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── next.config.js
├── docker-compose.yml                        # Production Docker config
├── .env.example                              # Environment template
└── README.md                                 # Setup instructions
```

## Database Schema

### Core Tables

**diseases**
- `id` (PK), `disease_name`, `disease_id` (EFO ID), `description`, timestamps
- Stores disease records from searches

**targets**
- `id` (PK), `target_id` (Ensembl gene ID), `gene_symbol`, `protein_name`, `uniprot_id`, `pathways[]`, `functions`, timestamps
- Stores gene/protein targets

**drugs**
- `id` (PK), `chembl_id` (unique), `drug_name`, `max_phase` (1-4), `molecule_type`, `mechanism_of_action`, `indications[]`, timestamps
- Stores approved drugs from ChEMBL

**disease_target_associations**
- `id` (PK), `disease_id` (FK), `target_id` (FK), `association_score`, `data_sources[]`, timestamps
- Links diseases to targets with Open Targets scores

**drug_target_interactions**
- `id` (PK), `drug_id` (FK), `target_id` (FK), `interaction_type`, `activity_value`, `activity_units`, timestamps
- Links drugs to targets

**evidence_records**
- `id` (PK), `disease_id` (FK), `drug_id` (FK), `target_id` (FK)
- Score components: `open_targets_score`, `chembl_score`, `uniprot_score`, `omim_score`, `total_score`
- Metadata: `confidence_level`, `data_completeness`, `search_timestamp`
- Stores complete search results for caching and analytics

**omim_associations**
- `id` (PK), `omim_id`, `gene_symbol`, `disease_name`, `phenotype_description`, `inheritance_pattern`, timestamps
- Caches OMIM gene-disease relationships

**Indexes:** All foreign keys, disease_name, gene_symbol, chembl_id, total_score DESC, search_timestamp

## Implementation Steps

### Phase 1: Infrastructure Foundation
**Goal:** Set up Docker environment and verify service communication

1. Create project directory structure
2. Configure `docker-compose.yml`:
   - PostgreSQL service (port 5432)
   - Redis service (port 6379)
   - Backend service (port 8000)
   - Frontend service (port 3000)
3. Create backend `Dockerfile` with Python 3.11-slim
4. Create frontend `Dockerfile` with Node 18-alpine (multi-stage build)
5. Initialize FastAPI app with health check endpoint
6. Initialize Next.js app with TypeScript
7. Test: `docker-compose up` and verify all services start

**Files to create:**
- `docker-compose.yml`
- `backend/Dockerfile`
- `backend/app/main.py`
- `backend/requirements.txt` (fastapi, uvicorn, sqlalchemy, psycopg2-binary, alembic, pydantic, pydantic-settings, httpx, tenacity, redis)
- `frontend/Dockerfile`
- `frontend/package.json`
- `.env.example`

### Phase 2: Database Layer
**Goal:** Create schema and implement data access layer

1. Define SQLAlchemy ORM models in `app/models/domain.py`:
   - Disease, Target, Drug, DiseaseTargetAssociation, DrugTargetInteraction, EvidenceRecord, OMIMAssociation
2. Configure database connection in `app/database.py`
3. Create Alembic migration for initial schema: `alembic revision --autogenerate -m "initial schema"`
4. Implement base repository pattern in `app/repositories/base.py`
5. Implement specific repositories: disease.py, target.py, drug.py, evidence.py
6. Add `get_or_create()` methods to avoid duplicates
7. Test: Run migrations, verify tables created

**Critical files:**
- `backend/app/models/domain.py` - Complete ORM models with relationships
- `backend/app/database.py` - SQLAlchemy engine and session factory
- `backend/app/repositories/base.py` - Generic CRUD repository
- `backend/app/migrations/versions/001_initial_schema.py` - Alembic migration
- `backend/alembic.ini` - Alembic configuration

### Phase 3: API Client Infrastructure
**Goal:** Build robust HTTP client layer with resilience patterns

1. Create base HTTP client in `app/services/api_clients/base_client.py`:
   - Use `httpx.AsyncClient` with connection pooling
   - Implement retry logic with `tenacity` (3 attempts, exponential backoff)
   - Add request/response logging
   - Handle timeouts (30s default)

2. Implement circuit breaker in `app/services/api_clients/circuit_breaker.py`:
   - States: CLOSED, OPEN, HALF_OPEN
   - Failure threshold: 5 failures → OPEN
   - Timeout: 60s before attempting HALF_OPEN
   - Track failure count and timestamps

3. Create API client implementations:
   - **open_targets.py**: GraphQL queries for disease → targets
   - **chembl.py**: REST API for target → drugs, filter by max_phase=4 (approved)
   - **uniprot.py**: REST API for protein info by gene symbol
   - **omim.py**: REST API for gene-disease associations (graceful degradation if no API key)

4. Add unit tests with mocked responses

**Critical files:**
- `backend/app/services/api_clients/base_client.py` - HTTP client foundation
- `backend/app/services/api_clients/circuit_breaker.py` - Resilience pattern
- `backend/app/services/api_clients/open_targets.py` - GraphQL client
- `backend/app/services/api_clients/chembl.py` - Drug discovery client
- `backend/app/services/api_clients/uniprot.py` - Protein data client
- `backend/app/services/api_clients/omim.py` - Gene-disease client

### Phase 4: Business Logic Layer
**Goal:** Implement caching, scoring, and orchestration

1. Create cache service in `app/services/cache_service.py`:
   - Redis connection management
   - `get(key)` and `set(key, value, ttl)` methods
   - Key generation: `search:{disease_name_normalized}`
   - Default TTL: 43200s (12 hours)

2. Implement scoring algorithm in `app/services/scoring.py`:
   - `EvidenceScorer` class with `calculate_total_score()` method
   - Sub-methods: `_score_open_targets()`, `_score_chembl()`, `_score_uniprot()`, `_score_omim()`
   - Calculate data completeness (% of APIs that succeeded)
   - Determine confidence level based on score + completeness

3. Create orchestrator in `app/services/orchestrator.py`:
   - `SearchOrchestrator` class
   - Main method: `search_drug_candidates(disease_name)`
   - Flow:
     a. Check Redis cache
     b. Query Open Targets for targets (top 20)
     c. For each target: query ChEMBL for approved drugs
     d. Parallel enrichment: UniProt + OMIM
     e. Calculate scores for each drug-target pair
     f. Store in PostgreSQL
     g. Cache results
     h. Return top 50 candidates sorted by score

4. Add error handling with try/except blocks for graceful degradation
5. Add integration tests

**Critical files:**
- `backend/app/services/cache_service.py` - Redis caching wrapper
- `backend/app/services/scoring.py` - Evidence scoring algorithm (MOST CRITICAL)
- `backend/app/services/orchestrator.py` - Main business logic (MOST CRITICAL)

### Phase 5: Backend API Endpoints
**Goal:** Expose REST API for frontend consumption

1. Define Pydantic schemas in `app/models/schemas.py`:
   - `SearchRequest` (disease_name: str)
   - `DrugCandidate` (all fields from orchestrator response)
   - `SearchResponse` (disease_name, total_candidates, candidates[])

2. Implement search endpoint in `app/api/v1/endpoints/search.py`:
   - `POST /api/v1/search`
   - Validate disease_name (min 3 chars)
   - Call orchestrator
   - Return SearchResponse
   - Handle exceptions with HTTPException

3. Implement health endpoint in `app/api/v1/endpoints/health.py`:
   - `GET /api/v1/health`
   - Check database connection
   - Check Redis connection
   - Return status

4. Configure CORS middleware in `main.py`
5. Add dependency injection for DB session and cache service
6. Test with curl/httpx

**Critical files:**
- `backend/app/models/schemas.py` - Request/response models
- `backend/app/api/v1/endpoints/search.py` - Main search endpoint
- `backend/app/dependencies.py` - Dependency injection
- `backend/app/config.py` - Environment configuration

### Phase 6: Frontend Components
**Goal:** Build user interface for search and results display

1. Set up TypeScript types in `src/lib/types.ts`:
   - `DrugCandidate`, `SearchResponse` interfaces matching backend

2. Create API client in `src/lib/api.ts`:
   - `searchDrugCandidates(diseaseName)` function
   - Fetch from `${API_BASE_URL}/api/v1/search`
   - Error handling with custom `APIError` class

3. Create search hook in `src/hooks/useSearch.ts`:
   - State management: isLoading, error, results
   - `search()` function to call API
   - Return state and search function

4. Build components:
   - **SearchForm.tsx**: Input + submit button, min 3 chars validation
   - **ResultsList.tsx**: Container, displays total count
   - **ResultCard.tsx**: Drug name, ChEMBL link, target, mechanism, score, confidence badge
   - **EvidenceBreakdown.tsx**: Horizontal bar charts for score components
   - **LoadingSpinner.tsx**: Loading animation
   - **ErrorMessage.tsx**: Error display

5. Create main page in `src/app/page.tsx`:
   - Use `useSearch` hook
   - Render SearchForm, LoadingSpinner, ErrorMessage, ResultsList conditionally

6. Style with Tailwind CSS (gradient background, cards, badges, responsive)

**Critical files:**
- `frontend/src/lib/api.ts` - Backend API client
- `frontend/src/lib/types.ts` - TypeScript definitions
- `frontend/src/hooks/useSearch.ts` - Search state management
- `frontend/src/components/SearchForm.tsx` - User input
- `frontend/src/components/ResultCard.tsx` - Drug display
- `frontend/src/components/EvidenceBreakdown.tsx` - Score visualization
- `frontend/src/app/page.tsx` - Main application page

### Phase 7: Docker Configuration
**Goal:** Complete containerization and deployment setup

1. Configure backend Dockerfile:
   - Base: python:3.11-slim
   - Install system deps (gcc, postgresql-client)
   - Copy requirements.txt, install Python deps
   - Copy app code
   - Run as non-root user
   - CMD: run migrations + uvicorn

2. Configure frontend Dockerfile:
   - Multi-stage build (builder + runner)
   - Builder: install deps, build Next.js
   - Runner: copy built assets, run as non-root
   - CMD: npm start

3. Configure docker-compose.yml:
   - PostgreSQL with health check
   - Redis with health check
   - Backend depends on postgres + redis
   - Frontend depends on backend
   - Volume mounts for development
   - Environment variables from .env

4. Create .env.example with all required variables
5. Test full stack: `docker-compose up --build`

**Critical files:**
- `docker-compose.yml` - Service orchestration (MOST CRITICAL)
- `backend/Dockerfile` - Backend container
- `frontend/Dockerfile` - Frontend container
- `.env.example` - Environment template

### Phase 8: Documentation
**Goal:** Provide clear setup and usage instructions

1. Write comprehensive README.md:
   - Project description and purpose
   - Architecture overview
   - Prerequisites (Docker, Docker Compose)
   - Setup instructions:
     - Clone repo
     - Copy .env.example to .env
     - Optional: Add OMIM_API_KEY
     - Run `docker-compose up --build`
     - Access http://localhost:3000
   - Usage guide with example searches
   - API documentation link
   - Troubleshooting common issues

2. Create API.md:
   - Endpoint documentation
   - Request/response examples
   - Error codes

3. Create ARCHITECTURE.md:
   - System diagram
   - Data flow explanation
   - Scoring algorithm details
   - Technology choices rationale

**Files to create:**
- `README.md` - Main documentation
- `docs/API.md` - API documentation
- `docs/ARCHITECTURE.md` - Technical documentation

## Critical Files (Implementation Priority)

### Tier 1 - Core Foundation (Must implement first)
1. `backend/app/models/domain.py` - Database schema
2. `backend/app/services/api_clients/base_client.py` - HTTP client
3. `backend/app/services/api_clients/circuit_breaker.py` - Resilience
4. `backend/app/services/scoring.py` - Scoring algorithm
5. `backend/app/services/orchestrator.py` - Business logic
6. `docker-compose.yml` - Deployment config

### Tier 2 - API Integration (Implement in parallel)
7. `backend/app/services/api_clients/open_targets.py`
8. `backend/app/services/api_clients/chembl.py`
9. `backend/app/services/api_clients/uniprot.py`
10. `backend/app/services/api_clients/omim.py`

### Tier 3 - Data Access & API Layer
11. `backend/app/repositories/base.py` + specific repos
12. `backend/app/api/v1/endpoints/search.py`
13. `backend/app/services/cache_service.py`

### Tier 4 - Frontend
14. `frontend/src/lib/api.ts` + `frontend/src/lib/types.ts`
15. `frontend/src/hooks/useSearch.ts`
16. `frontend/src/components/SearchForm.tsx`
17. `frontend/src/components/ResultCard.tsx`
18. `frontend/src/app/page.tsx`

## Verification & Testing

### Unit Tests
```bash
cd backend
pytest tests/unit/ -v
```
- Test scoring algorithm with mock data
- Test circuit breaker state transitions
- Test API client retry logic
- Test cache key generation

### Integration Tests
```bash
cd backend
pytest tests/integration/ -v
```
- Test orchestrator with mocked API responses
- Test database CRUD operations
- Test search endpoint end-to-end

### Manual End-to-End Testing

1. **Start all services:**
   ```bash
   docker-compose up --build
   ```

2. **Verify services healthy:**
   - PostgreSQL: `docker exec -it drug-finder-db psql -U drugfinder -d drug_repurposing -c '\dt'`
   - Redis: `docker exec -it drug-finder-cache redis-cli PING`
   - Backend: `curl http://localhost:8000/api/v1/health`
   - Frontend: Open http://localhost:3000

3. **Test search flow:**
   - Search for "Alzheimer's disease"
   - Verify loading state appears
   - Verify results display within 30-60 seconds
   - Verify scores, targets, mechanisms displayed
   - Verify confidence badges (HIGH/MEDIUM/LOW)
   - Verify evidence breakdown bar charts

4. **Test caching:**
   - Search same disease again
   - Verify results return immediately (<1s)
   - Check Redis: `docker exec -it drug-finder-cache redis-cli KEYS "search:*"`

5. **Test error handling:**
   - Search with 1-2 character input (should show validation error)
   - Stop Redis: `docker stop drug-finder-cache`
   - Search (should work but slower, no caching)
   - Restart Redis: `docker start drug-finder-cache`

6. **Test graceful degradation:**
   - Remove OMIM_API_KEY from .env
   - Restart backend
   - Search should still work with reduced scores

7. **Test additional diseases:**
   - "diabetes mellitus"
   - "breast cancer"
   - "Parkinson's disease"
   - "rheumatoid arthritis"
   - Verify different drugs and scores for each

### Performance Validation

- Search latency: 20-60s for first search (fresh APIs)
- Cache hit latency: <1s
- Database query time: <100ms
- Frontend render: <500ms
- Memory usage: Backend <512MB, Frontend <256MB

### Expected Results

**Sample search: "Alzheimer's disease"**
- Expected candidates: 10-50 drugs
- Top candidates likely include:
  - Donepezil (acetylcholinesterase inhibitor)
  - Memantine (NMDA receptor antagonist)
  - Various beta-amyloid targeting compounds
- Scores should range 20-80
- Confidence levels mixed (HIGH for well-studied targets, MEDIUM/LOW for novel targets)

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://drugfinder:drugfinder123@postgres:5432/drug_repurposing
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_TTL=43200
OMIM_API_KEY=your_key_here (optional)
DEBUG=false
CORS_ORIGINS=["http://localhost:3000"]
HTTP_TIMEOUT=30
HTTP_MAX_RETRIES=3
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Known Limitations & Future Enhancements

### MVP Limitations
- No pagination (returns top 50 candidates only)
- No authentication/user accounts
- No search history
- No result export (CSV/PDF)
- Limited to approved drugs (max_phase=4)
- No clinical trial data
- No literature citations

### Post-MVP Enhancements
1. Add user authentication and saved searches
2. Implement pagination for large result sets
3. Add drug comparison feature
4. Integrate PubMed for literature support
5. Add ClinicalTrials.gov data
6. Implement background job queue for long-running searches
7. Add admin dashboard for monitoring
8. Deploy to cloud (AWS/GCP/Azure)
9. Add Prometheus metrics and Grafana dashboards
10. Implement GraphQL API as alternative to REST

## Risk Mitigation

### Technical Risks
- **API rate limits**: Mitigated by caching and circuit breaker
- **API downtime**: Mitigated by graceful degradation
- **Slow queries**: Mitigated by database indexes and Redis caching
- **Data inconsistency**: Mitigated by normalized schema and constraints

### Operational Risks
- **High latency on first search**: Expected behavior, user feedback via loading spinner
- **OMIM API requires key**: Graceful degradation, system works without it
- **Large result sets**: Limited to top 50 candidates initially
