from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime, timedelta
import uuid

from .config import settings
from .database import get_db, init_db
from .models import Document, Job, JobStatus, DocumentType, AIProvider as AIProviderEnum
from .document_processor import DocumentProcessor
from .ai_providers.manager import AIProviderManager
from .tasks import process_document, generate_demo_jobs, calculate_system_stats
from pydantic import BaseModel
from .sentry_config import init_sentry

# Initialize Sentry
init_sentry()

# Initialize FastAPI app
app = FastAPI(title="AI Document Summary API", version="1.0.0")

# CORS middleware with support for Sentry headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=settings.cors_allow_headers,
    expose_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    # Create upload directory if it doesn't exist
    os.makedirs(settings.storage_path, exist_ok=True)

# Pydantic models for requests/responses
class JobCreate(BaseModel):
    document_id: int
    ai_provider: AIProviderEnum
    fallback_provider: Optional[AIProviderEnum] = None

class JobResponse(BaseModel):
    id: int
    document_id: int
    status: JobStatus
    ai_provider: AIProviderEnum
    fallback_provider: Optional[AIProviderEnum]
    created_at: datetime
    completed_at: Optional[datetime]
    summary: Optional[str]
    key_points: List[str]
    entities: List[dict]
    estimated_cost: float
    actual_cost: float
    error_message: Optional[str]

class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    document_type: DocumentType
    file_size: int
    upload_date: datetime

class StatsResponse(BaseModel):
    total_jobs: int
    pending_jobs: int
    processing_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_documents: int
    total_cost: float
    avg_processing_time: float
    provider_usage: dict
    document_types: dict

class CostEstimate(BaseModel):
    estimated_tokens: int
    estimated_cost: float
    provider: str

# Routes
@app.get("/")
async def root():
    return {"message": "AI Document Summary API", "version": "1.0.0"}

@app.post("/api/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a document for processing"""
    
    # Validate file size (max 10MB)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.storage_path, unique_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Detect document type
    doc_type = DocumentProcessor.detect_document_type(file.filename)
    
    # Create document record
    document = Document(
        filename=unique_filename,
        original_filename=file.filename,
        document_type=doc_type,
        file_size=file.size,
        file_path=file_path
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        original_filename=document.original_filename,
        document_type=document.document_type,
        file_size=document.file_size,
        upload_date=document.upload_date
    )

@app.post("/api/jobs", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new processing job"""
    
    # Verify document exists
    document = db.query(Document).filter(Document.id == job_data.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Estimate cost
    manager = AIProviderManager()
    try:
        text, _ = DocumentProcessor.extract_text(document.file_path, document.document_type)
        estimated_cost = manager.estimate_cost(text, job_data.ai_provider)
        estimated_tokens = len(text) // 4
    except:
        estimated_cost = 0.1  # Default estimate
        estimated_tokens = 1000
    
    # Create job
    job = Job(
        document_id=job_data.document_id,
        ai_provider=job_data.ai_provider,
        fallback_provider=job_data.fallback_provider,
        estimated_tokens=estimated_tokens,
        estimated_cost=estimated_cost,
        is_demo=settings.demo_mode
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Queue processing task
    from .tasks import process_document
    
    if settings.demo_mode and not settings.redis_url.startswith("redis://"):
        # In demo mode without Redis, process synchronously
        try:
            process_document(job.id)
        except:
            pass  # Will be handled by the task
    else:
        process_document.delay(job.id)
    
    return JobResponse(
        id=job.id,
        document_id=job.document_id,
        status=job.status,
        ai_provider=job.ai_provider,
        fallback_provider=job.fallback_provider,
        created_at=job.created_at,
        completed_at=job.completed_at,
        summary=job.summary,
        key_points=job.key_points or [],
        entities=job.entities or [],
        estimated_cost=job.estimated_cost,
        actual_cost=job.actual_cost,
        error_message=job.error_message
    )

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get job details"""
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(
        id=job.id,
        document_id=job.document_id,
        status=job.status,
        ai_provider=job.ai_provider,
        fallback_provider=job.fallback_provider,
        created_at=job.created_at,
        completed_at=job.completed_at,
        summary=job.summary,
        key_points=job.key_points or [],
        entities=job.entities or [],
        estimated_cost=job.estimated_cost,
        actual_cost=job.actual_cost,
        error_message=job.error_message
    )

@app.get("/api/jobs", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[JobStatus] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List jobs with optional filtering"""
    
    query = db.query(Job)
    
    if status:
        query = query.filter(Job.status == status)
    
    jobs = query.order_by(Job.created_at.desc()).limit(limit).offset(offset).all()
    
    return [
        JobResponse(
            id=job.id,
            document_id=job.document_id,
            status=job.status,
            ai_provider=job.ai_provider,
            fallback_provider=job.fallback_provider,
            created_at=job.created_at,
            completed_at=job.completed_at,
            summary=job.summary,
            key_points=job.key_points or [],
            entities=job.entities or [],
            estimated_cost=job.estimated_cost,
            actual_cost=job.actual_cost,
            error_message=job.error_message
        )
        for job in jobs
    ]

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    
    from sqlalchemy import func
    from .models import SystemStats
    
    # Get latest stats or calculate on the fly
    latest_stats = db.query(SystemStats).order_by(SystemStats.timestamp.desc()).first()
    
    if latest_stats and (datetime.utcnow() - latest_stats.timestamp).seconds < 300:
        # Use cached stats if less than 5 minutes old
        return StatsResponse(
            total_jobs=latest_stats.total_jobs,
            pending_jobs=latest_stats.pending_jobs,
            processing_jobs=latest_stats.processing_jobs,
            completed_jobs=latest_stats.completed_jobs,
            failed_jobs=latest_stats.failed_jobs,
            total_documents=latest_stats.total_documents,
            total_cost=latest_stats.total_cost,
            avg_processing_time=latest_stats.avg_processing_time,
            provider_usage=latest_stats.provider_usage or {},
            document_types=latest_stats.document_types or {}
        )
    
    # Calculate fresh stats
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
    for doc_type, count in db.query(Document.document_type, func.count()).group_by(Document.document_type):
        doc_types[doc_type.value if doc_type else "unknown"] = count
    
    return StatsResponse(
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

@app.post("/api/estimate-cost", response_model=CostEstimate)
async def estimate_cost(
    file: UploadFile = File(...),
    provider: AIProviderEnum = AIProviderEnum.OPENAI_GPT35
):
    """Estimate processing cost for a document"""
    
    # Save temporary file
    temp_path = f"/tmp/{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text
        doc_type = DocumentProcessor.detect_document_type(file.filename)
        text, _ = DocumentProcessor.extract_text(temp_path, doc_type)
        
        # Estimate cost
        manager = AIProviderManager()
        estimated_tokens = len(text) // 4
        estimated_cost = manager.estimate_cost(text, provider)
        
        return CostEstimate(
            estimated_tokens=estimated_tokens,
            estimated_cost=estimated_cost,
            provider=provider.value
        )
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/demo/generate-jobs")
async def generate_demo_data(count: int = 5):
    """Generate demo jobs for testing"""
    
    if not settings.demo_mode:
        raise HTTPException(status_code=403, detail="Demo mode is disabled")
    
    result = generate_demo_jobs.delay(count)
    return {"message": f"Generating {count} demo jobs", "task_id": result.id}

@app.get("/api/providers")
async def list_providers():
    """List available AI providers"""
    
    manager = AIProviderManager()
    available = manager.get_available_providers()
    
    provider_display_names = {
        "openai_gpt4": "OpenAI GPT-4",
        "openai_gpt35": "OpenAI GPT-3.5",
        "anthropic_claude": "Anthropic Claude",
        "google_gemini": "Google Gemini"
    }
    
    providers = []
    for provider in AIProviderEnum:
        providers.append({
            "id": provider.value,
            "name": provider_display_names.get(provider.value, provider.value.replace("_", " ").title()),
            "available": provider in available,
            "input_cost": getattr(settings, f"{provider.value.lower()}_input_cost", 0),
            "output_cost": getattr(settings, f"{provider.value.lower()}_output_cost", 0)
        })
    
    return providers

@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: int, db: Session = Depends(get_db)):
    """Cancel a pending job"""
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    
    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Job cancelled successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)