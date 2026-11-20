import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Search,
  Filter,
} from 'lucide-react';
import type { ActionItem } from '../services/api';
import { DecisionBadge } from './DecisionBadge';

interface EvaluationsViewProps {
  actions: ActionItem[];
}

export const EvaluationsView: React.FC<EvaluationsViewProps> = ({ actions }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [decisionFilter, setDecisionFilter] = useState('ALL');

  const filtered = actions.filter((act) => {
    const matchesSearch =
      act.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      act.action_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (act.rationale || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDecision =
      decisionFilter === 'ALL' || act.decision === decisionFilter;
    return matchesSearch && matchesDecision;
  });

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="space-y-6">
      {/* Header & Filters */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Tripwire Safety Evaluations
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Multi-dimensional evaluation breakdown: Evidence ground-truth, Task alignment reason, and Risk classification.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            {/* Search */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search action or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50 w-48"
              />
            </div>

            {/* Filter */}
            <div className="flex items-center space-x-1.5 bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-400">
              <Filter className="w-3 h-3 text-slate-400" />
              <select
                value={decisionFilter}
                onChange={(e) => setDecisionFilter(e.target.value)}
                className="bg-transparent text-slate-300 focus:outline-none text-xs cursor-pointer"
              >
                <option value="ALL" className="bg-slate-900 text-slate-200">All Decisions</option>
                <option value="RUN" className="bg-slate-900 text-slate-200">RUN Only</option>
                <option value="SNAPSHOT_AND_RUN" className="bg-slate-900 text-slate-200">SNAPSHOT Only</option>
                <option value="PAUSE" className="bg-slate-900 text-slate-200">PAUSE Only</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Evaluations List */}
      <div className="space-y-3">
        {filtered.map((act) => {
          const isExpanded = expandedId === act.id;
          return (
            <div
              key={act.id}
              className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden transition-all shadow-xs"
            >
              {/* Row Summary */}
              <div
                onClick={() => toggleExpand(act.id)}
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors select-none"
              >
                <div className="flex items-center space-x-3 min-w-0">
                  <DecisionBadge decision={act.decision} size="sm" />
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-emerald-400 text-xs font-bold">
                        {act.action_name}
                      </span>
                      <span className="font-mono text-slate-400 text-xs">
                        {act.params.path || act.params.target || ''}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        ({act.id})
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5 truncate max-w-xl">
                      {act.rationale || 'No rationale provided'}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-6 flex-shrink-0">
                  {/* Scores pills */}
                  <div className="hidden sm:flex items-center space-x-4 text-xs font-mono">
                    <span className="text-slate-400 text-[11px]">
                      EV: <strong className="text-slate-200">{act.evidence_score?.toFixed(2)}</strong>
                    </span>
                    <span className="text-slate-400 text-[11px]">
                      RS: <strong className="text-slate-200">{act.reason_score?.toFixed(2)}</strong>
                    </span>
                    <span className="text-slate-400 text-[11px]">
                      RK: <strong className="text-slate-200">{act.risk_score?.toFixed(2)}</strong>
                    </span>
                    <span className="text-slate-300 text-xs font-bold bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      Trust: {act.trust_score?.toFixed(3)}
                    </span>
                  </div>

                  <button className="text-slate-400 hover:text-slate-200 p-1">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Expandable Evaluation Details */}
              {isExpanded && (
                <div className="border-t border-slate-800 bg-slate-950 p-5 space-y-4 text-xs font-sans">
                  {/* Synthesis Explanation */}
                  <div className="bg-slate-900 p-3.5 rounded border border-slate-800">
                    <span className="font-bold text-slate-400 uppercase text-[10px] tracking-wider block mb-1">
                      Tripwire Decision &amp; Trust Explanation:
                    </span>
                    <p className="text-slate-200 leading-relaxed">
                      {act.trust_explanation || 'No detailed trust explanation generated.'}
                    </p>
                  </div>

                  {/* 3 Pillars of Evaluation */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {/* Evidence Pillar */}
                    <div className="bg-slate-900 p-3.5 rounded border border-slate-800 space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] font-bold text-slate-300 uppercase">
                        <span>1. Evidence Check</span>
                        <span className="font-mono text-emerald-400 font-bold">{act.evidence_score?.toFixed(2)}</span>
                      </div>
                      <p className="text-slate-400 text-[11px] leading-relaxed">
                        {act.evidence_explanation || 'No evidence explanation recorded.'}
                      </p>
                      {act.evidence_details && Object.keys(act.evidence_details).length > 0 && (
                        <div className="mt-2 pt-2 border-t border-slate-800 font-mono text-[10px] text-slate-400 space-y-0.5">
                          <div>Verified: <span className="text-slate-300">{String(act.evidence_verified)}</span></div>
                          {act.evidence_details.target_file && (
                            <div>File: <span className="text-slate-300">{act.evidence_details.target_file}</span></div>
                          )}
                          {act.evidence_details.has_content_diff !== undefined && (
                            <div>Diff Detected: <span className="text-slate-300">{String(act.evidence_details.has_content_diff)}</span></div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Reason Pillar */}
                    <div className="bg-slate-900 p-3.5 rounded border border-slate-800 space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] font-bold text-slate-300 uppercase">
                        <span>2. Reason Check</span>
                        <span className="font-mono text-emerald-400 font-bold">{act.reason_score?.toFixed(2)}</span>
                      </div>
                      <p className="text-slate-400 text-[11px] leading-relaxed">
                        {act.reason_explanation || 'No reason explanation recorded.'}
                      </p>
                      <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] text-slate-400 font-mono">
                        <div>Mode: <span className="text-slate-300">{act.evaluation_mode || 'deterministic_fallback'}</span></div>
                        <div>Relevant: <span className="text-slate-300">{String(act.reason_is_relevant)}</span></div>
                      </div>
                    </div>

                    {/* Risk Pillar */}
                    <div className="bg-slate-900 p-3.5 rounded border border-slate-800 space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] font-bold text-slate-300 uppercase">
                        <span>3. Risk Check</span>
                        <span className="font-mono text-rose-400 font-bold">{act.risk_score?.toFixed(2)}</span>
                      </div>
                      <p className="text-slate-400 text-[11px] leading-relaxed">
                        {act.risk_explanation || 'No risk explanation recorded.'}
                      </p>
                      <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] text-slate-400 font-mono">
                        <div>Level: <span className="text-slate-300 capitalize">{act.risk_level}</span></div>
                        <div>Reversible: <span className="text-slate-300">{String(act.is_reversible)}</span></div>
                        {act.impact_scope && (
                          <div>Impact: <span className="text-slate-300">{act.impact_scope}</span></div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Overrides if any */}
                  {act.overrides_applied && act.overrides_applied.length > 0 && (
                    <div className="bg-rose-950/40 border border-rose-500/40 p-3 rounded text-rose-300 text-xs">
                      <strong className="block mb-1">Enforced Safety Overrides:</strong>
                      {act.overrides_applied.map((o, idx) => (
                        <div key={idx} className="font-mono text-[11px]">&bull; {o}</div>
                      ))}
                    </div>
                  )}

                  {/* Raw Params & Execution Output */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-[11px]">
                    <div className="bg-slate-900 p-3 rounded border border-slate-800">
                      <span className="font-bold text-slate-400 uppercase text-[10px] font-sans block mb-1">
                        Parameters JSON
                      </span>
                      <pre className="text-slate-300 whitespace-pre-wrap overflow-x-auto max-h-36">
                        {JSON.stringify(act.params, null, 2)}
                      </pre>
                    </div>

                    <div className="bg-slate-900 p-3 rounded border border-slate-800">
                      <span className="font-bold text-slate-400 uppercase text-[10px] font-sans block mb-1">
                        Execution Output
                      </span>
                      <pre className="text-slate-300 whitespace-pre-wrap overflow-x-auto max-h-36">
                        {act.execution_output || act.execution_error || '(No output recorded)'}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {filtered.length === 0 && (
          <div className="py-12 bg-slate-900 border border-slate-800 rounded-lg text-center text-slate-400 text-xs">
            No matching actions found.
          </div>
        )}
      </div>
    </div>
  );
};
