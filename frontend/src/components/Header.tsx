import React from 'react';
import { ShieldCheck, RefreshCw, Radio, ServerCrash } from 'lucide-react';
import type { HealthInfo } from '../services/api';

interface HeaderProps {
  health: HealthInfo | null;
  loading: boolean;
  sseConnected: boolean;
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, loading, sseConnected, onRefresh }) => {
  return (
    <header className="bg-slate-900/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand identity */}
        <div className="flex items-center space-x-3.5">
          <div className="w-9 h-9 rounded bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold tracking-wider text-sm shadow-sm">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-base font-extrabold tracking-wider text-white">TRIPWIRE</span>
              <span className="text-[10px] font-bold tracking-widest uppercase text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700">
                SUPERNOVA
              </span>
            </div>
            <div className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
              AI AGENT SAFETY MONITOR &bull; RUNTIME MIDDLEWARE
            </div>
          </div>
        </div>

        {/* Live telemetry indicators */}
        <div className="flex items-center space-x-4">
          {/* SSE Live stream indicator */}
          <div className="hidden sm:flex items-center space-x-1.5 text-xs px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-slate-300">
            <Radio className={`w-3 h-3 ${sseConnected ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`} />
            <span className="text-[11px] font-medium">
              {sseConnected ? 'Live Telemetry' : 'Connecting SSE...'}
            </span>
          </div>

          {/* Backend Health Badge */}
          <div className="flex items-center space-x-2 text-xs">
            {loading ? (
              <span className="inline-flex items-center px-2.5 py-1 rounded text-xs bg-slate-800 text-slate-400 border border-slate-700">
                <RefreshCw className="w-3 h-3 animate-spin mr-1.5" />
                Connecting...
              </span>
            ) : health ? (
              <span className="inline-flex items-center px-2.5 py-1 rounded text-xs font-medium bg-emerald-950/60 text-emerald-400 border border-emerald-500/30">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-2 animate-pulse"></span>
                FastAPI v{health.version} ({health.environment})
              </span>
            ) : (
              <span className="inline-flex items-center px-2.5 py-1 rounded text-xs font-semibold bg-rose-950/60 text-rose-400 border border-rose-500/40">
                <ServerCrash className="w-3.5 h-3.5 mr-1.5" />
                Backend Disconnected
              </span>
            )}
          </div>

          {/* Manual Refresh */}
          <button
            onClick={onRefresh}
            title="Refresh system state"
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded border border-slate-700 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
