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
│   │   ├── demo_runner.py    # End-to-end terminal demonstration
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── planner.py    # Deterministic & LLM-assisted action planners
│   │   │   └── agent_engine.py# Agent lifecycle, state machine & safety loop
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── actions.py    # Action execution endpoints
│   │   │   ├── agent.py      # Agent session orchestration & approval endpoints
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
│   │       ├── executor.py   # Controlled WorkspaceExecutor engine
│   │       └── snapshot.py   # Workspace point-in-time snapshot manager
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_agent.py     # End-to-end repair & safety gating tests
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

### 4. Running the Complete End-to-End Demo

You can run the full backend agent loop demonstration (both successful repair and dangerous-action blocking) via:

```powershell
cd c:\projects\tripwire
$env:PYTHONPATH="c:\projects\tripwire\backend"
c:\projects\tripwire\backend\venv\Scripts\python.exe -m app.demo_runner
```

---

## API Endpoints Reference

### Core Tasks & Actions

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/tasks` | Create and start an autonomous agent task (`user_goal`, `auto_run`) |
| `GET` | `/api/tasks` | List all persisted tasks with status and step counts |
| `GET` | `/api/tasks/{task_id}` | Retrieve full task details and audited step trace |
| `POST` | `/api/tasks/{task_id}/stop` | Immediately halt a running or paused task |
| `GET` | `/api/actions` | Query audited actions (filter by `status`, `task_id`, `limit`) |
| `GET` | `/api/actions/{action_id}` | Retrieve complete evaluation breakdown for a single action |
| `POST` | `/api/actions/{action_id}/approve` | Human-in-the-loop: Authorize a PAUSED action to execute |
| `POST` | `/api/actions/{action_id}/reject` | Human-in-the-loop: Reject a PAUSED action and stop the task |

### Snapshots & Rollbacks

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/snapshots` | List point-in-time filesystem rollback checkpoints |
| `POST` | `/api/snapshots/{snapshot_id}/restore` | Roll back `demo_workspace` to specified snapshot |

### Real-Time Monitoring & Telemetry

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/stats` | Dynamic statistics aggregated live from SQLite (tasks, actions, trust avg, approvals) |
| `GET` | `/api/events` | Server-Sent Events (SSE) live event stream |
| `GET` | `/api/health` | Service health probe and version metadata |

### SSE Streamed Event Types

Clients connecting to `GET /api/events` receive real-time JSON events:
- `task_started`: Fired when a task is initialized
- `action_proposed`: Fired when agent plans next operation
- `evidence_checked`: Ground-truth disk, diff & test check completed
- `reason_checked`: Task alignment and goal relevance evaluation completed
- `risk_checked`: Operational risk and reversibility classification completed
- `trust_calculated`: Weighted composite trust score computed
- `decision_generated`: Gating decision (`RUN`, `SNAPSHOT_AND_RUN`, `PAUSE`)
- `approval_requested`: Fired when action is PAUSED for human review
- `action_executed`: Fired following controlled execution in sandbox
- `action_rejected`: Fired when human operator rejects an action
- `task_completed`: Fired when task finishes or is halted

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

## Frontend Dashboard (Step 7: Cybersecurity SaaS Interface)

TRIPWIRE includes a complete React + TypeScript dashboard designed specifically for AI agent safety and control.

### Design Principles
- **Theme**: Dark navy/charcoal cybersecurity theme (`#020617` / `#0f172a` slate palette).
- **Branding**: `TRIPWIRE` • `AI AGENT SAFETY MONITOR` • `SUPERNOVA`.
- **Decision Color Mapping**:
  - `RUN`: Emerald / Green (`#10b981`)
  - `SNAPSHOT_AND_RUN`: Amber (`#f59e0b`)
  - `PAUSE`: Rose / Red (`#f43f5e`)
- **Zero Fake Statistics**: Every chart, table, card, and indicator is bound directly to backend REST endpoints and live Server-Sent Events (SSE).

### Dashboard Views
1. **Overview**:
   - Executive telemetry metrics: Total Tasks, Total Actions, Executed Actions, Blocked/Paused Actions, Pending Approvals, Average Trust Score.
   - Interactive Recharts Trust Score Trajectory chart with threshold reference lines (0.80 `RUN`, 0.50 `SNAPSHOT`).
   - Recent action stream with sub-score breakdowns and decision badges.
2. **Agent Execution**:
   - Agent prompt console with preset workflows (Safe bug fix, dangerous deletion demo, etc.).
   - Start Agent and Stop Task controls with live execution status badges.
   - Real-time step-by-step progress trace with rationale, parameters, decision, and sandbox execution outputs.
   - Inline approval action banners when a step triggers a `PAUSE`.
3. **Tripwire Evaluations**:
   - Comprehensive action inspection with search and decision filter (`ALL`, `RUN`, `SNAPSHOT_AND_RUN`, `PAUSE`).
   - Detailed sub-score breakdowns: Evidence Score (disk/diff verification), Reason Score (goal alignment), and Risk Score (blast radius).
   - Expandable evidence cards showing Git diffs, test outputs, exit codes, and override logs.
4. **Approval Center**:
   - Human-in-the-loop authorization queue showing all paused actions with reasons and risk classifications.
   - One-click **Approve** and **Reject** buttons directly integrated with `POST /api/actions/{id}/approve` and `/reject`.
5. **Execution History**:
   - Chronological audit log of all historical agent actions.
   - Filter and search by file path, action name, or terminal output.
   - Complete capture of execution timestamps, exit codes, and output text.
6. **Snapshots**:
   - Workspace checkpoint manager listing all point-in-time Git snapshots.
   - File counts and storage footprints.
   - Working **Restore Snapshot** button connected to `POST /api/snapshots/{id}/restore`.

---

## Starting the Full Application

### 1. Start the Backend Server

```bash
cd backend
venv\Scripts\activate   # Windows
# source venv/bin/activate # Linux/macOS
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Start the Frontend Application

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` (or `http://localhost:5174`) in your browser.


