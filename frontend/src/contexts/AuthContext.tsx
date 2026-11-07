import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, UserRole, AuthState } from '../types';
import { api } from '../api/client';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  switchDemoRole: (role: UserRole) => Promise<User>;
  hasRole: (roles: UserRole | UserRole[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Quick credentials map for easy role previewing
export const DEMO_CREDENTIALS: Record<UserRole, { email: string; pass: string; title: string }> = {
  student: { email: 'student@smartcampus.edu', pass: 'StudentPass123!', title: 'Alex Mercer (Student)' },
  faculty: { email: 'faculty@smartcampus.edu', pass: 'FacultyPass123!', title: 'Dr. Elena Rostova (Faculty)' },
  mentor: { email: 'mentor@smartcampus.edu', pass: 'MentorPass123!', title: 'Prof. David K. Sterling (Mentor)' },
  admin: { email: 'admin@smartcampus.edu', pass: 'AdminPass123!', title: 'Dr. Sarah Jenkins (Admin / HOD)' },
  placement_officer: { email: 'placement@smartcampus.edu', pass: 'PlacementPass123!', title: 'Marcus Vance (Placement)' },
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const cached = localStorage.getItem('user_data');
    return cached ? JSON.parse(cached) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'));
  const [refreshToken, setRefreshToken] = useState<string | null>(() => localStorage.getItem('refresh_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const verifyToken = async () => {
      const storedToken = localStorage.getItem('access_token');
      if (!storedToken) {
        setIsLoading(false);
        return;
      }
      try {
        const currentUser = await api.getMe();
        setUser(currentUser);
        localStorage.setItem('user_data', JSON.stringify(currentUser));
      } catch (err) {
        console.warn('Session verification failed, logging out', err);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        setUser(null);
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    };

    verifyToken();
  }, []);

  const login = async (email: string, pass: string): Promise<User> => {
    setIsLoading(true);
    try {
      const data = await api.login(email, pass);
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user_data', JSON.stringify(data.user));
      setToken(data.access_token);
      setRefreshToken(data.refresh_token);
      setUser(data.user);
      return data.user;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    setIsLoading(true);
    try {
      await api.logout();
    } finally {
      setUser(null);
      setToken(null);
      setRefreshToken(null);
      setIsLoading(false);
    }
  };

  const switchDemoRole = async (role: UserRole): Promise<User> => {
    const creds = DEMO_CREDENTIALS[role];
    return login(creds.email, creds.pass);
  };

  const hasRole = (roles: UserRole | UserRole[]): boolean => {
    if (!user) return false;
    const allowed = Array.isArray(roles) ? roles : [roles];
    return allowed.includes(user.role);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        refreshToken,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        logout,
        switchDemoRole,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
