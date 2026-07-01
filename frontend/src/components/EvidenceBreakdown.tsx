'use client';

import { DrugCandidate, ScoringWeights } from '@/lib/types';

interface EvidenceBreakdownProps {
  candidate: DrugCandidate;
  weightsUsed: ScoringWeights | null | undefined;
}

export function EvidenceBreakdown({ candidate, weightsUsed }: EvidenceBreakdownProps) {
  // Fallback to deriving weights from scores if actual_weights_used not available
  const actualWeights = weightsUsed || {
    open_targets: 30,
    chembl: 25,
    string: 15,
    expression: 15,
    reactome: 10,
    omim: 5
  };

  // Debug logging
  if (typeof window !== 'undefined' && !weightsUsed) {
    console.warn('No actual_weights_used for candidate:', candidate.drug_name, 'using fallback');
  }

  const scores = [
    {
      label: 'Target Association',
      value: candidate.open_targets_score,
      max: actualWeights.open_targets,
      color: 'bg-blue-500',
      description: 'Disease-target association strength from Open Targets'
    },
    {
      label: 'Drug Approval',
      value: candidate.chembl_score,
      max: actualWeights.chembl,
      color: 'bg-green-500',
      description: 'FDA approval status from ChEMBL'
    },
    {
      label: 'Network Proximity',
      value: candidate.string_score,
      max: actualWeights.string,
      color: 'bg-pink-500',
      description: 'Protein-protein interaction network distance (STRING)'
    },
    {
      label: 'Expression Alignment',
      value: candidate.expression_score,
      max: actualWeights.expression,
      color: 'bg-teal-500',
      description: 'Gene expression + drug mechanism alignment'
    },
    {
      label: 'Pathway Overlap',
      value: candidate.reactome_score,
      max: actualWeights.reactome,
      color: 'bg-indigo-500',
      description: 'Shared biological pathways (Reactome)'
    },
    {
      label: 'Genetic Evidence',
      value: candidate.omim_score,
      max: actualWeights.omim,
      color: 'bg-orange-500',
      description: 'Gene-disease validation from OMIM'
    },
  ];

  // Find the maximum possible score (weight) to scale all gray bars
  const maxWeight = Math.max(...scores.map(s => s.max));

  return (
    <div className="space-y-2 w-full">
      <p className="text-sm font-semibold text-gray-700 mb-2">
        Evidence Breakdown (Total: {candidate.total_score.toFixed(1)}/100):
      </p>
      {scores.map((score) => {
        // Gray bar width is proportional to the max possible score (weight)
        const grayBarWidth = maxWeight > 0 ? (score.max / maxWeight) * 100 : 0;
        // Colored bar width is the achieved score as percentage of max
        const coloredBarWidth = score.max > 0 ? (score.value / score.max) * 100 : 0;

        return (
          <div key={score.label} className="flex items-center gap-2 w-full">
            <span className="text-xs text-gray-600 w-28 flex-shrink-0" title={score.description}>
              {score.label}
            </span>
            <div className="flex-1 min-w-0 max-w-full">
              <div
                className="bg-gray-200 rounded-full h-4 relative overflow-hidden"
                style={{ width: `${grayBarWidth}%` }}
              >
                <div
                  className={`${score.color} h-4 rounded-full transition-all duration-300 absolute top-0 left-0`}
                  style={{ width: `${coloredBarWidth}%`, maxWidth: '100%' }}
                />
                <span className="absolute inset-0 flex items-center justify-end pr-2 text-xs text-gray-700 font-semibold whitespace-nowrap pointer-events-none z-10">
                  {score.value.toFixed(1)}/{score.max}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
