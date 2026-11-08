import React, { useState, useEffect } from 'react';
import {
  X,
  Calendar,
  Clock,
  User,
  CheckCircle2,
  AlertTriangle,
  MessageSquare,
  Shield,
  Send,
  PlusCircle,
  FileText,
  Activity,
  Award
} from 'lucide-react';
import { api } from '../../api/client';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface InterventionDetailModalProps {
  interventionId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdated?: () => void;
  userRole?: string;
}

export const InterventionDetailModal: React.FC<InterventionDetailModalProps> = ({
  interventionId,
  isOpen,
  onClose,
  onUpdated,
  userRole = 'mentor'
}) => {
  const [data, setData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // New Note state
  const [noteText, setNoteText] = useState('');
  const [noteType, setNoteType] = useState('COUNSELING');
  const [isSubmittingNote, setIsSubmittingNote] = useState(false);

  // Status transition state
  const [newStatus, setNewStatus] = useState('');
  const [resolutionSummary, setResolutionSummary] = useState('');
  const [isSubmittingStatus, setIsSubmittingStatus] = useState(false);

  // Follow-up state
  const [showFollowupForm, setShowFollowupForm] = useState(false);
  const [followupDate, setFollowupDate] = useState('');
  const [followupNotes, setFollowupNotes] = useState('');
  const [isSubmittingFollowup, setIsSubmittingFollowup] = useState(false);

  // Follow-up outcome state
  const [activeFollowupId, setActiveFollowupId] = useState<number | null>(null);
  const [outcomeNotes, setOutcomeNotes] = useState('');
  const [studentFeedback, setStudentFeedback] = useState('');
  const [isSubmittingOutcome, setIsSubmittingOutcome] = useState(false);

  const loadDetail = async () => {
    if (!interventionId) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getInterventionDetail(interventionId);
      setData(res);
      setNewStatus(res.status);
    } catch (err: any) {
      setError(err.message || 'Failed to load intervention details');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && interventionId) {
      loadDetail();
    }
  }, [isOpen, interventionId]);

  if (!isOpen || !interventionId) return null;

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteText.trim()) return;
    setIsSubmittingNote(true);
    try {
      await api.addInterventionNote(interventionId, {
        note_text: noteText.trim(),
        note_type: noteType
      });
      setNoteText('');
      await loadDetail();
      if (onUpdated) onUpdated();
    } catch (err: any) {
      alert(err.message || 'Failed to add note');
    } finally {
      setIsSubmittingNote(false);
    }
  };

  const handleUpdateStatus = async () => {
    if (!newStatus) return;
    setIsSubmittingStatus(true);
    try {
      await api.updateInterventionStatus(interventionId, {
        status: newStatus,
        resolution_summary: resolutionSummary.trim() || undefined
      });
      await loadDetail();
      if (onUpdated) onUpdated();
    } catch (err: any) {
      alert(err.message || 'Failed to update status');
    } finally {
      setIsSubmittingStatus(false);
    }
  };

  const handleScheduleFollowup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!followupDate) return;
    setIsSubmittingFollowup(true);
    try {
      await api.scheduleInterventionFollowup(interventionId, {
        scheduled_date: followupDate,
        outcome_notes: followupNotes.trim() || undefined
      });
      setShowFollowupForm(false);
      setFollowupDate('');
      setFollowupNotes('');
      await loadDetail();
      if (onUpdated) onUpdated();
    } catch (err: any) {
      alert(err.message || 'Failed to schedule follow-up');
    } finally {
      setIsSubmittingFollowup(false);
    }
  };

  const handleRecordOutcome = async (followupId: number) => {
    setIsSubmittingOutcome(true);
    try {
      await api.recordFollowupOutcome(followupId, {
        followup_status: 'COMPLETED',
        outcome_notes: outcomeNotes.trim() || undefined,
        student_feedback: studentFeedback.trim() || undefined
      });
      setActiveFollowupId(null);
      setOutcomeNotes('');
      setStudentFeedback('');
      await loadDetail();
      if (onUpdated) onUpdated();
    } catch (err: any) {
      alert(err.message || 'Failed to record outcome');
    } finally {
      setIsSubmittingOutcome(false);
    }
  };

  const getPriorityBadgeVariant = (priority: string): 'brand' | 'success' | 'warning' | 'danger' | 'slate' => {
    switch (priority?.toUpperCase()) {
      case 'URGENT':
      case 'HIGH':
        return 'danger';
      case 'MEDIUM':
        return 'warning';
      default:
        return 'slate';
    }
  };

  const getStatusBadgeVariant = (status: string): 'brand' | 'success' | 'warning' | 'danger' | 'slate' => {
    switch (status?.toUpperCase()) {
      case 'RESOLVED':
      case 'CLOSED':
        return 'success';
      case 'IN_PROGRESS':
        return 'brand';
      case 'ASSIGNED':
        return 'warning';
      default:
        return 'slate';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden my-8 max-h-[90vh] flex flex-col">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/30">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-brand-50 dark:bg-brand-950/50 rounded-2xl text-brand-600 dark:text-brand-400">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Intervention Case #{interventionId}
                </span>
                {data && (
                  <>
                    <Badge variant={getPriorityBadgeVariant(data.priority)} size="sm">
                      {data.priority} Priority
                    </Badge>
                    <Badge variant={getStatusBadgeVariant(data.status)} size="sm">
                      {data.status}
                    </Badge>
                  </>
                )}
              </div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white mt-0.5">
                {data?.title || 'Loading Dossier...'}
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {isLoading ? (
            <LoadingSpinner label="Retrieving intervention dossier & timeline..." />
          ) : error || !data ? (
            <div className="p-4 bg-rose-50 text-rose-700 rounded-xl text-sm">{error}</div>
          ) : (
            <>
              {/* Student & Assigned Mentor Info Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 text-xs">
                <div>
                  <span className="text-slate-400 block mb-0.5 font-medium">Target Student</span>
                  <strong className="text-slate-900 dark:text-slate-100 text-sm block">{data.student_name}</strong>
                  <span className="text-slate-500">{data.student_usn} &bull; Sem {data.student_semester || 5}</span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5 font-medium">Department</span>
                  <strong className="text-slate-900 dark:text-slate-100 block">{data.student_department || 'Computer Science'}</strong>
                  <span className="text-slate-500">B.Tech Programme</span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5 font-medium">Assigned Mentor</span>
                  <strong className="text-slate-900 dark:text-slate-100 block">{data.mentor_name || 'Unassigned'}</strong>
                  <span className="text-slate-500">By: {data.assigned_by_name || 'Academic Dean'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5 font-medium">Target Completion</span>
                  <strong className="text-slate-900 dark:text-slate-100 block">
                    {data.target_resolution_date ? new Date(data.target_resolution_date).toLocaleDateString() : 'Open-ended'}
                  </strong>
                  <span className="text-slate-500">{data.intervention_type?.replace(/_/g, ' ')}</span>
                </div>
              </div>

              {/* Status Transition Control (Mentor / Faculty / Admin) */}
              {userRole !== 'student' && (
                <div className="p-4 rounded-2xl bg-brand-50/50 dark:bg-brand-950/20 border border-brand-200 dark:border-brand-900/50 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-brand-800 dark:text-brand-300">
                      Manage Case Lifecycle
                    </h4>
                    <p className="text-xs text-brand-700/80 dark:text-brand-400 mt-0.5">
                      Advance intervention status or record institutional resolution summary.
                    </p>
                  </div>
                  <div className="flex items-center space-x-2 w-full sm:w-auto">
                    <select
                      value={newStatus}
                      onChange={(e) => setNewStatus(e.target.value)}
                      className="px-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-medium text-slate-800 dark:text-slate-100"
                    >
                      <option value="OPEN">OPEN</option>
                      <option value="ASSIGNED">ASSIGNED</option>
                      <option value="IN_PROGRESS">IN_PROGRESS</option>
                      <option value="RESOLVED">RESOLVED</option>
                      <option value="CLOSED">CLOSED</option>
                    </select>

                    <button
                      onClick={handleUpdateStatus}
                      disabled={isSubmittingStatus || newStatus === data.status}
                      className="px-3.5 py-1.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-semibold shadow-sm transition disabled:opacity-50"
                    >
                      {isSubmittingStatus ? 'Updating...' : 'Update Status'}
                    </button>
                  </div>
                </div>
              )}

              {/* If Resolved or Resolving, Resolution Summary display / input */}
              {data.resolution_summary ? (
                <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 text-xs">
                  <div className="flex items-center space-x-2 text-emerald-800 dark:text-emerald-300 font-bold mb-1">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Resolution Summary & Institutional Closure</span>
                  </div>
                  <p className="text-emerald-900 dark:text-emerald-100">{data.resolution_summary}</p>
                </div>
              ) : newStatus === 'RESOLVED' && (
                <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 text-xs space-y-2">
                  <span className="font-bold text-amber-800 dark:text-amber-300 block">
                    Record Resolution Outcome & Findings:
                  </span>
                  <textarea
                    rows={2}
                    value={resolutionSummary}
                    onChange={(e) => setResolutionSummary(e.target.value)}
                    placeholder="E.g., Student achieved 82% attendance, cleared makeup assessment, and mentor confirms stable standing."
                    className="w-full px-3 py-2 rounded-xl border border-amber-300 dark:border-amber-700 bg-white dark:bg-slate-900 text-xs"
                  />
                </div>
              )}

              {/* Scheduled Review & Follow-up Sessions */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center">
                    <Calendar className="w-4 h-4 mr-1.5 text-brand-600" />
                    Scheduled Review & Counseling Sessions ({data.followups?.length || 0})
                  </h3>
                  {userRole !== 'student' && !showFollowupForm && (
                    <button
                      onClick={() => setShowFollowupForm(true)}
                      className="inline-flex items-center px-3 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-xs font-medium transition"
                    >
                      <PlusCircle className="w-3.5 h-3.5 mr-1" />
                      Schedule Follow-up
                    </button>
                  )}
                </div>

                {/* Follow-up Booking Form */}
                {showFollowupForm && (
                  <form onSubmit={handleScheduleFollowup} className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs space-y-3">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-slate-500 mb-1 font-medium">Session Date</label>
                        <input
                          type="date"
                          required
                          value={followupDate}
                          onChange={(e) => setFollowupDate(e.target.value)}
                          className="w-full px-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-500 mb-1 font-medium">Session Agenda / Target</label>
                        <input
                          type="text"
                          placeholder="E.g., Review Week 8 quiz scores and lab logbook"
                          value={followupNotes}
                          onChange={(e) => setFollowupNotes(e.target.value)}
                          className="w-full px-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                        />
                      </div>
                    </div>
                    <div className="flex justify-end space-x-2">
                      <button
                        type="button"
                        onClick={() => setShowFollowupForm(false)}
                        className="px-3 py-1.5 text-slate-500 hover:text-slate-700 text-xs"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={isSubmittingFollowup}
                        className="px-4 py-1.5 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-xl text-xs transition"
                      >
                        {isSubmittingFollowup ? 'Scheduling...' : 'Save Follow-Up'}
                      </button>
                    </div>
                  </form>
                )}

                {/* List Follow-ups */}
                {data.followups && data.followups.length > 0 ? (
                  <div className="space-y-2">
                    {data.followups.map((f: any) => (
                      <div
                        key={f.id}
                        className="p-3.5 rounded-2xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold text-slate-900 dark:text-slate-100">
                              {new Date(f.scheduled_date).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
                            </span>
                            <Badge variant={f.followup_status === 'COMPLETED' ? 'success' : 'warning'} size="sm">
                              {f.followup_status}
                            </Badge>
                          </div>
                          {userRole !== 'student' && f.followup_status === 'SCHEDULED' && activeFollowupId !== f.id && (
                            <button
                              onClick={() => {
                                setActiveFollowupId(f.id);
                                setOutcomeNotes(f.outcome_notes || '');
                              }}
                              className="text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400"
                            >
                              Record Outcome &bull; Close Session
                            </button>
                          )}
                        </div>

                        {f.outcome_notes && (
                          <p className="text-slate-600 dark:text-slate-300">
                            <strong>Mentor Notes:</strong> {f.outcome_notes}
                          </p>
                        )}
                        {f.student_feedback && (
                          <p className="text-slate-500 italic">
                            <strong>Student Feedback:</strong> "{f.student_feedback}"
                          </p>
                        )}

                        {/* Record Outcome Form Drawer */}
                        {activeFollowupId === f.id && (
                          <div className="mt-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
                            <h5 className="font-bold text-slate-800 dark:text-slate-200">Session Outcome & Progress</h5>
                            <textarea
                              rows={2}
                              value={outcomeNotes}
                              onChange={(e) => setOutcomeNotes(e.target.value)}
                              placeholder="Notes on student progress, concept clarity, actions taken..."
                              className="w-full px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 text-xs"
                            />
                            <textarea
                              rows={1}
                              value={studentFeedback}
                              onChange={(e) => setStudentFeedback(e.target.value)}
                              placeholder="Student feedback / self-assessment comments..."
                              className="w-full px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 text-xs"
                            />
                            <div className="flex justify-end space-x-2">
                              <button
                                type="button"
                                onClick={() => setActiveFollowupId(null)}
                                className="px-2.5 py-1 text-slate-500 text-xs"
                              >
                                Cancel
                              </button>
                              <button
                                type="button"
                                onClick={() => handleRecordOutcome(f.id)}
                                disabled={isSubmittingOutcome}
                                className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold"
                              >
                                {isSubmittingOutcome ? 'Saving...' : 'Mark Completed'}
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic py-2">No follow-up review sessions scheduled yet.</p>
                )}
              </div>

              {/* Timeline Notes & Communications History */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center">
                  <MessageSquare className="w-4 h-4 mr-1.5 text-brand-600" />
                  Counseling Notes & Activity Timeline ({data.notes?.length || 0})
                </h3>

                {/* Add Note Form */}
                {userRole !== 'student' && (
                  <form onSubmit={handleAddNote} className="space-y-2">
                    <div className="flex gap-2">
                      <select
                        value={noteType}
                        onChange={(e) => setNoteType(e.target.value)}
                        className="px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs font-medium text-slate-800 dark:text-slate-200"
                      >
                        <option value="COUNSELING">COUNSELING</option>
                        <option value="OBSERVATION">OBSERVATION</option>
                        <option value="ACTION_ITEM">ACTION_ITEM</option>
                        <option value="PARENT_COMMUNICATION">PARENT_COMMUNICATION</option>
                        <option value="GENERAL">GENERAL</option>
                      </select>
                      <input
                        type="text"
                        required
                        value={noteText}
                        onChange={(e) => setNoteText(e.target.value)}
                        placeholder="Log clinical observation, action item, or counseling meeting takeaway..."
                        className="flex-1 px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                      />
                      <button
                        type="submit"
                        disabled={isSubmittingNote || !noteText.trim()}
                        className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-xl text-xs flex items-center space-x-1 transition disabled:opacity-50"
                      >
                        <Send className="w-3.5 h-3.5 mr-1" />
                        <span>Log Note</span>
                      </button>
                    </div>
                  </form>
                )}

                {/* Notes Stream */}
                <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                  {data.notes && data.notes.length > 0 ? (
                    data.notes.map((n: any) => (
                      <div
                        key={n.id}
                        className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-700/60 text-xs space-y-1"
                      >
                        <div className="flex items-center justify-between text-slate-400 text-[11px]">
                          <span className="font-semibold text-slate-700 dark:text-slate-300">
                            {n.author_name} &bull; <strong className="capitalize">{n.author_role}</strong>
                          </span>
                          <div className="flex items-center space-x-2">
                            <Badge variant="slate" size="sm">
                              {n.note_type}
                            </Badge>
                            <span>{new Date(n.created_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                          </div>
                        </div>
                        <p className="text-slate-800 dark:text-slate-200">{n.note_text}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-400 italic">No notes recorded on this case yet.</p>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-800 dark:text-slate-100 text-xs font-semibold transition"
          >
            Close Dossier
          </button>
        </div>
      </div>
    </div>
  );
};
