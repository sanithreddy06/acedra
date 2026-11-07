import React, { useState, useEffect } from 'react';
import {
  X,
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  Clock,
  Sparkles,
  UserCheck,
  FileText,
  History,
  Send,
  RotateCcw,
  BookOpen,
  ArrowRight,
  User,
  GraduationCap
} from 'lucide-react';
import { api } from '../../api/client';

interface AlertDetailModalProps {
  alertId: number | null;
  onClose: () => void;
  onAlertUpdated: () => void;
  mentors?: any[];
}

export const AlertDetailModal: React.FC<AlertDetailModalProps> = ({
  alertId,
  onClose,
  onAlertUpdated,
  mentors = [],
}) => {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'details' | 'history' | 'actions'>('details');

  // Form states
  const [actionType, setActionType] = useState<'note' | 'assign' | 'resolve' | 'reopen' | null>(null);
  const [reviewNote, setReviewNote] = useState('');
  const [selectedMentorId, setSelectedMentorId] = useState<number | ''>('');
  const [resolutionReason, setResolutionReason] = useState('');
  const [reopenReason, setReopenReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    if (alertId) {
      loadAlert();
    }
  }, [alertId]);

  const loadAlert = async () => {
    if (!alertId) return;
    setLoading(true);
    setFeedback(null);
    try {
      const res = await api.getRiskAlertDetail(alertId);
      setData(res);
      if (res.alert.assigned_mentor_id) {
        setSelectedMentorId(res.alert.assigned_mentor_id);
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Failed to load alert detail' });
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async () => {
    if (!alertId) return;
    setSubmitting(true);
    try {
      await api.acknowledgeAlert(alertId, 'Acknowledged by authorized reviewer.');
      setFeedback({ type: 'success', message: 'Alert successfully acknowledged.' });
      await loadAlert();
      onAlertUpdated();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!alertId || !reviewNote.trim()) return;
    setSubmitting(true);
    try {
      await api.addAlertNote(alertId, reviewNote);
      setReviewNote('');
      setActionType(null);
      setFeedback({ type: 'success', message: 'Review note added to alert history.' });
      await loadAlert();
      onAlertUpdated();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  const handleAssignMentor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!alertId || !selectedMentorId) return;
    setSubmitting(true);
    try {
      await api.assignAlertMentor(alertId, Number(selectedMentorId), reviewNote);
      setReviewNote('');
      setActionType(null);
      setFeedback({ type: 'success', message: 'Alert assigned to designated mentor.' });
      await loadAlert();
      onAlertUpdated();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!alertId || !resolutionReason.trim()) return;
    setSubmitting(true);
    try {
      await api.resolveAlert(alertId, resolutionReason, reviewNote);
      setResolutionReason('');
      setReviewNote('');
      setActionType(null);
      setFeedback({ type: 'success', message: 'Alert marked as resolved.' });
      await loadAlert();
      onAlertUpdated();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  const handleReopen = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!alertId || !reopenReason.trim()) return;
    setSubmitting(true);
    try {
      await api.reopenAlert(alertId, reopenReason);
      setReopenReason('');
      setActionType(null);
      setFeedback({ type: 'success', message: 'Alert reopened for review.' });
      await loadAlert();
      onAlertUpdated();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  if (!alertId) return null;

  const alert = data?.alert;
  const history = data?.history || [];

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-900">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
            Critical Risk
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-900">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            High Risk
          </span>
        );
      case 'MODERATE':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200 dark:border-blue-900">
            <span className="w-2 h-2 rounded-full bg-blue-500" />
            Moderate
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            Normal
          </span>
        );
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RESOLVED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Resolved
          </span>
        );
      case 'UNDER_REVIEW':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-900">
            <Clock className="w-3.5 h-3.5" />
            Under Review
          </span>
        );
      case 'ACKNOWLEDGED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-100 text-cyan-800 dark:bg-cyan-950/60 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-900">
            <UserCheck className="w-3.5 h-3.5" />
            Acknowledged
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-900">
            <AlertTriangle className="w-3.5 h-3.5" />
            System Flagged
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl max-h-[92vh] flex flex-col bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400 border border-rose-100 dark:border-rose-900">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Early-Warning Alert #{alertId}
                </h3>
                {alert && getSeverityBadge(alert.severity)}
                {alert && getStatusBadge(alert.status)}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Rule-Based Early Warning · Non-punitive supportive intervention
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div
            className={`px-6 py-2.5 text-xs font-medium flex items-center justify-between ${
              feedback.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300 border-b border-emerald-100 dark:border-emerald-900'
                : 'bg-rose-50 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300 border-b border-rose-100 dark:border-rose-900'
            }`}
          >
            <span>{feedback.message}</span>
            <button onClick={() => setFeedback(null)} className="underline ml-4">
              Dismiss
            </button>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 px-6 bg-white dark:bg-slate-900">
          <button
            onClick={() => setActiveTab('details')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 text-xs font-semibold transition ${
              activeTab === 'details'
                ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Alert Evidence & AI Explanation
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 text-xs font-semibold transition ${
              activeTab === 'history'
                ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            Audit History ({history.length})
          </button>
          <button
            onClick={() => setActiveTab('actions')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 text-xs font-semibold transition ${
              activeTab === 'actions'
                ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <UserCheck className="w-3.5 h-3.5" />
            Intervention Actions
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mb-3" />
              <p className="text-xs">Loading alert evidence and history...</p>
            </div>
          ) : !alert ? (
            <div className="text-center py-8 text-slate-500 text-xs">Alert information not found.</div>
          ) : (
            <>
              {activeTab === 'details' && (
                <div className="space-y-5">
                  {/* Student & Rule Meta */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-2">
                      <div className="flex items-center gap-2 text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        <User className="w-3.5 h-3.5 text-brand-600" />
                        Student Profile
                      </div>
                      <div className="text-sm font-bold text-slate-900 dark:text-slate-100">
                        {alert.student_name}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 space-y-0.5">
                        <p>USN / Roll: <span className="font-mono text-slate-700 dark:text-slate-300">{alert.student_usn}</span> · {alert.student_srn || 'N/A'}</p>
                        <p>Dept / Class: {alert.student_department} · Sem {alert.student_semester} (Sec {alert.student_section})</p>
                      </div>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-2">
                      <div className="flex items-center gap-2 text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        <GraduationCap className="w-3.5 h-3.5 text-brand-600" />
                        Triggered Rule
                      </div>
                      <div className="text-sm font-bold text-slate-900 dark:text-slate-100">
                        {alert.rule_name}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 space-y-0.5">
                        <p>Rule Code: <span className="font-mono text-slate-700 dark:text-slate-300">{alert.rule_code}</span></p>
                        <p>Category: <span className="capitalize">{alert.rule_category?.toLowerCase()}</span> · Period: {alert.academic_period}</p>
                      </div>
                    </div>
                  </div>

                  {/* Quantitative Metric Comparison Card */}
                  <div className="p-4 rounded-xl bg-gradient-to-r from-amber-50/70 to-rose-50/70 dark:from-slate-800 dark:to-slate-800/80 border border-amber-200/80 dark:border-slate-700">
                    <div className="text-xs font-bold text-amber-900 dark:text-amber-300 uppercase tracking-wider mb-2">
                      Quantitative Metric Evidence
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                      <div>
                        <span className="text-[11px] text-slate-500 dark:text-slate-400">Observed Value</span>
                        <p className="text-base font-bold text-rose-600 dark:text-rose-400">
                          {alert.observed_display || `${alert.observed_value}`}
                        </p>
                      </div>
                      <div>
                        <span className="text-[11px] text-slate-500 dark:text-slate-400">Configured Threshold</span>
                        <p className="text-base font-bold text-slate-700 dark:text-slate-300">
                          {alert.threshold_display || `${alert.threshold_value}`}
                        </p>
                      </div>
                      <div>
                        <span className="text-[11px] text-slate-500 dark:text-slate-400">Detection Date</span>
                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mt-1">
                          {new Date(alert.detected_date).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    {alert.subject_name && (
                      <div className="mt-3 pt-3 border-t border-amber-200/60 dark:border-slate-700 text-xs text-slate-600 dark:text-slate-400">
                        Course Affected: <span className="font-semibold text-slate-900 dark:text-slate-200">{alert.subject_name}</span>
                      </div>
                    )}
                  </div>

                  {/* AI Explanation Box (Strictly Grounded) */}
                  <div className="p-4 rounded-xl bg-brand-50/60 dark:bg-brand-950/30 border border-brand-200 dark:border-brand-900 space-y-2">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-brand-700 dark:text-brand-300">
                      <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                      AI Evidence Explanation (Fact-Grounded)
                    </div>
                    <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                      {alert.ai_explanation}
                    </p>
                    <div className="text-[10px] text-slate-400 dark:text-slate-500 italic">
                      Notice: Formulated strictly from verified academic and attendance records. Does not represent a prediction or punitive academic judgment.
                    </div>
                  </div>

                  {/* Suggested Action */}
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-800 dark:text-slate-200 mb-1">
                      <BookOpen className="w-3.5 h-3.5 text-indigo-500" />
                      Recommended Support Intervention
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      {alert.suggested_action || 'Review student performance in upcoming advisor meeting.'}
                    </p>
                  </div>

                  {/* Mentor Assignment & Notes Summary */}
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-700 dark:text-slate-300">Assigned Mentor:</span>
                      <span className="font-semibold text-brand-600 dark:text-brand-400">
                        {alert.assigned_mentor_name || 'Unassigned'}
                      </span>
                    </div>
                    {alert.resolution_reason && (
                      <div className="flex items-center justify-between border-t border-slate-200 dark:border-slate-700 pt-2">
                        <span className="font-bold text-emerald-700 dark:text-emerald-400">Resolution Reason:</span>
                        <span className="text-slate-700 dark:text-slate-300">{alert.resolution_reason}</span>
                      </div>
                    )}
                    {alert.review_notes && (
                      <div className="border-t border-slate-200 dark:border-slate-700 pt-2">
                        <span className="font-bold text-slate-700 dark:text-slate-300 block mb-1">Documented Notes:</span>
                        <pre className="text-[11px] text-slate-600 dark:text-slate-400 whitespace-pre-wrap font-sans bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800">
                          {alert.review_notes}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'history' && (
                <div className="space-y-4">
                  <div className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                    Audit Trail & Lifecycle Events
                  </div>
                  {history.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No history records logged yet.</p>
                  ) : (
                    <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
                      {history.map((h: any) => (
                        <div key={h.id} className="relative group">
                          <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-brand-500 ring-4 ring-white dark:ring-slate-900" />
                          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="font-bold text-slate-900 dark:text-slate-100">
                                {h.action}
                              </span>
                              <span className="text-[10px] text-slate-400">
                                {new Date(h.created_at).toLocaleString()}
                              </span>
                            </div>
                            <p className="text-xs text-slate-600 dark:text-slate-400">
                              {h.notes}
                            </p>
                            <div className="mt-2 text-[10px] text-slate-400 flex items-center gap-1">
                              <span>Action by:</span>
                              <span className="font-semibold text-slate-600 dark:text-slate-300">
                                {h.performed_by_name}
                              </span>
                              {h.old_status && h.new_status && (
                                <span className="ml-auto font-mono text-[10px] text-slate-500">
                                  {h.old_status} → {h.new_status}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'actions' && (
                <div className="space-y-6">
                  {/* Quick Action Buttons */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <button
                      onClick={handleAcknowledge}
                      disabled={submitting || alert.status !== 'FLAGGED'}
                      className="flex flex-col items-center justify-center p-3 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-cyan-500 hover:bg-cyan-50/50 dark:hover:bg-cyan-950/20 text-slate-700 dark:text-slate-300 transition disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <UserCheck className="w-4 h-4 text-cyan-600 mb-1" />
                      <span className="text-xs font-semibold">Acknowledge</span>
                    </button>

                    <button
                      onClick={() => setActionType('assign')}
                      className={`flex flex-col items-center justify-center p-3 rounded-xl border transition ${
                        actionType === 'assign'
                          ? 'border-indigo-500 bg-indigo-50/70 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300'
                          : 'border-slate-200 dark:border-slate-800 hover:border-indigo-500 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <User className="w-4 h-4 text-indigo-600 mb-1" />
                      <span className="text-xs font-semibold">Assign Mentor</span>
                    </button>

                    <button
                      onClick={() => setActionType('note')}
                      className={`flex flex-col items-center justify-center p-3 rounded-xl border transition ${
                        actionType === 'note'
                          ? 'border-brand-500 bg-brand-50/70 dark:bg-brand-950/30 text-brand-700 dark:text-brand-300'
                          : 'border-slate-200 dark:border-slate-800 hover:border-brand-500 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <FileText className="w-4 h-4 text-brand-600 mb-1" />
                      <span className="text-xs font-semibold">Add Note</span>
                    </button>

                    {alert.status === 'RESOLVED' ? (
                      <button
                        onClick={() => setActionType('reopen')}
                        className={`flex flex-col items-center justify-center p-3 rounded-xl border transition ${
                          actionType === 'reopen'
                            ? 'border-amber-500 bg-amber-50/70 dark:bg-amber-950/30 text-amber-700 dark:text-amber-300'
                            : 'border-slate-200 dark:border-slate-800 hover:border-amber-500 text-slate-700 dark:text-slate-300'
                        }`}
                      >
                        <RotateCcw className="w-4 h-4 text-amber-600 mb-1" />
                        <span className="text-xs font-semibold">Reopen Alert</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => setActionType('resolve')}
                        className={`flex flex-col items-center justify-center p-3 rounded-xl border transition ${
                          actionType === 'resolve'
                            ? 'border-emerald-500 bg-emerald-50/70 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300'
                            : 'border-slate-200 dark:border-slate-800 hover:border-emerald-500 text-slate-700 dark:text-slate-300'
                        }`}
                      >
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 mb-1" />
                        <span className="text-xs font-semibold">Resolve Alert</span>
                      </button>
                    )}
                  </div>

                  {/* Form Panes */}
                  {actionType === 'note' && (
                    <form onSubmit={handleAddNote} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 space-y-3">
                      <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">Add Review Note</h4>
                      <textarea
                        required
                        rows={3}
                        value={reviewNote}
                        onChange={(e) => setReviewNote(e.target.value)}
                        placeholder="Document observations, meeting outcomes, or guidance given..."
                        className="w-full text-xs p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-brand-500 outline-none"
                      />
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setActionType(null)}
                          className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={submitting}
                          className="px-4 py-1.5 rounded-lg text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 transition"
                        >
                          Save Note
                        </button>
                      </div>
                    </form>
                  )}

                  {actionType === 'assign' && (
                    <form onSubmit={handleAssignMentor} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 space-y-3">
                      <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">Assign Alert to Academic Mentor</h4>
                      <div>
                        <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">
                          Select Mentor
                        </label>
                        <select
                          required
                          value={selectedMentorId}
                          onChange={(e) => setSelectedMentorId(Number(e.target.value))}
                          className="w-full text-xs p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 outline-none"
                        >
                          <option value="">-- Choose Assigned Mentor --</option>
                          {mentors.map((m: any) => (
                            <option key={m.id} value={m.id}>
                              {m.name || `Mentor #${m.id}`} ({m.designation || 'Faculty Mentor'})
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">
                          Assignment Instructions / Note
                        </label>
                        <textarea
                          rows={2}
                          value={reviewNote}
                          onChange={(e) => setReviewNote(e.target.value)}
                          placeholder="e.g., Please meet with Alex to discuss tutorial registration..."
                          className="w-full text-xs p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 outline-none"
                        />
                      </div>
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setActionType(null)}
                          className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={submitting}
                          className="px-4 py-1.5 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition"
                        >
                          Confirm Assignment
                        </button>
                      </div>
                    </form>
                  )}

                  {actionType === 'resolve' && (
                    <form onSubmit={handleResolve} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 space-y-3">
                      <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">Resolve Early-Warning Alert</h4>
                      <div>
                        <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">
                          Resolution Justification / Reason *
                        </label>
                        <input
                          type="text"
                          required
                          value={resolutionReason}
                          onChange={(e) => setResolutionReason(e.target.value)}
                          placeholder="e.g., Medical Absence Excused, Remedial Sessions Completed, Attendance Recovered"
                          className="w-full text-xs p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 outline-none"
                        />
                      </div>
                      <div>
                        <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">
                          Closing Documentation
                        </label>
                        <textarea
                          rows={2}
                          value={reviewNote}
                          onChange={(e) => setReviewNote(e.target.value)}
                          placeholder="Add supportive closure notes..."
                          className="w-full text-xs p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 outline-none"
                        />
                      </div>
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setActionType(null)}
                          className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={submitting}
                          className="px-4 py-1.5 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 transition"
                        >
                          Mark as Resolved
                        </button>
                      </div>
                    </form>
                  )}

                  {actionType === 'reopen' && (
                    <form onSubmit={handleReopen} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 space-y-3">
                      <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">Reopen Alert for Review</h4>
                      <div>
                        <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">
                          Reason for Reopening *
                        </label>
                        <input
                          type="text"
                          required
                          value={reopenReason}
                          onChange={(e) => setReopenReason(e.target.value)}
                          placeholder="e.g., Continued attendance decline in subsequent week"
                          className="w-full text-xs p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 outline-none"
                        />
                      </div>
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setActionType(null)}
                          className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={submitting}
                          className="px-4 py-1.5 rounded-lg text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 transition"
                        >
                          Confirm Reopen
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-xs">
          <span className="text-slate-400">
            Smart Campus Intelligence · Early Warning System (Module 2)
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg font-semibold text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/60 transition"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
