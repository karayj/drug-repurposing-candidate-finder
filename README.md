# Drug Repurposing Candidate Finder

A full-stack application for discovering FDA-approved drugs that may be repurposed for new therapeutic applications. The system queries multiple bioinformatics APIs (Open Targets, ChEMBL, UniProt, OMIM), calculates evidence-based scores, and presents ranked drug candidates.

## Features

- **Multi-API Integration**: Queries Open Targets, ChEMBL, UniProt, and OMIM for comprehensive drug-disease-target data
- **Evidence-Based Scoring**: Multi-factor algorithm (0-100 scale) combining association scores, approval status, pathway relevance, and gene-disease validation
- **Intelligent Caching**: Redis-backed caching reduces API load and improves response times
- **Resilient Architecture**: Circuit breaker pattern and retry logic for reliable API communication
- **Modern UI**: Next.js frontend with real-time search, interactive result cards, and visual evidence breakdowns
- **Docker Deployment**: Complete Docker Compose setup for easy local deployment

## Architecture

### Tech Stack

- **Backend**: FastAPI (Python 3.11) with async/await
- **Frontend**: Next.js 14 + TypeScript + React + Tailwind CSS
- **Database**: PostgreSQL 14+
- **Caching**: Redis 7
- **Deployment**: Docker Compose

### Evidence Scoring Algorithm

Total Score: **0-100 points**

- **Open Targets** (40 points): Disease-target association strength
- **ChEMBL** (30 points): Drug approval status (FDA approved = 30, Phase 3 = 20, etc.)
- **UniProt** (20 points): Pathway relevance and protein function information
- **OMIM** (10 points): Gene-disease association validation

**Confidence Levels**:
- **HIGH**: Score ≥70 AND ≥75% APIs succeeded
- **MEDIUM**: Score ≥40 AND ≥50% APIs succeeded
- **LOW**: All other cases

## Prerequisites

- Docker Desktop (Mac/Windows) or Docker + Docker Compose (Linux)
- 8GB RAM minimum (16GB recommended)
- Internet connection for API access

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd drug-repurposing-candidate-finder
```

### 2. Copy SSL Certificates (RAND Users Only)

If you're on the RAND corporate network, copy the SSL certificates:

```bash
cp /Users/Shared/RANDCerts/RAND_PKI_Root.pem backend/
cp /Users/Shared/RANDCerts/RAND_PKI_Chain.pem backend/
```

> **Note**: These certificates are required for pip to download packages through RAND's SSL infrastructure. They are already configured in the Dockerfile.

### 3. Set Up Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Optional: Add OMIM API key to .env for enhanced results
# Register at https://omim.org/api
# OMIM_API_KEY=your_key_here
```

### 3. Start All Services

```bash
docker-compose up --build
```

This command will:
- Build backend and frontend Docker images
- Start PostgreSQL and Redis containers
- Run database migrations
- Start the FastAPI backend on port 8000
- Start the Next.js frontend on port 3000

### 4. Access the Application

Open your browser and navigate to:

**Frontend**: [http://localhost:3000](http://localhost:3000)

**Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)

### 5. Test the Application

Try searching for:
- "Alzheimer's disease"
- "diabetes mellitus"
- "breast cancer"
- "Parkinson's disease"
- "rheumatoid arthritis"

**Note**: First searches take 30-60 seconds as the system queries multiple APIs. Subsequent searches for the same disease are cached and return instantly.

## Usage Guide

1. **Enter a Disease Name**: Type at least 3 characters (e.g., "diabetes")
2. **Click Search**: The system queries bioinformatics databases
3. **View Results**: Drug candidates are ranked by evidence score
4. **Explore Details**: Each card shows:
   - Drug name and ChEMBL ID (clickable link)
   - Total evidence score (0-100)
   - Confidence level badge (HIGH/MEDIUM/LOW)
   - Target gene and mechanism of action
   - Evidence breakdown by source
   - Associated biological pathways
   - OMIM gene-disease associations

## API Endpoints

### Search for Drug Candidates

```bash
POST /api/v1/search
Content-Type: application/json

{
  "disease_name": "Alzheimer's disease"
}
```

**Response**:
```json
{
  "disease_name": "Alzheimer's disease",
  "total_candidates": 25,
  "candidates": [
    {
      "drug_name": "Donepezil",
      "chembl_id": "CHEMBL502",
      "target_gene": "ACHE",
      "target_id": "ENSG00000087085",
      "mechanism": "Acetylcholinesterase inhibitor",
      "open_targets_score": 32.5,
      "chembl_score": 30.0,
      "uniprot_score": 15.0,
      "omim_score": 5.0,
      "total_score": 82.5,
      "confidence_level": "HIGH",
      "data_completeness": 1.0,
      "uniprot_pathways": ["Cholinergic synapse", "Neurotransmitter metabolism"],
      "omim_associations": 1
    }
  ]
}
```

### Health Check

```bash
GET /api/v1/health
```

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## Project Structure

```
drug-repurposing-candidate-finder/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/     # API endpoints
│   │   ├── models/               # SQLAlchemy & Pydantic models
│   │   ├── services/             # Business logic & API clients
│   │   ├── repositories/         # Data access layer
│   │   └── migrations/           # Alembic migrations
│   ├── tests/                    # Backend tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                  # Next.js pages
│   │   ├── components/           # React components
│   │   ├── hooks/                # Custom hooks
│   │   └── lib/                  # API client & types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker ps

# View logs
docker-compose logs backend
docker-compose logs frontend

# Restart services
docker-compose down
docker-compose up --build
```

### Database connection errors

```bash
# Reset database
docker-compose down -v
docker-compose up --build
```

### Slow API responses

- **First search**: 30-60s is normal (querying external APIs)
- **Cached search**: Should be <1s
- Check internet connection
- Verify external APIs are accessible

### Frontend can't connect to backend

- Ensure backend is running on port 8000
- Check CORS settings in [backend/.env](backend/.env)
- Verify `NEXT_PUBLIC_API_URL` in frontend

## Performance

- **Search latency**: 20-60s for first search (fresh APIs), <1s for cached
- **Cache TTL**: 12 hours (configurable)
- **Database query time**: <100ms
- **Memory usage**: Backend <512MB, Frontend <256MB

## Known Limitations

- No pagination (returns top 50 candidates)
- No authentication/user accounts
- No search history
- Limited to FDA-approved drugs (max_phase=4)
- OMIM requires API key (optional but recommended)

## Future Enhancements

- User authentication and saved searches
- Result export (CSV/PDF)
- Drug comparison feature
- PubMed literature integration
- Clinical trials data (ClinicalTrials.gov)
- Background job queue for long-running searches
- Cloud deployment configurations

## Data Sources

- **Open Targets**: Disease-target associations - [https://www.opentargets.org/](https://www.opentargets.org/)
- **ChEMBL**: Drug discovery database - [https://www.ebi.ac.uk/chembl/](https://www.ebi.ac.uk/chembl/)
- **UniProt**: Protein information - [https://www.uniprot.org/](https://www.uniprot.org/)
- **OMIM**: Gene-disease relationships - [https://www.omim.org/](https://www.omim.org/)

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Support

For issues, questions, or feature requests, please open a GitHub issue.
