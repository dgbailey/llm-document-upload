import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, type Job } from '../api/client';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  DollarSign,
  Hash
} from 'lucide-react';

interface JobsListProps {
  refreshInterval?: number;
}

export const JobsList: React.FC<JobsListProps> = ({ refreshInterval = 2000 }) => {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => api.listJobs(),
    refetchInterval: refreshInterval,
  });

  const getStatusIcon = (status: Job['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'processing':
        return <AlertCircle className="h-5 w-5 text-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'cancelled':
        return <XCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: Job['status']) => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
    switch (status) {
      case 'pending':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'processing':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'completed':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'failed':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'cancelled':
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Jobs</h2>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Jobs</h2>
      
      {!jobs || jobs.length === 0 ? (
        <p className="text-gray-500">No jobs yet. Upload a document to get started!</p>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="border rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center">
                  {getStatusIcon(job.status)}
                  <span className={`ml-2 ${getStatusBadge(job.status)}`}>
                    {job.status.toUpperCase()}
                  </span>
                  <span className="ml-3 text-sm text-gray-500 flex items-center">
                    <Hash className="h-3 w-3 mr-1" />
                    Job #{job.id}
                  </span>
                </div>
                <div className="text-sm text-gray-500">
                  {formatDate(job.created_at)}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-3">
                <div>
                  <p className="text-sm text-gray-600">Provider</p>
                  <p className="font-medium">{job.ai_provider.replace('_', ' ').toUpperCase()}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Cost</p>
                  <p className="font-medium flex items-center">
                    <DollarSign className="h-4 w-4 mr-1" />
                    {job.actual_cost > 0 
                      ? job.actual_cost.toFixed(4)
                      : `Est: ${job.estimated_cost.toFixed(4)}`}
                  </p>
                </div>
              </div>

              {job.summary && (
                <div className="mt-4 p-3 bg-gray-50 rounded">
                  <p className="text-sm font-medium text-gray-700 mb-1">Summary</p>
                  <p className="text-sm text-gray-600 line-clamp-3">
                    {job.summary}
                  </p>
                </div>
              )}

              {job.key_points && job.key_points.length > 0 && (
                <div className="mt-3">
                  <p className="text-sm font-medium text-gray-700 mb-1">Key Points</p>
                  <ul className="list-disc list-inside text-sm text-gray-600">
                    {job.key_points.slice(0, 3).map((point, idx) => (
                      <li key={idx} className="line-clamp-1">{point}</li>
                    ))}
                  </ul>
                </div>
              )}

              {job.error_message && (
                <div className="mt-3 p-3 bg-red-50 rounded">
                  <p className="text-sm text-red-700">
                    Error: {job.error_message}
                  </p>
                </div>
              )}

              {job.status === 'processing' && (
                <div className="mt-3">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};