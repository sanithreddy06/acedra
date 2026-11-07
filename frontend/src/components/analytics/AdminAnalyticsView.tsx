import React, { useState, useEffect } from 'react';
import {
  Building2,
  Users,
  GraduationCap,
  CalendarCheck,
  TrendingUp,
  AlertTriangle,
  FileSpreadsheet,
  BarChart3,
  Award
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { api } from '../../api/client';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';

export const AdminAnalyticsView: React.FC = () => {
  const [data, setData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getAdminAnalytics();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load institutional analytics');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (isLoading) {
    return <LoadingSpinner label="Compiling institutional student analytics..." />;
  }

  if (error || !data) {
    return <ErrorAlert message={error || 'Failed to load institutional analytics'} onRetry={loadData} />;
  }

  // Attendance distribution data for charts
  const attendanceData = [
    { name: 'High Attendance (≥85%)', value: data.attendance_distribution.above_85, color: '#10b981' },
    { name: 'Satisfactory (75-85%)', value: data.attendance_distribution.between_75_85, color: '#f59e0b' },
    { name: 'Critical Risk (<75%)', value: data.attendance_distribution.below_75_at_risk, color: '#ef4444' },
  ];

  // CGPA Distribution data
  const cgpaData = [
    { name: 'Tier 1 (≥9.0)', count: data.cgpa_distribution.tier_1_above_9 },
    { name: 'Tier 2 (8.0-8.9)', count: data.cgpa_distribution.tier_2_8_to_9 },
    { name: 'Tier 3 (7.0-7.9)', count: data.cgpa_distribution.tier_3_7_to_8 },
    { name: 'Tier 4 (6.0-6.9)', count: data.cgpa_distribution.tier_4_6_to_7 },
    { name: 'At Risk (<6.0)', count: data.cgpa_distribution.below_6_at_risk },
  ];

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center">
            <GraduationCap className="w-5 h-5 mr-2 text-brand-600" />
            Institutional Student Intelligence & Analytics
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Campus-wide academic metrics, attendance thresholds, and departmental performance summaries.
          </p>
        </div>
      </div>

      {/* Institutional Top Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Total Enrolled Students</span>
          <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{data.institutional_stats.total_students}</h3>
          <p className="text-[11px] text-emerald-600 font-semibold mt-1">{data.institutional_stats.active_students} Active status</p>
        </div>
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Academic Departments</span>
          <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{data.institutional_stats.total_departments}</h3>
          <p className="text-[11px] text-slate-400 mt-1">{data.institutional_stats.total_faculty} Faculty staff</p>
        </div>
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Campus Mean CGPA</span>
          <h3 className="text-2xl font-bold text-brand-600 dark:text-brand-400 mt-1">{data.institutional_stats.campus_average_cgpa}</h3>
          <p className="text-[11px] text-slate-400 mt-1">Scale of 10.0</p>
        </div>
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Campus Mean Attendance</span>
          <h3 className="text-2xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">{data.institutional_stats.campus_average_attendance}%</h3>
          <p className="text-[11px] text-slate-400 mt-1">Aggregate calculated</p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Department Comparison Chart */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center">
            <Building2 className="w-4 h-4 mr-2 text-brand-600" />
            Department-Wise Academic Performance (CGPA & Attendance)
          </h3>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.department_wise_stats}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="department_code" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" orientation="left" domain={[0, 10]} tick={{ fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff', fontSize: '11px' }} />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Bar yAxisId="left" dataKey="average_cgpa" name="Avg CGPA (10)" fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar yAxisId="right" dataKey="average_attendance" name="Avg Attendance %" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* CGPA Cohort Distribution Chart */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center">
            <Award className="w-4 h-4 mr-2 text-brand-600" />
            Institutional CGPA Tier Distribution
          </h3>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cgpaData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff', fontSize: '11px' }} />
                <Bar dataKey="count" name="Student Count" fill="#818cf8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Attendance Risk Breakdown Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center">
            <CalendarCheck className="w-4 h-4 mr-2 text-brand-600" />
            Departmental Attendance & Risk Overview
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400">
                  <th className="pb-2 font-semibold">Department</th>
                  <th className="pb-2 font-semibold">HOD</th>
                  <th className="pb-2 font-semibold text-center">Enrolled</th>
                  <th className="pb-2 font-semibold text-center">Avg Attendance</th>
                  <th className="pb-2 font-semibold text-center">Avg CGPA</th>
                  <th className="pb-2 font-semibold text-center">At-Risk Count</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {data.department_wise_stats?.map((d: any) => (
                  <tr key={d.department_code} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 font-bold text-slate-900 dark:text-slate-100">
                      <span className="font-mono text-brand-600 mr-1.5">{d.department_code}</span>
                      {d.department_name}
                    </td>
                    <td className="py-2.5 text-slate-500">{d.hod_name}</td>
                    <td className="py-2.5 text-center font-bold">{d.total_students}</td>
                    <td className="py-2.5 text-center font-mono font-bold text-emerald-600">{d.average_attendance}%</td>
                    <td className="py-2.5 text-center font-mono font-bold">{d.average_cgpa}</td>
                    <td className="py-2.5 text-center">
                      <Badge variant={d.at_risk_count > 0 ? 'danger' : 'success'} size="sm">
                        {d.at_risk_count} Alert{d.at_risk_count === 1 ? '' : 's'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Data Import Audit Widget */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center">
            <FileSpreadsheet className="w-4 h-4 mr-2 text-brand-600" />
            Data Ingestion Audits
          </h3>
          <p className="text-xs text-slate-500">
            Total Batches Ingested: <strong className="text-slate-900 dark:text-slate-100">{data.import_stats.total_import_batches}</strong>
          </p>
          <div className="space-y-2.5">
            {data.import_stats.recent_batches?.map((b: any) => (
              <div key={b.id} className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-900 dark:text-slate-100 truncate">{b.filename}</span>
                  <Badge variant={b.status === 'completed' ? 'success' : 'warning'} size="sm">
                    {b.status}
                  </Badge>
                </div>
                <div className="flex justify-between text-[11px] text-slate-400 mt-1">
                  <span>Success: <strong className="text-emerald-600">{b.success}</strong> &bull; Fail: <strong className="text-rose-600">{b.failed}</strong></span>
                  <span>{b.date}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
