import React from 'react';
import {
  LayoutDashboard,
  Terminal,
  ShieldAlert,
  CheckSquare,
  History,
  Camera,
  FolderLock,
} from 'lucide-react';

export type TabKey =
  | 'overview'
  | 'agent-execution'
  | 'evaluations'
  | 'approvals'
  | 'history'
  | 'snapshots';

interface SidebarProps {
  activeTab: TabKey;
  onSelectTab: (tab: TabKey) => void;
  pendingApprovalsCount: number;
}

interface NavItem {
  key: TabKey;
  label: string;
  icon: typeof LayoutDashboard;
  badge?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  pendingApprovalsCount,
}) => {
  const navItems: NavItem[] = [
    { key: 'overview', label: 'Overview', icon: LayoutDashboard },
    { key: 'agent-execution', label: 'Agent Execution', icon: Terminal },
    { key: 'evaluations', label: 'Tripwire Evaluations', icon: ShieldAlert },
    {
      key: 'approvals',
      label: 'Approval Center',
      icon: CheckSquare,
      badge: pendingApprovalsCount,
    },
    { key: 'history', label: 'Execution History', icon: History },
    { key: 'snapshots', label: 'Snapshots', icon: Camera },
  ];

  return (
    <aside className="w-64 flex-shrink-0">
      <nav className="bg-slate-900 border border-slate-800 rounded-lg p-2 space-y-1 shadow-sm">
        <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.key;
          return (
            <button
              key={item.key}
              onClick={() => onSelectTab(item.key)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-md text-xs font-semibold tracking-wide transition-all ${
                isActive
                  ? 'bg-slate-800 text-emerald-400 border border-emerald-500/30 shadow-xs'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center space-x-3 truncate">
                <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span className="truncate">{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="ml-2 px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 animate-pulse">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Target Sandbox Card */}
      <div className="mt-4 bg-slate-900 border border-slate-800 rounded-lg p-3.5 text-xs text-slate-400 space-y-2 shadow-sm">
        <div className="font-bold text-slate-200 flex items-center space-x-2 text-[11px] uppercase tracking-wider">
          <FolderLock className="w-3.5 h-3.5 text-emerald-400" />
          <span>Restricted Sandbox</span>
        </div>
        <div className="font-mono text-[11px] bg-slate-950 text-emerald-300/90 px-2 py-1 rounded border border-slate-800 break-all">
          demo_workspace/
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Actions are evaluated against Tripwire policies before filesystem execution.
        </p>
      </div>
    </aside>
  );
};

