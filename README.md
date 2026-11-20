# TRIPWIRE – AI Agent Safety and Control Middleware
### Powered by SUPERNOVA

TRIPWIRE is an interception and control middleware designed to monitor, guardrail, and enforce safety policies on autonomous AI agents executing code and commands in target workspaces.

---

## Repository Structure

```
tripwire/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py         # Application configuration & settings
│   │   ├── main.py           # FastAPI application entry & router binding
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── actions.py    # Action execution endpoints
│   │   │   └── evaluations.py# Tripwire evaluation endpoints (/intercept, /trust, /decision)
│   │   ├── tripwire/
│   │   │   ├── __init__.py
│   │   │   ├── evidence_checker.py # Ground-truth disk, diff & test verification
│   │   │   ├── reason_checker.py   # LLM judge & deterministic fallback alignment
│   │   │   ├── risk_checker.py     # Operational risk, blast radius & reversibility
│   │   │   ├── trust_scorer.py     # Weighted composite trust scoring engine
│   │   │   ├── decision_engine.py  # Policy thresholds & non-bypassable safety overrides
│   │   │   └── interceptor.py      # Central 6-stage interception pipeline
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── actions.py    # Pydantic schemas for actions & results
│   │   └── services/
│   │       ├── __init__.py
│   │       └── executor.py   # Controlled WorkspaceExecutor engine
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_executor.py  # Unit tests for actions & security restrictions
│   │   ├── test_api.py       # API route integration tests
│   │   ├── test_evidence_checker.py # Evidence checker tests
│   │   ├── test_reason_checker.py   # Reason checker tests
│   │   ├── test_risk_checker.py     # Risk checker tests
│   │   ├── test_trust_scorer.py     # Trust scoring formula & bounds tests
│   │   ├── test_decision_engine.py  # Thresholds & safety override tests
│   │   └── test_interceptor.py      # End-to-end interception pipeline tests
│   ├── requirements.txt      # Python dependencies
│   └── venv/                 # Python virtual environment (ignored)
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Tripwire shell & navigation dashboard
│   │   ├── main.tsx          # React application entry
│   │   └── index.css         # Tailwind CSS styling
│   ├── package.json          # Node dependencies (React, Vite, Lucide, Tailwind)
│   ├── vite.config.ts        # Vite configuration
│   └── .env.example          # Frontend environment variables template
├── demo_workspace/           # Isolated workspace monitored by Tripwire
│   ├── app.py                # Demo authentication module with intentional logic bug
│   ├── test_app.py           # Unit tests that fail on the intentional bug
│   └── README.md             # Workspace project overview
├── .env.example              # Root environment template
├── .gitignore                # Git ignore rules
└── README.md                 # Setup & running instructions
```

---

## Prerequisites

- **Python**: 3.10 or later (Tested with Python 3.13)
- **Node.js**: v18.0 or later (Tested with Node.js v22.20)
- **npm**: v9.0 or later

---

## Getting Started

### 1. Environment Configuration

Copy the example environment files:

```bash
# In the repository root
cp .env.example .env

# In frontend directory
cp frontend/.env.example frontend/.env
```

Default environment configuration:
- Backend: `http://127.0.0.1:8000`
- Frontend: `http://localhost:5173`
- Allowed CORS: `http://localhost:5173,http://127.0.0.1:5173`

---

### 2. Backend Setup & Run

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   - On Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - On Linux / macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. Verify backend health:
   ```bash
   curl http://127.0.0.1:8000/api/health
   ```
   Expected response:
   ```json
   {
     "status": "healthy",
     "service": "TRIPWIRE",
     "subtitle": "SUPERNOVA",
     "version": "0.1.0",
     "environment": "development",
     "timestamp": "..."
   }
   ```

---

### 3. Frontend Setup & Run

1. Open a new terminal and navigate to `frontend/`:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open your browser at [http://localhost:5173](http://localhost:5173).

---

## Trust Scoring & Decision Gating Engine

### 1. Composite Trust Formula

$$ \text{trust\_score} = (0.40 \times \text{evidence\_score}) + (0.35 \times \text{reason\_score}) + (0.25 \times (1 - \text{risk\_score})) $$

All sub-scores are validated strictly between $0.0$ and $1.0$.

### 2. Gating Decision Thresholds

- **0.80 to 1.00**: `RUN` — Autonomous execution approved.
- **0.50 to 0.79**: `SNAPSHOT_AND_RUN` — Pre-execution filesystem snapshot required prior to run.
- **Below 0.50**: `PAUSE` — Action execution halted; requires explicit human authorization.

### 3. Non-Bypassable Safety Overrides

Regardless of how high the computed `trust_score` is, the following overrides unconditionally force a `PAUSE`:
1. **Critical-Risk Operations**: Operations with `risk_level == "critical"` or `risk_score >= 0.90` (e.g. sandbox boundary escapes, path traversal, arbitrary commands).
2. **Unsupported Operations**: Operations not recognized by Tripwire.
3. **Non-Recoverable High-Impact Operations**: Irreversible operations (such as core source code deletion) where rollback is impossible without prior snapshots.

---

## Features (Step 1-4 Foundation)

- **FastAPI Core**: Async REST API with configured CORS origins and standard health check (`GET /api/health`).
- **Clean Light Dashboard**: Professional enterprise light theme with neutral slate/zinc styling (no generic AI color palettes or gradients).
- **Navigation Shell**:
  - **Overview**: Core middleware connectivity and runtime readiness
  - **Agent Execution**: Execution orchestration view for `demo_workspace/`
  - **Tripwire Evaluations**: Guardrail policy checks and interception events
  - **Approvals**: Human-in-the-loop authorization queue
  - **Execution History**: Audit trail of executed commands
  - **Snapshots**: Point-in-time filesystem rollback checkpoints
- **Live Health Status**: Real-time probe connecting frontend to FastAPI backend.
- **Zero Mock Statistics**: Clean empty states with explicit status indicators instead of fabricated metrics.

