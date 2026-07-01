# Backend Tests

This directory contains unit and integration tests for the drug repurposing candidate finder backend.

## Test Structure

```
tests/
├── unit/                       # Unit tests (isolated, fast)
│   ├── test_scoring.py        # Scoring algorithm tests
│   ├── test_circuit_breaker.py # Circuit breaker pattern tests
│   ├── test_omim_client.py    # OMIM API client tests
│   └── test_open_targets_client.py # Open Targets client tests
├── integration/                # Integration tests (multi-component)
│   └── test_search_flow.py   # End-to-end search workflow tests
├── conftest.py                # Shared fixtures and configuration
└── README.md                  # This file
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
# From backend directory
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_scoring.py -v

# Specific test class
pytest tests/unit/test_scoring.py::TestEvidenceScorer -v

# Specific test method
pytest tests/unit/test_scoring.py::TestEvidenceScorer::test_calculate_total_score_all_sources -v
```

### Run Tests in Docker

```bash
# From project root
docker-compose exec backend pytest

# With coverage
docker-compose exec backend pytest --cov=app --cov-report=term-missing
```

## Test Coverage

Current test coverage:

### Unit Tests
- ✅ **Scoring Service** (`test_scoring.py`) - 30+ tests
  - Weight redistribution algorithm
  - Custom scoring weights
  - Individual source scoring (Open Targets, ChEMBL, OMIM, STRING, Expression, Reactome)
  - Expression-mechanism alignment
  - Confidence level determination

- ✅ **Circuit Breaker** (`test_circuit_breaker.py`) - 8 tests
  - State transitions (CLOSED → OPEN → HALF_OPEN)
  - Failure threshold handling
  - Timeout and recovery
  - Concurrent call handling

- ✅ **OMIM Client** (`test_omim_client.py`) - 6 tests
  - Gene-disease association retrieval
  - No hardcoded limits (bug fix verification)
  - Error handling and graceful degradation

- ✅ **Open Targets Client** (`test_open_targets_client.py`) - 9 tests
  - Disease target retrieval
  - Expression data extraction
  - Tissue-specific expression matching
  - Disease-to-tissue mapping

### Integration Tests
- ✅ **Search Flow** (`test_search_flow.py`) - 7 tests
  - End-to-end search workflow
  - Custom weight profiles
  - Graceful degradation with API failures
  - Cache hit/miss behavior
  - Result sorting and ranking

## Writing New Tests

### Unit Test Template

```python
import pytest
from app.services.your_module import YourClass

class TestYourClass:
    def setup_method(self):
        """Set up test fixtures."""
        self.instance = YourClass()
    
    def test_your_feature(self):
        """Test your feature description."""
        result = self.instance.your_method()
        assert result == expected_value
```

### Async Test Template

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestAsyncFeature:
    @pytest.mark.asyncio
    async def test_async_method(self):
        """Test async method."""
        result = await your_async_function()
        assert result is not None
```

### Using Fixtures

```python
def test_with_fixtures(sample_open_targets_data, default_weights):
    """Test using shared fixtures from conftest.py."""
    scorer = EvidenceScorer()
    scores = scorer.calculate_total_score(
        open_targets_data=sample_open_targets_data,
        weights=default_weights
    )
    assert scores["total_score"] > 0
```

## Best Practices

1. **Isolation**: Unit tests should not depend on external services
2. **Mocking**: Use `unittest.mock` or `pytest-mock` for API calls
3. **Fixtures**: Share common test data using pytest fixtures
4. **Assertions**: Use clear, specific assertions with helpful messages
5. **Coverage**: Aim for >80% code coverage for critical paths
6. **Speed**: Unit tests should be fast (<1s each)
7. **Documentation**: Add docstrings explaining what each test verifies

## Continuous Integration

Tests are automatically run on:
- Every pull request
- Before deployment to staging/production
- Nightly builds for regression detection

## Troubleshooting

### Import Errors

If you see import errors, ensure you're running tests from the backend directory:
```bash
cd backend
pytest
```

### Async Test Failures

Make sure pytest-asyncio is installed and `asyncio_mode = auto` is set in `pytest.ini`.

### Mock Not Working

Verify the import path in `@patch()` matches the actual import in your code:
```python
# If code uses: from app.services.api_clients.omim import OMIMClient
# Then patch: @patch('app.services.api_clients.omim.OMIMClient.get')
```

### Database Connection Errors

Integration tests may require a test database. Configure via environment variables:
```bash
export DATABASE_URL="postgresql://test:test@localhost/test_db"
```

## Future Test Additions

Tests to add:
- [ ] ChEMBL client tests
- [ ] STRING client tests
- [ ] Reactome client tests
- [ ] Cache service tests
- [ ] API endpoint tests (FastAPI TestClient)
- [ ] Database repository tests
- [ ] Error handling edge cases
- [ ] Performance/load tests
