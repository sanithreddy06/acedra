export type UserRole = 'student' | 'faculty' | 'mentor' | 'admin' | 'placement_officer';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  phone?: string;
  department_id?: number;
  department_name?: string;
  is_active: boolean;
  avatar_url?: string;
  student_id?: number;
  roll_number?: string;
  usn?: string;
  cgpa?: number;
  current_semester?: number;
  faculty_id?: number;
  employee_id?: string;
  designation?: string;
  mentor_id?: number;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface SummaryCard {
  title: string;
  value: string;
  change: string;
  trend: 'positive' | 'negative' | 'neutral';
  icon: string;
}

export interface RoleDashboardData {
  role: UserRole;
  summary_cards: SummaryCard[];
  quick_stats: Record<string, any>;
  recent_activity: Array<{
    id: number;
    action: string;
    time: string;
    details: string;
    user?: string;
    ip?: string;
  }>;
  details: Record<string, any>;
}

export interface Department {
  id: number;
  code: string;
  name: string;
  description?: string;
  hod_name?: string;
}

export interface AuditLog {
  id: number;
  user_id?: number;
  action: string;
  resource_type?: string;
  resource_id?: string;
  ip_address?: string;
  user_agent?: string;
  details: Record<string, any>;
  created_at: string;
  user_email?: string;
  user_name?: string;
}

export interface SystemSetting {
  id: number;
  key: string;
  value: any;
  description?: string;
  category: string;
  updated_at: string;
}
