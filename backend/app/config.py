from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost/ai_doc_summary"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # AI Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Storage
    storage_type: str = "local"  # local, s3, minio
    storage_path: str = "./uploads"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_s3_bucket: Optional[str] = None
    aws_region: str = "us-east-1"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Cost Estimation (per 1000 tokens)
    openai_gpt4_input_cost: float = 0.03
    openai_gpt4_output_cost: float = 0.06
    openai_gpt35_input_cost: float = 0.001
    openai_gpt35_output_cost: float = 0.002
    anthropic_claude_input_cost: float = 0.008
    anthropic_claude_output_cost: float = 0.024
    google_gemini_input_cost: float = 0.00025
    google_gemini_output_cost: float = 0.0005
    
    # Demo Mode
    demo_mode: bool = True
    demo_failure_rate: float = 0.1
    demo_slow_task_rate: float = 0.2
    
    # Sentry configuration
    sentry_dsn: Optional[str] = None
    environment: str = "development"
    app_version: str = "1.0.0"
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_headers: list = ["*"]  # Allow all headers including sentry-trace and baggage
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()