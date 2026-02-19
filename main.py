"""Main FastAPI application with GitLab integration and RCA agents."""
from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import requests
import uuid

from core.config import settings
from db.database import init_db, get_session
from db.models import CIFailure
from agents.graph import run_rca_analysis

app = FastAPI(title="CI/CD RCA System", version="1.0.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    await init_db()
    print("✅ Database initialized")

# ============================================================
# MODELS
# ============================================================

class PipelineInfo(BaseModel):
    pipeline_id: str
    status: str
    ref: str
    web_url: str

class JobLog(BaseModel):
    job_id: int
    job_name: str
    job_status: str
    logs: str

class PipelineLogsResponse(BaseModel):
    pipeline_id: str
    pipeline_status: str
    jobs: List[JobLog]

class RCARequest(BaseModel):
    pipeline_id: str
    project_name: str
    job_name: str
    stage: str
    raw_log: str
    job_status: str

class RCAResponse(BaseModel):
    failure_id: str
    error_type: str
    category: str
    root_cause: str
    suggested_fix: str
    confidence: float
    similar_cases: List[dict]
    seen_count: int
    processing_time_ms: int

class MetricsSummary(BaseModel):
    total_failures: int
    avg_processing_time_ms: float
    category_breakdown: dict

# ============================================================
# GITLAB ENDPOINTS (Your existing code, improved)
# ============================================================

def gitlab_headers():
    return {"PRIVATE-TOKEN": settings.gitlab_token}

@app.get("/api/latest-pipeline", response_model=PipelineInfo)
def get_latest_pipeline():
    """Get the latest pipeline for the configured project."""
    url = f"{settings.api_base}/projects/{settings.project_id}/pipelines?per_page=1"
    res = requests.get(url, headers=gitlab_headers())
    
    if res.status_code != 200:
        return {"error": res.text}
    
    pipeline = res.json()[0]
    return {
        "pipeline_id": str(pipeline["id"]),
        "status": pipeline["status"],
        "ref": pipeline.get("ref", "unknown"),
        "web_url": pipeline.get("web_url", "")
    }

@app.get("/api/latest-pipeline-logs", response_model=PipelineLogsResponse)
def get_latest_pipeline_logs():
    """Get logs for all jobs in the latest pipeline."""
    # 1) Get latest pipeline
    pipelines_url = f"{settings.api_base}/projects/{settings.project_id}/pipelines?per_page=1"
    pipelines_res = requests.get(pipelines_url, headers=gitlab_headers())
    
    if pipelines_res.status_code != 200:
        return {"error": "Failed to fetch pipelines", "details": pipelines_res.text}
    
    pipeline = pipelines_res.json()[0]
    pipeline_id = pipeline["id"]
    
    # 2) Get jobs of that pipeline
    jobs_url = f"{settings.api_base}/projects/{settings.project_id}/pipelines/{pipeline_id}/jobs"
    jobs_res = requests.get(jobs_url, headers=gitlab_headers())
    
    if jobs_res.status_code != 200:
        return {"error": "Failed to fetch jobs", "details": jobs_res.text}
    
    jobs = jobs_res.json()
    
    output = {
        "pipeline_id": str(pipeline_id),
        "pipeline_status": pipeline["status"],
        "jobs": []
    }
    
    # 3) For each job, fetch logs
    for job in jobs:
        job_id = job["id"]
        job_name = job["name"]
        job_status = job["status"]
        
        trace_url = f"{settings.api_base}/projects/{settings.project_id}/jobs/{job_id}/trace"
        trace_res = requests.get(trace_url, headers=gitlab_headers())
        
        logs_text = trace_res.text if trace_res.status_code == 200 else f"ERROR: {trace_res.text}"
        
        output["jobs"].append({
            "job_id": job_id,
            "job_name": job_name,
            "job_status": job_status,
            "logs": logs_text
        })
    
    return output

# ============================================================
# RCA ANALYSIS ENDPOINTS
# ============================================================

async def process_rca_background(
    failure_id: str,
    pipeline_id: str,
    project_name: str,
    job_name: str,
    stage: str,
    raw_log: str,
    job_status: str,
    db: AsyncSession
):
    """Background task to run RCA analysis and save to DB."""
    try:
        # Run the agent pipeline
        result = await run_rca_analysis(
            pipeline_id=pipeline_id,
            project_name=project_name,
            job_name=job_name,
            stage=stage,
            raw_log=raw_log,
            job_status=job_status
        )
        
        # Save to database
        failure = CIFailure(
            failure_id=failure_id,
            pipeline_id=pipeline_id,
            project_name=project_name,
            job_name=job_name,
            stage=stage,
            job_status=job_status,
            raw_log=raw_log[:5000],  # Store first 5000 chars
            error_type=result["parsed_errors"].get("error_type", "Unknown"),
            error_keywords=result["error_keywords"],
            failure_category=result["failure_category"],
            root_cause=result["parsed_errors"].get("error_message", ""),
            suggested_fix=result["suggested_fix"],
            fix_commands=result["fix_commands"],
            confidence=result["total_confidence"],
            similar_cases=[c["error_type"] for c in result["similar_cases"]],
            seen_count=result["seen_count"],
            processing_time_ms=result["processing_time_ms"]
        )
        
        db.add(failure)
        await db.commit()
        
        print(f"✅ RCA saved: {failure_id}")
        
    except Exception as e:
        print(f"❌ RCA failed: {e}")
        await db.rollback()

@app.post("/api/analyze", response_model=dict)
async def analyze_failure(
    request: RCARequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """Trigger RCA analysis for a CI failure."""
    failure_id = str(uuid.uuid4())
    
    # Queue background processing
    background_tasks.add_task(
        process_rca_background,
        failure_id=failure_id,
        pipeline_id=request.pipeline_id,
        project_name=request.project_name,
        job_name=request.job_name,
        stage=request.stage,
        raw_log=request.raw_log,
        job_status=request.job_status,
        db=db
    )
    
    return {
        "failure_id": failure_id,
        "status": "processing",
        "message": "RCA analysis started. Check /api/failures/{failure_id} for results."
    }

@app.post("/api/analyze-latest")
async def analyze_latest_pipeline(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """Analyze all failed jobs in the latest pipeline."""
    # Get latest pipeline logs
    pipeline_data = get_latest_pipeline_logs()
    
    results = []
    for job in pipeline_data["jobs"]:
        if job["job_status"] == "failed":
            failure_id = str(uuid.uuid4())
            
            background_tasks.add_task(
                process_rca_background,
                failure_id=failure_id,
                pipeline_id=pipeline_data["pipeline_id"],
                project_name=settings.project_id,
                job_name=job["job_name"],
                stage="unknown",
                raw_log=job["logs"],
                job_status=job["job_status"],
                db=db
            )
            
            results.append({
                "failure_id": failure_id,
                "job_name": job["job_name"],
                "status": "processing"
            })
    
    return {
        "pipeline_id": pipeline_data["pipeline_id"],
        "failures_queued": len(results),
        "results": results
    }

# ============================================================
# QUERY ENDPOINTS
# ============================================================

@app.get("/api/failures", response_model=List[dict])
async def get_failures(
    category: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_session)
):
    """Get list of analyzed failures."""
    query = select(CIFailure).order_by(CIFailure.created_at.desc()).limit(limit)
    
    if category:
        query = query.where(CIFailure.failure_category == category)
    
    result = await db.execute(query)
    failures = result.scalars().all()
    
    return [f.to_dict() for f in failures]

@app.get("/api/failures/{failure_id}", response_model=dict)
async def get_failure_detail(
    failure_id: str,
    db: AsyncSession = Depends(get_session)
):
    """Get detailed RCA for a specific failure."""
    query = select(CIFailure).where(CIFailure.failure_id == failure_id)
    result = await db.execute(query)
    failure = result.scalar_one_or_none()
    
    if not failure:
        return {"error": "Failure not found"}
    
    return failure.to_dict()

@app.get("/api/metrics/summary", response_model=MetricsSummary)
async def get_metrics_summary(db: AsyncSession = Depends(get_session)):
    """Get aggregate metrics."""
    # Total failures
    total_query = select(func.count(CIFailure.id))
    total_result = await db.execute(total_query)
    total = total_result.scalar()
    
    # Avg processing time
    avg_query = select(func.avg(CIFailure.processing_time_ms))
    avg_result = await db.execute(avg_query)
    avg_time = avg_result.scalar() or 0
    
    # Category breakdown
    category_query = select(
        CIFailure.failure_category,
        func.count(CIFailure.id)
    ).group_by(CIFailure.failure_category)
    category_result = await db.execute(category_query)
    categories = {cat: count for cat, count in category_result.all()}
    
    return {
        "total_failures": total,
        "avg_processing_time_ms": float(avg_time),
        "category_breakdown": categories
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "CI RCA System"}
