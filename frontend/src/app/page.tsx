'use client';

import { SearchForm } from '@/components/SearchForm';
import { ResultsList } from '@/components/ResultsList';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorMessage } from '@/components/ErrorMessage';
import { useSearch } from '@/hooks/useSearch';

export default function Home() {
  const { search, isLoading, error, results } = useSearch();

  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <div className="container mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Drug Repurposing Candidate Finder
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Discover approved drugs that may be repurposed for new therapeutic applications.
            Powered by Open Targets, ChEMBL, STRING, Expression Atlas, Reactome, and OMIM.
          </p>
        </div>

        <div className="mb-12">
          <SearchForm onSearch={search} isLoading={isLoading} />
        </div>

        {isLoading && <LoadingSpinner />}

        {error && <ErrorMessage message={error} />}

        {results && !isLoading && <ResultsList results={results} />}
      </div>
    </main>
  );
}
