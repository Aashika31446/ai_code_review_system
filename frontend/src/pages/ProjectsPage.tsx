import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectsApi, getErrorMessage } from '../services/api';
import { Project } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import {
  FolderGit2,
  PlusCircle,
  Search,
  Calendar,
  Layers,
  ArrowRight,
  Trash2,
  AlertCircle,
  Code,
} from 'lucide-react';
import toast from 'react-hot-toast';

export const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  const navigate = useNavigate();

  const fetchProjects = async () => {
    try {
      setIsLoading(true);
      const data = await projectsApi.getProjects();
      setProjects(data);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleDeleteProject = async () => {
    if (!projectToDelete) return;

    try {
      setIsDeleting(true);
      await projectsApi.deleteProject(projectToDelete.id);
      setProjects((prev) => prev.filter((p) => p.id !== projectToDelete.id));
      toast.success(`Project "${projectToDelete.name}" deleted`);
      setProjectToDelete(null);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredProjects = projects.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  if (isLoading) {
    return <LoadingSpinner message="Loading your repositories..." />;
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2.5">
            <FolderGit2 className="w-8 h-8 text-indigo-400" />
            <span>Projects & Repositories</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Manage tracked codebases, view past scans, and trigger new security reviews.
          </p>
        </div>

        <button
          onClick={() => navigate('/projects/new')}
          className="btn-primary px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 shadow-lg cursor-pointer"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Project</span>
        </button>
      </div>

      {/* Filter / Search Bar */}
      {projects.length > 0 && (
        <div className="relative max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search projects by name or description..."
            className="w-full glass-input text-xs sm:text-sm rounded-xl pl-10 pr-4 py-2.5 text-slate-200 placeholder-slate-500"
          />
        </div>
      )}

      {/* Projects Grid */}
      {filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <div
              key={project.id}
              className="glass-card rounded-2xl p-6 border border-slate-800/80 flex flex-col justify-between group transition-all duration-300 hover:border-indigo-500/40"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 group-hover:scale-105 transition-transform">
                    <Code className="w-5 h-5" />
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setProjectToDelete(project);
                    }}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-950/20 transition-colors"
                    title="Delete project"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <h3
                  onClick={() => navigate(`/projects/${project.id}`)}
                  className="text-lg font-bold text-white hover:text-indigo-300 cursor-pointer transition-colors line-clamp-1"
                >
                  {project.name}
                </h3>

                <p className="text-xs text-slate-400 mt-2 line-clamp-2 min-h-[32px]">
                  {project.description || 'No description provided for this project.'}
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800/70 space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{project.scan_count ?? 0} Scans</span>
                  </span>

                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-500" />
                    <span>
                      {project.last_scan_date
                        ? new Date(project.last_scan_date).toLocaleDateString()
                        : 'Never scanned'}
                    </span>
                  </span>
                </div>

                <button
                  onClick={() => navigate(`/projects/${project.id}`)}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-semibold bg-slate-800/80 hover:bg-indigo-600/20 text-slate-200 hover:text-indigo-300 border border-slate-700/80 hover:border-indigo-500/40 transition-all duration-200"
                >
                  <span>View Project & Scans</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty State */
        <div className="glass rounded-2xl p-12 text-center border border-slate-800 max-w-lg mx-auto mt-12">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto mb-4">
            <FolderGit2 className="w-8 h-8" />
          </div>

          <h3 className="text-lg font-bold text-white">
            {searchQuery ? 'No matching projects found' : 'No projects created yet'}
          </h3>

          <p className="text-xs sm:text-sm text-slate-400 mt-2 mb-6">
            {searchQuery
              ? 'Try modifying your search keywords.'
              : 'Create your first project repository to upload files and perform automated security reviews.'}
          </p>

          <button
            onClick={() => navigate('/projects/new')}
            className="btn-primary px-6 py-2.5 rounded-xl text-xs sm:text-sm font-semibold inline-flex items-center gap-2"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Create New Project</span>
          </button>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {projectToDelete && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card rounded-2xl p-6 max-w-md w-full border border-rose-500/30 animate-in fade-in zoom-in-95">
            <div className="flex items-center gap-3 text-rose-400 mb-3">
              <div className="p-2 rounded-xl bg-rose-500/20 border border-rose-500/30">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Confirm Deletion</h3>
            </div>

            <p className="text-xs sm:text-sm text-slate-300">
              Are you sure you want to delete project{' '}
              <strong className="text-white">"{projectToDelete.name}"</strong>? All
              associated scans and AI review findings will be permanently removed.
            </p>

            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                onClick={() => setProjectToDelete(null)}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteProject}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white transition-colors"
              >
                {isDeleting ? 'Deleting...' : 'Delete Project'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectsPage;
