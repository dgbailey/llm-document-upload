from celery import Task
from .celery_app import celery_app
from .database import SessionLocal
from .models import Job, Document, JobStatus, AIProvider as AIProviderEnum
from .ai_providers.manager import AIProviderManager
from .document_processor import DocumentProcessor
from datetime import datetime, timedelta
import random
import asyncio
import time
import sentry_sdk
from sentry_sdk import start_span, set_tag, set_context, get_current_span, metrics

class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        """Success handler"""
        pass
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Error handler"""
        pass

@celery_app.task(base=CallbackTask, bind=True, max_retries=3)
def process_document(self=None, job_id: int=None):
    """Main task to process a document and generate summary"""
    
    # Start a Sentry transaction for this task
    with sentry_sdk.start_transaction(op="task", name="process_document") as transaction:
        # Set basic tags on the transaction (for searchability)
        transaction.set_tag("job.id", job_id)
        transaction.set_tag("task.name", "process_document")
        
        # Get the current span (which is the transaction) to set attributes
        current_span = get_current_span()
        if current_span:
            current_span.set_data("job.id", int(job_id))
        
        db = SessionLocal()
        try:
            # Get job and document
            with start_span(op="db.query", description="Fetch job and document"):
                job = db.query(Job).filter(Job.id == job_id).first()
                if not job:
                    raise ValueError(f"Job {job_id} not found")
                
                document = db.query(Document).filter(Document.id == job.document_id).first()
                if not document:
                    raise ValueError(f"Document {job.document_id} not found")
            
            # Set document and provider tags on transaction
            transaction.set_tag("document.id", document.id)
            transaction.set_tag("document.type", document.document_type)
            transaction.set_tag("ai.provider", job.ai_provider)
            if job.fallback_provider:
                transaction.set_tag("ai.fallback_provider", job.fallback_provider)
            transaction.set_tag("job.is_demo", job.is_demo)
            transaction.set_tag("job.retry_count", job.retry_count)  # Add retry count as tag
            
            # Set span attributes on the transaction for metrics
            current_span = get_current_span()
            if current_span:
                current_span.set_data("document.size", int(document.file_size) if document.file_size is not None else 0)
                current_span.set_data("document.id", int(document.id))
                current_span.set_data("document.type", str(document.document_type))
                current_span.set_data("ai.provider", str(job.ai_provider))
                current_span.set_data("ai.cost.estimated", float(job.estimated_cost) if job.estimated_cost is not None else 0.0)
                current_span.set_data("ai.tokens.estimated", int(job.estimated_tokens) if job.estimated_tokens is not None else 0)
                current_span.set_data("job.is_demo", bool(job.is_demo))
                current_span.set_data("job.retry_count", int(job.retry_count))  # Add retry count to span data
            
            # Update job status
            with start_span(op="db.update", description="Update job status to processing"):
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.utcnow()
                db.commit()
        
            # Extract text from document
            with start_span(op="document.extract", description="Extract text from document") as extract_span:
                text, page_count = DocumentProcessor.extract_text(
                    document.file_path,
                    document.document_type
                )
                
                if not text:
                    raise ValueError("No text could be extracted from document")
                
                # Use set_data for span-specific data
                extract_span.set_data("text.length", int(len(text)))
                extract_span.set_data("text.estimated_tokens", int(len(text) // 4))
                extract_span.set_data("document.pages", int(page_count) if page_count is not None else 0)
                extract_span.set_data("document.id", int(document.id))
                extract_span.set_data("document.type", str(document.document_type))
                extract_span.set_data("document.size", int(document.file_size) if document.file_size is not None else 0)
                
                # Record metrics for document processing
                metrics.distribution(
                    key="document.size",
                    value=int(document.file_size) if document.file_size else 0,
                    unit="byte",
                    tags={
                        "document_type": str(document.document_type),
                        "provider": str(job.ai_provider)
                    }
                )
                metrics.gauge(
                    key="document.pages",
                    value=int(page_count) if page_count else 0,
                    unit="page",
                    tags={"document_type": str(document.document_type)}
                )
        
            # Initialize AI provider manager
            manager = AIProviderManager()
            
            # Run async summarization
            with start_span(op="ai.summarize", description="AI summarization") as ai_span:
                # Set data before processing
                ai_span.set_data("ai.provider.primary", str(job.ai_provider))
                ai_span.set_data("ai.provider.fallback", str(job.fallback_provider) if job.fallback_provider else "none")
                ai_span.set_data("ai.cost.estimated", float(job.estimated_cost) if job.estimated_cost is not None else 0.0)
                ai_span.set_data("ai.tokens.estimated", int(job.estimated_tokens) if job.estimated_tokens is not None else 0)
                ai_span.set_data("ai.demo_mode", bool(job.is_demo))
                # Also set document size on AI span for aggregation
                ai_span.set_data("document.size", int(document.file_size) if document.file_size is not None else 0)
                ai_span.set_data("document.id", int(document.id))
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = loop.run_until_complete(
                        manager.summarize_with_fallback(
                            text,
                            job.ai_provider,
                            job.fallback_provider,
                            demo_mode=job.is_demo
                        )
                    )
                finally:
                    loop.close()
                
                # Set AI processing result data
                ai_span.set_data("ai.tokens.actual", int(result.tokens_used) if result.tokens_used is not None else 0)
                ai_span.set_data("ai.cost.actual", float(result.cost) if result.cost is not None else 0.0)
                ai_span.set_data("ai.provider.used", str(result.provider_used))
                ai_span.set_data("ai.summary.length", int(len(result.summary)) if result.summary else 0)
                ai_span.set_data("ai.key_points.count", int(len(result.key_points)) if result.key_points else 0)
                ai_span.set_data("ai.entities.count", int(len(result.entities)) if result.entities else 0)
                
                # Record token metrics
                metrics.distribution(
                    key="ai.tokens.used",
                    value=int(result.tokens_used) if result.tokens_used else 0,
                    unit="token",
                    tags={
                        "provider": str(result.provider_used),
                        "document_id": str(document.id),
                        "is_demo": str(job.is_demo)
                    }
                )
                
                # Record cost metrics
                metrics.distribution(
                    key="ai.cost",
                    value=float(result.cost) if result.cost else 0.0,
                    unit="usd",
                    tags={
                        "provider": str(result.provider_used),
                        "document_type": str(document.document_type)
                    }
                )
                
                # Calculate cost savings
                if job.estimated_cost:
                    ai_span.set_data("ai.cost.savings", float(job.estimated_cost - result.cost))
                    ai_span.set_data("ai.cost.savings_percent", float(((job.estimated_cost - result.cost) / job.estimated_cost) * 100))
                    
                    # Record cost savings metric
                    metrics.gauge(
                        key="ai.cost.savings",
                        value=float(job.estimated_cost - result.cost),
                        unit="usd",
                        tags={"provider": str(result.provider_used)}
                    )
        
            # Update job with results
            with start_span(op="db.update", description="Save job results") as update_span:
                job.summary = result.summary
                job.key_points = result.key_points
                job.entities = result.entities
                job.actual_tokens = result.tokens_used
                job.actual_cost = result.cost
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.processing_time = (job.completed_at - job.started_at).total_seconds()
                
                # Add data to the update span
                update_span.set_data("job.id", int(job_id))
                update_span.set_data("job.final_status", "completed")
                update_span.set_data("job.processing_time_seconds", float(job.processing_time))
                
                # Record processing time metric
                metrics.distribution(
                    key="job.processing_time",
                    value=float(job.processing_time) if job.processing_time else 0.0,
                    unit="second",
                    tags={
                        "provider": str(result.provider_used),
                        "status": "completed",
                        "retry_count": str(job.retry_count),
                        "document_type": str(document.document_type)
                    }
                )
                
                # Record retry metrics
                metrics.distribution(
                    key="job.retry_count",
                    value=int(job.retry_count),
                    unit="retry",
                    tags={
                        "provider": str(job.ai_provider),
                        "status": "completed"
                    }
                )
                
                # Record cost efficiency (cost per 1000 tokens)
                if result.tokens_used > 0:
                    cost_per_1k_tokens = (result.cost / result.tokens_used) * 1000
                    metrics.distribution(
                        key="ai.cost_per_1k_tokens",
                        value=float(cost_per_1k_tokens),
                        unit="usd",
                        tags={
                            "provider": str(result.provider_used),
                            "document_type": str(document.document_type)
                        }
                    )
                
                # Record token density (tokens per KB)
                if document.file_size > 0:
                    tokens_per_kb = result.tokens_used / (document.file_size / 1024)
                    metrics.distribution(
                        key="document.token_density",
                        value=float(tokens_per_kb),
                        unit="token/kb",
                        tags={
                            "document_type": str(document.document_type),
                            "provider": str(result.provider_used)
                        }
                    )
                
                # Record cost variance
                if job.estimated_cost > 0:
                    cost_variance_pct = ((result.cost - job.estimated_cost) / job.estimated_cost) * 100
                    metrics.distribution(
                        key="ai.cost_variance_pct",
                        value=float(cost_variance_pct),
                        unit="percent",
                        tags={
                            "provider": str(result.provider_used),
                            "document_type": str(document.document_type)
                        }
                    )
                
                # Record document size bucket for analysis
                size_bucket = "small"  # < 100KB
                if document.file_size > 1024 * 1024:  # > 1MB
                    size_bucket = "large"
                elif document.file_size > 100 * 1024:  # > 100KB
                    size_bucket = "medium"
                
                metrics.distribution(
                    key="job.processing_time_by_size",
                    value=float(job.processing_time) if job.processing_time else 0.0,
                    unit="second",
                    tags={
                        "size_bucket": size_bucket,
                        "provider": str(result.provider_used)
                    }
                )
                
                db.commit()
            
            # Set final transaction tags
            transaction.set_tag("job.status", "completed")
            transaction.set_tag("ai.provider.final", result.provider_used)
            
            # Update transaction span attributes with final metrics
            current_span = get_current_span()
            if current_span:
                current_span.set_data("ai.tokens.actual", int(result.tokens_used) if result.tokens_used is not None else 0)
                current_span.set_data("ai.cost.actual", float(result.cost) if result.cost is not None else 0.0)
                current_span.set_data("ai.provider.used", str(result.provider_used))
                current_span.set_data("job.processing_time", float(job.processing_time) if job.processing_time else 0.0)
                current_span.set_data("job.status", "completed")
            
            # Set data on the transaction for detailed view
            transaction.set_data("job.id", job_id)
            transaction.set_data("job.tokens.total", result.tokens_used)
            transaction.set_data("job.cost.total", result.cost)
            transaction.set_data("job.processing_time_seconds", job.processing_time)
            transaction.set_data("job.document.type", document.document_type)
            transaction.set_data("job.document.size_bytes", document.file_size)
            if job.estimated_cost:
                transaction.set_data("job.cost.savings", job.estimated_cost - result.cost)
            
            # Set detailed context for Sentry
            set_context("job_metrics", {
                "job_id": job_id,
                "provider_used": result.provider_used,
                "tokens": {
                    "estimated": job.estimated_tokens,
                    "actual": result.tokens_used,
                    "difference": job.estimated_tokens - result.tokens_used if job.estimated_tokens else 0
                },
                "cost": {
                    "estimated": job.estimated_cost,
                    "actual": result.cost,
                    "savings": job.estimated_cost - result.cost if job.estimated_cost else 0
                },
                "document": {
                    "type": document.document_type,
                    "size_bytes": document.file_size,
                    "text_length": len(text),
                    "pages": page_count
                },
                "processing": {
                    "time_seconds": job.processing_time,
                    "summary_length": len(result.summary) if result.summary else 0,
                    "key_points_count": len(result.key_points) if result.key_points else 0,
                    "entities_count": len(result.entities) if result.entities else 0
                }
            })
            
            return {
                "job_id": job_id,
                "status": "completed",
                "summary": result.summary[:200] + "...",
                "tokens_used": result.tokens_used,
                "cost": result.cost
            }
            
        except Exception as e:
            # Set error tags on transaction
            transaction.set_tag("job.status", "failed")
            transaction.set_tag("error.type", type(e).__name__)
            
            # Set error data on transaction
            transaction.set_data("error.message", str(e))
            transaction.set_data("job.id", job_id)
            
            # Handle failure
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.retry_count += 1
                
                # Update Sentry span with actual retry count after increment
                if 'job' in locals() and job:
                    transaction.set_data("job.retry_count", job.retry_count)
                    current_span = get_current_span()
                    if current_span:
                        current_span.set_data("job.retry_count", int(job.retry_count))
                    
                    # Record failure metrics
                    metrics.increment(
                        key="job.failures",
                        value=1,
                        tags={
                            "provider": str(job.ai_provider),
                            "retry_attempt": str(job.retry_count),
                            "error_type": type(e).__name__
                        }
                    )
                
                # Retry if under max retries
                if job.retry_count < job.max_retries and self:
                    job.status = JobStatus.PENDING
                    db.commit()
                    # Retry with exponential backoff
                    raise self.retry(exc=e, countdown=2 ** job.retry_count)
                else:
                    job.completed_at = datetime.utcnow()
                    db.commit()
            
            raise e
            
        finally:
            db.close()

@celery_app.task
def generate_demo_jobs(count: int = 5):
    """Generate demo jobs for testing"""
    
    db = SessionLocal()
    try:
        demo_texts = [
            "Annual Financial Report 2023: Revenue increased by 25% year-over-year...",
            "Technical Documentation: This guide covers the installation and setup...",
            "Legal Contract: Agreement between Party A and Party B regarding...",
            "Research Paper: Machine Learning Applications in Healthcare...",
            "Meeting Minutes: Q4 2023 Strategy Discussion - Key decisions..."
        ]
        
        providers = list(AIProviderEnum)
        
        for i in range(count):
            # Create demo document
            doc = Document(
                filename=f"demo_doc_{i}.pdf",
                original_filename=f"Demo Document {i}.pdf",
                document_type="pdf",
                file_size=random.randint(10000, 1000000),
                file_path=f"/demo/doc_{i}.pdf",
                doc_metadata={"demo": True, "text": random.choice(demo_texts)}
            )
            db.add(doc)
            db.flush()
            
            # Create demo job
            job = Job(
                document_id=doc.id,
                status=JobStatus.PENDING,
                ai_provider=random.choice(providers),
                fallback_provider=random.choice(providers),
                estimated_tokens=random.randint(1000, 5000),
                estimated_cost=random.uniform(0.01, 0.50),
                is_demo=True,
                demo_delay=random.uniform(2, 10)
            )
            db.add(job)
            db.flush()
            
            # Process the job
            process_document.delay(job.id)
        
        db.commit()
        return {"created": count, "status": "demo jobs queued"}
        
    finally:
        db.close()

@celery_app.task
def cleanup_old_jobs(days: int = 30):
    """Clean up old completed/failed jobs"""
    
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old jobs
        deleted = db.query(Job).filter(
            Job.completed_at < cutoff_date,
            Job.status.in_([JobStatus.COMPLETED, JobStatus.FAILED])
        ).delete()
        
        db.commit()
        return {"deleted_jobs": deleted}
        
    finally:
        db.close()

@celery_app.task
def calculate_system_stats():
    """Calculate and store system statistics"""
    
    db = SessionLocal()
    try:
        from sqlalchemy import func
        from .models import SystemStats
        
        # Calculate stats
        total_jobs = db.query(Job).count()
        pending_jobs = db.query(Job).filter(Job.status == JobStatus.PENDING).count()
        processing_jobs = db.query(Job).filter(Job.status == JobStatus.PROCESSING).count()
        completed_jobs = db.query(Job).filter(Job.status == JobStatus.COMPLETED).count()
        failed_jobs = db.query(Job).filter(Job.status == JobStatus.FAILED).count()
        
        total_documents = db.query(Document).count()
        total_cost = db.query(func.sum(Job.actual_cost)).scalar() or 0.0
        
        avg_time = db.query(func.avg(Job.processing_time)).filter(
            Job.status == JobStatus.COMPLETED
        ).scalar() or 0.0
        
        # Provider usage
        provider_usage = {}
        for provider in AIProviderEnum:
            count = db.query(Job).filter(Job.ai_provider == provider).count()
            provider_usage[provider.value] = count
        
        # Document types
        doc_types = {}
        for doc_type in db.query(Document.document_type, func.count()).group_by(Document.document_type):
            doc_types[doc_type[0].value if doc_type[0] else "unknown"] = doc_type[1]
        
        # Create stats entry
        stats = SystemStats(
            total_jobs=total_jobs,
            pending_jobs=pending_jobs,
            processing_jobs=processing_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            total_documents=total_documents,
            total_cost=total_cost,
            avg_processing_time=avg_time,
            provider_usage=provider_usage,
            document_types=doc_types
        )
        
        db.add(stats)
        db.commit()
        
        return {
            "total_jobs": total_jobs,
            "pending": pending_jobs,
            "processing": processing_jobs,
            "completed": completed_jobs,
            "failed": failed_jobs
        }
        
    finally:
        db.close()