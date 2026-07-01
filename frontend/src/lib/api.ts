import { SearchResponse, ScoringWeights, WeightProfile } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

export async function searchDrugCandidates(
  diseaseName: string,
  weights: ScoringWeights | null,
  profile: WeightProfile
): Promise<SearchResponse> {
  const requestBody: any = { disease_name: diseaseName };

  // Add weights or profile to request
  if (weights) {
    requestBody.weights = weights;
  } else if (profile && profile !== 'custom') {
    requestBody.profile = profile;
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new APIError(response.status, error.detail || 'Search failed');
  }

  return response.json();
}

export async function healthCheck(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`);
  return response.json();
}
