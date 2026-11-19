import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { scansApi, getErrorMessage } from '../services/api';
import { Scan, Finding } from '../types';
import FindingsTable from '../components/FindingsTable';
import ScanStatusBadge from '../components/ScanStatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import {
  ShieldAlert,
  AlertOctagon,
  AlertTriangle,
  AlertCircle,
  Info,
  Clock,
  FileCode,
  FolderGit2,
  ArrowLeft,
  RefreshCw,
  XCircle,
  Sparkles,
  Download,
} from 'lucide-react';
import toast from 'react-hot-toast';

export const ScanResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [scan, setScan] = useState<Scan | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isManualRefreshing, setIsManualRefreshing] = useState<boolean>(false);
  const [autoRefreshCount, setAutoRefreshCount] = useState<number>(0);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchScanData = async (isSilent = false) => {
    if (!id) return;
    try {
      if (!isSilent) setIsLoading(true);
      const scanResponse = await scansApi.getScan(id);

      // Backend may return { scan, findings } or scan directly
      if (scanResponse && 'scan' in scanResponse) {
        setScan(scanResponse.scan);
        setFindings(scanResponse.findings || []);
      } else {
        const scanObj = scanResponse as unknown as Scan;
        setScan(scanObj);
        // fetch findings separately if not returned
        try {
          const findingsList = await scansApi.getFindings(id);
          setFindings(findingsList);
        } catch (e) {
          console.warn('Findings fetch error:', e);
        }
      }
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      if (!isSilent) setIsLoading(false);
      setIsManualRefreshing(false);
    }
  };

  useEffect(() => {
    fetchScanData();
  }, [id]);

  // Polling logic when scan is pending or running
  useEffect(() => {
    if (!scan) return;

    const isRunning =
      scan.status.toLowerCase() === 'running' ||
      scan.status.toLowerCase() === 'pending' ||
      scan.status.toLowerCase() === 'in_progress';

    if (isRunning) {
      pollIntervalRef.current = setInterval(() => {
        setAutoRefreshCount((prev) => prev + 1);
        fetchScanData(true);
      }, 5000);
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [scan?.status, id]);

  const handleManualRefresh = () => {
    setIsManualRefreshing(true);
    fetchScanData(true);
  };

  const handleUpdateFinding = (updatedFinding: Finding) => {
    setFindings((prev) =>
      prev.map((f) => (f.id === updatedFinding.id ? updatedFinding : f))
    );
  };

  const handleExportJSON = () => {
    if (!scan) return;
    const exportData = {
      scan,
      findings,
      exported_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scan-${scan.id}-report.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success('Scan report downloaded');
  };

  if (isLoading && !scan) {
    return <LoadingSpinner message="Extracting scan telemetry and AST results..." />;
  }

  if (!scan) {
    return (
      <div className="glass rounded-2xl p-12 text-center border border-slate-800">
        <ShieldAlert className="w-12 h-12 text-rose-400 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-white">Scan Not Found</h3>
        <p className="text-xs text-slate-400 mt-1 mb-5">
          The requested scan record does not exist or has been removed.
        </p>
        <button
          onClick={() => navigate('/projects')}
          className="btn-primary px-5 py-2.5 rounded-xl text-xs font-semibold inline-flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Projects</span>
        </button>
      </div>
    );
  }

  // Count severities from findings or scan metadata
  const criticalCount =
    scan.critical_count ??
    findings.filter((f) => f.severity.toLowerCase() === 'critical').length;
  const highCount =
    scan.high_count ??
    findings.filter((f) => f.severity.toLowerCase() === 'high').length;
  const mediumCount =
    scan.medium_count ??
    findings.filter((f) => f.severity.toLowerCase() === 'medium').length;
  const lowCount =
    scan.low_count ??
    findings.filter((f) => f.severity.toLowerCase() === 'low').length;

  const isScanRunning =
    scan.status.toLowerCase() === 'running' ||
    scan.status.toLowerCase() === 'pending' ||
    scan.status.toLowerCase() === 'in_progress';

  const isScanFailed =
    scan.status.toLowerCase() === 'failed' ||
    scan.status.toLowerCase() === 'error';

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Link
            to={`/projects/${scan.project_id}`}
            className="hover:text-indigo-300 flex items-center gap-1.5 transition-colors"
          >
            <FolderGit2 className="w-4 h-4" />
            <span>{scan.project_name || `Project #${scan.project_id}`}</span>
          </Link>
          <span>/</span>
          <span className="text-slate-200 font-mono">Scan #{scan.id}</span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleManualRefresh}
            disabled={isManualRefreshing}
            className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-700/80 transition-colors flex items-center gap-1.5 text-xs"
            title="Refresh Scan Data"
          >
            <RefreshCw
              className={`w-4 h-4 ${isManualRefreshing || isScanRunning ? 'animate-spin text-indigo-400' : ''}`}
            />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          <button
            onClick={handleExportJSON}
            className="px-3.5 py-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-700/80 transition-colors flex items-center gap-1.5 text-xs font-medium"
          >
            <Download className="w-4 h-4 text-cyan-400" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* Running State Banner */}
      {isScanRunning && (
        <div className="p-4 rounded-2xl bg-cyan-950/40 border border-cyan-500/40 flex items-center justify-between gap-4 animate-pulse">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-400">
              <Sparkles className="w-5 h-5 animate-spin" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-cyan-200">
                Code Review & AI Heuristics in Progress
              </h4>
              <p className="text-xs text-cyan-300/80 mt-0.5">
                Scanning AST rules and generating AI remediation recommendations. Automatically polling for updates every 5 seconds (checks: {autoRefreshCount}).
              </p>
            </div>
          </div>
          <ScanStatusBadge status={scan.status} />
        </div>
      )}

      {/* Failed State Banner */}
      {isScanFailed && (
        <div className="p-5 rounded-2xl bg-rose-950/40 border border-rose-500/40 flex items-start gap-3.5">
          <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400 shrink-0">
            <XCircle className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <h4 className="text-sm font-bold text-rose-200">
              Scan Execution Failed
            </h4>
            <p className="text-xs text-rose-300/80 mt-1">
              {scan.error_message ||
                'An error occurred during static analysis or AST evaluation. Please verify file syntax and attempt a new scan.'}
            </p>
            <button
              onClick={() => navigate(`/projects/${scan.project_id}`)}
              className="mt-3 px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-600/30 hover:bg-rose-600/50 text-rose-200 border border-rose-500/30 transition-colors"
            >
              Upload Code Again
            </button>
          </div>
        </div>
      )}

      {/* Scan Metadata Header Card */}
      <div className="glass-card rounded-2xl p-6 sm:p-8 border border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
                <span>Code Review Report</span>
                <span className="font-mono text-indigo-400">#{scan.id}</span>
              </h1>
              <ScanStatusBadge status={scan.status} />
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mt-3 font-mono">
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-indigo-400" />
                <span>{new Date(scan.created_at).toLocaleString()}</span>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5">
                <FileCode className="w-4 h-4 text-cyan-400" />
                <span>{scan.files_analyzed ?? 1} Files Analyzed</span>
              </span>
              <span>•</span>
              <span className="text-slate-200 font-semibold">
                {scan.total_issues} Total Findings
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Severity Breakdown: 4 Colored Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Critical Card */}
        <div className="glass rounded-2xl p-5 border border-red-500/20 bg-red-950/10 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-red-400 mb-1">
              Critical Risk
            </p>
            <h3 className="text-3xl font-extrabold text-white tracking-tight">
              {criticalCount}
            </h3>
            <p className="text-[11px] text-red-300/70 mt-1">Immediate fix needed</p>
          </div>
          <div className="p-3 rounded-xl bg-red-500/15 border border-red-500/30 text-red-400">
            <AlertOctagon className="w-6 h-6 animate-pulse" />
          </div>
        </div>

        {/* High Card */}
        <div className="glass rounded-2xl p-5 border border-amber-500/20 bg-amber-950/10 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-amber-400 mb-1">
              High Severity
            </p>
            <h3 className="text-3xl font-extrabold text-white tracking-tight">
              {highCount}
            </h3>
            <p className="text-[11px] text-amber-300/70 mt-1">High priority bugs</p>
          </div>
          <div className="p-3 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-400">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        {/* Medium Card */}
        <div className="glass rounded-2xl p-5 border border-yellow-500/20 bg-yellow-950/10 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-yellow-400 mb-1">
              Medium Severity
            </p>
            <h3 className="text-3xl font-extrabold text-white tracking-tight">
              {mediumCount}
            </h3>
            <p className="text-[11px] text-yellow-300/70 mt-1">Code smell & smells</p>
          </div>
          <div className="p-3 rounded-xl bg-yellow-500/15 border border-yellow-500/30 text-yellow-400">
            <AlertCircle className="w-6 h-6" />
          </div>
        </div>

        {/* Low Card */}
        <div className="glass rounded-2xl p-5 border border-blue-500/20 bg-blue-950/10 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-blue-400 mb-1">
              Low Severity
            </p>
            <h3 className="text-3xl font-extrabold text-white tracking-tight">
              {lowCount}
            </h3>
            <p className="text-[11px] text-blue-300/70 mt-1">Style & formatting</p>
          </div>
          <div className="p-3 rounded-xl bg-blue-500/15 border border-blue-500/30 text-blue-400">
            <Info className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Findings Table Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
              <span>Security & Quality Findings</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-950/80 text-indigo-300 border border-indigo-500/30 font-normal">
                {findings.length} Total
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Select any finding row to expand and review AI root-cause analysis, impact, and copyable fixed code.
            </p>
          </div>
        </div>

        <FindingsTable
          findings={findings}
          onUpdateFinding={handleUpdateFinding}
        />
      </div>
    </div>
  );
};

export default ScanResultsPage;
