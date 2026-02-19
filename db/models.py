"""Database models for storing CI failures and RCA results."""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class CIFailure(Base):
    __tablename__ = "ci_failures"
    
    id = Column(Integer, primary_key=True, index=True)
    failure_id = Column(String, unique=True, index=True)
    
    # Pipeline Info
    pipeline_id = Column(String, index=True)
    project_name = Column(String, index=True)
    job_name = Column(String)
    stage = Column(String)
    job_status = Column(String)
    
    # Log Content
    raw_log = Column(Text)
    
    # RCA Results
    error_type = Column(String)
    error_keywords = Column(JSON)  # List of keywords
    failure_category = Column(String)  # Infra, Auth, Dependency, Test, Config
    root_cause = Column(Text)
    suggested_fix = Column(Text)
    fix_commands = Column(JSON)  # List of commands
    confidence = Column(Float)
    
    # Similar Cases
    similar_cases = Column(JSON)  # List of similar failure IDs
    seen_count = Column(Integer, default=0)
    
    # Metadata
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "failure_id": self.failure_id,
            "pipeline_id": self.pipeline_id,
            "project_name": self.project_name,
            "job_name": self.job_name,
            "stage": self.stage,
            "job_status": self.job_status,
            "error_type": self.error_type,
            "error_keywords": self.error_keywords,
            "failure_category": self.failure_category,
            "root_cause": self.root_cause,
            "suggested_fix": self.suggested_fix,
            "fix_commands": self.fix_commands,
            "confidence": self.confidence,
            "similar_cases": self.similar_cases,
            "seen_count": self.seen_count,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
