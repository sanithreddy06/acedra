import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  CalendarCheck,
  CheckCircle2,
  AlertTriangle,
  GraduationCap,
  Users,
  ShieldCheck,
  Building2,
  Clock,
  ArrowRight
} from 'lucide-react';
import { RoleDashboardData } from '../../types';
import { api } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { SummaryCardsGrid } from './SummaryCardsGrid';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import { Badge } from '../common/Badge';

export const RoleDashboardView: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<RoleDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getMyDashboard();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch dashboard intelligence');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, [user?.role]);

  if (isLoading) {
    return <LoadingSpinner label="Querying institutional data store..." />;
  }

  if (error || !data) {
    return <ErrorAlert message={error || 'Failed to load dashboard'} onRetry={loadDashboard} />;
  }

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-brand-600 to-indigo-700 text-white shadow-lg shadow-brand-500/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold tracking-wider uppercase text-brand-200">
            Smart Campus Intelligence
          </span>
          <h2 className="text-2xl font-bold tracking-tight mt-0.5">
            Welcome back, {user?.full_name}
          </h2>
          <p className="text-xs text-brand-100 mt-1">
            Authenticated as <strong className="capitalize">{user?.role?.replace('_', ' ')}</strong> &bull; Fall 2026 Term Active
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="brand" size="md">
            Verified Account
          </Badge>
        </div>
      </div>

      {/* Dynamic Summary Cards Grid (Directly from database queries) */}
      <SummaryCardsGrid cards={data.summary_cards} />

      {/* Role-Specific Intelligent Panels */}
      {data.role === 'student' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Courses */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                <BookOpen className="w-4 h-4 mr-2 text-brand-600" />
                Curriculum Subjects — Semester {data.quick_stats.batch_year ? 5 : 1}
              </h3>
              <Badge variant="brand" size="sm">
                {data.quick_stats.department || 'Engineering'}
              </Badge>
            </div>
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {data.quick_stats.courses?.map((c: any, i: number) => (
                <div key={i} className="py-3 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-mono font-bold text-brand-600 dark:text-brand-400 mr-2">
                      {c.code}
                    </span>
                    <span className="text-sm font-medium text-slate-800 dark:text-slate-200">
                      {c.name}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3 text-xs text-slate-500">
                    <span>{c.type}</span>
                    <span className="font-semibold text-slate-700 dark:text-slate-300">
                      {c.credits} Credits
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Student Profile Quick Reference */}
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
              Academic Credentials
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">University Seat No (USN)</span>
                <span className="font-mono font-bold text-slate-900 dark:text-slate-100">
                  {data.quick_stats.usn}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Roll Number</span>
                <span className="font-mono font-medium text-slate-900 dark:text-slate-100">
                  {data.quick_stats.roll_number}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Class Section</span>
                <span className="font-medium text-slate-900 dark:text-slate-100">
                  Section {data.quick_stats.section}
                </span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-500">Cohort Batch</span>
                <span className="font-medium text-slate-900 dark:text-slate-100">
                  {data.quick_stats.batch_year}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {data.role === 'faculty' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mb-4 flex items-center">
              <BookOpen className="w-4 h-4 mr-2 text-brand-600" />
              Active Course Teaching Assignments
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400">
                    <th className="pb-3 font-semibold">Course Code</th>
                    <th className="pb-3 font-semibold">Subject Title</th>
                    <th className="pb-3 font-semibold">Section</th>
                    <th className="pb-3 font-semibold">Credits</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {data.quick_stats.assigned_courses?.map((c: any) => (
                    <tr key={c.id}>
                      <td className="py-3 font-mono font-semibold text-brand-600 dark:text-brand-400">
                        {c.subject_code}
                      </td>
                      <td className="py-3 font-medium text-slate-800 dark:text-slate-200">
                        {c.subject_name}
                      </td>
                      <td className="py-3">Sec {c.section}</td>
                      <td className="py-3 font-semibold">{c.credits}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mb-3">
              Faculty Profile
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Employee ID</span>
                <span className="font-mono font-bold text-slate-900 dark:text-slate-100">
                  {data.quick_stats.employee_id}
                </span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-500">Department</span>
                <span className="font-semibold text-slate-900 dark:text-slate-100">
                  {data.quick_stats.department}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {data.role === 'mentor' && (
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                <Users className="w-4 h-4 mr-2 text-brand-600" />
                Mentee Cohort Roster & Performance Tracking
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Students dynamically tracked for early warning risk signals
              </p>
            </div>
            <Badge variant="warning" size="sm">
              {data.quick_stats.at_risk_count} Intervention Alerts
            </Badge>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400">
                  <th className="pb-3 font-semibold">Student Name</th>
                  <th className="pb-3 font-semibold">USN</th>
                  <th className="pb-3 font-semibold">Roll No</th>
                  <th className="pb-3 font-semibold">Current CGPA</th>
                  <th className="pb-3 font-semibold">Attendance</th>
                  <th className="pb-3 font-semibold">Alert Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {data.quick_stats.mentee_roster?.map((m: any) => (
                  <tr key={m.id}>
                    <td className="py-3 font-semibold text-slate-800 dark:text-slate-200">
                      {m.name}
                    </td>
                    <td className="py-3 font-mono text-slate-500">{m.usn}</td>
                    <td className="py-3 font-mono text-slate-500">{m.roll_number}</td>
                    <td className="py-3 font-bold text-slate-900 dark:text-slate-100">
                      {m.cgpa.toFixed(2)}
                    </td>
                    <td className="py-3 font-medium">
                      <span className={m.attendance < 75 ? 'text-rose-600 font-bold' : 'text-emerald-600'}>
                        {m.attendance.toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-3">
                      <Badge
                        variant={m.status === 'At Risk' ? 'danger' : 'success'}
                        size="sm"
                      >
                        {m.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {data.role === 'admin' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mb-4 flex items-center">
              <Building2 className="w-4 h-4 mr-2 text-brand-600" />
              Academic Department Directory & Enrollment
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {data.quick_stats.departments?.map((d: any) => (
                <div
                  key={d.code}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-850"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-brand-600 dark:text-brand-400">
                      {d.code}
                    </span>
                    <span className="text-[11px] text-slate-400">Department</span>
                  </div>
                  <h4 className="font-semibold text-sm text-slate-800 dark:text-slate-200 mt-1">
                    {d.name}
                  </h4>
                  <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700/60 flex justify-between text-xs text-slate-500">
                    <span>Students: <strong className="text-slate-800 dark:text-slate-200">{d.students}</strong></span>
                    <span>Faculty: <strong className="text-slate-800 dark:text-slate-200">{d.faculty}</strong></span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mb-3 flex items-center">
              <ShieldCheck className="w-4 h-4 mr-2 text-brand-600" />
              Recent Security Audit Events
            </h3>
            <div className="space-y-3">
              {data.recent_activity.slice(0, 5).map((act: any) => (
                <div key={act.id} className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 text-xs">
                  <div className="flex items-center justify-between font-semibold text-slate-800 dark:text-slate-200">
                    <span>{act.action}</span>
                    <span className="text-[10px] text-slate-400">{act.time}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 truncate">
                    User: {act.user} &bull; IP: {act.ip}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {data.role === 'placement_officer' && (
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                <GraduationCap className="w-4 h-4 mr-2 text-brand-600" />
                Placement Drive Candidate Eligibility Roster
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Students meeting baseline criteria (CGPA &ge; 7.0 &bull; Attendance &ge; 75%)
              </p>
            </div>
            <Badge variant="success" size="sm">
              {data.quick_stats.eligible_count} Eligible Candidates
            </Badge>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400">
                  <th className="pb-3 font-semibold">Candidate Name</th>
                  <th className="pb-3 font-semibold">USN</th>
                  <th className="pb-3 font-semibold">Department</th>
                  <th className="pb-3 font-semibold">CGPA</th>
                  <th className="pb-3 font-semibold">Recruitment Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {data.quick_stats.eligible_roster?.map((s: any) => (
                  <tr key={s.id}>
                    <td className="py-3 font-semibold text-slate-800 dark:text-slate-200">{s.name}</td>
                    <td className="py-3 font-mono text-slate-500">{s.usn}</td>
                    <td className="py-3 font-semibold text-brand-600">{s.department}</td>
                    <td className="py-3 font-bold text-slate-900 dark:text-slate-100">{s.cgpa.toFixed(2)}</td>
                    <td className="py-3">
                      <Badge
                        variant={s.status === 'Placed' ? 'success' : 'brand'}
                        size="sm"
                      >
                        {s.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
