import React from 'react';
import { ScanStatus } from '../types';
import { CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react';

interface ScanStatusBadgeProps {
  status: ScanStatus | string;
  className?: string;
}

export const ScanStatusBadge: React.FC<ScanStatusBadgeProps> = ({ status, className = '' }) => {
  const normStatus = (status || 'pending').toLowerCase();

  switch (normStatus) {
    case 'completed':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-950/60 text-emerald-300 border border-emerald-500/30 ${className}`}
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Completed</span>
        </span>
      );

    case 'running':
    case 'in_progress':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-cyan-950/60 text-cyan-300 border border-cyan-500/40 animate-pulse ${className}`}
        >
          <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
          <span>Running...</span>
        </span>
      );

    case 'failed':
    case 'error':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-950/60 text-rose-300 border border-rose-500/40 ${className}`}
        >
          <XCircle className="w-3.5 h-3.5 text-rose-400" />
          <span>Failed</span>
        </span>
      );

    case 'pending':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800/70 text-slate-300 border border-slate-600/40 ${className}`}
        >
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>Pending</span>
        </span>
      );
  }
};

export default ScanStatusBadge;
