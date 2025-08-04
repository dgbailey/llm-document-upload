import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import {
  FileText,
  Clock,
  CheckCircle,
  DollarSign
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: api.getStats,
    refetchInterval: 5000,
  });

  if (isLoading || !stats) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
        <div className="animate-pulse">
          <div className="grid grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const statusData = [
    { name: 'Pending', value: stats.pending_jobs, color: '#EAB308' },
    { name: 'Processing', value: stats.processing_jobs, color: '#3B82F6' },
    { name: 'Completed', value: stats.completed_jobs, color: '#10B981' },
    { name: 'Failed', value: stats.failed_jobs, color: '#EF4444' },
  ];

  const providerData = Object.entries(stats.provider_usage).map(([provider, count]) => ({
    name: provider.replace('_', ' ').toUpperCase(),
    jobs: count,
  }));

  const documentTypeData = Object.entries(stats.document_types).map(([type, count]) => ({
    name: type.toUpperCase(),
    count: count,
  }));

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-80">Total Jobs</p>
              <p className="text-2xl font-bold">{stats.total_jobs}</p>
            </div>
            <FileText className="h-8 w-8 opacity-80" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-80">Completed</p>
              <p className="text-2xl font-bold">{stats.completed_jobs}</p>
            </div>
            <CheckCircle className="h-8 w-8 opacity-80" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-80">Avg Time</p>
              <p className="text-2xl font-bold">{stats.avg_processing_time.toFixed(1)}s</p>
            </div>
            <Clock className="h-8 w-8 opacity-80" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-80">Total Cost</p>
              <p className="text-2xl font-bold">${stats.total_cost.toFixed(2)}</p>
            </div>
            <DollarSign className="h-8 w-8 opacity-80" />
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Job Status Distribution */}
        <div className="border rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-4">Job Status Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {statusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Provider Usage */}
        <div className="border rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-4">Provider Usage</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={providerData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="jobs" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Document Types */}
        <div className="border rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-4">Document Types</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={documentTypeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {documentTypeData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Quick Stats */}
        <div className="border rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-4">Current Status</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Pending Jobs</span>
              <span className="font-semibold text-yellow-600">{stats.pending_jobs}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Processing Jobs</span>
              <span className="font-semibold text-blue-600">{stats.processing_jobs}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Documents</span>
              <span className="font-semibold">{stats.total_documents}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Success Rate</span>
              <span className="font-semibold text-green-600">
                {stats.total_jobs > 0 
                  ? ((stats.completed_jobs / stats.total_jobs) * 100).toFixed(1)
                  : 0}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Failure Rate</span>
              <span className="font-semibold text-red-600">
                {stats.total_jobs > 0
                  ? ((stats.failed_jobs / stats.total_jobs) * 100).toFixed(1)
                  : 0}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};