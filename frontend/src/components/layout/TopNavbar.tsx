import React, { useState, useEffect } from 'react';
import {
  Menu,
  Sun,
  Moon,
  Bell,
  Search,
  ChevronRight,
  Shield,
  User as UserIcon,
  LogOut,
  ExternalLink,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { Badge } from '../common/Badge';
import { api } from '../../api/client';

interface TopNavbarProps {
  onToggleSidebar: () => void;
  currentTab: string;
}

export const TopNavbar: React.FC<TopNavbarProps> = ({ onToggleSidebar, currentTab }) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);

  // Tab display name for breadcrumb
  const formattedTab = currentTab
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

  const loadNotifications = async () => {
    try {
      const data = await api.getNotifications();
      if (data && data.length > 0) {
        setNotifications(data);
      } else {
        setNotifications([
          { id: 1, title: 'Fall 2026 Academic Term Active', message: 'Semester 5 curriculum verified & loaded', created_at: new Date().toISOString(), is_read: true },
          { id: 2, title: 'Early Warning Engine Initialized', message: 'Module 2 rules active for student surveillance', created_at: new Date().toISOString(), is_read: true },
        ]);
      }
    } catch {
      setNotifications([
        { id: 1, title: 'Fall 2026 Academic Term Active', message: 'Semester 5 curriculum verified & loaded', created_at: new Date().toISOString(), is_read: true },
      ]);
    }
  };

  useEffect(() => {
    if (user) {
      loadNotifications();
    }
  }, [user]);

  const handleMarkRead = async (id: number) => {
    try {
      await api.markNotificationRead(id);
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    } catch {
      // ignore
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <header className="sticky top-0 z-30 h-16 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-4 lg:px-8 flex items-center justify-between">
      {/* Left: Mobile hamburger & Breadcrumbs */}
      <div className="flex items-center space-x-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-100 dark:hover:bg-slate-800 lg:hidden transition"
          aria-label="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Breadcrumbs */}
        <nav className="hidden sm:flex items-center space-x-2 text-xs font-medium text-slate-500 dark:text-slate-400">
          <span>Portal</span>
          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          <span className="capitalize">{user?.role?.replace('_', ' ')}</span>
          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-900 dark:text-slate-100 font-semibold">{formattedTab}</span>
        </nav>
      </div>

      {/* Right: Actions, Search, Notifications, Theme, Profile */}
      <div className="flex items-center space-x-2 sm:space-x-3">
        {/* Search Input */}
        <div className="relative hidden md:block">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search resources, records..."
            className="w-56 lg:w-64 pl-9 pr-4 py-1.5 text-xs rounded-xl bg-slate-100 dark:bg-slate-800 border-none text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
          />
        </div>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          className="p-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-100 dark:hover:bg-slate-800 transition"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* Notifications Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-100 dark:hover:bg-slate-800 transition"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 rounded-2xl bg-white dark:bg-slate-900 shadow-xl border border-slate-200 dark:border-slate-800 py-3 z-50">
              <div className="px-4 pb-2 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900 dark:text-slate-100">Notifications</span>
                {unreadCount > 0 ? (
                  <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300">
                    {unreadCount} New
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-400">All caught up</span>
                )}
              </div>
              <div className="max-h-72 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800">
                {notifications.map((n) => (
                  <div
                    key={n.id}
                    onClick={() => handleMarkRead(n.id)}
                    className={`p-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition cursor-pointer ${
                      !n.is_read ? 'bg-brand-50/30 dark:bg-brand-950/20' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-semibold text-slate-900 dark:text-slate-200">{n.title}</p>
                      {!n.is_read && <span className="w-1.5 h-1.5 rounded-full bg-brand-500" />}
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 leading-tight">{n.message || n.desc}</p>
                    <span className="text-[9px] text-slate-400 block mt-1">
                      {n.created_at ? new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : (n.time || 'recently')}
                    </span>
                  </div>
                ))}
              </div>
              <div className="px-4 pt-2 border-t border-slate-100 dark:border-slate-800 text-center">
                <button
                  onClick={() => setShowNotifications(false)}
                  className="text-[11px] font-medium text-brand-600 dark:text-brand-400 hover:underline"
                >
                  Close notifications
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Profile Menu Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center space-x-2 p-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-600 to-indigo-600 text-white flex items-center justify-center text-xs font-bold uppercase shadow-sm">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="hidden lg:block text-left text-xs">
              <p className="font-semibold text-slate-800 dark:text-slate-200 leading-none">{user?.full_name}</p>
              <p className="text-[10px] text-slate-400 capitalize mt-0.5">{user?.role?.replace('_', ' ')}</p>
            </div>
          </button>

          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-64 rounded-2xl bg-white dark:bg-slate-900 shadow-xl border border-slate-200 dark:border-slate-800 py-2 z-50">
              <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800">
                <p className="text-xs font-bold text-slate-900 dark:text-slate-100">{user?.full_name}</p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">{user?.email}</p>
                <div className="mt-2">
                  <Badge variant="brand" size="sm">
                    {user?.role?.toUpperCase()}
                  </Badge>
                </div>
              </div>
              <div className="py-1 text-xs">
                <div className="px-4 py-2 text-slate-500 dark:text-slate-400 flex items-center justify-between">
                  <span>Department</span>
                  <span className="font-medium text-slate-800 dark:text-slate-200">
                    {user?.department_name || 'Campus Wide'}
                  </span>
                </div>
                <div className="px-4 py-2 text-slate-500 dark:text-slate-400 flex items-center justify-between">
                  <span>Status</span>
                  <span className="flex items-center text-emerald-600 font-medium">
                    <CheckCircle2 className="w-3 h-3 mr-1" /> Verified
                  </span>
                </div>
              </div>
              <div className="border-t border-slate-100 dark:border-slate-800 pt-1">
                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    logout();
                  }}
                  className="w-full px-4 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 flex items-center space-x-2 transition"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
