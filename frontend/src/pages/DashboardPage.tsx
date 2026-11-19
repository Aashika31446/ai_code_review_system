import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { dashboardApi, getErrorMessage } from '../services/api';
import { DashboardStats, Scan } from '../types';
import StatsCard from '../components/StatsCard';
import ScanStatusBadge from '../components/ScanStatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  PieChart,
  Pie,
  Legend,
} from 'recharts';
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  FolderGit2,
  PlusCircle,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Clock,
  FileCode,
} from 'lucide-react';
import toast from 'react-hot-toast';

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#dc2626',
  high: '#f59e0b',
  medium: '#eab308',
  low: '#3b82f6',
};

const CATEGORY_COLORS = [
  '#6366f1',
  '#8b5cf6',
  '#06b6d4',
  '#10b981',
  '#f59e0b',
  '#ec4899',
  '#3b82f6',
];

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const fetchStats = async (showToast = false) => {
    try {
      if (showToast) setIsRefreshing(true);
      const data = await dashboardApi.getStats();
      setStats(data);
      if (showToast) toast.success('Dashboard data updated');
    } catch (err) {
      console.warn('Dashboard fetch error:', err);
      // Fallback empty structure if brand new database
      if (!stats) {
        setStats({
          total_scans: 0,
          total_issues: 0,
          critical_issues: 0,
          total_projects: 0,
          issues_by_severity: [
            { severity: 'critical', count: 0 },
            { severity: 'high', count: 0 },
            { severity: 'medium', count: 0 },
            { severity: 'low', count: 0 },
          ],
          issues_by_category: [],
          recent_scans: [],
        });
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (isLoading) {
    return <LoadingSpinner message="Loading dashboard analytics..." />;
  }

  // Prepare chart data with default fallbacks
  const severityData = stats?.issues_by_severity?.length
    ? stats.issues_by_severity.map((item) => ({
        name: item.severity.charAt(0).toUpperCase() + item.severity.slice(1),
        count: item.count,
        color: SEVERITY_COLORS[item.severity.toLowerCase()] || '#6366f1',
      }))
    : [
        { name: 'Critical', count: 0, color: '#dc2626' },
        { name: 'High', count: 0, color: '#f59e0b' },
        { name: 'Medium', count: 0, color: '#eab308' },
        { name: 'Low', count: 0, color: '#3b82f6' },
      ];

  const categoryData = stats?.issues_by_category?.length
    ? stats.issues_by_category.map((item, index) => ({
        name: item.category.replace(/_/g, ' ').toUpperCase(),
        value: item.count,
        color: CATEGORY_COLORS[index % CATEGORY_COLORS.length],
      }))
    : [{ name: 'No Issues Yet', value: 1, color: '#334155' }];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
            <span>Welcome back,</span>
            <span className="gradient-text">{user?.username || 'Engineer'}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Real-time telemetry and security vulnerability breakdown across your repositories.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchStats(true)}
            disabled={isRefreshing}
            className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-700/80 transition-colors"
            title="Refresh statistics"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={() => navigate('/projects/new')}
            className="btn-primary px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold flex items-center gap-2 shadow-lg"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Scan</span>
          </button>
        </div>
      </div>

      {/* Stats Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Scans"
          value={stats?.total_scans ?? 0}
          icon={Activity}
          colorScheme="primary"
          subtitle="All time"
          trend={{ value: 'Active', isPositive: true }}
        />
        <StatsCard
          title="Total Issues"
          value={stats?.total_issues ?? 0}
          icon={AlertTriangle}
          colorScheme="warning"
          subtitle="Detected"
          trend={{ value: `${stats?.total_issues ?? 0} tracked`, isPositive: false }}
        />
        <StatsCard
          title="Critical Issues"
          value={stats?.critical_issues ?? 0}
          icon={AlertOctagon}
          colorScheme="critical"
          subtitle="Immediate action"
          trend={{
            value: (stats?.critical_issues ?? 0) === 0 ? 'Secure' : 'Needs Fix',
            isPositive: (stats?.critical_issues ?? 0) === 0,
          }}
        />
        <StatsCard
          title="Active Projects"
          value={stats?.total_projects ?? 0}
          icon={FolderGit2}
          colorScheme="accent"
          subtitle="Monitored"
          trend={{ value: 'Synced', isPositive: true }}
        />
      </div>

      {/* Recharts Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Issues by Severity Bar Chart */}
        <div className="glass rounded-2xl p-6 border border-slate-800 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">
                Issues by Severity
              </h3>
              <p className="text-xs text-slate-400">
                Distribution of risk levels across all scanned files
              </p>
            </div>
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
          </div>

          <div className="h-64 w-full mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={severityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2238" vertical={false} />
                <XAxis
                  dataKey="name"
                  stroke="#64748b"
                  fontSize={12}
                  tickLine={false}
                  axisLine={{ stroke: '#1e2238' }}
                />
                <YAxis
                  stroke="#64748b"
                  fontSize={12}
                  tickLine={false}
                  axisLine={{ stroke: '#1e2238' }}
                  allowDecimals={false}
                />
                <Tooltip
                  cursor={{ fill: 'rgba(99, 102, 241, 0.08)' }}
                  contentStyle={{
                    backgroundColor: '#12121a',
                    borderColor: '#2e2e50',
                    borderRadius: '10px',
                    color: '#e2e8f0',
                    fontSize: '12px',
                    boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Issues by Category Pie Chart */}
        <div className="glass rounded-2xl p-6 border border-slate-800 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">
                Issues by Category
              </h3>
              <p className="text-xs text-slate-400">
                Classification by vulnerability, style, and bug risk type
              </p>
            </div>
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
              <FileCode className="w-5 h-5" />
            </div>
          </div>

          <div className="h-64 w-full mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`pie-cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#12121a',
                    borderColor: '#2e2e50',
                    borderRadius: '10px',
                    color: '#e2e8f0',
                    fontSize: '12px',
                    boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  iconType="circle"
                  formatter={(val) => (
                    <span className="text-xs text-slate-300 font-medium">{val}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Scans Table */}
      <div className="glass rounded-2xl p-6 border border-slate-800">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-base font-bold text-white tracking-wide">
              Recent Code Scans
            </h3>
            <p className="text-xs text-slate-400">
              Latest static analysis & AI evaluation reports
            </p>
          </div>

          <button
            onClick={() => navigate('/projects')}
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
          >
            <span>View All Projects</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {stats?.recent_scans && stats.recent_scans.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold">
                  <th className="py-3 px-4">Scan ID</th>
                  <th className="py-3 px-4">Project</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Issues Found</th>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {stats.recent_scans.slice(0, 5).map((scan) => (
                  <tr
                    key={scan.id}
                    onClick={() => navigate(`/scans/${scan.id}`)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-3.5 px-4 font-mono font-medium text-indigo-300">
                      #{scan.id}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-200">
                      {scan.project_name || `Project #${scan.project_id}`}
                    </td>
                    <td className="py-3.5 px-4">
                      <ScanStatusBadge status={scan.status} />
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="font-semibold text-slate-100">
                        {scan.total_issues}
                      </span>{' '}
                      <span className="text-slate-500">issues</span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{new Date(scan.created_at).toLocaleString()}</span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <span className="text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1">
                        Report <ArrowRight className="w-3 h-3" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center rounded-xl border border-dashed border-slate-800 bg-[#0d0d16]">
            <Activity className="w-8 h-8 text-slate-500 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-300">
              No scans performed yet
            </h4>
            <p className="text-xs text-slate-500 mt-1 mb-4">
              Upload your Python source files or ZIP archives to run your first AI security scan.
            </p>
            <button
              onClick={() => navigate('/projects/new')}
              className="btn-primary px-4 py-2 rounded-xl text-xs font-semibold inline-flex items-center gap-2"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create Project & Scan</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
