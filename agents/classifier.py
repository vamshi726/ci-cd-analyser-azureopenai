"""Agent 2: Failure Classifier - Categorize CI failures."""
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from core.config import settings
import json
import re

llm = AzureChatOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    azure_deployment=settings.azure_openai_deployment,
    api_key=settings.azure_openai_api_key,
    api_version=settings.azure_openai_api_version,
    temperature=0.0
)

CLASSIFIER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a CI/CD failure classification expert for UBS DevCloud.

Classify failures into ONE of these categories:
1. Infrastructure - Runner issues, OOM, Docker pull failed, network timeout
2. Auth - Vault failures, token expired, namespace mismatch, permission denied
3. Dependency - Nexus errors, npm/maven failures, artifact not found
4. Test - JUnit failures, E2E timeout, assertion errors
5. Misconfiguration - terraform fmt, YAML errors, missing env vars
6. Runner - Runner timeout, no available runners

Return ONLY valid JSON:
{{
  "category": "one of the 6 categories above",
  "confidence": 0.85,
  "reasoning": "why this category"
}}"""),
    ("user", """Error Type: {error_type}
Keywords: {keywords}
Failing Tool: {failing_tool}
Job: {job_name} | Stage: {stage}

Classify this failure:""")
])

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
            "category": "Misconfiguration",
            "confidence": 0.5,
            "reasoning": "Failed to classify"
        }

async def classifier_agent(state: dict) -> dict:
    """Classify the failure type."""
    print("\n[Agent 2: Classifier] Starting...")
    
    parsed = state["parsed_errors"]
    
    chain = CLASSIFIER_PROMPT | llm
    response = await chain.ainvoke({
        "error_type": parsed["error_type"],
        "keywords": ", ".join(parsed["keywords"]),
        "failing_tool": parsed["failing_tool"],
        "job_name": state["job_name"],
        "stage": state["stage"]
    })
    
    result = parse_json_response(response.content)
    
    print(f"[Agent 2] Category: {result['category']} ({result['confidence']:.0%})")
    print(f"[Agent 2] Reasoning: {result['reasoning']}")
    
    return {
        "failure_category": result["category"],
        "category_confidence": result["confidence"]
    }
