"""Agent 3: Fix Suggester - Suggest fixes using RAG."""
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from core.config import settings
from rag.knowledge_base import KNOWLEDGE_BASE
import json
import re

llm = AzureChatOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    azure_deployment=settings.azure_openai_deployment,
    api_key=settings.azure_openai_api_key,
    api_version=settings.azure_openai_api_version,
    temperature=0.0
)

FIX_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a CI/CD troubleshooting expert for UBS DevCloud.

Given a failure classification and similar past failures, provide a specific, actionable fix.

Return ONLY valid JSON:
{{
  "suggested_fix": "clear step-by-step fix instructions",
  "commands": ["command 1", "command 2", "command 3"],
  "confidence": 0.85
}}

Be specific. Include actual commands, file paths, and concrete steps."""),
    ("user", """Error: {error_type}
Category: {category}
Keywords: {keywords}

Similar past failures:
{similar_cases}

What is the fix?""")
])

def find_similar_cases(error_type: str, category: str, keywords: list) -> list:
    """Simple similarity search in knowledge base."""
    matches = []
    
    # Exact category match
    for kb_item in KNOWLEDGE_BASE:
        if kb_item["category"] == category:
            matches.append(kb_item)
    
    # If no category matches, try keyword overlap
    if not matches:
        for kb_item in KNOWLEDGE_BASE:
            kb_keywords = kb_item["description"].lower().split()
            overlap = sum(1 for kw in keywords if kw.lower() in kb_keywords)
            if overlap > 0:
                matches.append(kb_item)
    
    # Return top 3
    return matches[:3]

def format_similar_cases(cases: list) -> str:
    """Format cases for prompt."""
    if not cases:
        return "No similar cases found."
    
    output = []
    for i, case in enumerate(cases, 1):
        output.append(f"{i}. {case['error_type']} (seen {case['seen_count']}x)")
        output.append(f"   Fix: {case['fix']}")
        output.append(f"   Commands: {', '.join(case['commands'][:2])}")
    return "\n".join(output)

def parse_json_response(text: str) -> dict:
    """Extract JSON from response."""
    text = text.strip()
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {
            "suggested_fix": "Unable to determine fix. Check logs manually.",
            "commands": ["Review logs", "Search DevCloud community"],
            "confidence": 0.3
        }

async def fix_suggester_agent(state: dict) -> dict:
    """Suggest fixes based on classification and RAG."""
    print("\n[Agent 3: Fix Suggester] Starting...")
    
    parsed = state["parsed_errors"]
    category = state["failure_category"]
    keywords = state["error_keywords"]
    
    # RAG: Find similar cases
    similar = find_similar_cases(parsed["error_type"], category, keywords)
    similar_text = format_similar_cases(similar)
    
    print(f"[Agent 3] Found {len(similar)} similar cases")
    
    chain = FIX_PROMPT | llm
    response = await chain.ainvoke({
        "error_type": parsed["error_type"],
        "category": category,
        "keywords": ", ".join(keywords),
        "similar_cases": similar_text
    })
    
    result = parse_json_response(response.content)
    
    print(f"[Agent 3] Fix confidence: {result['confidence']:.0%}")
    print(f"[Agent 3] Suggested: {result['suggested_fix'][:80]}...")
    
    return {
        "suggested_fix": result["suggested_fix"],
        "fix_commands": result["commands"]
    }
