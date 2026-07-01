'use client';

import { SearchResponse } from '@/lib/types';
import { ResultCard } from './ResultCard';

interface ResultsListProps {
  results: SearchResponse;
}

export function ResultsList({ results }: ResultsListProps) {
  if (results.candidates.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">
          No drug candidates found for "{results.disease_name}"
        </p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">
          Results for: {results.disease_name}
        </h2>
        <p className="text-gray-600 mt-2">
          Found {results.total_candidates} potential drug candidate{results.total_candidates !== 1 ? 's' : ''}
        </p>

        {/* NEW: Show weights used */}
        <div className="bg-blue-50 p-4 rounded-lg mt-4">
          <p className="text-sm text-gray-700">
            <strong>Weights used:</strong> Open Targets: {results.weights_used.open_targets},
            ChEMBL: {results.weights_used.chembl}, STRING: {results.weights_used.string},
            Expression: {results.weights_used.expression}, Reactome: {results.weights_used.reactome},
            OMIM: {results.weights_used.omim}
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {results.candidates.map((candidate, index) => (
          <ResultCard
            key={`${candidate.chembl_id}-${index}`}
            candidate={candidate}
            rank={index + 1}
          />
        ))}
      </div>
    </div>
  );
}
