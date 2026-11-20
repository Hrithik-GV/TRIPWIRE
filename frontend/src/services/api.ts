const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export interface HealthInfo {
  status: string;
  service: string;
  subtitle: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface SystemStats {
  total_tasks: number;
  completed_tasks: number;
  running_tasks: number;
  waiting_approval_tasks: number;
  stopped_tasks: number;
  total_actions: number;
  executed_actions: number;
  paused_actions: number;
  human_approved_count: number;
  human_rejected_count: number;
  average_trust_score: number;
  snapshots_count: number;
}

export interface ActionItem {
  id: string;
  task_id: string;
  step_number: number;
  action_name: string;
  params: Record<string, any>;
  rationale?: string;
  expected_outcome?: string;
  claimed_outcome?: string;
  status: string;
  evidence_score?: number;
  evidence_verified?: boolean;
  evidence_explanation?: string;
  evidence_details?: Record<string, any>;
  reason_score?: number;
  reason_is_relevant?: boolean;
  reason_explanation?: string;
  evaluation_mode?: string;
  risk_score?: number;
  risk_level?: string;
  is_reversible?: boolean;
  risk_explanation?: string;
  impact_scope?: string;
  trust_score?: number;
  trust_explanation?: string;
  decision?: string; // RUN, SNAPSHOT_AND_RUN, PAUSE
  decision_reasons?: string[];
  overrides_applied?: string[];
  snapshot_id?: string;
  execution_success?: boolean;
  execution_exit_code?: number;
  execution_output?: string;
  execution_error?: string;
  execution_time_ms?: number;
  human_approval?: boolean | null;
  approval_timestamp?: string;
  created_at: string;
  updated_at: string;
}

export interface TaskSummary {
  id: string;
  user_goal: string;
  state: string;
  summary?: string;
  action_count: number;
  created_at: string;
  updated_at: string;
}

export interface TaskDetail {
  id: string;
  user_goal: string;
  state: string;
  summary?: string;
  actions: ActionItem[];
  created_at: string;
  updated_at: string;
}

export interface SnapshotItem {
  snapshot_id: string;
  description: string;
  timestamp: string;
  file_count: number;
  total_size_bytes: number;
}

export async function checkHealth(): Promise<HealthInfo> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health probe failed (${res.status})`);
  return res.json();
}

export async function fetchStats(): Promise<SystemStats> {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) throw new Error(`Failed to load system stats (${res.status})`);
  return res.json();
}

export async function fetchTasks(limit = 50): Promise<TaskSummary[]> {
  const res = await fetch(`${API_BASE}/tasks?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to load tasks (${res.status})`);
  return res.json();
}

export async function fetchTaskDetail(taskId: string): Promise<TaskDetail> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}`);
  if (!res.ok) throw new Error(`Failed to load task ${taskId} (${res.status})`);
  return res.json();
}

export async function createTask(userGoal: string, autoRun = true): Promise<TaskDetail> {
  const res = await fetch(`${API_BASE}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_goal: userGoal, auto_run: autoRun }),
  });
  if (!res.ok) throw new Error(`Failed to start agent task (${res.status})`);
  return res.json();
}

export async function stopTask(taskId: string): Promise<TaskDetail> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/stop`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to stop task (${res.status})`);
  return res.json();
}

export async function fetchActions(status?: string, taskId?: string, limit = 100): Promise<ActionItem[]> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (taskId) params.append('task_id', taskId);
  params.append('limit', limit.toString());

  const res = await fetch(`${API_BASE}/actions?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to load actions (${res.status})`);
  return res.json();
}

export async function approveAction(actionId: string): Promise<ActionItem> {
  const res = await fetch(`${API_BASE}/actions/${actionId}/approve`, { method: 'POST' });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Approval failed (${res.status})`);
  }
  return res.json();
}

export async function rejectAction(actionId: string): Promise<ActionItem> {
  const res = await fetch(`${API_BASE}/actions/${actionId}/reject`, { method: 'POST' });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Rejection failed (${res.status})`);
  }
  return res.json();
}

export async function fetchSnapshots(): Promise<SnapshotItem[]> {
  const res = await fetch(`${API_BASE}/snapshots`);
  if (!res.ok) throw new Error(`Failed to load snapshots (${res.status})`);
  return res.json();
}

export async function restoreSnapshot(snapshotId: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/snapshots/${snapshotId}/restore`, { method: 'POST' });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Restore failed (${res.status})`);
  }
  return res.json();
}

export function subscribeToEvents(onEvent: (eventData: any) => void): () => void {
  const sseUrl = `${API_BASE}/events`;
  const eventSource = new EventSource(sseUrl);

  const eventTypes = [
    'connected',
    'task_started',
    'action_proposed',
    'evidence_checked',
    'reason_checked',
    'risk_checked',
    'trust_calculated',
    'decision_generated',
    'action_executed',
    'approval_requested',
    'action_rejected',
    'task_completed',
  ];

  eventTypes.forEach((type) => {
    eventSource.addEventListener(type, (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        onEvent(data);
      } catch (err) {
        console.error('Failed to parse SSE event payload', err);
      }
    });
  });

  return () => {
    eventSource.close();
  };
}

