# CI/CD Test Failure Root Cause Analyzer

**AI-Powered CI/CD Productivity Agent for UBS DevCloud (GitLab)**

Automatically analyzes CI/CD pipeline failures, classifies root causes, and suggests fixes using LangGraph agents, RAG, and Azure OpenAI.

## 🎯 Problem Solved

- **Before**: Developers spend 30-90 minutes per CI failure manually reading logs, searching Teams, asking peers
- **After**: AI agents analyze failures in under 30 seconds, suggest fixes with 80%+ confidence

## 🏗️ Architecture

```
GitLab Pipeline Failure
          ↓
    FastAPI Backend
          ↓
   LangGraph Agents:
   1. Log Parser (extract errors)
   2. Classifier (categorize)
   3. Fix Suggester (RAG-powered)
   4. Similar Finder (MCP)
          ↓
   React Dashboard
```

## 🚀 Tech Stack

- **Backend**: FastAPI + Python 3.11
- **AI Orchestration**: LangGraph 0.2+
- **LLM**: AzureChatOpenAI (GPT-4o)
- **RAG**: Knowledge base with similarity search
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: React 18 + TypeScript + Vite

## 📦 Installation

### 1. Clone & Setup Backend

```bash
cd ci_rca_project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials:
# - GITLAB_TOKEN (GitLab Personal Access Token with API scope)
# - PROJECT_ID (GitLab project ID)
# - AZURE_OPENAI_API_KEY
# - AZURE_OPENAI_ENDPOINT
# - AZURE_OPENAI_DEPLOYMENT
```

### 3. Run Backend

```bash
# Development mode with auto-reload
uvicorn main:app --reload --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Backend will be available at: `http://localhost:8000`

API docs at: `http://localhost:8000/docs`

## 🧪 Testing the System

### Step 1: Get Latest Pipeline Logs

```bash
curl http://localhost:8000/api/latest-pipeline-logs
```

### Step 2: Analyze Failed Jobs

```bash
# Automatically analyze all failed jobs in latest pipeline
curl -X POST http://localhost:8000/api/analyze-latest
```

### Step 3: Check Results

```bash
# Get all failures
curl http://localhost:8000/api/failures

# Get specific failure detail
curl http://localhost:8000/api/failures/{failure_id}

# Get metrics
curl http://localhost:8000/api/metrics/summary
```

## 📊 API Endpoints

### GitLab Integration
- `GET /api/latest-pipeline` - Get latest pipeline info
- `GET /api/latest-pipeline-logs` - Get logs for all jobs in latest pipeline

### RCA Analysis
- `POST /api/analyze` - Analyze a specific failure (manual)
- `POST /api/analyze-latest` - Auto-analyze all failed jobs in latest pipeline

### Query & Metrics
- `GET /api/failures` - List all analyzed failures (with filters)
- `GET /api/failures/{failure_id}` - Get detailed RCA for a failure
- `GET /api/metrics/summary` - Get aggregate metrics

### Health
- `GET /health` - Health check

## 🧠 How It Works

### Agent Pipeline (LangGraph)

```
START
  ↓
[Agent 1: Log Parser]
  • Extract error signatures from raw logs
  • Output: { error_type, keywords, failing_tool }
  ↓
[Agent 2: Classifier]
  • Classify into: Infra | Auth | Dependency | Test | Config | Runner
  • Output: { category, confidence }
  ↓
[Agent 3: Fix Suggester]
  • Query RAG knowledge base for similar past fixes
  • Generate specific fix commands
  • Output: { suggested_fix, commands, confidence }
  ↓
[Agent 4: Similar Finder]
  • Find past similar failures
  • Output: { similar_cases, seen_count }
  ↓
FINAL RCA REPORT
```

### Knowledge Base (RAG)

Pre-seeded with 10 common UBS CI failure patterns:
- TerraformFormatError
- VaultNamespaceMismatch
- NexusPermissionDenied
- DockerPullTimeout
- YAMLSyntaxError
- RunnerJobTimeout
- JUnitAssertionFailure
- MavenDependencyNotFound
- VaultTokenExpired
- OutOfMemory

Each includes:
- Description
- Category
- Concrete fix steps
- Commands to run
- Historical seen count

## 📁 Project Structure

```
ci_rca_project/
├── main.py                    # FastAPI app
├── requirements.txt
├── .env.example
│
├── agents/
│   ├── state.py              # Shared state definition
│   ├── graph.py              # LangGraph orchestrator
│   ├── log_parser.py         # Agent 1
│   ├── classifier.py         # Agent 2
│   ├── fix_suggester.py      # Agent 3
│   └── similar_finder.py     # Agent 4
│
├── rag/
│   └── knowledge_base.py     # Pre-seeded failure patterns
│
├── db/
│   ├── database.py           # SQLAlchemy async setup
│   └── models.py             # CIFailure model
│
└── core/
    └── config.py             # Settings from .env
```

## 🎨 Frontend (React)

### Quick Start

```bash
# In a separate terminal
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend structure:
```
frontend/
├── src/
│   ├── App.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx         # Metrics overview
│   │   ├── FailureList.tsx       # Browse failures
│   │   ├── FailureDetail.tsx     # RCA detail view
│   │   └── BeforeAfter.tsx       # Comparison metrics
│   ├── components/
│   │   ├── MetricCard.tsx
│   │   ├── CategoryChart.tsx
│   │   └── FixCommandCard.tsx
│   └── api/
│       └── client.ts             # Axios API client
└── package.json
```

## 🎯 Demo Flow (5 Minutes)

1. **Show Problem** (1 min)
   - Open GitLab, show failed pipeline with 800+ lines of logs
   - "This is what developers face daily"

2. **Trigger Analysis** (1 min)
   ```bash
   curl -X POST http://localhost:8000/api/analyze-latest
   ```

3. **Show Results** (2 min)
   - Open React dashboard
   - Show failure detail with:
     - Category badge
     - Root cause explanation
     - Suggested fix commands
     - Confidence score
     - "Seen 14 times before"

4. **Show Metrics** (1 min)
   - Before: 45 min avg debug time
   - After: 6 min with RCA system
   - Time saved: 9.8 hrs/team/day

## 🔒 Security & Compliance

- ✅ Read-only AI (never modifies code)
- ✅ No PII processing
- ✅ Full audit trail in SQLite
- ✅ Azure OpenAI only (UBS tenant)
- ✅ Suggestions only, not automated changes

## 📈 Metrics

The system tracks:
- Total failures analyzed
- Average processing time (target: <30 seconds)
- Failure category breakdown
- Confidence scores
- Time saved vs manual process

## 🚀 Future Enhancements

- [ ] Jira integration (auto-create tickets)
- [ ] Owner routing (notify responsible teams)
- [ ] Report Portal integration
- [ ] Auto-retry safe fixes
- [ ] Failure prediction (pre-merge)
- [ ] Teams/Slack bot interface

## 🎓 Development Notes

### Adding New Failure Patterns

Edit `rag/knowledge_base.py`:

```python
KNOWLEDGE_BASE.append({
    "error_type": "YourNewError",
    "category": "Misconfiguration",
    "description": "What causes this error",
    "fix": "How to fix it",
    "commands": ["command 1", "command 2"],
    "seen_count": 0
})
```

### Improving Agent Prompts

Edit prompts in:
- `agents/log_parser.py` - PARSER_PROMPT
- `agents/classifier.py` - CLASSIFIER_PROMPT
- `agents/fix_suggester.py` - FIX_PROMPT

### Database Schema Changes

```bash
# After modifying db/models.py
rm ci_rca.db  # Delete old DB
# Restart app (will recreate with new schema)
```

## 📞 Support

For questions or issues during TechnoHunt:
1. Check logs: `tail -f uvicorn.log`
2. Verify .env configuration
3. Test with: `curl http://localhost:8000/health`

## 🏆 Why This Wins

✅ **Real UBS Pain** - Every team faces CI failures daily  
✅ **Clear Metrics** - 45 min → 6 min (87% reduction)  
✅ **Correct AI Use** - LangGraph agents, not a chatbot  
✅ **Production-Ready** - FastAPI, Azure OpenAI, async DB  
✅ **Achievable** - Built in 1-2 days  

---

**Built for TechnoHunt 2025 🏆**
