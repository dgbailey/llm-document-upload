import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import { useMutation, useQuery } from '@tanstack/react-query';

interface FileUploadProps {
  onUploadSuccess: (documentId: number) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>('openai_gpt35');
  const [fallbackProvider, setFallbackProvider] = useState<string>('');
  const [costEstimate, setCostEstimate] = useState<number | null>(null);

  const { data: providers } = useQuery({
    queryKey: ['providers'],
    queryFn: api.listProviders,
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile) throw new Error('No file selected');
      
      // Upload document
      const document = await api.uploadDocument(selectedFile);
      
      // Create job
      const job = await api.createJob(
        document.id,
        selectedProvider,
        fallbackProvider || undefined
      );
      
      return job;
    },
    onSuccess: (job) => {
      onUploadSuccess(job.document_id);
      setSelectedFile(null);
      setCostEstimate(null);
    },
  });

  const estimateCostMutation = useMutation({
    mutationFn: async (file: File) => {
      const estimate = await api.estimateCost(file, selectedProvider);
      return estimate.estimated_cost;
    },
    onSuccess: (cost) => {
      setCostEstimate(cost);
    },
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setSelectedFile(file);
      estimateCostMutation.mutate(file);
    }
  }, [selectedProvider]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  // In demo mode, all providers are simulated so we show all of them
  const availableProviders = providers || [];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Upload Document</h2>
      
      {/* Provider Selection */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          AI Provider
        </label>
        <select
          value={selectedProvider}
          onChange={(e) => {
            setSelectedProvider(e.target.value);
            if (selectedFile) {
              estimateCostMutation.mutate(selectedFile);
            }
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {availableProviders.map((provider) => (
            <option key={provider.id} value={provider.id}>
              {provider.name} (${provider.input_cost}/1k tokens)
            </option>
          ))}
        </select>
      </div>

      {/* Fallback Provider */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Fallback Provider (Optional)
        </label>
        <select
          value={fallbackProvider}
          onChange={(e) => setFallbackProvider(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">None</option>
          {availableProviders
            .filter(p => p.id !== selectedProvider)
            .map((provider) => (
              <option key={provider.id} value={provider.id}>
                {provider.name}
              </option>
            ))}
        </select>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        {isDragActive ? (
          <p className="text-lg">Drop the file here...</p>
        ) : (
          <>
            <p className="text-lg mb-2">Drag & drop a document here</p>
            <p className="text-sm text-gray-500">or click to select a file</p>
            <p className="text-xs text-gray-400 mt-2">
              Supported: PDF, DOCX, TXT, Images (max 10MB)
            </p>
          </>
        )}
      </div>

      {/* Selected File */}
      {selectedFile && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg flex items-center justify-between">
          <div className="flex items-center">
            <FileText className="h-8 w-8 text-blue-500 mr-3" />
            <div>
              <p className="font-medium">{selectedFile.name}</p>
              <p className="text-sm text-gray-500">
                {(selectedFile.size / 1024).toFixed(2)} KB
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              setSelectedFile(null);
              setCostEstimate(null);
            }}
            className="text-red-500 hover:text-red-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      )}

      {/* Cost Estimate */}
      {costEstimate !== null && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg flex items-start">
          <AlertCircle className="h-5 w-5 text-blue-500 mr-2 mt-0.5" />
          <div>
            <p className="font-medium text-blue-900">Estimated Cost</p>
            <p className="text-sm text-blue-700">
              ${costEstimate.toFixed(4)} for processing this document
            </p>
          </div>
        </div>
      )}

      {/* Upload Button */}
      <button
        onClick={() => uploadMutation.mutate()}
        disabled={!selectedFile || uploadMutation.isPending}
        className={`mt-6 w-full py-3 px-4 rounded-md font-medium transition-colors
          ${selectedFile && !uploadMutation.isPending
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'}`}
      >
        {uploadMutation.isPending ? 'Processing...' : 'Upload & Process'}
      </button>

      {/* Error Message */}
      {uploadMutation.isError && (
        <div className="mt-4 p-4 bg-red-50 rounded-lg text-red-700">
          Error: {uploadMutation.error?.message || 'Upload failed'}
        </div>
      )}
    </div>
  );
};