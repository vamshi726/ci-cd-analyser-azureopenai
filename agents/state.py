"""LangGraph agent state definitions."""
from typing import TypedDict, List, Dict, Optional

class AgentState(TypedDict):
    """Shared state between all agents in the graph."""
    
    # Input (from FastAPI)
    pipeline_id: str
    project_name: str
    job_name: str
    stage: str
    raw_log: str
    job_status: str
    
    # Agent 1: Log Parser Output
    error_signatures: List[str]
    error_keywords: List[str]
    parsed_errors: Dict[str, str]
    
    # Agent 2: Classifier Output
    failure_category: str  # Infra, Auth, Dependency, Test, Config, Runner
    category_confidence: float
    
    # Agent 3: Fix Suggester Output
    suggested_fix: str
    fix_commands: List[str]
    
    # Agent 4: Similar Finder Output
    similar_cases: List[Dict[str, str]]
    seen_count: int
    
    # Final Output
    final_rca: str
    total_confidence: float
    processing_time_ms: Optional[int]
