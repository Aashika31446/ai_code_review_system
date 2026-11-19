import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import toast from 'react-hot-toast';
import {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
  Project,
  CreateProjectRequest,
  Scan,
  ScanResponse,
  Finding,
  AIReview,
  DashboardStats,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle common errors (such as 401 Unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string; message?: string }>) => {
    if (error.response?.status === 401) {
      // Only trigger if we had a token, to avoid loops on failed login
      const hadToken = !!localStorage.getItem('token');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      if (hadToken && !window.location.pathname.includes('/login')) {
        toast.error('Session expired. Please log in again.');
        window.location.href = '/login';
      }
    } else if (error.response?.status === 403) {
      toast.error('You do not have permission to perform this action.');
    } else if (error.code === 'ERR_NETWORK') {
      toast.error('Network error: Unable to reach the server at ' + API_BASE_URL);
    }
    return Promise.reject(error);
  }
);

// Helper for error messages
export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (typeof data?.detail === 'string') return data.detail;
    if (typeof data?.message === 'string') return data.message;
    if (error.message) return error.message;
  }
  return 'An unexpected error occurred. Please try again.';
};

// ==================== AUTH API ====================
export const authApi = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    // Some OAuth2 / FastAPI backends expect FormData / x-www-form-urlencoded or JSON
    // We try JSON first, and if requested with username/password, both work
    const response = await api.post<AuthResponse>('/auth/login', credentials);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/register', data);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};

// ==================== PROJECTS API ====================
export const projectsApi = {
  getProjects: async (): Promise<Project[]> => {
    const response = await api.get<Project[]>('/projects');
    return response.data;
  },

  getProject: async (id: string | number): Promise<Project> => {
    const response = await api.get<Project>(`/projects/${id}`);
    return response.data;
  },

  createProject: async (data: CreateProjectRequest): Promise<Project> => {
    const response = await api.post<Project>('/projects', data);
    return response.data;
  },

  deleteProject: async (id: string | number): Promise<{ message: string }> => {
    const response = await api.delete<{ message: string }>(`/projects/${id}`);
    return response.data;
  },
};

// ==================== SCANS API ====================
export const scansApi = {
  uploadScan: async (projectId: string | number, formData: FormData): Promise<Scan> => {
    const response = await api.post<Scan>(`/projects/${projectId}/scans`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getScans: async (projectId?: string | number): Promise<Scan[]> => {
    const url = projectId ? `/projects/${projectId}/scans` : '/scans';
    const response = await api.get<Scan[]>(url);
    return response.data;
  },

  getScan: async (id: string | number): Promise<ScanResponse> => {
    const response = await api.get<ScanResponse>(`/scans/${id}`);
    return response.data;
  },

  getFindings: async (scanId: string | number): Promise<Finding[]> => {
    const response = await api.get<Finding[]>(`/scans/${scanId}/findings`);
    return response.data;
  },

  getAIReview: async (findingId: string | number): Promise<AIReview> => {
    const response = await api.get<AIReview>(`/findings/${findingId}/ai-review`);
    return response.data;
  },

  triggerAIReview: async (findingId: string | number): Promise<AIReview> => {
    const response = await api.post<AIReview>(`/findings/${findingId}/ai-review`);
    return response.data;
  },
};

// ==================== DASHBOARD API ====================
export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const response = await api.get<DashboardStats>('/dashboard/stats');
    return response.data;
  },
};

export default api;
