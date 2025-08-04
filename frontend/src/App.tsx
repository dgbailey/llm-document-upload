import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FileUpload } from './components/FileUpload';
import { JobsList } from './components/JobsList';
import { Dashboard } from './components/Dashboard';
import { DemoMode } from './components/DemoMode';
import { FileText, BarChart3, Upload, PlayCircle } from 'lucide-react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

type TabType = 'upload' | 'jobs' | 'dashboard' | 'demo';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('upload');

  const handleUploadSuccess = () => {
    setActiveTab('jobs');
  };

  const tabs = [
    { id: 'upload' as TabType, label: 'Upload', icon: Upload },
    { id: 'jobs' as TabType, label: 'Jobs', icon: FileText },
    { id: 'dashboard' as TabType, label: 'Dashboard', icon: BarChart3 },
    { id: 'demo' as TabType, label: 'Demo', icon: PlayCircle },
  ];

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <FileText className="h-8 w-8 text-blue-600 mr-3" />
                <h1 className="text-2xl font-bold text-gray-900">
                  AI Document Summary
                </h1>
              </div>
              <div className="text-sm text-gray-500">
                Demo Mode Active
              </div>
            </div>
          </div>
        </header>

        {/* Navigation Tabs */}
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav className="flex space-x-8">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      flex items-center py-4 px-1 border-b-2 font-medium text-sm
                      transition-colors duration-200
                      ${activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                    `}
                  >
                    <Icon className="h-5 w-5 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {activeTab === 'upload' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <FileUpload onUploadSuccess={handleUploadSuccess} />
              <div className="space-y-4">
                <div className="bg-blue-50 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-blue-900 mb-3">
                    How It Works
                  </h3>
                  <ol className="list-decimal list-inside space-y-2 text-blue-800">
                    <li>Upload your document (PDF, DOCX, TXT, or Image)</li>
                    <li>Select an AI provider for processing</li>
                    <li>Optionally choose a fallback provider</li>
                    <li>Get instant cost estimation</li>
                    <li>Receive AI-generated summary with key points</li>
                  </ol>
                </div>
                
                <div className="bg-green-50 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-green-900 mb-3">
                    Features
                  </h3>
                  <ul className="space-y-2 text-green-800">
                    <li className="flex items-start">
                      <span className="mr-2">✓</span>
                      <span>Multi-provider support with automatic fallback</span>
                    </li>
                    <li className="flex items-start">
                      <span className="mr-2">✓</span>
                      <span>Real-time cost estimation</span>
                    </li>
                    <li className="flex items-start">
                      <span className="mr-2">✓</span>
                      <span>Asynchronous processing with queue management</span>
                    </li>
                    <li className="flex items-start">
                      <span className="mr-2">✓</span>
                      <span>Entity extraction and key points identification</span>
                    </li>
                    <li className="flex items-start">
                      <span className="mr-2">✓</span>
                      <span>Demo mode for testing without API keys</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'jobs' && <JobsList />}
          
          {activeTab === 'dashboard' && <Dashboard />}
          
          {activeTab === 'demo' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <DemoMode />
              <div className="bg-yellow-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-yellow-900 mb-3">
                  Demo Mode Information
                </h3>
                <div className="space-y-3 text-yellow-800">
                  <p>
                    The system is currently running in demo mode. This means:
                  </p>
                  <ul className="list-disc list-inside space-y-1 ml-4">
                    <li>No actual AI API calls are made</li>
                    <li>Processing is simulated with random delays</li>
                    <li>Summaries are generated with placeholder content</li>
                    <li>Costs are estimated based on typical usage</li>
                  </ul>
                  <p className="mt-4">
                    To use real AI providers, update the .env file with your API keys
                    and set DEMO_MODE=false.
                  </p>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;