import * as Sentry from '@sentry/browser';

export function initSentry() {
  const sentryDsn = import.meta.env.VITE_SENTRY_DSN;
  
  if (!sentryDsn) {
    console.warn('Sentry DSN not configured. Set VITE_SENTRY_DSN environment variable.');
    return;
  }

  Sentry.init({
    dsn: sentryDsn,
    
    // Integrations
    integrations: [
      Sentry.replayIntegration({
        // Mask all text content, but keep media playback
        maskAllText: true,
        blockAllMedia: false,
      }),
    ],
    
    // Performance Monitoring
    tracesSampleRate: 1.0, // Capture 100% of transactions
    
    // Session Replay
    replaysSessionSampleRate: 0.1, // Sample 10% of sessions
    replaysOnErrorSampleRate: 1.0, // Sample 100% of sessions with errors
    
    // Release tracking
    release: import.meta.env.VITE_APP_VERSION || 'ai-doc-summary@1.0.0',
    environment: import.meta.env.VITE_ENVIRONMENT || 'development',
    
    // Additional options
    normalizeDepth: 10,
    attachStacktrace: true,
    
    // Before send hook for custom filtering
    beforeSend(event, hint) {
      // Filter out sensitive data
      if (event.request) {
        // Remove sensitive headers
        const sensitiveHeaders = ['authorization', 'cookie', 'x-api-key'];
        if (event.request.headers) {
          sensitiveHeaders.forEach(header => {
            if (event.request!.headers![header]) {
              event.request!.headers![header] = '[FILTERED]';
            }
          });
        }
        
        // Remove sensitive query params
        if (event.request.query_string) {
          const sensitiveParams = ['token', 'api_key', 'secret'];
          const params = new URLSearchParams(event.request.query_string);
          sensitiveParams.forEach(param => {
            if (params.has(param)) {
              params.set(param, '[FILTERED]');
            }
          });
          event.request.query_string = params.toString();
        }
      }
      
      // Filter console errors we don't care about
      if (hint.originalException) {
        const error = hint.originalException as Error;
        
        // Ignore network errors during development
        if (error.message && error.message.includes('NetworkError')) {
          if (import.meta.env.DEV) {
            return null;
          }
        }
        
        // Ignore ResizeObserver errors (common and usually harmless)
        if (error.message && error.message.includes('ResizeObserver')) {
          return null;
        }
      }
      
      return event;
    },
    
    // Ignore certain errors
    ignoreErrors: [
      // Browser extensions
      'top.GLOBALS',
      // Facebook related errors
      'fb_xd_fragment',
      // Chrome extensions
      /extensions\//i,
      /^chrome:\/\//i,
      // Other common but irrelevant errors
      'ResizeObserver loop limit exceeded',
      'Non-Error promise rejection captured',
    ],
  });
  
  console.log('Sentry initialized successfully');
}

