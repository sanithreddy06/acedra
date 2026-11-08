import React from 'react';
import {
  GraduationCap,
  BookOpen,
  CalendarCheck,
  Users,
  Award,
  Layers,
  ShieldCheck,
  Settings,
  ChevronRight,
  LogOut,
  Building2,
  FileText,
  Briefcase,
  Compass,
  AlertTriangle,
  UserCheck,
  ShieldAlert
} from 'lucide-react';
import { UserRole } from '../../types';
import { useAuth, DEMO_CREDENTIALS } from '../../contexts/AuthContext';
import { Badge } from '../common/Badge';

interface SidebarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  badge?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onTabChange, isOpen, onClose }) => {
  const { user, logout, switchDemoRole } = useAuth();
  const role = user?.role || 'student';

  // Role-specific navigation configurations
  const getNavItems = (): NavItem[] => {
    switch (role) {
      case 'student':
        return [
          { id: 'dashboard', label: 'Academic Dashboard', icon: Compass },
          { id: 'profile', label: 'My Intelligence Dossier', icon: GraduationCap, badge: 'Full' },
          { id: 'recommendations', label: 'Personalized Roadmap', icon: Award, badge: 'M3' },
          { id: 'risk_guidance', label: 'Early-Warning Status', icon: ShieldAlert },
          { id: 'courses', label: 'My Enrolled Courses', icon: BookOpen },
          { id: 'attendance', label: 'Attendance Intelligence', icon: CalendarCheck },
          { id: 'settings', label: 'Account Settings', icon: Settings },
        ];
      case 'faculty':
        return [
          { id: 'dashboard', label: 'Faculty Dashboard', icon: Compass },
          { id: 'faculty_analytics', label: 'Cohort Performance Analytics', icon: Award, badge: 'Live' },
          { id: 'risk_management', label: 'Early-Warning Radar', icon: ShieldAlert, badge: 'Alerts' },
          { id: 'recommendations', label: 'Student Guidance & Roadmaps', icon: BookOpen, badge: 'M3' },
          { id: 'students', label: 'Student Directory', icon: Users },
          { id: 'teaching', label: 'Allocated Courses', icon: BookOpen },
          { id: 'settings', label: 'Account Settings', icon: Settings },
        ];
      case 'mentor':
        return [
          { id: 'dashboard', label: 'Mentorship Central', icon: Compass },
          { id: 'risk_management', label: 'Early-Warning Radar', icon: ShieldAlert, badge: 'Active' },
          { id: 'recommendations', label: 'Mentee Recommendations', icon: Award, badge: 'M3' },
          { id: 'mentees', label: 'Mentee Roster', icon: Users },
          { id: 'students', label: 'Student Directory', icon: Users },
          { id: 'settings', label: 'Account Settings', icon: Settings },
        ];
      case 'admin':
        return [
          { id: 'dashboard', label: 'Executive Intelligence', icon: Compass },
          { id: 'risk_management', label: 'Early-Warning & Risk', icon: ShieldAlert, badge: 'Policy' },
          { id: 'recommendations', label: 'Recommendation Catalogue', icon: Award, badge: 'M3' },
          { id: 'students', label: 'Student Directory', icon: Users, badge: 'Directory' },
          { id: 'admin_analytics', label: 'Institutional Analytics', icon: Award, badge: 'Metrics' },
          { id: 'data_imports', label: 'Data Import Center', icon: FileText, badge: 'CSV/XLS' },
          { id: 'users', label: 'User Directory & Roles', icon: Users },
          { id: 'departments', label: 'Academic Structure', icon: Building2 },
          { id: 'audit_logs', label: 'Security & Audit Logs', icon: ShieldCheck },
          { id: 'system_settings', label: 'System Configuration', icon: Settings },
        ];
      case 'placement_officer':
        return [
          { id: 'dashboard', label: 'Placement Hub', icon: Compass },
          { id: 'recommendations', label: 'Placement Readiness Plans', icon: Award, badge: 'M3' },
          { id: 'students', label: 'Student Directory', icon: Users },
          { id: 'eligibility', label: 'Student Eligibility Roster', icon: Award },
          { id: 'recruitment', label: 'Corporate Drives', icon: Briefcase },
          { id: 'reports', label: 'Branch Analytics', icon: FileText },
          { id: 'settings', label: 'Account Settings', icon: Settings },
        ];
      default:
        return [{ id: 'dashboard', label: 'Dashboard', icon: Compass }];
    }
  };

  const navItems = getNavItems();

  const roleBadgeVariant = {
    student: 'brand',
    faculty: 'slate',
    mentor: 'success',
    admin: 'danger',
    placement_officer: 'warning',
  }[role] as any;

  const roleDisplayName = {
    student: 'Student Portal',
    faculty: 'Faculty Console',
    mentor: 'Mentor Workspace',
    admin: 'HOD / Admin Suite',
    placement_officer: 'Placement Cell',
  }[role];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand header */}
        <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-900 dark:text-white leading-tight">
                Smart Campus
              </h1>
              <span className="text-[11px] font-medium tracking-wide text-brand-600 dark:text-brand-400 uppercase">
                Intelligence v0.1
              </span>
            </div>
          </div>
        </div>

        {/* Current Role Banner */}
        <div className="px-6 py-4 bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800/60">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Mode
            </span>
            <Badge variant={roleBadgeVariant} size="sm">
              {role.toUpperCase()}
            </Badge>
          </div>
          <p className="mt-1 text-xs font-semibold text-slate-800 dark:text-slate-200">
            {roleDisplayName}
          </p>
        </div>

        {/* Navigation items */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-1">
          <div className="px-3 pb-2 text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            Main Navigation
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onTabChange(item.id);
                  onClose();
                }}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-brand-50 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300 font-semibold shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-brand-600 dark:text-brand-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-300">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}

          {/* Quick Demo Role Switcher (Convenient for evaluators) */}
          <div className="pt-6 mt-6 border-t border-slate-200 dark:border-slate-800">
            <div className="px-3 pb-2 text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              Quick Role Preview
            </div>
            <div className="grid grid-cols-1 gap-1">
              {(Object.keys(DEMO_CREDENTIALS) as UserRole[]).map((r) => {
                const isCurrent = role === r;
                return (
                  <button
                    key={r}
                    onClick={() => switchDemoRole(r)}
                    className={`flex items-center justify-between px-3 py-1.5 text-xs rounded-lg transition text-left ${
                      isCurrent
                        ? 'bg-slate-200 dark:bg-slate-800 font-semibold text-slate-900 dark:text-slate-100'
                        : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800/40'
                    }`}
                  >
                    <span className="capitalize">{r.replace('_', ' ')}</span>
                    {isCurrent && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* User profile footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-50 dark:bg-slate-850">
            <div className="flex items-center space-x-3 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center text-xs font-bold uppercase flex-shrink-0">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <div className="truncate">
                <p className="text-xs font-semibold text-slate-900 dark:text-slate-100 truncate">
                  {user?.full_name}
                </p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                  {user?.email}
                </p>
              </div>
            </div>
            <button
              onClick={() => logout()}
              title="Sign out"
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
