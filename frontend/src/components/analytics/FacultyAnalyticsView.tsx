import React, { useState, useEffect } from 'react';
import {
  Users,
  BookOpen,
  CalendarCheck,
  TrendingUp,
  Award,
  Filter,
  Eye,
  Building2
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { api } from '../../api/client';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import { StudentProfileModal } from '../students/StudentProfileModal';

export const FacultyAnalyticsView: React.FC = () => {
  const [data, setData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getFacultyAnalytics();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load faculty analytics');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (isLoading) {
    return <LoadingSpinner label="Compiling faculty cohort intelligence..." />;
  }

  if (error || !data) {
    return <ErrorAlert message={error || 'Failed to load faculty analytics'} onRetry={loadData} />;
  }

  // Course performance comparison data
  const courseComparisonData = data.assigned_courses.map((c: any) => ({
    name: c.subject_code,
    fullName: c.subject_name,
    attendance: data.average_cohort_attendance,
    marks: data.average_cohort_marks,
  }));

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center">
            <BookOpen className="w-5 h-5 mr-2 text-brand-600" />
            Faculty Cohort Analytics & Course Performance
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Academic evaluations, attendance tracking, and student performance for {data.faculty_name} ({data.department_name}).
          </p>
        </div>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Assigned Courses</span>
          <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{data.assigned_courses?.length || 0}</h3>
          <p className="text-[11px] text-brand-600 font-medium mt-1">Active sections</p>
        </div>
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Total Department Students</span>
          <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{data.total_assigned_students}</h3>
          <p className="text-[11px] text-slate-400 mt-1">Authorized scope</p>
        </div>
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Cohort Avg Attendance</span>
          <h3 className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{data.average_cohort_attendance}%</h3>
          <p className="text-[11px] text-slate-400 mt-1">Mandatory minimum 75%</p>
        </div>
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Evaluation Marks Mean</span>
          <h3 className="text-2xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">{data.average_cohort_marks}</h3>
          <p className="text-[11px] text-slate-400 mt-1">Scale out of 100</p>
        </div>
      </div>

      {/* Course Performance Chart */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center">
          <TrendingUp className="w-4 h-4 mr-2 text-brand-600" />
          Allocated Subject Benchmark Comparison
        </h3>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={courseComparisonData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff', fontSize: '11px' }} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Bar dataKey="attendance" name="Avg Attendance %" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="marks" name="Evaluation Aggregate" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Authorized Student List */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center">
          <Users className="w-4 h-4 mr-2 text-brand-600" />
          Authorized Department Student Cohort
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400">
                <th className="pb-2 font-semibold">Student Name</th>
                <th className="pb-2 font-semibold">USN</th>
                <th className="pb-2 font-semibold text-center">Semester</th>
                <th className="pb-2 font-semibold text-center">Section</th>
                <th className="pb-2 font-semibold text-center">CGPA</th>
                <th className="pb-2 font-semibold text-center">Attendance</th>
                <th className="pb-2 font-semibold text-right">Dossier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {data.students_summary?.map((st: any) => (
                <tr key={st.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                  <td className="py-2.5 font-semibold text-slate-900 dark:text-slate-100">{st.name}</td>
                  <td className="py-2.5 font-mono text-slate-500">{st.usn}</td>
                  <td className="py-2.5 text-center font-medium">Sem {st.semester}</td>
                  <td className="py-2.5 text-center font-semibold">{st.section}</td>
                  <td className="py-2.5 text-center font-mono font-bold">{st.cgpa.toFixed(2)}</td>
                  <td className="py-2.5 text-center font-mono font-bold">
                    <span className={st.attendance < 75 ? 'text-rose-600' : 'text-emerald-600'}>
                      {st.attendance.toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-2.5 text-right">
                    <button
                      onClick={() => setSelectedStudentId(st.id)}
                      className="p-1 rounded-lg text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-950"
                      title="View Student Dossier"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedStudentId && (
        <StudentProfileModal
          studentId={selectedStudentId}
          isOpen={!!selectedStudentId}
          onClose={() => setSelectedStudentId(null)}
        />
      )}
    </div>
  );
};
