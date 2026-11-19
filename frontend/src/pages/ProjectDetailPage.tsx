import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectsApi, scansApi, getErrorMessage } from '../services/api';
import { Project, Scan } from '../types';
import ScanStatusBadge from '../components/ScanStatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import {
  FolderGit2,
  Calendar,
  Clock,
  ArrowLeft,
  UploadCloud,
  FileCode,
  FileArchive,
  Layers,
  ArrowRight,
  Sparkles,
  X,
  ShieldAlert,
} from 'lucide-react';
import toast from 'react-hot-toast';

export const ProjectDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Upload modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchProjectData = async () => {
    if (!id) return;
    try {
      setIsLoading(true);
      const [projData, scansData] = await Promise.all([
        projectsApi.getProject(id),
        scansApi.getScans(id),
      ]);
      setProject(projData);
      setScans(scansData);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjectData();
  }, [id]);

  const handleFiles = (files: File[]) => {
    const validFiles = files.filter(
      (file) =>
        file.name.endsWith('.py') ||
        file.name.endsWith('.zip') ||
        file.name.endsWith('.tar') ||
        file.name.endsWith('.gz')
    );
    if (validFiles.length > 0) {
      setSelectedFiles((prev) => [...prev, ...validFiles]);
    }
  };

  const handleUploadScan = async () => {
    if (!id || selectedFiles.length === 0) {
      toast.error('Please select at least one source file or archive');
      return;
    }

    try {
      setIsUploading(true);
      const formData = new FormData();
      selectedFiles.forEach((file) => {
        formData.append('files', file);
      });
      formData.append('file', selectedFiles[0]);

      const newScan = await scansApi.uploadScan(id, formData);
      toast.success('Scan initiated successfully!');
      setShowUploadModal(false);
      setSelectedFiles([]);
      navigate(`/scans/${newScan.id}`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setIsUploading(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading project history and telemetry..." />;
  }

  if (!project) {
    return (
      <div className="glass rounded-2xl p-12 text-center border border-slate-800">
        <ShieldAlert className="w-12 h-12 text-rose-400 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-white">Project Not Found</h3>
        <p className="text-xs text-slate-400 mt-1 mb-5">
          The requested project repository could not be located.
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

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Back button */}
      <div>
        <button
          onClick={() => navigate('/projects')}
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-indigo-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Projects</span>
        </button>
      </div>

      {/* Project Header Card */}
      <div className="glass-card rounded-2xl p-6 sm:p-8 border border-slate-800 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-3 rounded-xl bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
                <FolderGit2 className="w-6 h-6" />
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                {project.name}
              </h1>
            </div>

            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl mt-2 leading-relaxed">
              {project.description || 'No description provided for this codebase.'}
            </p>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mt-4">
              <span className="flex items-center gap-1.5">
                <Calendar className="w-4 h-4 text-indigo-400" />
                <span>Created {new Date(project.created_at).toLocaleDateString()}</span>
              </span>
              <span className="flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-cyan-400" />
                <span>{scans.length} Total Scans Run</span>
              </span>
            </div>
          </div>

          <button
            onClick={() => setShowUploadModal(true)}
            className="btn-primary px-5 py-3 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 shadow-lg shrink-0"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload New Scan</span>
          </button>
        </div>
      </div>

      {/* Scans List Section */}
      <div className="glass rounded-2xl p-6 border border-slate-800">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">
              Scan History
            </h2>
            <p className="text-xs text-slate-400">
              Historical audits, vulnerability breakdowns, and deep AI inspection logs
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {scans.length} Records
          </span>
        </div>

        {scans.length > 0 ? (
          <div className="space-y-3">
            {scans.map((scan) => {
              const total = Math.max(1, scan.total_issues);
              const critPct = (((scan.critical_count ?? 0) / total) * 100).toFixed(0);
              const highPct = (((scan.high_count ?? 0) / total) * 100).toFixed(0);
              const medPct = (((scan.medium_count ?? 0) / total) * 100).toFixed(0);
              const lowPct = (((scan.low_count ?? 0) / total) * 100).toFixed(0);

              return (
                <div
                  key={scan.id}
                  onClick={() => navigate(`/scans/${scan.id}`)}
                  className="p-4 sm:p-5 rounded-xl bg-slate-900/50 hover:bg-slate-800/60 border border-slate-800/80 hover:border-indigo-500/30 cursor-pointer transition-all duration-200 flex flex-col md:flex-row md:items-center justify-between gap-4 group"
                >
                  <div className="flex items-start sm:items-center gap-4">
                    <div className="p-2.5 rounded-lg bg-slate-800/80 text-indigo-400 font-mono font-bold text-xs shrink-0">
                      #{scan.id}
                    </div>

                    <div>
                      <div className="flex items-center gap-3 flex-wrap">
                        <ScanStatusBadge status={scan.status} />
                        <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                          <Clock className="w-3.5 h-3.5 text-slate-500" />
                          {new Date(scan.created_at).toLocaleString()}
                        </span>
                      </div>

                      <div className="flex items-center gap-4 text-xs text-slate-300 mt-2">
                        <span>
                          Files Analyzed:{' '}
                          <strong className="text-white font-mono">
                            {scan.files_analyzed ?? 1}
                          </strong>
                        </span>
                        <span>•</span>
                        <span>
                          Total Issues:{' '}
                          <strong className="text-white font-mono">
                            {scan.total_issues}
                          </strong>
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Severity Breakdown Bar */}
                  <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 min-w-[240px]">
                    <div className="w-full sm:w-48 space-y-1">
                      <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                        <span className="text-rose-400">C:{scan.critical_count ?? 0}</span>
                        <span className="text-amber-400">H:{scan.high_count ?? 0}</span>
                        <span className="text-yellow-400">M:{scan.medium_count ?? 0}</span>
                        <span className="text-blue-400">L:{scan.low_count ?? 0}</span>
                      </div>

                      {/* Stacked bar */}
                      <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden flex">
                        {scan.total_issues > 0 ? (
                          <>
                            <div style={{ width: `${critPct}%` }} className="bg-red-500" />
                            <div style={{ width: `${highPct}%` }} className="bg-amber-500" />
                            <div style={{ width: `${medPct}%` }} className="bg-yellow-500" />
                            <div style={{ width: `${lowPct}%` }} className="bg-blue-500" />
                          </>
                        ) : (
                          <div className="w-full bg-emerald-500" />
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-1 text-xs font-semibold text-indigo-400 group-hover:text-indigo-300 group-hover:translate-x-1 transition-all">
                      <span>View</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="py-12 text-center rounded-xl border border-dashed border-slate-800 bg-[#0d0d16]">
            <Layers className="w-8 h-8 text-slate-500 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-300">
              No scans completed for this project
            </h4>
            <p className="text-xs text-slate-500 mt-1 mb-4">
              Upload Python source files or a repository zip to launch the first analysis.
            </p>
            <button
              onClick={() => setShowUploadModal(true)}
              className="btn-primary px-4 py-2 rounded-xl text-xs font-semibold inline-flex items-center gap-2"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Upload Source Code</span>
            </button>
          </div>
        )}
      </div>

      {/* Upload Scan Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card rounded-2xl p-6 sm:p-8 max-w-lg w-full border border-indigo-500/30 animate-in fade-in zoom-in-95 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400">
                  <UploadCloud className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white">
                  Upload Code to {project.name}
                </h3>
              </div>

              <button
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Dropzone */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                setIsDragging(false);
              }}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragging(false);
                if (e.dataTransfer.files) {
                  handleFiles(Array.from(e.dataTransfer.files));
                }
              }}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                isDragging
                  ? 'border-indigo-400 bg-indigo-950/40'
                  : 'border-slate-700 hover:border-indigo-500/50 bg-[#0d0d16]'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".py,.zip,.tar,.gz"
                onChange={(e) => {
                  if (e.target.files) handleFiles(Array.from(e.target.files));
                }}
                className="hidden"
              />
              <UploadCloud className="w-8 h-8 text-indigo-400 mx-auto mb-2" />
              <p className="text-xs font-semibold text-slate-200">
                Click or drag .py files or .zip repository
              </p>
              <p className="text-[11px] text-slate-500 mt-1">
                Static security analysis & AI review triggers immediately
              </p>
            </div>

            {/* Selected files preview */}
            {selectedFiles.length > 0 && (
              <div className="max-h-36 overflow-y-auto space-y-1.5 pr-1 text-xs">
                {selectedFiles.map((f, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-900 border border-slate-800"
                  >
                    <span className="font-mono text-slate-300 truncate max-w-[300px]">
                      {f.name}
                    </span>
                    <button
                      onClick={() =>
                        setSelectedFiles((prev) => prev.filter((_, idx) => idx !== i))
                      }
                      className="text-slate-500 hover:text-rose-400"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowUploadModal(false)}
                disabled={isUploading}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={handleUploadScan}
                disabled={isUploading || selectedFiles.length === 0}
                className="btn-primary px-5 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-2 disabled:opacity-50"
              >
                {isUploading ? (
                  <>
                    <Sparkles className="w-4 h-4 animate-spin" />
                    <span>Launching Scan...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Start AI Scan</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectDetailPage;
