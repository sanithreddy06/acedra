import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopNavbar } from './TopNavbar';
import { RoleDashboardView } from '../dashboard/RoleDashboardView';
import { UserManagementView } from '../users/UserManagementView';
import { useAuth } from '../../contexts/AuthContext';
import { EmptyState } from '../common/EmptyState';
import { ShieldAlert, BookOpen, CalendarCheck, Award, Briefcase, Settings } from 'lucide-react';

export const AppLayout: React.FC = () => {
  const { user } = useAuth();
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);

  // Tab router
  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <RoleDashboardView />;

      case 'users':
        if (user?.role === 'admin') {
          return <UserManagementView />;
        }
        return (
          <EmptyState
            title="Access Restricted"
            description="Institutional User Directory management requires Administrator / HOD privileges."
            icon={<ShieldAlert className="w-8 h-8 text-rose-500" />}
          />
        );

      case 'courses':
      case 'teaching':
        return (
          <div className="space-y-4">
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                <BookOpen className="w-4 h-4 mr-2 text-brand-600" />
                Active Curriculum & Syllabus Repository
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Course catalog and academic requirements for Fall 2026 term. Module 1 will introduce AI curriculum analysis.
              </p>
            </div>
            <RoleDashboardView />
          </div>
        );

      case 'mentees':
      case 'risk_tracking':
      case 'eligibility':
      case 'students':
        return <RoleDashboardView />;

      case 'settings':
      case 'system_settings':
        return (
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
              <Settings className="w-4 h-4 mr-2 text-brand-600" />
              Institutional Profile & Preferences
            </h3>
            <p className="text-xs text-slate-500">
              System identity: <strong>Smart Institute of Technology & Intelligence</strong>.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850">
                <span className="font-semibold text-slate-700 dark:text-slate-300">Identity Provider</span>
                <p className="text-slate-500 mt-1">JWT Bearer Auth &bull; HS256 Tokenization &bull; Bcrypt Salted</p>
              </div>
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850">
                <span className="font-semibold text-slate-700 dark:text-slate-300">Database Layer</span>
                <p className="text-slate-500 mt-1">PostgreSQL &bull; SQLAlchemy 2.0 &bull; Alembic Migrations</p>
              </div>
            </div>
          </div>
        );

      default:
        return <RoleDashboardView />;
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden">
      {/* Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopNavbar
          currentTab={currentTab}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        />

        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
          <div className="max-w-7xl mx-auto">{renderContent()}</div>
        </main>
      </div>
    </div>
  );
};
