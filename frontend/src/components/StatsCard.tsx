import React from 'react';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  subtitle?: string;
  trend?: {
    value: string | number;
    isPositive?: boolean;
    label?: string;
  };
  colorScheme?: 'primary' | 'secondary' | 'accent' | 'critical' | 'warning' | 'success';
}

const colorStyles = {
  primary: {
    bgGlow: 'from-indigo-600/20 to-indigo-900/10',
    iconBg: 'bg-indigo-500/15 border-indigo-500/30 text-indigo-400',
    accentBorder: 'hover:border-indigo-500/40',
  },
  secondary: {
    bgGlow: 'from-purple-600/20 to-purple-900/10',
    iconBg: 'bg-purple-500/15 border-purple-500/30 text-purple-400',
    accentBorder: 'hover:border-purple-500/40',
  },
  accent: {
    bgGlow: 'from-cyan-600/20 to-cyan-900/10',
    iconBg: 'bg-cyan-500/15 border-cyan-500/30 text-cyan-400',
    accentBorder: 'hover:border-cyan-500/40',
  },
  critical: {
    bgGlow: 'from-rose-600/20 to-red-900/10',
    iconBg: 'bg-rose-500/15 border-rose-500/30 text-rose-400',
    accentBorder: 'hover:border-rose-500/40',
  },
  warning: {
    bgGlow: 'from-amber-600/20 to-yellow-900/10',
    iconBg: 'bg-amber-500/15 border-amber-500/30 text-amber-400',
    accentBorder: 'hover:border-amber-500/40',
  },
  success: {
    bgGlow: 'from-emerald-600/20 to-green-900/10',
    iconBg: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400',
    accentBorder: 'hover:border-emerald-500/40',
  },
};

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon: Icon,
  subtitle,
  trend,
  colorScheme = 'primary',
}) => {
  const styles = colorStyles[colorScheme] || colorStyles.primary;

  return (
    <div
      className={`relative overflow-hidden rounded-2xl glass p-6 transition-all duration-300 border border-slate-800/80 ${styles.accentBorder} group shadow-lg`}
    >
      {/* Background ambient glow */}
      <div
        className={`absolute -right-6 -bottom-6 w-32 h-32 bg-gradient-to-br ${styles.bgGlow} rounded-full blur-2xl pointer-events-none group-hover:scale-125 transition-transform duration-500`}
      />

      <div className="flex items-start justify-between relative z-10">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
            {title}
          </p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-extrabold text-white tracking-tight">
              {value}
            </h3>
            {subtitle && (
              <span className="text-xs text-slate-400">{subtitle}</span>
            )}
          </div>
        </div>

        <div className={`p-3 rounded-xl border ${styles.iconBg} backdrop-blur-md`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>

      {trend && (
        <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center gap-1.5 text-xs relative z-10">
          {trend.isPositive ? (
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          ) : (
            <TrendingDown className="w-4 h-4 text-rose-400" />
          )}
          <span
            className={`font-semibold ${
              trend.isPositive ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {trend.value}
          </span>
          {trend.label && <span className="text-slate-400">{trend.label}</span>}
        </div>
      )}
    </div>
  );
};

export default StatsCard;
