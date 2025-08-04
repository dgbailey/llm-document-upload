import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../api/client';
import { PlayCircle, Loader2, AlertCircle } from 'lucide-react';

export const DemoMode: React.FC = () => {
  const [jobCount, setJobCount] = useState(5);
  const [isGenerating, setIsGenerating] = useState(false);

  const generateMutation = useMutation({
    mutationFn: (count: number) => api.generateDemoJobs(count),
    onSuccess: () => {
      setIsGenerating(false);
      // Trigger a refresh of jobs list
      window.location.reload();
    },
    onError: () => {
      setIsGenerating(false);
    },
  });

  const handleGenerate = () => {
    setIsGenerating(true);
    generateMutation.mutate(jobCount);
  };

  return (
    <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg shadow-lg p-6 text-white">
      <div className="flex items-center mb-4">
        <PlayCircle className="h-8 w-8 mr-3" />
        <h2 className="text-2xl font-bold">Demo Mode</h2>
      </div>

      <p className="mb-4 opacity-90">
        Generate sample jobs to see the system in action. These jobs will simulate
        real document processing with random delays and occasional failures.
      </p>

      <div className="bg-white/20 rounded-lg p-4 mb-4">
        <div className="flex items-center mb-2">
          <AlertCircle className="h-5 w-5 mr-2" />
          <span className="font-semibold">Demo Features:</span>
        </div>
        <ul className="list-disc list-inside space-y-1 text-sm opacity-90 ml-7">
          <li>Simulated processing delays (1-10 seconds)</li>
          <li>10% random failure rate</li>
          <li>20% slow task simulation</li>
          <li>Realistic cost estimation</li>
          <li>Multiple AI provider simulation</li>
        </ul>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-2">
            Number of Jobs to Generate
          </label>
          <input
            type="number"
            min="1"
            max="20"
            value={jobCount}
            onChange={(e) => setJobCount(parseInt(e.target.value) || 1)}
            className="w-full px-3 py-2 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-white"
          />
        </div>

        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className={`px-6 py-3 rounded-md font-medium transition-all transform hover:scale-105
            ${isGenerating
              ? 'bg-white/30 cursor-not-allowed'
              : 'bg-white text-purple-600 hover:bg-white/90'}`}
        >
          {isGenerating ? (
            <span className="flex items-center">
              <Loader2 className="h-5 w-5 mr-2 animate-spin" />
              Generating...
            </span>
          ) : (
            <span className="flex items-center">
              <PlayCircle className="h-5 w-5 mr-2" />
              Generate Jobs
            </span>
          )}
        </button>
      </div>

      {generateMutation.isError && (
        <div className="mt-4 p-3 bg-red-500/20 rounded-md">
          <p className="text-sm">
            Failed to generate demo jobs. Make sure the backend is running and demo mode is enabled.
          </p>
        </div>
      )}

      {generateMutation.isSuccess && (
        <div className="mt-4 p-3 bg-green-500/20 rounded-md">
          <p className="text-sm">
            Successfully queued {jobCount} demo jobs! Check the jobs list to see them processing.
          </p>
        </div>
      )}
    </div>
  );
};