'use client';

import { DrugCandidate } from '@/lib/types';
import { EvidenceBreakdown } from './EvidenceBreakdown';

interface ResultCardProps {
  candidate: DrugCandidate;
  rank: number;
}

export function ResultCard({ candidate, rank }: ResultCardProps) {
  const confidenceColor = {
    HIGH: 'bg-green-100 text-green-800',
    MEDIUM: 'bg-yellow-100 text-yellow-800',
    LOW: 'bg-red-100 text-red-800',
  }[candidate.confidence_level];

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow overflow-hidden">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-2xl font-bold text-gray-400">#{rank}</span>
            <h3 className="text-xl font-bold text-gray-900">{candidate.drug_name}</h3>
            <span className={`px-2 py-1 rounded text-xs font-semibold ${confidenceColor}`}>
              {candidate.confidence_level}
            </span>
          </div>
          <p className="text-sm text-gray-600">
            ChEMBL ID: <a href={`https://www.ebi.ac.uk/chembl/compound_report_card/${candidate.chembl_id}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{candidate.chembl_id}</a>
          </p>
        </div>

        <div className="text-right">
          <div className="text-3xl font-bold text-blue-600">{candidate.total_score.toFixed(1)}</div>
          <div className="text-xs text-gray-500">Evidence Score</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <span className="text-sm font-semibold text-gray-700">Target Gene:</span>
          <p className="text-sm text-gray-900">{candidate.target_gene}</p>
        </div>
        <div>
          <span className="text-sm font-semibold text-gray-700">Mechanism:</span>
          <p className="text-sm text-gray-900">{candidate.mechanism}</p>
        </div>
      </div>

      {/* NEW: Biological Evidence Section */}
      <div className="border-t pt-4 mt-4 mb-4">
        <p className="text-sm font-semibold text-gray-700 mb-3">Biological Evidence:</p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* STRING Interactions */}
          <div>
            <span className="text-xs text-gray-600 block">PPI Network</span>
            {candidate.string_interactions > 0 ? (
              <p className="text-sm font-semibold text-green-700">
                {candidate.string_interactions} direct interactions
              </p>
            ) : (
              <p className="text-sm text-gray-500">
                {candidate.network_distance === 1 ? '1-hop distance' :
                 candidate.network_distance === 2 ? '2-hop distance' :
                 'No connection'}
              </p>
            )}
          </div>

          {/* Expression Alignment */}
          <div>
            <span className="text-xs text-gray-600 block">Gene Expression</span>
            {candidate.expression_level !== 'unknown' ? (
              <div>
                <span className={`text-sm px-2 py-1 rounded font-semibold ${
                  candidate.expression_level === 'up' ? 'bg-red-100 text-red-800' :
                  candidate.expression_level === 'down' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {candidate.expression_level.toUpperCase()}
                </span>
                {candidate.expression_fold_change && (
                  <span className="text-xs text-gray-600 ml-1">
                    ({candidate.expression_fold_change.toFixed(1)}x)
                  </span>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">Not measured</p>
            )}
          </div>

          {/* Drug Action */}
          <div>
            <span className="text-xs text-gray-600 block">Drug Action</span>
            <p className="text-sm font-semibold text-purple-700">
              {candidate.action_type || 'Unknown'}
            </p>
          </div>

          {/* Pathway Overlap */}
          <div>
            <span className="text-xs text-gray-600 block">Shared Pathways</span>
            {candidate.shared_pathways.length > 0 ? (
              <p className="text-sm font-semibold text-indigo-700">
                {candidate.shared_pathways.length} pathways
                <span className="text-xs text-gray-600 ml-1">
                  ({Math.round(candidate.pathway_similarity * 100)}% overlap)
                </span>
              </p>
            ) : (
              <p className="text-sm text-gray-500">No overlap</p>
            )}
          </div>
        </div>

        {/* Show pathway names if available */}
        {candidate.shared_pathways.length > 0 && (
          <div className="mt-3">
            <details className="text-xs">
              <summary className="cursor-pointer text-gray-600 hover:text-gray-800">
                View shared pathways ({candidate.shared_pathways.length})
              </summary>
              <ul className="mt-2 ml-4 list-disc text-gray-700">
                {candidate.shared_pathways.slice(0, 5).map((pathway, idx) => (
                  <li key={idx}>{pathway}</li>
                ))}
                {candidate.shared_pathways.length > 5 && (
                  <li className="text-gray-500">+ {candidate.shared_pathways.length - 5} more</li>
                )}
              </ul>
            </details>
          </div>
        )}
      </div>

      <EvidenceBreakdown candidate={candidate} weightsUsed={candidate.actual_weights_used} />

      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          Data completeness: {(candidate.data_completeness * 100).toFixed(0)}% |
          OMIM associations: {candidate.omim_associations}
        </div>
      </div>
    </div>
  );
}
