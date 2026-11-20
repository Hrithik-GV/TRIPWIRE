import React from 'react';
import { Play, Camera, PauseOctagon, AlertTriangle } from 'lucide-react';

interface DecisionBadgeProps {
  decision?: string;
  size?: 'sm' | 'md';
}

export const DecisionBadge: React.FC<DecisionBadgeProps> = ({ decision, size = 'md' }) => {
  const norm = (decision || '').toUpperCase();
  const isSm = size === 'sm';
  const px = isSm ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs';

  if (norm === 'RUN') {
    return (
      <span className={`inline-flex items-center font-semibold rounded border bg-emerald-950/40 text-emerald-400 border-emerald-500/40 ${px}`}>
        <Play className={`${isSm ? 'w-2.5 h-2.5' : 'w-3 h-3'} mr-1.5 fill-current`} />
        RUN
      </span>
    );
  }

  if (norm === 'SNAPSHOT_AND_RUN') {
    return (
      <span className={`inline-flex items-center font-semibold rounded border bg-amber-950/40 text-amber-400 border-amber-500/40 ${px}`}>
        <Camera className={`${isSm ? 'w-2.5 h-2.5' : 'w-3 h-3'} mr-1.5`} />
        SNAPSHOT & RUN
      </span>
    );
  }

  if (norm === 'PAUSE') {
    return (
      <span className={`inline-flex items-center font-semibold rounded border bg-rose-950/40 text-rose-400 border-rose-500/40 ${px}`}>
        <PauseOctagon className={`${isSm ? 'w-2.5 h-2.5' : 'w-3 h-3'} mr-1.5`} />
        PAUSE
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center font-medium rounded border bg-slate-800 text-slate-400 border-slate-700 ${px}`}>
      <AlertTriangle className={`${isSm ? 'w-2.5 h-2.5' : 'w-3 h-3'} mr-1.5`} />
      {norm || 'PENDING'}
    </span>
  );
};

