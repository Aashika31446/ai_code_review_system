import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectsApi, scansApi, getErrorMessage } from '../services/api';
import {
  FolderPlus,
  UploadCloud,
  FileCode,
  FileArchive,
  X,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Layers,
} from 'lucide-react';
import toast from 'react-hot-toast';

export const NewProjectPage: React.FC = () => {
  const [step, setStep] = useState<1 | 2>(1);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const handleFiles = (files: File[]) => {
    const validFiles = files.filter(
      (file) =>
        file.name.endsWith('.py') ||
        file.name.endsWith('.zip') ||
        file.name.endsWith('.tar') ||
        file.name.endsWith('.gz')
    );

    if (validFiles.length < files.length) {
      toast('Only Python source files (.py) or archives (.zip) are analyzed', {
        icon: '⚠️',
      });
    }

    if (validFiles.length > 0) {
      setSelectedFiles((prev) => [...prev, ...validFiles]);
    }
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleProceedToStep2 = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error('Project name is required');
      return;
    }
    setStep(2);
  };

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);
      setUploadProgress(20);

      // 1. Create project
      const createdProject = await projectsApi.createProject({
        name: name.trim(),
        description: description.trim(),
      });
      setUploadProgress(50);

      // 2. If files provided, create scan
      if (selectedFiles.length > 0) {
        const formData = new FormData();
        selectedFiles.forEach((file) => {
          formData.append('files', file);
        });
        formData.append('file', selectedFiles[0]);

        setUploadProgress(75);
        const scan = await scansApi.uploadScan(createdProject.id, formData);
        setUploadProgress(100);
        toast.success('Project created and code scan initiated!');
        navigate(`/scans/${scan.id}`);
      } else {
        setUploadProgress(100);
        toast.success('Project created successfully!');
        navigate(`/projects/${createdProject.id}`);
      }
    } catch (err) {
      toast.error(getErrorMessage(err));
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
          <FolderPlus className="w-8 h-8 text-indigo-400" />
          <span>Create New Project</span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Set up a new codebase workspace and launch an automated static & AI code review.
        </p>
      </div>

      {/* Progress Stepper */}
      <div className="glass rounded-2xl p-5 border border-slate-800">
        <div className="flex items-center justify-between max-w-md mx-auto">
          {/* Step 1 indicator */}
          <div className="flex items-center gap-3">
            <div
              className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition-all ${
                step >= 1
                  ? 'bg-gradient-to-tr from-indigo-600 to-purple-600 text-white shadow-[0_0_12px_rgba(99,102,241,0.5)]'
                  : 'bg-slate-800 text-slate-400 border border-slate-700'
              }`}
            >
              {step > 1 ? <CheckCircle2 className="w-5 h-5" /> : '1'}
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-200">Step 1</p>
              <p className="text-[11px] text-slate-400">Project Details</p>
            </div>
          </div>

          {/* Stepper Line */}
          <div
            className={`flex-1 h-0.5 mx-4 transition-colors ${
              step >= 2 ? 'bg-indigo-500' : 'bg-slate-800'
            }`}
          />

          {/* Step 2 indicator */}
          <div className="flex items-center gap-3">
            <div
              className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition-all ${
                step >= 2
                  ? 'bg-gradient-to-tr from-indigo-600 to-cyan-500 text-white shadow-[0_0_12px_rgba(6,182,212,0.4)]'
                  : 'bg-slate-800 text-slate-400 border border-slate-700'
              }`}
            >
              2
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-200">Step 2</p>
              <p className="text-[11px] text-slate-400">Upload & Scan</p>
            </div>
          </div>
        </div>
      </div>

      {/* Form Content */}
      <div className="glass rounded-2xl p-6 sm:p-8 border border-slate-800">
        {step === 1 ? (
          /* STEP 1: Details */
          <form onSubmit={handleProceedToStep2} className="space-y-6">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Project Name <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. backend-auth-service"
                className="w-full glass-input text-sm rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500"
              />
              <p className="text-[11px] text-slate-500 mt-1.5">
                Descriptive identifier for your application or microservice.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Project Description (Optional)
              </label>
              <textarea
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description of the repository, technology stack, and scan goals..."
                className="w-full glass-input text-sm rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 resize-none"
              />
            </div>

            <div className="pt-4 flex items-center justify-end">
              <button
                type="submit"
                className="btn-primary px-6 py-3 rounded-xl text-sm font-semibold flex items-center gap-2"
              >
                <span>Continue to Code Upload</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>
        ) : (
          /* STEP 2: Drag & Drop Files */
          <div className="space-y-6">
            <div>
              <h3 className="text-base font-bold text-white mb-1">
                Attach Code for Analysis
              </h3>
              <p className="text-xs text-slate-400">
                Upload single or multiple Python (.py) source files, or a .zip package.
              </p>
            </div>

            {/* Dropzone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-200 ${
                isDragging
                  ? 'border-indigo-400 bg-indigo-950/30 scale-[1.01]'
                  : 'border-slate-700/80 hover:border-indigo-500/50 bg-[#0d0d16]/70'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".py,.zip,.tar,.gz"
                onChange={handleFileInputChange}
                className="hidden"
              />

              <div className="flex flex-col items-center justify-center gap-3">
                <div className="p-4 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <UploadCloud className="w-8 h-8" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-200">
                    Drag and drop files here, or{' '}
                    <span className="text-indigo-400 underline">browse</span>
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Supports .py files or .zip repository archives (up to 50MB)
                  </p>
                </div>
              </div>
            </div>

            {/* Selected Files List */}
            {selectedFiles.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Files Ready for Scanning ({selectedFiles.length})
                </p>
                <div className="max-h-48 overflow-y-auto space-y-2 pr-1">
                  {selectedFiles.map((file, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs"
                    >
                      <div className="flex items-center gap-2.5 overflow-hidden">
                        {file.name.endsWith('.zip') ? (
                          <FileArchive className="w-4 h-4 text-amber-400 shrink-0" />
                        ) : (
                          <FileCode className="w-4 h-4 text-cyan-400 shrink-0" />
                        )}
                        <span className="font-mono text-slate-200 truncate">
                          {file.name}
                        </span>
                        <span className="text-slate-500 shrink-0">
                          ({(file.size / 1024).toFixed(1)} KB)
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemoveFile(idx);
                        }}
                        className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Upload Progress Bar if submitting */}
            {isSubmitting && (
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Uploading codebase & generating initial AST...</span>
                  <span className="font-semibold text-indigo-400">
                    {uploadProgress}%
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-indigo-500 to-cyan-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="pt-4 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStep(1)}
                disabled={isSubmitting}
                className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-300 hover:bg-slate-800 flex items-center gap-1.5 transition-colors disabled:opacity-50"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back to Details</span>
              </button>

              <button
                type="button"
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="btn-primary px-6 py-3 rounded-xl text-sm font-semibold flex items-center gap-2 disabled:opacity-60"
              >
                {isSubmitting ? (
                  <>
                    <Sparkles className="w-4 h-4 animate-spin" />
                    <span>Processing Scan...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>
                      {selectedFiles.length > 0
                        ? 'Create & Launch AI Scan'
                        : 'Create Project (Empty)'}
                    </span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NewProjectPage;
