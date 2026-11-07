import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopNavbar } from './TopNavbar';
import { RoleDashboardView } from '../dashboard/RoleDashboardView';
import { UserManagementView } from '../users/UserManagementView';
import { StudentDirectory } from '../students/StudentDirectory';
import { StudentProfileModal } from '../students/StudentProfileModal';
import { DataImportCenter } from '../imports/DataImportCenter';
import { FacultyAnalyticsView } from '../analytics/FacultyAnalyticsView';
import { AdminAnalyticsView } from '../analytics/AdminAnalyticsView';
import { RiskDashboard } from '../risk/RiskDashboard';
import { useAuth } from '../../contexts/AuthContext';
import { EmptyState } from '../common/EmptyState';
import { ShieldAlert, BookOpen, CalendarCheck, Award, Briefcase, Settings, GraduationCap } from 'lucide-react';

export const AppLayout: React.FC = () => {
  const { user } = useAuth();
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);

  // Student self-profile modal trigger
  const [isStudentSelfModalOpen, setIsStudentSelfModalOpen] = useState<boolean>(false);

  // Tab router
  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <RoleDashboardView />;

      // MODULE 1: Student Directory & Management
      case 'students':
      case 'directory':
        return <StudentDirectory />;

      // MODULE 2: AI-Assisted Risk Early-Warning Dashboard
      case 'risk_management':
        return <RiskDashboard userRole={user?.role} />;

      case 'risk_guidance':
        if (user?.role === 'student') {
          const studentId = user.student_id || 1;
          return (
            <div className="space-y-4">
              <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                    <ShieldAlert className="w-5 h-5 mr-2 text-rose-600" />
                    Early-Warning & Academic Support Guidance
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    View personal transparent indicators and recommended support interventions.
                  </p>
                </div>
                <button
                  onClick={() => setIsStudentSelfModalOpen(true)}
                  className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs shadow-sm"
                >
                  View My Early-Warning Status
                </button>
              </div>
              <RoleDashboardView />
              <StudentProfileModal
                studentId={studentId}
                isOpen={isStudentSelfModalOpen}
                onClose={() => setIsStudentSelfModalOpen(false)}
              />
            </div>
          );
        }
        return <RiskDashboard userRole={user?.role} />;

      // MODULE 1: Institutional Admin Analytics
      case 'admin_analytics':
        if (user?.role === 'admin') {
          return <AdminAnalyticsView />;
        }
        return (
          <EmptyState
            title="Access Restricted"
            description="Institutional Analytics requires Administrator / HOD credentials."
            icon={<ShieldAlert className="w-8 h-8 text-rose-500" />}
          />
        );

      // MODULE 1: Faculty Cohort Analytics
      case 'faculty_analytics':
        if (user?.role === 'faculty' || user?.role === 'admin') {
          return <FacultyAnalyticsView />;
        }
        return (
          <EmptyState
            title="Access Restricted"
            description="Faculty Cohort Analytics is restricted to teaching staff and administrators."
            icon={<ShieldAlert className="w-8 h-8 text-rose-500" />}
          />
        );

      // MODULE 1: Data Import Center
      case 'data_imports':
        if (user?.role === 'admin') {
          return <DataImportCenter />;
        }
        return (
          <EmptyState
            title="Access Restricted"
            description="Data Import Center requires Administrator privileges."
            icon={<ShieldAlert className="w-8 h-8 text-rose-500" />}
          />
        );

      // MODULE 1: Student Self Dossier
      case 'profile':
        if (user?.role === 'student') {
          const studentId = user.student_id || 1;
          return (
            <div className="space-y-4">
              <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                    <GraduationCap className="w-5 h-5 mr-2 text-brand-600" />
                    My Student Intelligence Dossier
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Consolidated record of your academic standing, calculated attendance, continuous evaluations, and portfolio.
                  </p>
                </div>
                <button
                  onClick={() => setIsStudentSelfModalOpen(true)}
                  className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs shadow-sm"
                >
                  Open Full Dossier Modal
                </button>
              </div>

              <RoleDashboardView />

              <StudentProfileModal
                studentId={studentId}
                isOpen={isStudentSelfModalOpen}
                onClose={() => setIsStudentSelfModalOpen(false)}
              />
            </div>
          );
        }
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
                Course catalog and academic requirements for Fall 2026 term.
              </p>
            </div>
            <RoleDashboardView />
          </div>
        );

      case 'attendance':
        return (
          <div className="space-y-4">
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                <CalendarCheck className="w-4 h-4 mr-2 text-brand-600" />
                Attendance Intelligence Log
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Real-time subject-wise class tracking calculated from verified session logs.
              </p>
            </div>
            <RoleDashboardView />
          </div>
        );

      case 'mentees':
      case 'eligibility':
        return <StudentDirectory />;

      case 'risk_tracking':
        return <RiskDashboard userRole={user?.role} />;

      case 'settings':
      case 'system_settings':
        return (
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
              <Settings className="w-4 h-4 mr-2 text-brand-600" />
              Institutional Profile & Platform Architecture
            </h3>
            <p className="text-xs text-slate-500">
              System identity: <strong>Smart Institute of Technology & Intelligence</strong>.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850">
                <span className="font-semibold text-slate-700 dark:text-slate-300">Identity & RBAC Provider</span>
                <p className="text-slate-500 mt-1">JWT Bearer Auth &bull; Bcrypt (12 rounds) &bull; Role Scoped</p>
              </div>
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850">
                <span className="font-semibold text-slate-700 dark:text-slate-300">Module 1 Data Store</span>
                <p className="text-slate-500 mt-1">PostgreSQL &bull; SQLAlchemy 2.0 &bull; Recharts Engine</p>
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
