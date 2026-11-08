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
  ArrowRight,
  TrendingUp,
  Target,
  Award,
  Briefcase,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Activity,
  Layers,
  FileSpreadsheet
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar
} from 'recharts';
import { RoleDashboardData } from '../../types';
import { api } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { SummaryCardsGrid } from './SummaryCardsGrid';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import { Badge } from '../common/Badge';
import { InterventionDetailModal } from '../interventions/InterventionDetailModal';

export const RoleDashboardView: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<RoleDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modal state for intervention dossier
  const [selectedInterventionId, setSelectedInterventionId] = useState<number | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);

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
    return <LoadingSpinner label="Querying integrated campus data store & AI metrics..." />;
  }

  if (error || !data) {
    return <ErrorAlert message={error || 'Failed to load dashboard'} onRetry={loadDashboard} />;
  }

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-brand-700 via-indigo-700 to-slate-900 text-white shadow-xl shadow-brand-500/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold tracking-wider uppercase text-brand-200">
            Smart Campus Intelligence &bull; Module 6
          </span>
          <h2 className="text-2xl font-bold tracking-tight mt-0.5">
            Welcome back, {user?.full_name}
          </h2>
          <p className="text-xs text-brand-100 mt-1">
            Authenticated as <strong className="capitalize">{user?.role?.replace('_', ' ')}</strong> &bull; Fall 2026 Term Active &bull; Real-time AI Analytics Connected
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="brand" size="md">
            Verified Role
          </Badge>
        </div>
      </div>

      {/* Dynamic Summary Cards Grid */}
      <SummaryCardsGrid cards={data.summary_cards} />

      {/* ========================================================================= */}
      {/* ROLE 1: STUDENT INTEGRATED DASHBOARD */}
      {/* ========================================================================= */}
      {data.role === 'student' && (
        <div className="space-y-6">
          {/* Top Row: SGPA Trend Chart & Placement Readiness Radar */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Academic Progression Curve */}
            <div className="lg:col-span-2 p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                    <TrendingUp className="w-4 h-4 mr-2 text-brand-600" />
                    Semester SGPA Progression & Cumulative Trend
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Verified university grading scale (10.0 scale) across active terms
                  </p>
                </div>
                <Badge variant="brand" size="sm">
                  Sem {data.quick_stats.current_semester || 5}
                </Badge>
              </div>

              <div className="h-60 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.quick_stats.sgpa_trends || []}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                    <XAxis dataKey="semester" stroke="#94a3b8" fontSize={11} />
                    <YAxis domain={[0, 10]} stroke="#94a3b8" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        borderRadius: '12px',
                        border: 'none',
                        color: '#f8fafc',
                        fontSize: '12px',
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="sgpa"
                      stroke="#4f46e5"
                      strokeWidth={3}
                      dot={{ r: 4, fill: '#4f46e5' }}
                      activeDot={{ r: 6 }}
                      name="Semester SGPA"
                    />
                    <Line
                      type="monotone"
                      dataKey="cgpa"
                      stroke="#10b981"
                      strokeWidth={2}
                      strokeDasharray="4 4"
                      dot={false}
                      name="Cumulative CGPA"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Placement Readiness & Mentor Dossier */}
            <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4 flex flex-col justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                  <Target className="w-4 h-4 mr-2 text-brand-600" />
                  Career & Placement Readiness
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Algorithmic alignment with industry benchmarks
                </p>

                <div className="my-5 text-center">
                  <div className="text-4xl font-extrabold text-brand-600 dark:text-brand-400">
                    {data.quick_stats.readiness_score || 85}%
                  </div>
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mt-1">
                    Placement Benchmark Score
                  </span>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 h-2.5 rounded-full overflow-hidden mt-3">
                    <div
                      className="bg-brand-600 h-full rounded-full transition-all duration-500"
                      style={{ width: `${data.quick_stats.readiness_score || 85}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-2 text-xs border-t border-slate-100 dark:border-slate-800 pt-3">
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Verified Technical Skills</span>
                    <strong className="text-slate-900 dark:text-slate-100">{data.quick_stats.skills_count || 5} Skills</strong>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Active Interventions</span>
                    <strong className="text-amber-600">{data.quick_stats.interventions_count || 0} Open Cases</strong>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Early-Warning Alerts</span>
                    <strong className={data.quick_stats.active_alerts_count > 0 ? 'text-rose-600' : 'text-emerald-600'}>
                      {data.quick_stats.active_alerts_count || 0} Flags
                    </strong>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-brand-50 dark:bg-brand-950/40 rounded-2xl border border-brand-100 dark:border-brand-900 text-xs text-brand-800 dark:text-brand-300 flex items-center justify-between">
                <span>Personal AI Assistant Online</span>
                <span className="font-bold flex items-center text-brand-600 dark:text-brand-400">
                  <Sparkles className="w-3.5 h-3.5 mr-1" />
                  RAG Active
                </span>
              </div>
            </div>
          </div>

          {/* Middle Row: Active Early-Warning Risk Alerts & Top Recommendations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Transparent Early-Warning Alerts */}
            <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                  <AlertTriangle className="w-4 h-4 mr-2 text-rose-500" />
                  Active Early-Warning Signals ({data.details?.alerts?.length || 0})
                </h3>
                <span className="text-xs text-slate-400">Transparent threshold alerts</span>
              </div>

              {data.details?.alerts && data.details.alerts.length > 0 ? (
                <div className="space-y-3">
                  {data.details.alerts.map((a: any) => (
                    <div
                      key={a.id}
                      className="p-4 rounded-2xl bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200/80 dark:border-rose-900/50 text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900 dark:text-slate-100">{a.title}</span>
                        <Badge variant="danger" size="sm">
                          {a.severity}
                        </Badge>
                      </div>
                      <p className="text-slate-600 dark:text-slate-300">{a.description}</p>
                      <span className="text-[11px] text-slate-400 block">Flagged on: {a.created_at}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 text-center text-slate-400 text-xs italic">
                  <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
                  No active risk flags. Academic performance & attendance are within normal institutional policy bands.
                </div>
              )}
            </div>

            {/* Personalized Recommendations */}
            <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                  <Award className="w-4 h-4 mr-2 text-indigo-500" />
                  Personalized Learning & Skill Recommendations
                </h3>
                <span className="text-xs text-slate-400">Targeted for your goals</span>
              </div>

              {data.details?.recommendations && data.details.recommendations.length > 0 ? (
                <div className="space-y-3">
                  {data.details.recommendations.map((r: any) => (
                    <div
                      key={r.id}
                      className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/60 text-xs flex items-center justify-between gap-3"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-slate-900 dark:text-slate-100">{r.title}</span>
                          <Badge variant="brand" size="sm">
                            {r.category?.replace(/_/g, ' ')}
                          </Badge>
                        </div>
                        <span className="text-[11px] text-slate-500 dark:text-slate-400 block">
                          Priority: {r.difficulty || 'Medium'} &bull; Match: {r.score}%
                        </span>
                      </div>
                      {r.resource_url && (
                        <a
                          href={r.resource_url}
                          target="_blank"
                          rel="noreferrer"
                          className="p-2 rounded-xl bg-white dark:bg-slate-700 hover:bg-slate-100 text-brand-600 dark:text-brand-400 border border-slate-200 dark:border-slate-600 transition"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 text-center text-slate-400 text-xs italic">
                  Recommendations engine is currently evaluating your latest submissions.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* ROLE 2: FACULTY COHORT DASHBOARD */}
      {/* ========================================================================= */}
      {data.role === 'faculty' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Grade Performance Distribution */}
            <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                <Award className="w-4 h-4 mr-2 text-brand-600" />
                Department Grade Distribution
              </h3>
              <p className="text-xs text-slate-500">Academic performance breakdown for enrolled cohort</p>

              <div className="space-y-3 pt-2">
                {data.quick_stats.performance_distribution?.map((p: any, idx: number) => (
                  <div key={idx} className="space-y-1 text-xs">
                    <div className="flex justify-between font-medium">
                      <span className="text-slate-700 dark:text-slate-300">{p.category}</span>
                      <span className="font-bold text-slate-900 dark:text-white">{p.count} students ({p.percentage}%)</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-brand-600 h-full rounded-full transition-all duration-500"
                        style={{ width: `${p.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Active Teaching Course Allocations */}
            <div className="lg:col-span-2 p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                <BookOpen className="w-4 h-4 mr-2 text-brand-600" />
                Allocated Teaching Courses & Cohorts
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                      <th className="pb-3">Course Code</th>
                      <th className="pb-3">Course Title</th>
                      <th className="pb-3">Section</th>
                      <th className="pb-3">Credits</th>
                      <th className="pb-3">Semester</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {data.details?.assigned_courses?.map((c: any) => (
                      <tr key={c.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                        <td className="py-3 font-mono font-bold text-brand-600 dark:text-brand-400">{c.code}</td>
                        <td className="py-3 font-semibold text-slate-800 dark:text-slate-200">{c.name}</td>
                        <td className="py-3">Section {c.section}</td>
                        <td className="py-3 font-semibold">{c.credits} Credits</td>
                        <td className="py-3 text-slate-500">Sem {c.semester}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* ROLE 3: MENTOR CENTRAL DASHBOARD */}
      {/* ========================================================================= */}
      {data.role === 'mentor' && (
        <div className="space-y-6">
          {/* Top Row: Active Interventions Cases & Pending Followups */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Active Interventions */}
            <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                    <ShieldCheck className="w-4 h-4 mr-2 text-brand-600" />
                    Active Mentee Interventions ({data.details?.active_interventions?.length || 0})
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">Click case to review full notes history & followups</p>
                </div>
                <Badge variant="brand" size="sm">
                  {data.quick_stats.open_interventions || 0} Open
                </Badge>
              </div>

              {data.details?.active_interventions && data.details.active_interventions.length > 0 ? (
                <div className="space-y-2.5">
                  {data.details.active_interventions.map((it: any) => (
                    <div
                      key={it.id}
                      onClick={() => {
                        setSelectedInterventionId(it.id);
                        setIsDetailModalOpen(true);
                      }}
                      className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 hover:border-brand-500 transition cursor-pointer flex items-center justify-between text-xs"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-slate-900 dark:text-slate-100">{it.title}</span>
                          <Badge variant={it.priority === 'HIGH' || it.priority === 'URGENT' ? 'danger' : 'warning'} size="sm">
                            {it.priority}
                          </Badge>
                        </div>
                        <span className="text-slate-500 text-[11px] block">
                          Mentee: <strong>{it.student_name}</strong> &bull; {it.type?.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">No active interventions assigned.</p>
              )}
            </div>

            {/* Upcoming Review Follow-ups */}
            <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                    <Clock className="w-4 h-4 mr-2 text-brand-600" />
                    Upcoming Follow-Up Review Sessions
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">Scheduled check-ins requiring review notes</p>
                </div>
                <Badge variant="warning" size="sm">
                  {data.quick_stats.pending_followups_count || 0} Pending
                </Badge>
              </div>

              {data.details?.pending_followups && data.details.pending_followups.length > 0 ? (
                <div className="space-y-2.5">
                  {data.details.pending_followups.map((f: any) => (
                    <div
                      key={f.id}
                      onClick={() => {
                        setSelectedInterventionId(f.intervention_id);
                        setIsDetailModalOpen(true);
                      }}
                      className="p-4 rounded-2xl bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-900/40 text-xs flex items-center justify-between cursor-pointer hover:border-amber-500 transition"
                    >
                      <div>
                        <strong className="text-slate-900 dark:text-slate-100 block">{f.student_name}</strong>
                        <span className="text-[11px] text-slate-500">Scheduled: {f.scheduled_date}</span>
                      </div>
                      <Badge variant="warning" size="sm">
                        {f.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">All scheduled review sessions are up to date.</p>
              )}
            </div>
          </div>

          {/* Mentee Cohort Roster */}
          <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
              <Users className="w-4 h-4 mr-2 text-brand-600" />
              Assigned Mentee Roster ({data.details?.mentee_roster?.length || 0})
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                    <th className="pb-3">Student Name</th>
                    <th className="pb-3">USN</th>
                    <th className="pb-3">Department</th>
                    <th className="pb-3">Semester</th>
                    <th className="pb-3">CGPA</th>
                    <th className="pb-3">Attendance</th>
                    <th className="pb-3">Academic Standing</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {data.details?.mentee_roster?.map((m: any) => (
                    <tr key={m.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                      <td className="py-3 font-semibold text-slate-800 dark:text-slate-200">{m.name}</td>
                      <td className="py-3 font-mono text-slate-500">{m.usn}</td>
                      <td className="py-3">{m.department}</td>
                      <td className="py-3">Sem {m.semester}</td>
                      <td className="py-3 font-bold text-slate-900 dark:text-slate-100">{m.cgpa?.toFixed(2)}</td>
                      <td className="py-3">
                        <span className={m.attendance < 75 ? 'text-rose-600 font-bold' : 'text-emerald-600 font-semibold'}>
                          {m.attendance?.toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3">
                        <Badge variant={m.status === 'At Risk' ? 'danger' : 'success'} size="sm">
                          {m.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* ROLE 4: ADMINISTRATOR / HOD EXECUTIVE DASHBOARD */}
      {/* ========================================================================= */}
      {data.role === 'admin' && (
        <div className="space-y-6">
          {/* Institutional Department Breakdown */}
          <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
              <Building2 className="w-4 h-4 mr-2 text-brand-600" />
              Academic Departments Performance & Attendance Overview
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                    <th className="pb-3">Dept Code</th>
                    <th className="pb-3">Department Name</th>
                    <th className="pb-3">Enrolled Students</th>
                    <th className="pb-3">Faculty Count</th>
                    <th className="pb-3">Average CGPA</th>
                    <th className="pb-3">Average Attendance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {data.details?.departments?.map((d: any) => (
                    <tr key={d.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                      <td className="py-3 font-mono font-bold text-brand-600 dark:text-brand-400">{d.code}</td>
                      <td className="py-3 font-semibold text-slate-800 dark:text-slate-200">{d.name}</td>
                      <td className="py-3 font-semibold">{d.students} students</td>
                      <td className="py-3 text-slate-500">{d.faculty} faculty</td>
                      <td className="py-3 font-bold text-slate-900 dark:text-slate-100">{d.avg_cgpa?.toFixed(2)}</td>
                      <td className="py-3 font-semibold text-emerald-600">{d.avg_attendance?.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Risk Alerts & Interventions Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                <AlertTriangle className="w-4 h-4 mr-2 text-rose-500" />
                Active Early-Warning Severity Distribution
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                {data.quick_stats.risk_distribution?.map((r: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60">
                    <span className="text-xs font-semibold text-slate-500">{r.severity}</span>
                    <div className="text-2xl font-black text-slate-900 dark:text-white mt-1">{r.count}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                <ShieldCheck className="w-4 h-4 mr-2 text-emerald-500" />
                Support Interventions Summary
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60">
                  <span className="text-xs font-semibold text-slate-500">Open</span>
                  <div className="text-2xl font-black text-slate-900 dark:text-white mt-1">{data.quick_stats.intervention_stats?.open || 0}</div>
                </div>
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60">
                  <span className="text-xs font-semibold text-slate-500">In Progress</span>
                  <div className="text-2xl font-black text-amber-600 mt-1">{data.quick_stats.intervention_stats?.in_progress || 0}</div>
                </div>
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60">
                  <span className="text-xs font-semibold text-slate-500">Resolved</span>
                  <div className="text-2xl font-black text-emerald-600 mt-1">{data.quick_stats.intervention_stats?.resolved || 0}</div>
                </div>
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60">
                  <span className="text-xs font-semibold text-slate-500">Total Cases</span>
                  <div className="text-2xl font-black text-brand-600 mt-1">{data.quick_stats.intervention_stats?.total || 0}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* ROLE 5: PLACEMENT OFFICER DASHBOARD */}
      {/* ========================================================================= */}
      {data.role === 'placement_officer' && (
        <div className="space-y-6">
          {/* Recruitment Funnel Pipeline */}
          <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
              <Briefcase className="w-4 h-4 mr-2 text-brand-600" />
              Corporate Recruitment Pipeline & Funnel Conversion
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {data.quick_stats.pipeline?.map((st: any, idx: number) => (
                <div key={idx} className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 text-center">
                  <span className="text-xs font-semibold text-slate-500">{st.stage}</span>
                  <div className="text-2xl font-extrabold text-brand-600 dark:text-brand-400 mt-1">{st.count}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Active Job Opportunities & Eligible Candidates Roster */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                <Target className="w-4 h-4 mr-2 text-brand-600" />
                Active Campus Recruitment Drives ({data.details?.opportunities?.length || 0})
              </h3>
              <div className="space-y-2.5">
                {data.details?.opportunities?.map((o: any) => (
                  <div key={o.id} className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <strong className="text-slate-900 dark:text-slate-100">{o.company}</strong>
                      <Badge variant="brand" size="sm">{o.salary_package}</Badge>
                    </div>
                    <span className="text-slate-600 dark:text-slate-300 block">{o.title} &bull; {o.location}</span>
                    <span className="text-[11px] text-slate-400 block">Deadline: {o.application_deadline}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center">
                <CheckCircle2 className="w-4 h-4 mr-2 text-emerald-500" />
                Placement Eligible Candidates
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                      <th className="pb-3">Candidate</th>
                      <th className="pb-3">USN</th>
                      <th className="pb-3">Branch</th>
                      <th className="pb-3">CGPA</th>
                      <th className="pb-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {data.details?.eligible_roster?.map((c: any) => (
                      <tr key={c.id}>
                        <td className="py-2.5 font-semibold text-slate-800 dark:text-slate-200">{c.name}</td>
                        <td className="py-2.5 font-mono text-slate-500">{c.usn}</td>
                        <td className="py-2.5">{c.department}</td>
                        <td className="py-2.5 font-bold text-slate-900 dark:text-slate-100">{c.cgpa?.toFixed(2)}</td>
                        <td className="py-2.5">
                          <Badge variant="success" size="sm">{c.status}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Intervention Detail Modal */}
      <InterventionDetailModal
        interventionId={selectedInterventionId}
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false);
          setSelectedInterventionId(null);
        }}
        onUpdated={loadDashboard}
        userRole={user?.role}
      />
    </div>
  );
};
