import { User, RoleDashboardData, Department, AuditLog, SystemSetting } from '../types';

const API_BASE = '/api/v1';

class ApiClient {
  private getHeaders(): HeadersInit {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (response.status === 401) {
      // Don't auto-redirect on login attempt failure
      if (!response.url.includes('/auth/login')) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        window.location.href = '/login';
      }
    }
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || data.detail || 'An unexpected error occurred');
    }
    return data as T;
  }

  async login(email: string, password: string): Promise<{ access_token: string; refresh_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return this.handleResponse(res);
  }

  async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: this.getHeaders(),
      });
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');
    }
  }

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getMyDashboard(): Promise<RoleDashboardData> {
    const res = await fetch(`${API_BASE}/dashboards/me`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getUsers(role?: string): Promise<User[]> {
    const url = role ? `${API_BASE}/users/?role=${role}` : `${API_BASE}/users/`;
    const res = await fetch(url, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async createUser(userData: any): Promise<User> {
    const res = await fetch(`${API_BASE}/users/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(userData),
    });
    return this.handleResponse(res);
  }

  async getDepartments(): Promise<Department[]> {
    const res = await fetch(`${API_BASE}/departments/`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getAuditLogs(limit = 50): Promise<AuditLog[]> {
    const res = await fetch(`${API_BASE}/audit-logs/?limit=${limit}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getSystemSettings(): Promise<SystemSetting[]> {
    const res = await fetch(`${API_BASE}/settings/`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async requestPasswordReset(email: string): Promise<{ message: string; reset_token?: string }> {
    const res = await fetch(`${API_BASE}/auth/password-reset-request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    return this.handleResponse(res);
  }

  async confirmPasswordReset(token: string, new_password: string): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE}/auth/password-reset-confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, new_password }),
    });
    return this.handleResponse(res);
  }
}

export const api = new ApiClient();
