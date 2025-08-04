import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging
from .config import settings

def init_sentry():
    """Initialize Sentry with all integrations"""
    
    # Get DSN from environment or use a placeholder
    sentry_dsn = settings.sentry_dsn if hasattr(settings, 'sentry_dsn') else None
    
    if not sentry_dsn:
        logging.warning("Sentry DSN not configured. Set SENTRY_DSN environment variable.")
        return
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        
        # Integrations
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",
                failed_request_status_codes=[400, 401, 403, 404, 405, 406, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 421, 422, 423, 424, 425, 426, 428, 429, 431, 451, 500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511],
            ),
            StarletteIntegration(
                transaction_style="endpoint",
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
                propagate_traces=True,
            ),
            RedisIntegration(),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=logging.INFO,        # Capture info and above as breadcrumbs
                event_level=logging.ERROR   # Send errors as events
            ),
        ],
        
        # Performance Monitoring
        traces_sample_rate=1.0,  # Capture 100% of transactions for performance monitoring
        profiles_sample_rate=1.0,  # Profile 100% of sampled transactions
        
        # Session tracking
        release=settings.app_version if hasattr(settings, 'app_version') else "ai-doc-summary@1.0.0",
        environment=settings.environment if hasattr(settings, 'environment') else "development",
        
        # Additional options
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send personally identifiable information
        
        # Before send hook for custom filtering
        before_send=before_send_filter,
    )
    
    logging.info("Sentry initialized successfully")

def before_send_filter(event, hint):
    """Filter sensitive data before sending to Sentry"""
    
    # Remove sensitive headers
    if 'request' in event and 'headers' in event['request']:
        sensitive_headers = ['authorization', 'cookie', 'x-api-key', 'x-auth-token']
        for header in sensitive_headers:
            if header in event['request']['headers']:
                event['request']['headers'][header] = '[FILTERED]'
    
    # Remove sensitive data from extra context
    if 'extra' in event:
        sensitive_keys = ['password', 'secret', 'token', 'api_key', 'private_key']
        for key in list(event['extra'].keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                event['extra'][key] = '[FILTERED]'
    
    return event