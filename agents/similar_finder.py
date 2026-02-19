"""Agent 4: Similar Case Finder - Find past similar failures."""
from rag.knowledge_base import KNOWLEDGE_BASE

async def similar_finder_agent(state: dict) -> dict:
    """Find similar past failures from knowledge base."""
    print("\n[Agent 4: Similar Finder] Starting...")
    
    category = state["failure_category"]
    error_type = state["parsed_errors"]["error_type"]
    
    # Simple lookup in knowledge base
    similar_cases = []
    seen_count = 0
    
    for kb_item in KNOWLEDGE_BASE:
        if kb_item["category"] == category or error_type.lower() in kb_item["error_type"].lower():
            similar_cases.append({
                "error_type": kb_item["error_type"],
                "seen_count": kb_item["seen_count"],
                "fix": kb_item["fix"]
            })
            seen_count += kb_item["seen_count"]
    
    print(f"[Agent 4] Found {len(similar_cases)} similar cases")
    print(f"[Agent 4] Total occurrences: {seen_count}")
    
    return {
        "similar_cases": similar_cases[:3],  # Top 3
        "seen_count": seen_count
    }
