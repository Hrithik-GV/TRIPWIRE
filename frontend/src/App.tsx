import { useState, useEffect, useCallback, useRef } from 'react';
import { Header } from './components/Header';
import { Sidebar, type TabKey } from './components/Sidebar';
import { OverviewView } from './components/OverviewView';
import { AgentExecutionView } from './components/AgentExecutionView';
import { EvaluationsView } from './components/EvaluationsView';
import { ApprovalCenterView } from './components/ApprovalCenterView';
import { ExecutionHistoryView } from './components/ExecutionHistoryView';
import { SnapshotsView } from './components/SnapshotsView';
import {
  type HealthInfo,
  type SystemStats,
  type ActionItem,
  type TaskDetail,
  type SnapshotItem,
  checkHealth,
  fetchStats,
  fetchActions,
  fetchSnapshots,
  fetchTasks,
  fetchTaskDetail,
  subscribeToEvents,
} from './services/api';
import { AlertCircle, RefreshCw } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [snapshots, setSnapshots] = useState<SnapshotItem[]>([]);
  const [currentTask, setCurrentTask] = useState<TaskDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [sseConnected, setSseConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Keep track of current task ID for SSE updates
  const currentTaskIdRef = useRef<string | null>(null);
  currentTaskIdRef.current = currentTask?.id || null;

  // Load all foundational data
  const loadAllData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthData, statsData, actionsData, snapshotsData, tasksData] = await Promise.allSettled([
        checkHealth(),
        fetchStats(),
        fetchActions(undefined, undefined, 100),
        fetchSnapshots(),
        fetchTasks(5),
      ]);

      if (healthData.status === 'fulfilled') {
        setHealth(healthData.value);
      } else {
        setHealth(null);
        setError('Cannot connect to Tripwire backend service. Ensure FastAPI is running on port 8000.');
      }

      if (statsData.status === 'fulfilled') {
        setStats(statsData.value);
      }

      if (actionsData.status === 'fulfilled') {
        setActions(actionsData.value);
      }

      if (snapshotsData.status === 'fulfilled') {
        setSnapshots(snapshotsData.value);
      }

      if (tasksData.status === 'fulfilled' && tasksData.value.length > 0) {
        // Load the latest active/recent task detail if we don't have one selected
        const latestId = currentTaskIdRef.current || tasksData.value[0].id;
        try {
          const detail = await fetchTaskDetail(latestId);
          setCurrentTask(detail);
        } catch {
          // If detailed task load fails, fall back to null
        }
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred while loading dashboard telemetry');
    } finally {
      setLoading(false);
    }
  }, []);

  // Quick refresh without showing global full spinner
  const refreshSilent = useCallback(async () => {
    try {
      const [statsData, actionsData, snapshotsData] = await Promise.allSettled([
        fetchStats(),
        fetchActions(undefined, undefined, 100),
        fetchSnapshots(),
      ]);

      if (statsData.status === 'fulfilled') setStats(statsData.value);
      if (actionsData.status === 'fulfilled') setActions(actionsData.value);
      if (snapshotsData.status === 'fulfilled') setSnapshots(snapshotsData.value);

      // Refresh current task detail if active
      if (currentTaskIdRef.current) {
        try {
          const updated = await fetchTaskDetail(currentTaskIdRef.current);
          setCurrentTask(updated);
        } catch {
          // Ignore background detail refresh error
        }
      }
    } catch {
      // Ignore background refresh errors
    }
  }, []);

  // Initial mount load
  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // Subscribe to live SSE events from Tripwire backend
  useEffect(() => {
    let unsubscribe: (() => void) | null = null;

    try {
      unsubscribe = subscribeToEvents(() => {
        setSseConnected(true);
        // On any live event (task started, action proposed, evaluated, executed, approval, etc.)
        // refresh stats & action stream
        refreshSilent();
      });
    } catch {
      setSseConnected(false);
    }

    // Health probe interval
    const interval = setInterval(async () => {
      try {
        const h = await checkHealth();
        setHealth(h);
      } catch {
        setHealth(null);
      }
    }, 15000);

    return () => {
      if (unsubscribe) unsubscribe();
      clearInterval(interval);
    };
  }, [refreshSilent]);

  // Count paused actions awaiting human approval
  const pendingApprovalsCount = actions.filter((a) => a.status === 'PAUSED').length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500/30 selection:text-emerald-200">
      {/* Top Header */}
      <Header
        health={health}
        loading={loading}
        sseConnected={sseConnected}
        onRefresh={loadAllData}
      />

      {/* Main Container */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col md:flex-row gap-6">
        {/* Navigation Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          pendingApprovalsCount={pendingApprovalsCount}
        />

        {/* Content Area */}
        <main className="flex-1 min-w-0">
          {/* Disconnection Warning */}
          {error && !health && (
            <div className="mb-6 p-4 bg-rose-950/40 border border-rose-800/60 rounded-lg text-xs text-rose-200 flex items-center justify-between shadow-lg">
              <div className="flex items-center space-x-3">
                <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
                <div>
                  <span className="font-bold text-rose-300">Backend Disconnected:</span> {error}
                </div>
              </div>
              <button
                onClick={loadAllData}
                className="ml-4 px-3 py-1.5 bg-rose-900/60 hover:bg-rose-800/80 text-rose-100 rounded border border-rose-700 font-medium transition-colors flex items-center space-x-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                <span>Reconnect</span>
              </button>
            </div>
          )}

          {/* Active Tab View */}
          {activeTab === 'overview' && (
            <OverviewView
              stats={stats}
              actions={actions}
              onNavigateToTab={(tab) => setActiveTab(tab as TabKey)}
            />
          )}

          {activeTab === 'agent-execution' && (
            <AgentExecutionView
              currentTask={currentTask}
              onTaskUpdated={(task) => {
                setCurrentTask(task);
                refreshSilent();
              }}
              onRefreshAll={loadAllData}
            />
          )}

          {activeTab === 'evaluations' && (
            <EvaluationsView actions={actions} />
          )}

          {activeTab === 'approvals' && (
            <ApprovalCenterView
              actions={actions}
              onActionProcessed={loadAllData}
            />
          )}

          {activeTab === 'history' && (
            <ExecutionHistoryView actions={actions} />
          )}

          {activeTab === 'snapshots' && (
            <SnapshotsView
              snapshots={snapshots}
              onSnapshotRestored={loadAllData}
            />
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 text-xs text-slate-500 text-center">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>TRIPWIRE &bull; SUPERNOVA &bull; AI Agent Safety & Control Middleware</span>
          <span className="font-mono text-[11px] text-slate-600">Active Target: demo_workspace/</span>
        </div>
      </footer>
    </div>
  );
}
