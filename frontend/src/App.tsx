import { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Terminal,
  ShieldAlert,
  CheckSquare,
  History,
  Camera,
  Activity,
  RefreshCw,
  FolderLock,
  ShieldCheck,
  Server
} from 'lucide-react';

interface BackendHealth {
  status: string;
  service: string;
  subtitle: string;
  version: string;
  environment: string;
  timestamp: string;
}

type TabKey =
  | 'overview'
  | 'agent-execution'
  | 'evaluations'
  | 'approvals'
  | 'history'
  | 'snapshots';

interface NavItem {
  key: TabKey;
  label: string;
  icon: typeof LayoutDashboard;
  description: string;
}

const NAV_ITEMS: NavItem[] = [
  { key: 'overview', label: 'Overview', icon: LayoutDashboard, description: 'System health & middleware state' },
  { key: 'agent-execution', label: 'Agent Execution', icon: Terminal, description: 'Workspace agent runner & sandboxing' },
  { key: 'evaluations', label: 'Tripwire Evaluations', icon: ShieldAlert, description: 'Safety rules & guardrail checks' },
  { key: 'approvals', label: 'Approvals', icon: CheckSquare, description: 'Human-in-the-loop authorization queue' },
  { key: 'history', label: 'Execution History', icon: History, description: 'Audit trail of executed commands' },
  { key: 'snapshots', label: 'Snapshots', icon: Camera, description: 'Workspace filesystem rollback points' },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [healthError, setHealthError] = useState<string | null>(null);

  const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

  const checkHealth = async () => {
    setLoadingHealth(true);
    setHealthError(null);
    try {
      const res = await fetch(`${apiBase}/health`);
      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }
      const data: BackendHealth = await res.json();
      setHealth(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to connect to backend';
      setHealthError(msg);
      setHealth(null);
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded bg-slate-900 text-white flex items-center justify-center font-bold tracking-wider text-sm shadow-sm">
              TW
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-lg font-bold tracking-tight text-slate-900">TRIPWIRE</span>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                SUPERNOVA
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-500 font-medium">Backend:</span>
              {loadingHealth ? (
                <span className="inline-flex items-center text-slate-500">
                  <RefreshCw className="w-3 h-3 animate-spin mr-1" />
                  Checking...
                </span>
              ) : health ? (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></span>
                  Active ({health.environment})
                </span>
              ) : (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5"></span>
                  Disconnected
                </span>
              )}
            </div>

            <button
              onClick={checkHealth}
              title="Refresh backend status"
              className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded border border-slate-200 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingHealth ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex gap-6">
        {/* Sidebar */}
        <aside className="w-64 flex-shrink-0">
          <nav className="bg-white border border-slate-200 rounded-lg p-2 space-y-1 shadow-xs">
            <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Navigation
            </div>
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.key;
              return (
                <button
                  key={item.key}
                  onClick={() => setActiveTab(item.key)}
                  className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors text-left ${
                    isActive
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Quick Context Card */}
          <div className="mt-4 bg-white border border-slate-200 rounded-lg p-4 text-xs text-slate-600 space-y-2 shadow-xs">
            <div className="font-semibold text-slate-900 flex items-center space-x-1.5">
              <FolderLock className="w-3.5 h-3.5 text-slate-500" />
              <span>Target Workspace</span>
            </div>
            <div className="font-mono text-[11px] bg-slate-100 text-slate-700 px-2 py-1 rounded border border-slate-200 break-all">
              demo_workspace/
            </div>
            <p className="text-[11px] text-slate-500">
              Tripwire guards agent actions inside this isolated workspace.
            </p>
          </div>
        </aside>

        {/* Content Area */}
        <main className="flex-1 min-w-0">
          {healthError && (
            <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-center justify-between">
              <div>
                <span className="font-semibold">Backend Unreachable:</span> {healthError}. Ensure the FastAPI server is running at <code className="font-mono">{apiBase}</code>.
              </div>
              <button
                onClick={checkHealth}
                className="ml-3 px-2 py-1 bg-amber-100 hover:bg-amber-200 text-amber-900 rounded font-medium transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-slate-900">Control Middleware Overview</h2>
                    <p className="text-sm text-slate-500 mt-1">
                      TRIPWIRE sits between Autonomous AI Agents and the host operating environment to enforce guardrails and policy gates.
                    </p>
                  </div>
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                    Step 1 Prototype
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                  <div className="p-4 rounded-md border border-slate-200 bg-slate-50/50">
                    <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      <Server className="w-3.5 h-3.5 text-slate-600" />
                      <span>API Gateway</span>
                    </div>
                    <div className="mt-2 text-lg font-bold text-slate-900">
                      {health ? 'Operational' : 'Unavailable'}
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      {health ? `FastAPI v${health.version} (${health.environment})` : 'Backend service offline'}
                    </p>
                  </div>

                  <div className="p-4 rounded-md border border-slate-200 bg-slate-50/50">
                    <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      <ShieldCheck className="w-3.5 h-3.5 text-slate-600" />
                      <span>Policy Interceptor</span>
                    </div>
                    <div className="mt-2 text-lg font-bold text-slate-900">Configured</div>
                    <p className="mt-1 text-xs text-slate-500">Awaiting agent dispatch session</p>
                  </div>

                  <div className="p-4 rounded-md border border-slate-200 bg-slate-50/50">
                    <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      <Activity className="w-3.5 h-3.5 text-slate-600" />
                      <span>Runtime State</span>
                    </div>
                    <div className="mt-2 text-lg font-bold text-slate-900">Ready</div>
                    <p className="mt-1 text-xs text-slate-500">Sandbox target: demo_workspace</p>
                  </div>
                </div>
              </div>

              {/* Endpoint Information */}
              <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs">
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Connected Infrastructure</h3>
                <div className="mt-4 border border-slate-200 rounded-md overflow-hidden text-xs">
                  <div className="grid grid-cols-3 bg-slate-50 font-semibold p-2.5 border-b border-slate-200 text-slate-600">
                    <div>Service</div>
                    <div>Endpoint</div>
                    <div>Status</div>
                  </div>
                  <div className="grid grid-cols-3 p-2.5 border-b border-slate-100 items-center">
                    <div className="font-medium text-slate-900">Health Probe</div>
                    <div className="font-mono text-slate-600">GET /api/health</div>
                    <div>
                      {health ? (
                        <span className="text-emerald-700 font-medium">200 OK</span>
                      ) : (
                        <span className="text-amber-700 font-medium">Pending Connection</span>
                      )}
                    </div>
                  </div>
                  <div className="grid grid-cols-3 p-2.5 items-center">
                    <div className="font-medium text-slate-900">Agent Middleware Socket</div>
                    <div className="font-mono text-slate-600">127.0.0.1:8000</div>
                    <div>
                      <span className="text-slate-500 font-medium">Ready for Step 2</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'agent-execution' && (
            <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs space-y-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Agent Execution Console</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Configure and trigger agent prompts within the protected demo workspace sandbox.
                </p>
              </div>

              <div className="border border-dashed border-slate-300 rounded-lg p-8 text-center bg-slate-50/50">
                <Terminal className="w-8 h-8 mx-auto text-slate-400 mb-2" />
                <h4 className="text-sm font-semibold text-slate-700">No active execution</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                  Agent run orchestration will be integrated in subsequent steps. All actions executed here will run against the tripwire safety filter.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'evaluations' && (
            <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs space-y-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Tripwire Evaluations</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Real-time safety evaluations and policy rule checks applied to agent commands.
                </p>
              </div>

              <div className="border border-dashed border-slate-300 rounded-lg p-8 text-center bg-slate-50/50">
                <ShieldAlert className="w-8 h-8 mx-auto text-slate-400 mb-2" />
                <h4 className="text-sm font-semibold text-slate-700">No evaluation logs yet</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                  When an agent invokes tools, file edits, or terminal commands, evaluation results will appear here in real-time.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'approvals' && (
            <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs space-y-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Human-in-the-Loop Approvals</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Actions tagged as sensitive or dangerous require human confirmation before execution.
                </p>
              </div>

              <div className="border border-dashed border-slate-300 rounded-lg p-8 text-center bg-slate-50/50">
                <CheckSquare className="w-8 h-8 mx-auto text-slate-400 mb-2" />
                <h4 className="text-sm font-semibold text-slate-700">Approval queue is empty</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                  High-risk operations flagged by Tripwire policies will pause agent execution and request manual review here.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs space-y-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Execution History</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Immutable audit trail of past agent runs, evaluation decisions, and human responses.
                </p>
              </div>

              <div className="border border-dashed border-slate-300 rounded-lg p-8 text-center bg-slate-50/50">
                <History className="w-8 h-8 mx-auto text-slate-400 mb-2" />
                <h4 className="text-sm font-semibold text-slate-700">No executions recorded</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                  Complete session transcripts and tool execution outputs will be archived in this view.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'snapshots' && (
            <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs space-y-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Workspace Snapshots</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Point-in-time filesystem snapshots of demo_workspace for rollbacks and differential analysis.
                </p>
              </div>

              <div className="border border-dashed border-slate-300 rounded-lg p-8 text-center bg-slate-50/50">
                <Camera className="w-8 h-8 mx-auto text-slate-400 mb-2" />
                <h4 className="text-sm font-semibold text-slate-700">No snapshots taken yet</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                  Before high-risk actions are performed in demo_workspace, automated snapshots allow rollback to a clean state.
                </p>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-3 text-xs text-slate-500 text-center">
        <span>TRIPWIRE &bull; SUPERNOVA &bull; AI Agent Safety & Control Middleware</span>
      </footer>
    </div>
  );
}
