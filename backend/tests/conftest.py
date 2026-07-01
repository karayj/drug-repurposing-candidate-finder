"""Pytest configuration and fixtures."""
import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Mock configuration settings."""
    return {
        "DATABASE_URL": "postgresql://test:test@localhost/test_db",
        "REDIS_URL": "redis://localhost:6379/1",
        "REDIS_CACHE_TTL": 3600,
        "OMIM_API_KEY": "test_key",
        "HTTP_TIMEOUT": 30,
        "HTTP_MAX_RETRIES": 3,
        "CIRCUIT_BREAKER_FAILURE_THRESHOLD": 5,
        "CIRCUIT_BREAKER_TIMEOUT": 60
    }


@pytest.fixture
def sample_open_targets_data():
    """Sample Open Targets API response data."""
    return {
        "target_id": "ENSG00000171105",
        "gene_symbol": "INSR",
        "association_score": 0.9,
        "data_sources": ["gwas", "literature"],
        "expressions": [
            {
                "tissue": {"id": "UBERON_0001264", "label": "pancreas"},
                "rna": {"value": 5703, "level": 4},
                "protein": {"level": 3}
            },
            {
                "tissue": {"id": "UBERON_0002107", "label": "liver"},
                "rna": {"value": 2000, "level": 2},
                "protein": {"level": 2}
            }
        ]
    }


@pytest.fixture
def sample_chembl_data():
    """Sample ChEMBL API response data."""
    return {
        "drug_name": "INSULIN HUMAN",
        "chembl_id": "CHEMBL1201631",
        "max_phase": 4,
        "molecule_type": "Protein",
        "mechanism": "Insulin receptor agonist",
        "action_type": "AGONIST"
    }


@pytest.fixture
def sample_omim_data():
    """Sample OMIM API response data."""
    return [
        {
            "omim_id": "147670",
            "gene_symbol": "INSR",
            "phenotype": "Diabetes mellitus, type 2",
            "inheritance": "Autosomal dominant"
        },
        {
            "omim_id": "147671",
            "gene_symbol": "INSR",
            "phenotype": "Insulin resistance",
            "inheritance": "Autosomal recessive"
        }
    ]


@pytest.fixture
def sample_string_data():
    """Sample STRING API response data."""
    return {
        "direct_interactions": 4,
        "network_distance": 0,
        "interaction_score": 0.95
    }


@pytest.fixture
def sample_reactome_data():
    """Sample Reactome API response data."""
    return {
        "shared_pathways": [
            "Insulin receptor signalling cascade",
            "IRS activation",
            "PI5P, PP2A and IER3 Regulate PI3K/AKT Signaling"
        ],
        "pathway_similarity": 0.4,
        "enriched_processes": ["Signal Transduction", "Metabolism"],
        "target_pathway_count": 10,
        "disease_pathway_count": 12
    }


@pytest.fixture
def sample_expression_data():
    """Sample expression data (from Open Targets)."""
    return {
        "expression_level": "high",
        "relevant_tissue": "pancreas",
        "rna_value": 5703,
        "tissue_specificity": True,
        "drug_action_type": "AGONIST"
    }


@pytest.fixture
def default_weights():
    """Default scoring weights."""
    return {
        "open_targets": 30.0,
        "chembl": 25.0,
        "string": 15.0,
        "expression": 15.0,
        "reactome": 10.0,
        "omim": 5.0
    }


@pytest.fixture
def clinical_weights():
    """Clinical focus scoring weights."""
    return {
        "open_targets": 35.0,
        "chembl": 35.0,
        "string": 10.0,
        "expression": 10.0,
        "reactome": 5.0,
        "omim": 5.0
    }
