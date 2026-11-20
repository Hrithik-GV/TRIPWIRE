import React, { useState } from 'react';
import {
  CheckSquare,
  Check,
  X,
  Clock,
} from 'lucide-react';
import { type ActionItem, approveAction, rejectAction } from '../services/api';

interface ApprovalCenterViewProps {
  actions: ActionItem[];
  onActionProcessed: () => void;
}

export const ApprovalCenterView: React.FC<ApprovalCenterViewProps> = ({
  actions,
  onActionProcessed,
}) => {
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Filter for paused actions awaiting decision
  const pendingActions = actions.filter((act) => act.status === 'PAUSED');

  const handleApprove = async (actionId: string) => {
    setLoadingId(actionId);
    setError(null);
    try {
      await approveAction(actionId);
      onActionProcessed();
    } catch (err: any) {
      setError(err.message || 'Failed to approve action');
    } finally {
      setLoadingId(null);
    }
  };

  const handleReject = async (actionId: string) => {
    setLoadingId(actionId);
    setError(null);
    try {
      await rejectAction(actionId);
      onActionProcessed();
    } catch (err: any) {
      setError(err.message || 'Failed to reject action');
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <CheckSquare className="w-4 h-4 text-amber-400" />
              <span>Human-in-the-Loop Authorization Center</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Actions flagged with critical risk, insufficient trust, or non-recoverable impact are halted here awaiting manual review.
            </p>
          </div>
          <span className="px-2.5 py-1 rounded text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            {pendingActions.length} Pending Actions
          </span>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-500/40 rounded text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Paused Actions Cards */}
      {pendingActions.length > 0 ? (
        <div className="space-y-4">
          {pendingActions.map((act) => (
            <div
              key={act.id}
              className="bg-slate-900 border border-amber-500/30 rounded-lg p-5 shadow-md space-y-4 font-sans text-xs"
            >
              {/* Card top */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2.5">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950/80 text-rose-400 border border-rose-500/30">
                    PAUSED
                  </span>
                  <span className="font-mono text-white text-sm font-bold">
                    {act.action_name}
                  </span>
                  <span className="font-mono text-emerald-400">
                    {act.params.path || act.params.target || ''}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 font-mono">
                  Action ID: <span className="text-slate-300">{act.id}</span> &bull; Task ID: <span className="text-slate-300">{act.task_id}</span>
                </div>
              </div>

              {/* Rationale & Reason for Pause */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-950 p-3.5 rounded border border-slate-800 space-y-1">
                  <span className="font-bold text-slate-400 uppercase text-[10px] block">
                    Agent Rationale:
                  </span>
                  <p className="text-slate-200 leading-relaxed">
                    {act.rationale || 'No rationale provided'}
                  </p>
                </div>

                <div className="bg-rose-950/20 p-3.5 rounded border border-rose-500/30 space-y-1">
                  <span className="font-bold text-rose-300 uppercase text-[10px] block">
                    Tripwire Gating Justification:
                  </span>
                  <p className="text-rose-200/90 leading-relaxed">
                    {act.trust_explanation || 'Action paused by safety thresholds.'}
                  </p>
                </div>
              </div>

              {/* Risk Details & Safety Overrides */}
              <div className="bg-slate-950 p-3.5 rounded border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-400 uppercase text-[10px]">
                    Risk Assessment &amp; Overrides
                  </span>
                  <span className="font-mono text-rose-400 font-bold capitalize">
                    {act.risk_level || 'high'} Risk (Score: {act.risk_score?.toFixed(2)})
                  </span>
                </div>
                {act.overrides_applied && act.overrides_applied.length > 0 && (
                  <div className="space-y-1 text-rose-300 font-mono text-[11px]">
                    {act.overrides_applied.map((o, idx) => (
                      <div key={idx}>&bull; {o}</div>
                    ))}
                  </div>
                )}
                {act.risk_explanation && (
                  <p className="text-slate-400 text-[11px]">
                    {act.risk_explanation}
                  </p>
                )}
              </div>

              {/* Bottom Actions Buttons */}
              <div className="flex items-center justify-between pt-2">
                <div className="text-[11px] text-slate-400 flex items-center space-x-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  <span>Logged at {new Date(act.created_at).toLocaleTimeString()}</span>
                </div>

                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => handleReject(act.id)}
                    disabled={loadingId === act.id}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-rose-300 rounded text-xs font-semibold border border-slate-700 flex items-center space-x-1.5 transition-colors disabled:opacity-50"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>Reject &amp; Abort Task</span>
                  </button>

                  <button
                    onClick={() => handleApprove(act.id)}
                    disabled={loadingId === act.id}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-bold flex items-center space-x-1.5 shadow-sm transition-colors disabled:opacity-50"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>{loadingId === act.id ? 'Authorizing...' : 'Authorize Execution'}</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-lg py-16 text-center space-y-2">
          <CheckSquare className="w-8 h-8 mx-auto text-emerald-400/80 mb-1" />
          <h4 className="text-sm font-bold text-slate-200">Approval Queue Is Empty</h4>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            No dangerous actions are currently paused. When an agent proposes an action tripping safety guardrails, it will appear here for human authorization.
          </p>
        </div>
      )}
    </div>
  );
};
