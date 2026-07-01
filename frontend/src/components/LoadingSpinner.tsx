'use client';

export function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      <p className="mt-4 text-gray-600">Searching drug databases...</p>
      <p className="mt-2 text-sm text-gray-500">This may take 30-60 seconds</p>
    </div>
  );
}
