import React from 'react';
import {
  Layers,
  Activity,
  CheckCircle2,
  AlertOctagon,
  Clock,
  Gauge,
  ArrowUpRight,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import type { SystemStats, ActionItem } from '../services/api';
import { DecisionBadge } from './DecisionBadge';

interface OverviewViewProps {
  stats: SystemStats | null;
  actions: ActionItem[];
  onNavigateToTab: (tab: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ stats, actions, onNavigateToTab }) => {
  // Prepare chart data from recent actions (reversed to show chronological left-to-right)
  const chartData = [...actions]
    .slice(0, 15)
    .reverse()
    .map((act, idx) => ({
      name: `Step ${act.step_number || idx + 1}`,
      action: act.action_name,
      trust: act.trust_score !== undefined && act.trust_score !== null ? Number(act.trust_score.toFixed(2)) : 0,
      decision: act.decision || 'UNKNOWN',
    }));

  return (
    <div className="space-y-6">
      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-bold uppercase tracking-wider">
            <span>Total Tasks</span>
            <Layers className="w-3.5 h-3.5 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">
            {stats ? stats.total_tasks : '—'}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-medium">
            {stats ? `${stats.completed_tasks} completed` : 'Loading...'}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-bold uppercase tracking-wider">
            <span>Total Actions</span>
            <Activity className="w-3.5 h-3.5 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">
            {stats ? stats.total_actions : '—'}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-medium">
            Evaluated by Tripwire
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 shadow-xs">
          <div className="flex items-center justify-between text-emerald-400/90 text-[11px] font-bold uppercase tracking-wider">
            <span>Executed</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">
            {stats ? stats.executed_actions : '—'}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-medium">
            Safely sandbox executed
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 shadow-xs">
          <div className="flex items-center justify-between text-rose-400/90 text-[11px] font-bold uppercase tracking-wider">
            <span>Blocked / Paused</span>
            <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-2">
            {stats ? stats.paused_actions : '—'}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-medium">
            Tripped safety guardrails
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 shadow-xs cursor-pointer hover:border-amber-500/50 transition-colors"
             onClick={() => onNavigateToTab('approvals')}>
          <div className="flex items-center justify-between text-amber-400/90 text-[11px] font-bold uppercase tracking-wider">
            <span>Pending Approvals</span>
            <Clock className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-2">
            {stats ? stats.waiting_approval_tasks : '—'}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 flex items-center font-medium">
            <span>Requires review</span>
            <ArrowUpRight className="w-3 h-3 ml-1" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 shadow-xs">
          <div className="flex items-center justify-between text-cyan-400/90 text-[11px] font-bold uppercase tracking-wider">
            <span>Avg Trust Score</span>
            <Gauge className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-cyan-300 mt-2">
            {stats ? stats.average_trust_score.toFixed(2) : '—'}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-medium">
            Composite 0.0 - 1.0 scale
          </div>
        </div>
      </div>

      {/* Trust Score Trajectory Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Real-Time Trust Score Evaluation Trajectory
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Synthesis: (0.40 &times; Evidence) + (0.35 &times; Reason) + (0.25 &times; Inverted Risk). Dynamic thresholds: RUN (&ge; 0.80), SNAPSHOT (&ge; 0.50), PAUSE (&lt; 0.50).
            </p>
          </div>
          <div className="flex items-center space-x-3 text-xs font-medium">
            <span className="flex items-center text-emerald-400">
              <span className="w-2.5 h-0.5 bg-emerald-500 mr-1.5"></span> RUN (0.80)
            </span>
            <span className="flex items-center text-amber-400">
              <span className="w-2.5 h-0.5 bg-amber-500 mr-1.5"></span> SNAPSHOT (0.50)
            </span>
          </div>
        </div>

        <div className="h-64 w-full">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="trustGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 1]} stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '6px', fontSize: '12px' }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <ReferenceLine y={0.80} stroke="#10b981" strokeDasharray="4 4" label={{ value: 'RUN (0.80)', fill: '#10b981', fontSize: 10 }} />
                <ReferenceLine y={0.50} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: 'SNAPSHOT (0.50)', fill: '#f59e0b', fontSize: 10 }} />
                <Area type="monotone" dataKey="trust" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#trustGradient)" name="Trust Score" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-slate-400">
              No action evaluation data available yet. Start an agent execution to see live telemetry.
            </div>
          )}
        </div>
      </div>

      {/* Recent Action Timeline */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Recent Action Telemetry
          </h3>
          <button
            onClick={() => onNavigateToTab('evaluations')}
            className="text-xs text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
          >
            View All Evaluations &rarr;
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                <th className="py-2.5 px-3">Action ID</th>
                <th className="py-2.5 px-3">Target / Operation</th>
                <th className="py-2.5 px-3">Tripwire Decision</th>
                <th className="py-2.5 px-3">Trust Score</th>
                <th className="py-2.5 px-3">Risk Level</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {actions.slice(0, 8).map((act) => (
                <tr key={act.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                    {act.id}
                  </td>
                  <td className="py-2.5 px-3 font-sans font-medium text-slate-200">
                    <span className="font-mono text-emerald-400 text-xs mr-1.5">{act.action_name}</span>
                    <span className="text-slate-400 text-xs">
                      {act.params.path || act.params.target || ''}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <DecisionBadge decision={act.decision} size="sm" />
                  </td>
                  <td className="py-2.5 px-3 font-bold text-slate-200">
                    {act.trust_score !== undefined && act.trust_score !== null ? act.trust_score.toFixed(3) : '—'}
                  </td>
                  <td className="py-2.5 px-3 font-sans capitalize text-slate-400">
                    {act.risk_level || '—'}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                      act.status === 'EXECUTED' ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-500/30' :
                      act.status === 'PAUSED' ? 'bg-rose-950/60 text-rose-400 border border-rose-500/30' :
                      act.status === 'REJECTED' ? 'bg-slate-800 text-slate-400 border border-slate-700' :
                      'bg-slate-800 text-slate-300'
                    }`}>
                      {act.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-400 text-[11px] font-sans">
                    {new Date(act.created_at).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
              {actions.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-center py-6 text-slate-400 font-sans">
                    No actions logged yet. Run an agent task from the Agent Execution tab.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
