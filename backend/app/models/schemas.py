from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict


class ScoringWeights(BaseModel):
    """User-configurable scoring weights (must sum to 100)."""
    open_targets: float = Field(default=30.0, ge=0, le=50, description="Open Targets weight (0-50)")
    chembl: float = Field(default=25.0, ge=0, le=50, description="ChEMBL weight (0-50)")
    string: float = Field(default=15.0, ge=0, le=50, description="STRING PPI weight (0-50)")
    expression: float = Field(default=15.0, ge=0, le=50, description="Expression Atlas weight (0-50)")
    reactome: float = Field(default=10.0, ge=0, le=50, description="Reactome weight (0-50)")
    omim: float = Field(default=5.0, ge=0, le=50, description="OMIM weight (0-50)")

    @field_validator('omim')
    @classmethod
    def check_sum(cls, v, info):
        """Validate weights sum to 100."""
        if info.data:
            # Get all previous values
            values = info.data
            total = sum(values.values()) + v
            if abs(total - 100.0) > 0.01:
                raise ValueError(f"Weights must sum to 100, got {total:.2f}")
        return v


class SearchRequest(BaseModel):
    """Request body for drug search endpoint."""
    disease_name: str = Field(..., min_length=3, max_length=255, description="Disease name to search")
    weights: Optional[ScoringWeights] = Field(default=None, description="Custom scoring weights (optional)")
    profile: Optional[str] = Field(default=None, description="Preset weight profile: 'balanced', 'clinical', 'mechanistic', 'expression'")

    @field_validator('profile')
    @classmethod
    def validate_profile(cls, v):
        """Ensure profile is valid."""
        if v and v not in ['balanced', 'clinical', 'mechanistic', 'expression']:
            raise ValueError(f"Invalid profile: {v}. Must be 'balanced', 'clinical', 'mechanistic', or 'expression'")
        return v


class DrugCandidate(BaseModel):
    """Drug repurposing candidate with evidence scores."""
    drug_name: str
    chembl_id: str
    target_gene: str
    target_id: str
    mechanism: str
    action_type: str  # Drug action type (INHIBITOR, ACTIVATOR, etc.)

    # Score components
    open_targets_score: float
    chembl_score: float
    uniprot_score: float
    omim_score: float
    string_score: float   
    expression_score: float  
    reactome_score: float   
    total_score: float

    confidence_level: str
    data_completeness: float

    # Actual weights used after redistribution
    actual_weights_used: Optional[Dict[str, float]] = None

    # Metadata (existing)
    omim_associations: int = 0

    # NEW metadata
    string_interactions: int = 0
    network_distance: float = 999
    expression_level: str = "unknown"
    expression_fold_change: Optional[float] = None
    shared_pathways: List[str] = []
    pathway_similarity: float = 0.0


class SearchResponse(BaseModel):
    """Response from drug search endpoint."""
    disease_name: str
    total_candidates: int
    weights_used: Dict[str, float]  # Show which weights were applied
    candidates: List[DrugCandidate]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str = "healthy"
    cache: str = "healthy"
