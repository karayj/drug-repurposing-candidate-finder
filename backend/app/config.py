from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import json


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Drug Repurposing Finder"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 43200  # 12 hours in seconds

    # API Configuration
    OPEN_TARGETS_BASE_URL: str = "https://api.platform.opentargets.org/api/v4/graphql"
    CHEMBL_BASE_URL: str = "https://www.ebi.ac.uk/chembl/api/data"
    UNIPROT_BASE_URL: str = "https://rest.uniprot.org"
    OMIM_BASE_URL: str = "https://api.omim.org/api"
    OMIM_API_KEY: str = ""

    # HTTP Client Settings
    HTTP_TIMEOUT: int = 30
    HTTP_MAX_RETRIES: int = 3
    HTTP_RETRY_BACKOFF: float = 0.5

    # Circuit Breaker Settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 60

    # Scoring Weights
    SCORE_WEIGHT_OPEN_TARGETS: float = 0.40
    SCORE_WEIGHT_CHEMBL: float = 0.30
    SCORE_WEIGHT_UNIPROT: float = 0.20
    SCORE_WEIGHT_OMIM: float = 0.10

    # CORS
    CORS_ORIGINS: str = '["http://localhost:3000"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
