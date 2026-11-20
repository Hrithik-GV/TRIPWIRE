import React, { useState } from 'react';
import {
  Camera,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  HardDrive,
  Clock,
} from 'lucide-react';
import type { SnapshotItem } from '../services/api';
import { restoreSnapshot } from '../services/api';

interface SnapshotsViewProps {
  snapshots: SnapshotItem[];
  onSnapshotRestored: () => void;
}

export const SnapshotsView: React.FC<SnapshotsViewProps> = ({
  snapshots,
  onSnapshotRestored,
}) => {
  const [restoringId, setRestoringId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRestore = async (id: string) => {
    if (!window.confirm(`Are you sure you want to roll back demo_workspace to snapshot ${id}?`)) {
      return;
    }

    setRestoringId(id);
    setMessage(null);
    setError(null);
    try {
      const res = await restoreSnapshot(id);
      setMessage(res.message);
      onSnapshotRestored();
    } catch (err: any) {
      setError(err.message || 'Failed to restore snapshot');
    } finally {
      setRestoringId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-xs flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
            <Camera className="w-4 h-4 text-amber-400" />
            <span>Workspace Rollback Snapshots</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Automated point-in-time filesystem snapshots captured by Tripwire prior to medium/high-risk code mutations.
          </p>
        </div>
        <div className="text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
          Target: <strong className="text-emerald-400">demo_workspace/</strong>
        </div>
      </div>

      {message && (
        <div className="p-3 bg-emerald-950/60 border border-emerald-500/40 rounded text-xs text-emerald-300 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-500/40 rounded text-xs text-rose-300 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Snapshots Grid */}
      {snapshots.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {snapshots.map((snap) => (
            <div
              key={snap.snapshot_id}
              className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3 hover:border-slate-700 transition-colors shadow-xs"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <HardDrive className="w-4 h-4 text-amber-400" />
                  <span className="font-mono text-xs font-bold text-white">
                    {snap.snapshot_id}
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950/60 text-amber-400 border border-amber-500/30">
                  {snap.file_count} Files Saved
                </span>
              </div>

              <p className="text-xs text-slate-400">
                {snap.description || 'Pre-execution safe checkpoint'}
              </p>

              <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs">
                <div className="text-slate-400 text-[11px] flex items-center space-x-1.5 font-mono">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  <span>{new Date(snap.timestamp).toLocaleString()}</span>
                </div>

                <button
                  onClick={() => handleRestore(snap.snapshot_id)}
                  disabled={restoringId === snap.snapshot_id}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs font-semibold border border-slate-700 flex items-center space-x-1.5 transition-colors disabled:opacity-50"
                >
                  <RotateCcw className={`w-3.5 h-3.5 ${restoringId === snap.snapshot_id ? 'animate-spin' : ''}`} />
                  <span>{restoringId === snap.snapshot_id ? 'Rolling back...' : 'Restore Snapshot'}</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-lg py-16 text-center space-y-2">
          <Camera className="w-8 h-8 mx-auto text-slate-700 mb-1" />
          <h4 className="text-sm font-bold text-slate-200">No Snapshots Captured Yet</h4>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            When an action trips the guarded execution threshold (<strong className="text-amber-400">SNAPSHOT_AND_RUN</strong>), Tripwire takes a point-in-time filesystem checkpoint before dispatching the modification.
          </p>
        </div>
      )}
    </div>
  );
};
