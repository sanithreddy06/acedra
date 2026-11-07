import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Filter,
  Search,
  RotateCcw,
  Sliders,
  Play,
  UserCheck,
  ChevronRight,
  TrendingDown,
  Building,
  GraduationCap,
  Sparkles,
  Info
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  AreaChart,
  Area,
  CartesianGrid
} from 'recharts';
import { api } from '../../api/client';
import { AlertDetailModal } from './AlertDetailModal';
import { RiskRuleConfigModal } from './RiskRuleConfigModal';

interface RiskDashboardProps {
  userRole?: string;
}

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#f43f5e',
  HIGH: '#f59e0b',
  MODERATE: '#3b82f6',
  NORMAL: '#10b981',
};

export const RiskDashboard: React.FC<RiskDashboardProps> = ({ userRole }) => {
  const [stats, setStats] = useState<any | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [totalAlerts, setTotalAlerts] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Filters
  const [selectedSeverity, setSelectedSeverity] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedDept, setSelectedDept] = useState<string>('');
  const [selectedSemester, setSelectedSemester] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals
  const [selectedAlertId, setSelectedAlertId] = useState<number | null>(null);
  const [showRuleConfig, setShowRuleConfig] = useState<boolean>(false);

  useEffect(() => {
    loadDashboardData();
  }, [selectedSeverity, selectedStatus, selectedDept, selectedSemester, searchQuery]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [statsData, alertsData] = await Promise.all([
        api.getRiskStatistics(selectedDept ? Number(selectedDept) : undefined),
        api.getRiskAlerts({
          severity: selectedSeverity || undefined,
          status: selectedStatus || undefined,
          department_id: selectedDept || undefined,
          semester: selectedSemester || undefined,
          search: searchQuery || undefined,
          limit: 100,
        }),
      ]);

      setStats(statsData);
      setAlerts(alertsData.items || []);
      setTotalAlerts(alertsData.total || 0);
    } catch (err: any) {
      console.error('Failed to load risk dashboard data:', err);
      setFeedback({ type: 'error', message: err.message || 'Error fetching risk alerts' });
    } finally {
      setLoading(false);
    }
  };

  const handleRunEvaluation = async () => {
    setEvaluating(true);
    setFeedback(null);
    try {
      const res = await api.triggerRiskEvaluation(
        undefined,
        selectedDept ? Number(selectedDept) : undefined
      );
      setFeedback({
        type: 'success',
        message: `Evaluation completed: ${res.evaluated_students_count} students evaluated, ${res.alerts_generated_count} active alert(s) mapped.`,
      });
      await loadDashboardData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Evaluation run failed' });
    } finally {
      setEvaluating(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/70 dark:text-rose-300 border border-rose-200 dark:border-rose-900">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
            Critical
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/70 dark:text-amber-300 border border-amber-200 dark:border-amber-900">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            High
          </span>
        );
      case 'MODERATE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/70 dark:text-blue-300 border border-blue-200 dark:border-blue-900">
            Moderate
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            Normal
          </span>
        );
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RESOLVED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
            <CheckCircle2 className="w-3 h-3" />
            Resolved
          </span>
        );
      case 'UNDER_REVIEW':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
            <Clock className="w-3 h-3" />
            Under Review
          </span>
        );
      case 'ACKNOWLEDGED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-cyan-50 text-cyan-700 dark:bg-cyan-950/50 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-800">
            <UserCheck className="w-3 h-3" />
            Acknowledged
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
            <AlertTriangle className="w-3 h-3" />
            Flagged
          </span>
        );
    }
  };

  // Prepare chart data
  const pieData = stats?.severity_distribution
    ? [
        { name: 'Critical', value: stats.severity_distribution.critical, color: SEVERITY_COLORS.CRITICAL },
        { name: 'High', value: stats.severity_distribution.high, color: SEVERITY_COLORS.HIGH },
        { name: 'Moderate', value: stats.severity_distribution.moderate, color: SEVERITY_COLORS.MODERATE },
        { name: 'Normal', value: stats.severity_distribution.normal, color: SEVERITY_COLORS.NORMAL },
      ].filter((d) => d.value > 0)
    : [];

  const deptData = (stats?.department_distribution || []).map((d: any) => ({
    name: d.department_code,
    alerts: d.alert_count,
    students: d.student_count,
  }));

  const semData = (stats?.semester_distribution || []).map((s: any) => ({
    semester: `Sem ${s.semester}`,
    alerts: s.alert_count,
  }));

  return (
    <div className="space-y-6">
      
      {/* Top Header & Reassessment Trigger */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400 border border-rose-100 dark:border-rose-900">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                AI-Assisted Early-Warning Intelligence
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Transparent, rule-based student support identification · Module 2
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {userRole === 'admin' && (
            <button
              onClick={() => setShowRuleConfig(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition"
            >
              <Sliders className="w-4 h-4 text-slate-500" />
              Configure Rules
            </button>
          )}

          <button
            onClick={handleRunEvaluation}
            disabled={evaluating}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 shadow-sm transition disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${evaluating ? 'animate-spin' : ''}`} />
            {evaluating ? 'Evaluating Rules...' : 'Run Risk Assessment'}
          </button>
        </div>
      </div>

      {/* Feedback Alert */}
      {feedback && (
        <div
          className={`p-4 rounded-xl text-xs font-semibold flex items-center justify-between ${
            feedback.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
              : 'bg-rose-50 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-800'
          }`}
        >
          <span>{feedback.message}</span>
          <button onClick={() => setFeedback(null)} className="underline ml-4">
            Dismiss
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              Active Early Warnings
            </span>
            <div className="p-2 rounded-xl bg-brand-50 dark:bg-brand-950/50 text-brand-600">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-black text-slate-900 dark:text-slate-100 mt-2">
            {stats?.total_active_alerts ?? 0}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Rule triggers pending intervention</p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              Students Requiring Review
            </span>
            <div className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/50 text-amber-600">
              <GraduationCap className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-black text-amber-600 dark:text-amber-400 mt-2">
            {stats?.total_students_at_risk ?? 0}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Distinct students flagged</p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              Critical Severity Alerts
            </span>
            <div className="p-2 rounded-xl bg-rose-50 dark:bg-rose-950/50 text-rose-600">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-center gap-2 mt-2">
            <p className="text-2xl font-black text-rose-600 dark:text-rose-400">
              {stats?.severity_distribution?.critical ?? 0}
            </p>
            {stats?.severity_distribution?.critical > 0 && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 animate-pulse">
                Action Required
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">&lt;65% Att / Multiple Backlogs</p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              High & Moderate Alerts
            </span>
            <div className="p-2 rounded-xl bg-blue-50 dark:bg-blue-950/50 text-blue-600">
              <TrendingDown className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-black text-slate-900 dark:text-slate-100 mt-2">
            {(stats?.severity_distribution?.high ?? 0) + (stats?.severity_distribution?.moderate ?? 0)}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">
            High: {stats?.severity_distribution?.high ?? 0} · Mod: {stats?.severity_distribution?.moderate ?? 0}
          </p>
        </div>
      </div>

      {/* Visual Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Severity Distribution Donut */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
              Severity Distribution
            </h3>
            <span className="text-[10px] text-slate-400">Active alerts</span>
          </div>
          <div className="h-52 flex items-center justify-center">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(15, 23, 42, 0.95)',
                      borderRadius: '8px',
                      fontSize: '11px',
                      color: '#fff',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-slate-400">No active alerts to chart</p>
            )}
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2 text-[11px]">
            {pieData.map((d) => (
              <div key={d.name} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  {d.name}: {d.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Department-wise BarChart */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
              Department Alerts
            </h3>
            <span className="text-[10px] text-slate-400">By Program</span>
          </div>
          <div className="h-52">
            {deptData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={deptData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(15, 23, 42, 0.95)',
                      borderRadius: '8px',
                      fontSize: '11px',
                      color: '#fff',
                    }}
                  />
                  <Bar dataKey="alerts" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-xs text-slate-400">
                No department distribution data
              </div>
            )}
          </div>
        </div>

        {/* Semester Trend AreaChart */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
              Semester Distribution
            </h3>
            <span className="text-[10px] text-slate-400">Curricular Progression</span>
          </div>
          <div className="h-52">
            {semData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={semData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="alertGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="semester" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(15, 23, 42, 0.95)',
                      borderRadius: '8px',
                      fontSize: '11px',
                      color: '#fff',
                    }}
                  />
                  <Area type="monotone" dataKey="alerts" stroke="#f59e0b" fillOpacity={1} fill="url(#alertGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-xs text-slate-400">
                No semester trend data
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Filterable Risk Alert Roster */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        
        {/* Filter Controls Header */}
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Identified Early-Warning Alerts
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Showing {alerts.length} of {totalAlerts} total records
              </p>
            </div>

            {/* Search Input */}
            <div className="relative w-full sm:w-64">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search student, roll, or rule..."
                className="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1 mr-1">
              <Filter className="w-3 h-3" /> Filters:
            </span>

            {/* Severity Filter */}
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="text-xs py-1 px-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none"
            >
              <option value="">All Severities</option>
              <option value="CRITICAL">Critical Risk</option>
              <option value="HIGH">High Risk</option>
              <option value="MODERATE">Moderate</option>
              <option value="NORMAL">Normal</option>
            </select>

            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="text-xs py-1 px-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none"
            >
              <option value="">All Statuses</option>
              <option value="FLAGGED">System Flagged</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="RESOLVED">Resolved</option>
            </select>

            {/* Semester Filter */}
            <select
              value={selectedSemester}
              onChange={(e) => setSelectedSemester(e.target.value)}
              className="text-xs py-1 px-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none"
            >
              <option value="">All Semesters</option>
              {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                <option key={s} value={s}>Semester {s}</option>
              ))}
            </select>

            {(selectedSeverity || selectedStatus || selectedSemester || searchQuery) && (
              <button
                onClick={() => {
                  setSelectedSeverity('');
                  setSelectedStatus('');
                  setSelectedSemester('');
                  setSearchQuery('');
                }}
                className="text-xs font-semibold text-rose-500 hover:text-rose-600 underline ml-2"
              >
                Reset Filters
              </button>
            )}
          </div>
        </div>

        {/* Alerts Table */}
        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-8 text-center text-xs text-slate-400">Loading alerts list...</div>
          ) : alerts.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-400 space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
              <p className="font-semibold text-slate-700 dark:text-slate-300">
                No active early-warning alerts matching selected filters.
              </p>
              <p className="text-[11px] text-slate-400">
                Try clearing filters or running a reassessment.
              </p>
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50/70 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="py-3 px-4 font-semibold">Student</th>
                  <th className="py-3 px-3 font-semibold">Triggered Rule</th>
                  <th className="py-3 px-3 font-semibold">Severity</th>
                  <th className="py-3 px-3 font-semibold">Observed vs Threshold</th>
                  <th className="py-3 px-3 font-semibold">Status</th>
                  <th className="py-3 px-3 font-semibold">Assigned Mentor</th>
                  <th className="py-3 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {alerts.map((alert) => (
                  <tr
                    key={alert.id}
                    className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition group cursor-pointer"
                    onClick={() => setSelectedAlertId(alert.id)}
                  >
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900 dark:text-slate-100">
                        {alert.student_name}
                      </div>
                      <div className="text-[10px] text-slate-400 space-x-1 font-mono">
                        <span>{alert.student_roll || alert.student_usn}</span>
                        <span>· Sem {alert.student_semester}</span>
                        <span>· {alert.student_department}</span>
                      </div>
                    </td>

                    <td className="py-3 px-3">
                      <div className="font-semibold text-slate-800 dark:text-slate-200 max-w-xs truncate">
                        {alert.rule_name}
                      </div>
                      <div className="text-[10px] font-mono text-slate-400">
                        {alert.rule_code}
                      </div>
                    </td>

                    <td className="py-3 px-3">
                      {getSeverityBadge(alert.severity)}
                    </td>

                    <td className="py-3 px-3 font-mono">
                      <div className="font-bold text-rose-600 dark:text-rose-400">
                        {alert.observed_display || alert.observed_value}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        target {alert.threshold_display || alert.threshold_value}
                      </div>
                    </td>

                    <td className="py-3 px-3">
                      {getStatusBadge(alert.status)}
                    </td>

                    <td className="py-3 px-3 text-slate-600 dark:text-slate-300">
                      {alert.assigned_mentor_name ? (
                        <span className="font-medium">{alert.assigned_mentor_name}</span>
                      ) : (
                        <span className="text-slate-400 italic">Unassigned</span>
                      )}
                    </td>

                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedAlertId(alert.id);
                        }}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold text-brand-600 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-950/50 transition"
                      >
                        Review
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

      </div>

      {/* Modals */}
      {selectedAlertId && (
        <AlertDetailModal
          alertId={selectedAlertId}
          onClose={() => setSelectedAlertId(null)}
          onAlertUpdated={loadDashboardData}
        />
      )}

      {showRuleConfig && (
        <RiskRuleConfigModal
          isOpen={showRuleConfig}
          onClose={() => setShowRuleConfig(false)}
          onRulesUpdated={loadDashboardData}
        />
      )}

    </div>
  );
};
