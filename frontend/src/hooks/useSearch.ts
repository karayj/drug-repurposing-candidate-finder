import { useState } from 'react';
import { searchDrugCandidates, APIError } from '@/lib/api';
import { SearchResponse, ScoringWeights, WeightProfile } from '@/lib/types';

export function useSearch() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResponse | null>(null);

  const search = async (
    diseaseName: string,
    weights: ScoringWeights | null,
    profile: WeightProfile
  ) => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      const data = await searchDrugCandidates(diseaseName, weights, profile);
      setResults(data);
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return { search, isLoading, error, results };
}
