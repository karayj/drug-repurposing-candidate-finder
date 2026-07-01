'use client';

import { useState } from 'react';
import { ScoringWeights, WeightProfile } from '@/lib/types';

interface WeightSelectorProps {
  onWeightsChange: (weights: ScoringWeights | null, profile: WeightProfile) => void;
}

const PRESET_PROFILES: Record<Exclude<WeightProfile, 'custom'>, {
  label: string;
  description: string;
  weights: ScoringWeights
}> = {
  balanced: {
    label: 'Balanced',
    description: 'Equal focus on clinical and mechanistic evidence',
    weights: { open_targets: 30, chembl: 25, string: 15, expression: 15, reactome: 10, omim: 5 }
  },
  clinical: {
    label: 'Clinical Focus',
    description: 'Prioritize FDA-approved drugs and validated targets',
    weights: { open_targets: 35, chembl: 35, string: 10, expression: 10, reactome: 5, omim: 5 }
  },
  mechanistic: {
    label: 'Mechanistic Discovery',
    description: 'Favor biological plausibility and novel mechanisms',
    weights: { open_targets: 20, chembl: 15, string: 20, expression: 25, reactome: 15, omim: 5 }
  },
  expression: {
    label: 'Expression-Driven',
    description: 'Require strong evidence of target dysregulation',
    weights: { open_targets: 20, chembl: 20, string: 15, expression: 30, reactome: 10, omim: 5 }
  }
};

export function WeightSelector({ onWeightsChange }: WeightSelectorProps) {
  const [selectedProfile, setSelectedProfile] = useState<WeightProfile>('balanced');
  const [customWeights, setCustomWeights] = useState<ScoringWeights>(PRESET_PROFILES.balanced.weights);
  const [showCustom, setShowCustom] = useState(false);

  const handleProfileChange = (profile: WeightProfile) => {
    setSelectedProfile(profile);
    if (profile === 'custom') {
      setShowCustom(true);
      onWeightsChange(customWeights, profile);
    } else {
      setShowCustom(false);
      onWeightsChange(null, profile);  // null = use backend preset
    }
  };

  const handleCustomWeightChange = (source: keyof ScoringWeights, value: number) => {
    const newWeights = { ...customWeights, [source]: value };
    setCustomWeights(newWeights);
    onWeightsChange(newWeights, 'custom');
  };

  const totalWeight = Object.values(customWeights).reduce((a, b) => a + b, 0);
  const isValidTotal = Math.abs(totalWeight - 100) < 0.01;

  return (
    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 mb-6">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Scoring Weight Profile</h3>

      {/* Profile Selection */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-4">
        {(Object.keys(PRESET_PROFILES) as (keyof typeof PRESET_PROFILES)[]).map((profile) => (
          <button
            key={profile}
            onClick={() => handleProfileChange(profile)}
            className={`p-3 rounded-lg border-2 text-left transition-all ${
              selectedProfile === profile
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 bg-white hover:border-gray-400'
            }`}
          >
            <div className="text-sm font-semibold text-gray-900">
              {PRESET_PROFILES[profile].label}
            </div>
            <div className="text-xs text-gray-600 mt-1">
              {PRESET_PROFILES[profile].description}
            </div>
          </button>
        ))}

        {/* Custom button */}
        <button
          onClick={() => handleProfileChange('custom')}
          className={`p-3 rounded-lg border-2 text-left transition-all ${
            selectedProfile === 'custom'
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-white hover:border-gray-400'
          }`}
        >
          <div className="text-sm font-semibold text-gray-900">
            Custom
          </div>
          <div className="text-xs text-gray-600 mt-1">
            Specify your own weights
          </div>
        </button>
      </div>

      {/* Custom Weight Sliders */}
      {showCustom && (
        <div className="mt-4 pt-4 border-t border-gray-300">
          <p className="text-xs text-gray-600 mb-3">
            Adjust weights (must sum to 100):
            <span className={`ml-2 font-semibold ${isValidTotal ? 'text-green-600' : 'text-red-600'}`}>
              Total: {totalWeight.toFixed(0)}
            </span>
          </p>

          <div className="space-y-3">
            {(Object.keys(customWeights) as (keyof ScoringWeights)[]).map((source) => {
              const labels: Record<keyof ScoringWeights, string> = {
                open_targets: 'Open Targets',
                chembl: 'ChEMBL',
                string: 'STRING PPI',
                expression: 'Expression',
                reactome: 'Reactome',
                omim: 'OMIM'
              };

              return (
                <div key={source} className="flex items-center gap-3">
                  <label className="text-xs text-gray-700 w-32">
                    {labels[source]}:
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="50"
                    step="5"
                    value={customWeights[source]}
                    onChange={(e) => handleCustomWeightChange(source, parseInt(e.target.value))}
                    className="flex-1"
                  />
                  <span className="text-xs text-gray-900 font-semibold w-8 text-right">
                    {customWeights[source]}
                  </span>
                </div>
              );
            })}
          </div>

          {!isValidTotal && (
            <p className="text-xs text-red-600 mt-2">
              ⚠️ Weights must sum to exactly 100
            </p>
          )}
        </div>
      )}
    </div>
  );
}
