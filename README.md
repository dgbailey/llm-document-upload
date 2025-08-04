# AI Document Summary System

A production-ready document processing system that leverages multiple AI providers to generate intelligent summaries, extract key points, and identify entities from various document types. Built with observability and reliability in mind, featuring comprehensive Sentry integration for monitoring and performance tracking.

## Overview

This system provides:
- **Multi-format document processing** (PDF, DOCX, TXT, Images)
- **AI provider abstraction** with automatic fallback mechanisms
- **Cost estimation and tracking** for AI processing
- **Real-time job monitoring** via WebSocket connections
- **Comprehensive observability** with Sentry APM and distributed tracing
- **Demo mode** for testing without AI provider credentials

## Architecture

### Services

- **Backend API** - FastAPI server handling document uploads and job management
- **Celery Workers** - Asynchronous task processing for document analysis
- **Redis** - Message broker for Celery and caching
- **PostgreSQL** - Primary database for jobs and documents
- **Frontend** - React dashboard for uploading documents and monitoring jobs
- **Nginx** - Reverse proxy and static file serving

### AI Providers Supported

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Sentry account (optional, for monitoring)
- AI provider API keys (optional, demo mode available)

### Getting Started

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-doc-summary
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs

5. **Generate demo data** (optional)
   ```bash
   curl -X POST "http://localhost:8000/api/demo/generate-jobs?count=10"
   ```

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart backend celery

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose build backend
docker-compose up -d
```

## Demo Mode

The system includes a comprehensive demo mode that simulates AI processing without requiring API keys:

- **Synthetic responses** - Generates realistic summaries and key points
- **Configurable failure rate** - 10% failure rate for testing retry logic
- **Processing delays** - Random 1-5 second delays to simulate AI processing
- **Cost simulation** - Tracks estimated costs even in demo mode

## Observability with Sentry

### Distributed Tracing

The system implements end-to-end distributed tracing across frontend and backend services:

- Frontend browser sessions with replay
- Backend API requests
- Celery task execution
- Database queries
- AI provider calls

### Span Attributes Captured

#### Transaction Level (process_document)
| Attribute | Type | Description |
|-----------|------|-------------|
| `job.id` | integer | Unique job identifier |
| `document.id` | integer | Document being processed |
| `document.size` | integer | File size in bytes |
| `document.type` | string | File type (pdf, docx, txt, image) |
| `ai.provider` | string | Primary AI provider used |
| `ai.cost.estimated` | float | Estimated processing cost |
| `ai.cost.actual` | float | Actual processing cost |
| `ai.tokens.estimated` | integer | Estimated token count |
| `ai.tokens.actual` | integer | Actual tokens used |
| `job.retry_count` | integer | Number of retry attempts |
| `job.processing_time` | float | Total processing time in seconds |
| `job.status` | string | Final job status (completed/failed) |

#### Metrics Collected
| Metric | Unit | Tags | Description |
|--------|------|------|-------------|
| `document.size` | bytes | provider, document_type | Document file size distribution |
| `document.pages` | pages | document_type | Page count for documents |
| `document.token_density` | tokens/KB | document_type, provider | Token density analysis |
| `ai.tokens.used` | tokens | provider, document_id, is_demo | Token usage tracking |
| `ai.cost` | USD | provider, document_type | Cost tracking |
| `ai.cost_per_1k_tokens` | USD | provider, document_type | Cost efficiency metric |
| `ai.cost_variance_pct` | percent | provider, document_type | Estimate accuracy |
| `ai.cost.savings` | USD | provider | Savings from fallback usage |
| `job.processing_time` | seconds | provider, status, retry_count | Processing performance |
| `job.processing_time_by_size` | seconds | size_bucket, provider | Performance by document size |
| `job.retry_count` | retries | provider, status | Retry distribution |
| `job.failures` | count | provider, retry_attempt, error_type | Failure tracking |

### Performance Insights

The Sentry integration provides insights into:

- **P95 processing times** by AI provider
- **Average costs** per provider and document type
- **Failure rates** and retry patterns
- **Document processing throughput**
- **Queue depth and worker utilization**
- **Cost estimation accuracy**

## API Endpoints

### Core Endpoints

- `POST /api/upload` - Upload a document for processing
- `POST /api/jobs` - Create a processing job for an uploaded document
- `GET /api/jobs/{job_id}` - Get job status and results
- `GET /api/jobs` - List all jobs with filtering options
- `GET /api/stats` - System statistics and metrics
- `GET /api/providers` - List available AI providers
- `POST /api/estimate-cost` - Estimate processing cost for a document

### Demo Endpoints

- `POST /api/demo/generate-jobs` - Generate synthetic jobs for testing

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/ai_doc_summary

# Redis
REDIS_URL=redis://redis:6379/0

# AI Providers (optional in demo mode)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Sentry (optional)
SENTRY_DSN=https://...@sentry.io/...
ENVIRONMENT=development
APP_VERSION=1.0.0

# Demo Mode
DEMO_MODE=true
DEMO_FAILURE_RATE=0.1
```

## Monitoring & Debugging

### View Celery Worker Logs
```bash
docker-compose logs -f celery
```

### Check Job Statistics
```bash
docker-compose exec celery python -c "
from app.database import SessionLocal
from app.models import Job
from sqlalchemy import func
db = SessionLocal()
stats = db.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
for status, count in stats:
    print(f'{status.value}: {count}')
"
```

### Monitor Queue Depth
```bash
docker-compose exec redis redis-cli LLEN celery
```

## System Requirements

- **Minimum**: 2 CPU cores, 4GB RAM
- **Recommended**: 4 CPU cores, 8GB RAM
- **Storage**: 10GB for documents and database

## Troubleshooting

### Services not starting
```bash
# Check service status
docker-compose ps

# View detailed logs
docker-compose logs backend celery postgres redis
```

### Jobs stuck in pending
```bash
# Restart workers
docker-compose restart celery

# Check Redis connectivity
docker-compose exec redis redis-cli ping
```

### Frontend not loading
```bash
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

## Development

### Running locally without Docker
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Celery
celery -A app.celery_app worker --loglevel=info
```

## License

MIT

## Support

For issues and questions, please check the logs first:
```bash
docker-compose logs --tail=100
```

For Sentry-specific metrics and traces, access your Sentry dashboard and navigate to:
- Performance > Transactions > process_document
- Discover > Metrics for custom queries
- Dashboards > Create custom dashboards using the metrics above