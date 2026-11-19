export type Severity = 'critical' | 'high' | 'medium' | 'low';

export type Category = 
  | 'security'
  | 'performance'
  | 'quality'
  | 'bug_risk'
  | 'syntax'
  | 'style'
  | 'best_practice'
  | string;

export type ScanStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface User {
  id: string | number;
  username: string;
  email: string;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type?: string;
  user: User;
}

export interface LoginRequest {
  email?: string;
  username?: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface AIReview {
  id?: string | number;
  finding_id?: string | number;
  explanation: string;
  impact: string;
  suggested_fix: string;
  fixed_code?: string;
  confidence?: number;
  created_at?: string;
}

export interface Finding {
  id: string | number;
  scan_id?: string | number;
  file_path: string;
  line_number: number;
  end_line_number?: number;
  rule_id: string;
  rule_name?: string;
  message: string;
  severity: Severity | string;
  category: Category;
  code_snippet?: string;
  ai_review?: AIReview;
}

export interface FindingWithReview extends Finding {
  ai_review?: AIReview;
}

export interface Scan {
  id: string | number;
  project_id: string | number;
  project_name?: string;
  status: ScanStatus | string;
  total_issues: number;
  critical_count?: number;
  high_count?: number;
  medium_count?: number;
  low_count?: number;
  files_analyzed?: number;
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface ScanResponse {
  scan: Scan;
  findings: Finding[];
}

export interface Project {
  id: string | number;
  name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  scan_count?: number;
  last_scan_date?: string;
  latest_scan?: Scan;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
}

export interface SeverityStat {
  severity: string;
  count: number;
  color?: string;
}

export interface CategoryStat {
  category: string;
  count: number;
  color?: string;
}

export interface DashboardStats {
  total_scans: number;
  total_issues: number;
  critical_issues: number;
  total_projects: number;
  issues_by_severity: SeverityStat[];
  issues_by_category: CategoryStat[];
  recent_scans: Scan[];
}
