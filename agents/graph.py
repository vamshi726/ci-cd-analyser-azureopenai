"""LangGraph orchestrator - connects all agents."""
from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.log_parser import log_parser_agent
from agents.classifier import classifier_agent
from agents.fix_suggester import fix_suggester_agent
from agents.similar_finder import similar_finder_agent
import time

def create_rca_graph():
    """Create the RCA agent graph."""
    
    workflow = StateGraph(AgentState)
    
    # Add nodes (agents)
    workflow.add_node("log_parser", log_parser_agent)
    workflow.add_node("classifier", classifier_agent)
    workflow.add_node("fix_suggester", fix_suggester_agent)
    workflow.add_node("similar_finder", similar_finder_agent)
    
    # Define edges (flow)
    workflow.set_entry_point("log_parser")
    workflow.add_edge("log_parser", "classifier")
    workflow.add_edge("classifier", "fix_suggester")
    workflow.add_edge("fix_suggester", "similar_finder")
    workflow.add_edge("similar_finder", END)
    
    return workflow.compile()

# Create the graph
rca_graph = create_rca_graph()

async def run_rca_analysis(
    pipeline_id: str,
    project_name: str,
    job_name: str,
    stage: str,
    raw_log: str,
    job_status: str
) -> dict:
    """Run the complete RCA analysis pipeline."""
    
    start_time = time.time()
    
    # Initial state
    initial_state = {
        "pipeline_id": pipeline_id,
        "project_name": project_name,
        "job_name": job_name,
        "stage": stage,
        "raw_log": raw_log,
        "job_status": job_status,
        # Initialize empty fields
        "error_signatures": [],
        "error_keywords": [],
        "parsed_errors": {},
        "failure_category": "",
        "category_confidence": 0.0,
        "suggested_fix": "",
        "fix_commands": [],
        "similar_cases": [],
        "seen_count": 0,
        "final_rca": "",
        "total_confidence": 0.0,
        "processing_time_ms": None
    }
    
    print("\n" + "="*60)
    print("Starting RCA Analysis Pipeline")
    print("="*60)
    
    # Run the graph
    result = await rca_graph.ainvoke(initial_state)
    
    # Calculate processing time
    processing_time = int((time.time() - start_time) * 1000)
    result["processing_time_ms"] = processing_time
    
    # Create final RCA summary
    result["final_rca"] = f"""Root Cause Analysis Complete:

Category: {result['failure_category']}
Error Type: {result['parsed_errors'].get('error_type', 'Unknown')}
Confidence: {result.get('category_confidence', 0.5):.0%}

Root Cause:
{result['parsed_errors'].get('error_message', 'See logs for details')}

Suggested Fix:
{result['suggested_fix']}

Commands:
{chr(10).join('  $ ' + cmd for cmd in result['fix_commands'])}

Similar Cases: Seen {result['seen_count']} times before in knowledge base
"""
    
    result["total_confidence"] = result.get("category_confidence", 0.5)
    
    print("\n" + "="*60)
    print(f"RCA Complete in {processing_time}ms")
    print("="*60)
    
    return result
