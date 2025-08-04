from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DocumentType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"
    UNKNOWN = "unknown"

class AIProvider(str, enum.Enum):
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT35 = "openai_gpt35"
    ANTHROPIC_CLAUDE = "anthropic_claude"
    GOOGLE_GEMINI = "google_gemini"

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    document_type = Column(SQLEnum(DocumentType), default=DocumentType.UNKNOWN)
    file_size = Column(Integer)  # in bytes
    file_path = Column(String)
    upload_date = Column(DateTime, default=func.now())
    user_id = Column(String, nullable=True)
    doc_metadata = Column(JSON, default={})
    
class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, index=True)
    ai_provider = Column(SQLEnum(AIProvider))
    fallback_provider = Column(SQLEnum(AIProvider), nullable=True)
    created_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    processing_time = Column(Float, nullable=True)  # in seconds
    
    # Summary results
    summary = Column(Text, nullable=True)
    key_points = Column(JSON, default=[])
    entities = Column(JSON, default=[])
    
    # Cost tracking
    estimated_tokens = Column(Integer, default=0)
    actual_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Demo fields
    is_demo = Column(Boolean, default=False)
    demo_delay = Column(Float, default=0.0)  # simulated processing time

class SystemStats(Base):
    __tablename__ = "system_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now())
    total_jobs = Column(Integer, default=0)
    pending_jobs = Column(Integer, default=0)
    processing_jobs = Column(Integer, default=0)
    completed_jobs = Column(Integer, default=0)
    failed_jobs = Column(Integer, default=0)
    
    total_documents = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    avg_processing_time = Column(Float, default=0.0)
    
    provider_usage = Column(JSON, default={})  # {provider: count}
    document_types = Column(JSON, default={})  # {type: count}
    hourly_stats = Column(JSON, default={})  # hourly breakdown