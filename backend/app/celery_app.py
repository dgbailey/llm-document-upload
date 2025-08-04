from celery import Celery
from .config import settings
from .sentry_config import init_sentry
import os

# Initialize Sentry for Celery worker
init_sentry()

# In demo mode, use in-memory broker if Redis is not available
if settings.demo_mode and not settings.redis_url.startswith('redis://'):
    # Use in-memory broker for demo mode when Redis is not available
    broker_url = 'memory://'
    backend_url = 'cache+memory://'
else:
    broker_url = settings.redis_url
    backend_url = settings.redis_url

# Create Celery app
celery_app = Celery(
    'ai_doc_summary',
    broker=broker_url,
    backend=backend_url,
    include=['app.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # For in-memory broker
    task_always_eager=settings.demo_mode and broker_url == 'memory://',
)