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
│   │   │   └── actions.py    # Action execution endpoints
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── actions.py    # Pydantic schemas for actions & results
│   │   └── services/
│   │       ├── __init__.py
│   │       └── executor.py   # Controlled WorkspaceExecutor engine
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_executor.py  # Unit tests for actions & security restrictions
│   │   └── test_api.py       # API route integration tests
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

## Features (Step 1 Foundation)

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

