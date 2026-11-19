import React from 'react';
import { Severity } from '../types';
import { AlertTriangle, AlertOctagon, AlertCircle, Info } from 'lucide-react';

interface SeverityBadgeProps {
  severity: Severity | string;
  className?: string;
  showIcon?: boolean;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  severity,
  className = '',
  showIcon = true,
}) => {
  const normSeverity = (severity || 'low').toLowerCase();

  switch (normSeverity) {
    case 'critical':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide bg-red-950/80 text-red-200 border border-red-500/50 shadow-[0_0_12px_rgba(239,68,68,0.3)] animate-pulse ${className}`}
        >
          {showIcon && <AlertOctagon className="w-3.5 h-3.5 text-red-400 shrink-0" />}
          <span>CRITICAL</span>
        </span>
      );

    case 'high':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide bg-amber-950/70 text-amber-200 border border-amber-500/40 shadow-[0_0_8px_rgba(245,158,11,0.2)] ${className}`}
        >
          {showIcon && <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
          <span>HIGH</span>
        </span>
      );

    case 'medium':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide bg-yellow-950/60 text-yellow-200 border border-yellow-500/30 ${className}`}
        >
          {showIcon && <AlertCircle className="w-3.5 h-3.5 text-yellow-400 shrink-0" />}
          <span>MEDIUM</span>
        </span>
      );

    case 'low':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide bg-slate-800/80 text-blue-200 border border-blue-500/30 ${className}`}
        >
          {showIcon && <Info className="w-3.5 h-3.5 text-blue-400 shrink-0" />}
          <span>LOW</span>
        </span>
      );
  }
};

export default SeverityBadge;
