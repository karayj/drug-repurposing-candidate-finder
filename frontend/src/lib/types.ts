export interface ScoringWeights {
  open_targets: number;
  chembl: number;
  string: number;
  expression: number;
  reactome: number;
  omim: number;
}

export type WeightProfile = 'balanced' | 'clinical' | 'mechanistic' | 'expression' | 'custom';

export interface SearchRequest {
  disease_name: string;
  weights?: ScoringWeights;
  profile?: WeightProfile;
}

export interface DrugCandidate {
  drug_name: string;
  chembl_id: string;
  target_gene: string;
  target_id: string;
  mechanism: string;
  action_type: string;  // NEW: Drug action type

  // Score components
  open_targets_score: number;
  chembl_score: number;
  uniprot_score: number;
  omim_score: number;
  string_score: number;  // NEW
  expression_score: number;  // NEW
  reactome_score: number;  // NEW
  total_score: number;

  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
  data_completeness: number;

  // Actual weights used after redistribution (per candidate)
  actual_weights_used?: ScoringWeights | null;  // NEW

  // Metadata
  omim_associations: number;
  string_interactions: number;  // NEW
  network_distance: number;  // NEW
  expression_level: 'up' | 'down' | 'unchanged' | 'unknown';  // NEW
  expression_fold_change: number | null;  // NEW
  shared_pathways: string[];  // NEW
  pathway_similarity: number;  // NEW
}

export interface SearchResponse {
  disease_name: string;
  total_candidates: number;
  weights_used: ScoringWeights;  // NEW: Backend echoes weights applied
  candidates: DrugCandidate[];
}
