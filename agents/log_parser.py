"""Agent 1: Log Parser - Extract error signatures from CI logs."""
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from core.config import settings
import json
import re

# Initialize Azure OpenAI
llm = AzureChatOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    azure_deployment=settings.azure_openai_deployment,
    api_key=settings.azure_openai_api_key,
    api_version=settings.azure_openai_api_version,
    temperature=0.0
)

PARSER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert CI/CD log analyzer for UBS DevCloud (GitLab).
Extract the PRIMARY error from CI job logs. Return ONLY valid JSON, no markdown.

JSON format:
{{
  "error_type": "descriptive name like TerraformFormatError or VaultAuthFailure",
  "keywords": ["key", "terms", "from", "error"],
  "failing_tool": "tool/service that failed (terraform, vault, nexus, etc)",
  "error_message": "the actual error message from logs"
}}

Focus on the FIRST meaningful error. Ignore warnings and info messages."""),
    ("user", "Job: {job_name} | Stage: {stage} | Status: {job_status}\n\nLogs (last 2000 chars):\n{log_snippet}")
])

def extract_last_n_chars(log: str, n: int = 2000) -> str:
    """Extract last N characters from log (where errors usually are)."""
    if len(log) <= n:
        return log
    return "...\n" + log[-n:]

def parse_json_response(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    # Remove markdown code blocks
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: try to find JSON object
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {
            "error_type": "ParseError",
            "keywords": ["unknown"],
            "failing_tool": "unknown",
            "error_message": "Failed to parse error"
        }

async def log_parser_agent(state: dict) -> dict:
    """Parse CI logs and extract error signatures."""
    print("\n[Agent 1: Log Parser] Starting...")
    
    log_snippet = extract_last_n_chars(state["raw_log"], 2000)
    
    chain = PARSER_PROMPT | llm
    response = await chain.ainvoke({
        "job_name": state["job_name"],
        "stage": state["stage"],
        "job_status": state["job_status"],
        "log_snippet": log_snippet
    })
    
    result = parse_json_response(response.content)
    
    print(f"[Agent 1] Error Type: {result['error_type']}")
    print(f"[Agent 1] Keywords: {result['keywords']}")
    
    return {
        "error_signatures": [result["error_type"]],
        "error_keywords": result["keywords"],
        "parsed_errors": result
    }
