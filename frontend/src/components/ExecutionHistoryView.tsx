import React, { useState } from 'react';
import {
  History,
  Terminal,
  Search,
} from 'lucide-react';
import type { ActionItem } from '../services/api';
import { DecisionBadge } from './DecisionBadge';

interface ExecutionHistoryViewProps {
  actions: ActionItem[];
}

export const ExecutionHistoryView: React.FC<ExecutionHistoryViewProps> = ({ actions }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = actions.filter((act) => {
    return (
      act.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      act.action_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (act.params.path || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (act.execution_output || '').toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
            <History className="w-4 h-4 text-slate-400" />
            <span>Immutable Execution Audit Trail</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Chronological audit log of all agent-proposed actions, safety decisions, and actual sandbox execution outputs.
          </p>
        </div>

        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search audit trail..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50 w-56"
          />
        </div>
      </div>

      {/* Audit Timeline */}
      <div className="space-y-3 font-mono text-xs">
        {filtered.map((act) => (
          <div
            key={act.id}
            className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3 hover:border-slate-700 transition-colors"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 font-sans">
              <div className="flex items-center space-x-3">
                <span className="w-6 h-6 rounded bg-slate-800 text-slate-300 text-xs font-bold flex items-center justify-center font-mono">
                  {act.step_number}
                </span>
                <span className="font-mono text-emerald-400 font-bold text-sm">
                  {act.action_name}
                </span>
                <span className="text-slate-400 font-mono text-xs">
                  {act.params.path || act.params.target || ''}
                </span>
              </div>

              <div className="flex items-center space-x-3">
                <DecisionBadge decision={act.decision} size="sm" />
                <span className="text-slate-400 text-xs">
                  Trust: <strong className="text-slate-200">{act.trust_score?.toFixed(3)}</strong>
                </span>
                <span className="text-slate-400 text-[11px]">
                  {new Date(act.created_at).toLocaleTimeString()}
                </span>
              </div>
            </div>

            {/* Rationale */}
            {act.rationale && (
              <div className="text-slate-300 font-sans text-xs bg-slate-950 p-2.5 rounded border border-slate-800/80">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">
                  Proposed Rationale:
                </span>
                {act.rationale}
              </div>
            )}

            {/* Execution Output Box */}
            <div className="bg-black/60 p-3 rounded border border-slate-800 text-[11px] space-y-1">
              <div className="flex items-center justify-between text-[10px] font-sans font-bold text-slate-400 uppercase">
                <div className="flex items-center space-x-1.5">
                  <Terminal className="w-3 h-3 text-slate-400" />
                  <span>Sandbox Output (exit_code: {act.execution_exit_code ?? 'None'})</span>
                </div>
                {act.execution_time_ms !== undefined && act.execution_time_ms !== null && (
                  <span className="text-slate-400 font-mono">
                    {act.execution_time_ms.toFixed(1)} ms
                  </span>
                )}
              </div>
              <pre className="text-slate-300 whitespace-pre-wrap max-h-36 overflow-y-auto font-mono text-[11px]">
                {act.execution_output || act.execution_error || '(No execution output recorded)'}
              </pre>
            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="py-12 bg-slate-900 border border-slate-800 rounded-lg text-center text-slate-400 text-xs">
            No execution history found.
          </div>
        )}
      </div>
    </div>
  );
};
