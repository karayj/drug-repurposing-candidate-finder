'use client';

import { useState, FormEvent } from 'react';
import { WeightSelector } from './WeightSelector';
import { ScoringWeights, WeightProfile } from '@/lib/types';

interface SearchFormProps {
  onSearch: (diseaseName: string, weights: ScoringWeights | null, profile: WeightProfile) => void;
  isLoading: boolean;
}

export function SearchForm({ onSearch, isLoading }: SearchFormProps) {
  const [diseaseName, setDiseaseName] = useState('');
  const [weights, setWeights] = useState<ScoringWeights | null>(null);
  const [profile, setProfile] = useState<WeightProfile>('balanced');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (diseaseName.trim().length >= 3) {
      onSearch(diseaseName.trim(), weights, profile);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-4xl mx-auto">
      <div className="flex flex-col gap-4">
        <label htmlFor="disease" className="text-lg font-semibold text-gray-700">
          Enter Disease Name
        </label>
        <div className="flex gap-2">
          <input
            id="disease"
            type="text"
            value={diseaseName}
            onChange={(e) => setDiseaseName(e.target.value)}
            placeholder="e.g., Alzheimer's disease, diabetes, cancer"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
            minLength={3}
            required
          />
          <button
            type="submit"
            disabled={isLoading || diseaseName.trim().length < 3}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-semibold"
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>
        <p className="text-sm text-gray-500">
          Enter a disease name to find approved drugs that may be repurposed for treatment
        </p>

        {/* NEW: Weight Selector */}
        <WeightSelector
          onWeightsChange={(w, p) => {
            setWeights(w);
            setProfile(p);
          }}
        />
      </div>
    </form>
  );
}
