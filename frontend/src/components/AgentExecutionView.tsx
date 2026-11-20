import React, { useState } from 'react';
import {
  Play,
  Square,
  Terminal,
  AlertTriangle,
  Cpu,
} from 'lucide-react';
import { type TaskDetail, createTask, stopTask, approveAction, rejectAction } from '../services/api';
import { DecisionBadge } from './DecisionBadge';

interface AgentExecutionViewProps {
  currentTask: TaskDetail | null;
  onTaskUpdated: (task: TaskDetail) => void;
  onRefreshAll: () => void;
}

export const AgentExecutionView: React.FC<AgentExecutionViewProps> = ({
  currentTask,
  onTaskUpdated,
  onRefreshAll,
}) => {
  const [prompt, setPrompt] = useState(
    'Inspect my Python project, fix the login bug and run the tests.'
  );
  const [running, setRunning] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStartTask = async () => {
    if (!prompt.trim()) return;
    setRunning(true);
    setError(null);
    try {
      const task = await createTask(prompt.trim(), true);
      onTaskUpdated(task);
      onRefreshAll();
    } catch (err: any) {
      setError(err.message || 'Failed to start agent task');
    } finally {
      setRunning(false);
    }
  };

  const handleStopTask = async () => {
    if (!currentTask) return;
    setRunning(true);
    try {
      const stopped = await stopTask(currentTask.id);
      onTaskUpdated(stopped);
      onRefreshAll();
    } catch (err: any) {
      setError(err.message || 'Failed to stop task');
    } finally {
      setRunning(false);
    }
  };

  const handleApprove = async (actionId: string) => {
    setActionLoading(true);
    try {
      await approveAction(actionId);
      onRefreshAll();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (actionId: string) => {
    setActionLoading(true);
    try {
      await rejectAction(actionId);
      onRefreshAll();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Control Console Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-xs">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Autonomous Agent Orchestration Console
            </h3>
          </div>
          {currentTask && (
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-400">Current Task:</span>
              <span className="font-mono text-slate-300">{currentTask.id}</span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase border ${
                  currentTask.state === 'COMPLETED'
                    ? 'bg-emerald-950/60 text-emerald-400 border-emerald-500/30'
                    : currentTask.state === 'WAITING_APPROVAL'
                    ? 'bg-amber-950/60 text-amber-400 border-amber-500/30 animate-pulse'
                    : currentTask.state === 'STOPPED'
                    ? 'bg-slate-800 text-slate-400 border-slate-700'
                    : 'bg-emerald-950/40 text-emerald-300 border-emerald-500/20'
                }`}
              >
                {currentTask.state}
              </span>
            </div>
          )}
        </div>

        <p className="text-xs text-slate-400 mb-4">
          Direct the autonomous software engineering agent. Every single action proposed is intercepted and evaluated against Tripwire safety policies.
        </p>

        {/* Prompt Input */}
        <div className="space-y-2.5">
          <textarea
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Assign a software engineering or debugging goal..."
            className="w-full bg-slate-950 border border-slate-800 rounded-md p-3 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50 font-mono resize-none transition-colors"
          />

          {/* Quick preset pills */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-400 text-[11px] font-semibold">Demo Presets:</span>
            <button
              onClick={() => setPrompt('Inspect my Python project, fix the login bug and run the tests.')}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px] border border-slate-700 transition-colors"
            >
              Repair Workflow (Bug Fix &amp; Test)
            </button>
            <button
              onClick={() => setPrompt('Demonstrate dangerous deletion of source files')}
              className="px-2.5 py-1 bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 rounded text-[11px] border border-rose-800/40 transition-colors"
            >
              Dangerous Action (Core Deletion)
            </button>
          </div>
        </div>

        {/* Execution buttons */}
        <div className="flex items-center justify-between pt-4 mt-4 border-t border-slate-800/80">
          <div className="text-xs text-slate-400">
            Target Workspace: <code className="font-mono text-emerald-400">demo_workspace/</code>
          </div>
          <div className="flex items-center space-x-3">
            {currentTask && currentTask.state === 'RUNNING' && (
              <button
                onClick={handleStopTask}
                disabled={running}
                className="px-3.5 py-1.5 bg-rose-900/40 hover:bg-rose-800/60 text-rose-300 rounded text-xs font-semibold border border-rose-700/50 flex items-center space-x-1.5 transition-colors"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>Stop Task</span>
              </button>
            )}

            <button
              onClick={handleStartTask}
              disabled={running || !prompt.trim()}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-bold tracking-wide flex items-center space-x-2 shadow-sm transition-colors disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{running ? 'Executing Under Tripwire...' : 'Start Autonomous Agent'}</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-3 p-3 bg-rose-950/60 border border-rose-500/40 rounded text-xs text-rose-300 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Human Approval Required Alert Box */}
      {currentTask && currentTask.state === 'WAITING_APPROVAL' && currentTask.actions.length > 0 && (
        <div className="bg-amber-950/30 border border-amber-500/40 rounded-lg p-5">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2.5">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-bold text-amber-300">
                  Human-in-the-Loop Approval Required
                </h4>
                <p className="text-xs text-amber-200/80 mt-0.5">
                  Tripwire safety policies have halted this operation. Autonomous execution cannot proceed without operator authorization.
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleReject(currentTask.actions[currentTask.actions.length - 1].id)}
                disabled={actionLoading}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-semibold border border-slate-700 transition-colors"
              >
                Reject Action
              </button>
              <button
                onClick={() => handleApprove(currentTask.actions[currentTask.actions.length - 1].id)}
                disabled={actionLoading}
                className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-bold transition-colors"
              >
                Authorize &amp; Execute
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Execution Trace Stream */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-slate-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Live Execution Trace
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {currentTask ? `${currentTask.actions.length} Steps Logged` : '0 Steps'}
          </span>
        </div>

        {currentTask && currentTask.actions.length > 0 ? (
          <div className="space-y-4">
            {currentTask.actions.map((act) => (
              <div
                key={act.id}
                className="bg-slate-950 border border-slate-800/80 rounded-lg p-4 font-mono text-xs space-y-3"
              >
                {/* Step header */}
                <div className="flex items-center justify-between font-sans">
                  <div className="flex items-center space-x-2.5">
                    <span className="w-6 h-6 rounded bg-slate-800 text-slate-300 text-xs font-bold flex items-center justify-center">
                      {act.step_number}
                    </span>
                    <span className="font-mono text-emerald-400 font-bold text-sm">
                      {act.action_name}
                    </span>
                    <span className="text-slate-400 text-xs">
                      {act.params.path || act.params.target || ''}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <DecisionBadge decision={act.decision} size="sm" />
                    <span className="text-slate-400 text-[11px]">
                      Trust: <strong className="text-slate-200">{act.trust_score?.toFixed(3)}</strong>
                    </span>
                  </div>
                </div>

                {/* Agent Rationale */}
                {act.rationale && (
                  <div className="text-slate-300 text-xs font-sans bg-slate-900/60 p-2.5 rounded border border-slate-800/60">
                    <span className="font-bold text-slate-400 uppercase text-[10px] tracking-wider block mb-1">
                      Agent Rationale:
                    </span>
                    {act.rationale}
                  </div>
                )}

                {/* Tripwire Sub-score cards */}
                <div className="grid grid-cols-3 gap-2 font-sans text-[11px]">
                  <div className="bg-slate-900 p-2 rounded border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-bold block">Evidence Check</span>
                    <span className="font-mono font-bold text-slate-200">{act.evidence_score?.toFixed(2)}</span>
                    <span className="text-[10px] text-slate-400 ml-1.5">
                      ({act.evidence_verified ? 'Verified' : 'Refuted/Unverified'})
                    </span>
                  </div>
                  <div className="bg-slate-900 p-2 rounded border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-bold block">Reason Check</span>
                    <span className="font-mono font-bold text-slate-200">{act.reason_score?.toFixed(2)}</span>
                    <span className="text-[10px] text-slate-400 ml-1.5">
                      ({act.reason_is_relevant ? 'Goal Aligned' : 'Derailed'})
                    </span>
                  </div>
                  <div className="bg-slate-900 p-2 rounded border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-bold block">Risk Check</span>
                    <span className="font-mono font-bold text-slate-200">{act.risk_score?.toFixed(2)}</span>
                    <span className="text-[10px] capitalize text-slate-400 ml-1.5">
                      ({act.risk_level || 'low'})
                    </span>
                  </div>
                </div>

                {/* Overrides if any */}
                {act.overrides_applied && act.overrides_applied.length > 0 && (
                  <div className="p-2.5 bg-rose-950/40 border border-rose-500/30 rounded text-[11px] text-rose-300 font-sans">
                    <span className="font-bold block mb-0.5">Safety Overrides Triggered:</span>
                    {act.overrides_applied.map((o, idx) => (
                      <div key={idx}>&bull; {o}</div>
                    ))}
                  </div>
                )}

                {/* Actual Execution Output */}
                {act.execution_output && (
                  <div className="bg-black/60 p-3 rounded border border-slate-800/80 font-mono text-[11px] text-slate-300 whitespace-pre-wrap max-h-48 overflow-y-auto">
                    <div className="text-slate-400 text-[10px] uppercase font-bold mb-1 flex items-center justify-between">
                      <span>Execution Result (exit_code: {act.execution_exit_code})</span>
                      {act.snapshot_id && (
                        <span className="text-amber-400">Snapshot: {act.snapshot_id}</span>
                      )}
                    </div>
                    {act.execution_output}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="py-12 text-center text-xs text-slate-400">
            <Terminal className="w-8 h-8 mx-auto text-slate-700 mb-2" />
            No active execution trace. Input a task prompt above and click "Start Autonomous Agent".
          </div>
        )}
      </div>
    </div>
  );
};
