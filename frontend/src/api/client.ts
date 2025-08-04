import axios from 'axios';
import * as Sentry from '@sentry/browser';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add Sentry tracing to axios requests
apiClient.interceptors.request.use((config) => {
  try {
    // Add Sentry trace headers for distributed tracing
    const client = Sentry.getClient();
    if (client) {
      const scope = Sentry.getCurrentScope();
      
      // Create a span for this request
      const httpSpan = Sentry.startInactiveSpan({
        op: 'http.client',
        name: `${config.method?.toUpperCase()} ${config.url}`,
      });
      
      if (httpSpan) {
        // Store span in config for later use
        (config as any).sentrySpan = httpSpan;
        
        // Add trace headers for distributed tracing
        const spanContext = httpSpan.spanContext();
        if (spanContext) {
          // Generate sentry-trace header
          const sentryTraceHeader = `${spanContext.traceId}-${spanContext.spanId}-1`;
          config.headers['sentry-trace'] = sentryTraceHeader;
          
          // Add baggage header with basic info
          const baggage = `sentry-trace_id=${spanContext.traceId},sentry-environment=${import.meta.env.VITE_ENVIRONMENT || 'development'}`;
          config.headers['baggage'] = baggage;
        }
      }
    }
  } catch (error) {
    // Silently fail if Sentry isn't properly initialized
    console.debug('Sentry tracing error:', error);
  }
  
  return config;
});

// Complete Sentry span on response
apiClient.interceptors.response.use(
  (response) => {
    try {
      // Finish the span if it exists
      const span = (response.config as any).sentrySpan;
      if (span && typeof span.setAttribute === 'function') {
        span.setAttribute('http.response.status_code', response.status);
        span.end();
      }
    } catch (error) {
      console.debug('Error finishing Sentry span:', error);
    }
    return response;
  },
  (error) => {
    try {
      // Finish the span with error status
      const span = (error.config as any)?.sentrySpan;
      if (span && typeof span.setAttribute === 'function') {
        span.setAttribute('http.response.status_code', error.response?.status || 0);
        span.setStatus({ code: 2, message: 'Internal Error' });
        span.end();
      }
      
      // Report error to Sentry
      Sentry.captureException(error, {
        contexts: {
          http: {
            method: error.config?.method,
            url: error.config?.url,
            status_code: error.response?.status,
          },
        },
      });
    } catch (sentryError) {
      console.debug('Error reporting to Sentry:', sentryError);
    }
    
    return Promise.reject(error);
  }
);

export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  document_type: string;
  file_size: number;
  upload_date: string;
}

export interface Job {
  id: number;
  document_id: number;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  ai_provider: string;
  fallback_provider?: string;
  created_at: string;
  completed_at?: string;
  summary?: string;
  key_points: string[];
  entities: Array<{ type: string; value: string }>;
  estimated_cost: number;
  actual_cost: number;
  error_message?: string;
}

export interface Stats {
  total_jobs: number;
  pending_jobs: number;
  processing_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  total_documents: number;
  total_cost: number;
  avg_processing_time: number;
  provider_usage: Record<string, number>;
  document_types: Record<string, number>;
}

export interface Provider {
  id: string;
  name: string;
  available: boolean;
  input_cost: number;
  output_cost: number;
}

export interface CostEstimate {
  estimated_tokens: number;
  estimated_cost: number;
  provider: string;
}

export const api = {
  // Documents
  uploadDocument: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<Document>('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Jobs
  createJob: async (documentId: number, provider: string, fallbackProvider?: string) => {
    const response = await apiClient.post<Job>('/api/jobs', {
      document_id: documentId,
      ai_provider: provider,
      fallback_provider: fallbackProvider,
    });
    return response.data;
  },

  getJob: async (jobId: number) => {
    const response = await apiClient.get<Job>(`/api/jobs/${jobId}`);
    return response.data;
  },

  listJobs: async (status?: string) => {
    const params = status ? { status } : {};
    const response = await apiClient.get<Job[]>('/api/jobs', { params });
    return response.data;
  },

  cancelJob: async (jobId: number) => {
    const response = await apiClient.delete(`/api/jobs/${jobId}`);
    return response.data;
  },

  // Stats
  getStats: async () => {
    const response = await apiClient.get<Stats>('/api/stats');
    return response.data;
  },

  // Providers
  listProviders: async () => {
    const response = await apiClient.get<Provider[]>('/api/providers');
    return response.data;
  },

  // Cost Estimation
  estimateCost: async (file: File, provider: string) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<CostEstimate>('/api/estimate-cost', formData, {
      params: { provider },
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Demo
  generateDemoJobs: async (count: number = 5) => {
    const response = await apiClient.post('/api/demo/generate-jobs', null, {
      params: { count },
    });
    return response.data;
  },
};