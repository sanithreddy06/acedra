import React, { useState } from 'react';
import {
  X,
  ExternalLink,
  Sparkles,
  CheckCircle2,
  Clock,
  BookOpen,
  Target,
  Award,
  Star,
  ThumbsUp,
  MessageSquare,
  AlertCircle,
  TrendingUp,
  UserCheck
} from 'lucide-react';
import { api } from '../../api/client';

interface RecommendationDetailModalProps {
  recommendation: any;
  isOpen: boolean;
  onClose: () => void;
  onUpdated: () => void;
  userRole?: string;
}

export const RecommendationDetailModal: React.FC<RecommendationDetailModalProps> = ({
  recommendation,
  isOpen,
  onClose,
  onUpdated,
  userRole,
}) => {
  if (!isOpen || !recommendation) return null;

  const [activeTab, setActiveTab] = useState<'details' | 'progress' | 'feedback' | 'guidance'>('details');
  const [submitting, setSubmitting] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Rejection Form
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  // Progress Form
  const [percentComplete, setPercentComplete] = useState<number>(
    recommendation.progress_logs?.[0]?.percent_complete || (recommendation.status === 'COMPLETED' ? 100 : 0)
  );
  const [hoursSpent, setHoursSpent] = useState<number>(recommendation.progress_logs?.[0]?.hours_spent || 0);
  const [progressNotes, setProgressNotes] = useState('');

  // Feedback Form
  const [rating, setRating] = useState<number>(recommendation.feedback?.rating || 5);
  const [helpful, setHelpful] = useState<boolean>(recommendation.feedback?.helpful ?? true);
  const [relevanceScore, setRelevanceScore] = useState<number>(recommendation.feedback?.relevance_score || 5);
  const [comments, setComments] = useState<string>(recommendation.feedback?.comments || '');
  const [outcomeAchieved, setOutcomeAchieved] = useState<boolean>(recommendation.feedback?.outcome_achieved || false);

  // Mentor Guidance Form
  const [mentorGuidance, setMentorGuidance] = useState('');

  const handleAccept = async () => {
    setSubmitting(true);
    try {
      await api.acceptRecommendation(recommendation.id);
      setFeedbackMsg({ type: 'success', text: 'Recommendation accepted into your active learning plan.' });
      onUpdated();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Failed to accept recommendation.' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectReason.trim()) return;
    setSubmitting(true);
    try {
      await api.rejectRecommendation(recommendation.id, rejectReason);
      setFeedbackMsg({ type: 'success', text: 'Recommendation marked as rejected.' });
      setShowRejectForm(false);
      onUpdated();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Failed to reject recommendation.' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveProgress = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const nextStatus = percentComplete >= 100 ? 'COMPLETED' : 'IN_PROGRESS';
      await api.updateRecommendationProgress(recommendation.id, {
        status: nextStatus,
        percent_complete: Number(percentComplete),
        hours_spent: Number(hoursSpent),
        notes: progressNotes,
      });
      setFeedbackMsg({ type: 'success', text: `Progress updated (${percentComplete}%).` });
      setProgressNotes('');
      onUpdated();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Failed to update progress.' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.submitRecommendationFeedback(recommendation.id, {
        rating,
        helpful,
        relevance_score: relevanceScore,
        comments,
        outcome_achieved: outcomeAchieved,
      });
      setFeedbackMsg({ type: 'success', text: 'Feedback submitted. Thank you for rating this resource!' });
      onUpdated();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Failed to submit feedback.' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddGuidance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mentorGuidance.trim()) return;
    setSubmitting(true);
    try {
      await api.addMentorGuidance(recommendation.id, mentorGuidance);
      setFeedbackMsg({ type: 'success', text: 'Personalized guidance documented for student.' });
      setMentorGuidance('');
      onUpdated();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Failed to add guidance.' });
    } finally {
      setSubmitting(false);
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300">Critical Priority</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">High Priority</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">Medium Priority</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">Standard</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">Completed</span>;
      case 'IN_PROGRESS':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300">In Progress</span>;
      case 'ACCEPTED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-300">Accepted</span>;
      case 'REJECTED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-400">Declined</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">Suggested</span>;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-brand-50 dark:bg-brand-950/50 text-brand-600 dark:text-brand-400 border border-brand-100 dark:border-brand-900">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold tracking-wider uppercase text-slate-400">
                  {recommendation.category?.replace(/_/g, ' ')}
                </span>
                {getPriorityBadge(recommendation.priority)}
                {getStatusBadge(recommendation.status)}
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 line-clamp-1">
                {recommendation.title}
              </h3>
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
        {feedbackMsg && (
          <div
            className={`px-6 py-2.5 text-xs font-medium flex items-center justify-between ${
              feedbackMsg.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300'
                : 'bg-rose-50 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300'
            }`}
          >
            <span>{feedbackMsg.text}</span>
            <button onClick={() => setFeedbackMsg(null)} className="underline ml-4">
              Dismiss
            </button>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 px-6 bg-white dark:bg-slate-900">
          <button
            onClick={() => setActiveTab('details')}
            className={`py-3 px-4 border-b-2 text-xs font-semibold transition ${
              activeTab === 'details'
                ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            Overview & Reason
          </button>
          <button
            onClick={() => setActiveTab('progress')}
            className={`py-3 px-4 border-b-2 text-xs font-semibold transition ${
              activeTab === 'progress'
                ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            Progress Tracking ({percentComplete}%)
          </button>
          <button
            onClick={() => setActiveTab('feedback')}
            className={`py-3 px-4 border-b-2 text-xs font-semibold transition ${
              activeTab === 'feedback'
                ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            Rating & Feedback
          </button>
          {(userRole === 'mentor' || userRole === 'faculty' || userRole === 'admin' || recommendation.mentor_guidance_notes) && (
            <button
              onClick={() => setActiveTab('guidance')}
              className={`py-3 px-4 border-b-2 text-xs font-semibold transition ${
                activeTab === 'guidance'
                  ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                  : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
            >
              Mentor Coaching
            </button>
          )}
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {activeTab === 'details' && (
            <div className="space-y-4">
              
              {/* Evidence & Grounded Reason */}
              <div className="p-4 rounded-xl bg-brand-50/60 dark:bg-brand-950/30 border border-brand-200 dark:border-brand-900 space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-bold text-brand-700 dark:text-brand-300 uppercase tracking-wider">
                  <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                  Why This Is Recommended (Fact-Grounded Analysis)
                </div>
                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                  {recommendation.reason}
                </p>
                {recommendation.gap_detail && (
                  <div className="pt-2 border-t border-brand-200/50 dark:border-brand-900/50 text-[11px] text-slate-500 dark:text-slate-400">
                    <strong>Specific Trigger / Gap:</strong> {recommendation.gap_detail}
                  </div>
                )}
              </div>

              {/* Metadata Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-semibold">Suggested Duration</span>
                  <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                    {recommendation.suggested_completion_time || '4 Weeks'}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-semibold">Origin Source</span>
                  <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                    {recommendation.source === 'MENTOR' ? 'Mentor Directed' : 'AI Curriculum Engine'}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-semibold">Target Outcome</span>
                  <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-0.5 truncate">
                    {recommendation.expected_outcome || 'Skill Mastery'}
                  </p>
                </div>
              </div>

              {/* Expected Learning Outcome */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 dark:text-slate-200">
                  <Target className="w-3.5 h-3.5 text-indigo-500" />
                  Expected Competency & Outcome
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  {recommendation.expected_outcome}
                </p>
              </div>

              {/* External Resource Link */}
              {recommendation.resource_url && (
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
                  <div className="text-xs">
                    <span className="font-bold text-slate-800 dark:text-slate-200 block">External Learning Portal</span>
                    <span className="text-slate-400 font-mono text-[10px] truncate max-w-xs block">
                      {recommendation.resource_url}
                    </span>
                  </div>
                  <a
                    href={recommendation.resource_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm transition"
                  >
                    Open Resource
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              )}

              {/* Quick Actions (Accept / Reject) */}
              {recommendation.status === 'SUGGESTED' && !showRejectForm && (
                <div className="flex items-center gap-3 pt-2">
                  <button
                    onClick={handleAccept}
                    disabled={submitting}
                    className="flex-1 py-2.5 rounded-xl font-bold text-xs text-white bg-emerald-600 hover:bg-emerald-700 shadow-sm transition"
                  >
                    Accept into Learning Plan
                  </button>
                  <button
                    onClick={() => setShowRejectForm(true)}
                    className="py-2.5 px-4 rounded-xl font-semibold text-xs text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 transition"
                  >
                    Decline
                  </button>
                </div>
              )}

              {showRejectForm && (
                <form onSubmit={handleReject} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 space-y-3">
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200">Decline Recommendation</span>
                  <input
                    type="text"
                    required
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                    placeholder="Provide reason (e.g., Already completed equivalent coursework, not aligned with current focus)..."
                    className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 outline-none"
                  />
                  <div className="flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setShowRejectForm(false)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-200"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={submitting}
                      className="px-4 py-1.5 rounded-lg text-xs font-bold text-white bg-rose-600 hover:bg-rose-700"
                    >
                      Confirm Decline
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}

          {activeTab === 'progress' && (
            <div className="space-y-5">
              <form onSubmit={handleSaveProgress} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900 dark:text-slate-100">
                    Completion Status: <span className="text-brand-600 font-mono">{percentComplete}%</span>
                  </span>
                  <span className="text-xs text-slate-400">Hours Logged: {hoursSpent} hrs</span>
                </div>

                {/* Progress Range Slider */}
                <div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={percentComplete}
                    onChange={(e) => setPercentComplete(parseInt(e.target.value))}
                    className="w-full accent-brand-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                    <span>0% (Started)</span>
                    <span>50% (Midway)</span>
                    <span>100% (Completed)</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">
                      Hours Dedicated
                    </label>
                    <input
                      type="number"
                      step="0.5"
                      min="0"
                      value={hoursSpent}
                      onChange={(e) => setHoursSpent(parseFloat(e.target.value) || 0)}
                      className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">
                      Current Milestone Status
                    </label>
                    <select
                      value={percentComplete >= 100 ? 'COMPLETED' : 'IN_PROGRESS'}
                      disabled
                      className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                    >
                      <option value="IN_PROGRESS">In Progress</option>
                      <option value="COMPLETED">Completed</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">
                    Learning Notes & Artifacts
                  </label>
                  <textarea
                    rows={3}
                    value={progressNotes}
                    onChange={(e) => setProgressNotes(e.target.value)}
                    placeholder="Document topics finished, practice repository links, or key takeaways..."
                    className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 outline-none"
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 shadow-sm transition"
                  >
                    Save Progress Log
                  </button>
                </div>
              </form>

              {/* Progress History */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider block">
                  Progress History Logs ({recommendation.progress_logs?.length || 0})
                </span>
                {(!recommendation.progress_logs || recommendation.progress_logs.length === 0) ? (
                  <p className="text-xs text-slate-400 italic">No progress logs recorded yet.</p>
                ) : (
                  recommendation.progress_logs.map((log: any) => (
                    <div key={log.id} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-slate-900 dark:text-slate-100">
                          {log.percent_complete}% Complete · {log.hours_spent} Hours
                        </span>
                        <span className="text-[10px] text-slate-400">
                          {new Date(log.created_at).toLocaleString()}
                        </span>
                      </div>
                      {log.notes && <p className="text-slate-600 dark:text-slate-400">{log.notes}</p>}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'feedback' && (
            <form onSubmit={handleSubmitFeedback} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-4">
              <span className="text-xs font-bold text-slate-900 dark:text-slate-100 block">
                Resource Rating & Utility Feedback
              </span>

              {/* Star Rating */}
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1.5">
                  Overall Resource Quality Rating (1 to 5 Stars)
                </label>
                <div className="flex items-center gap-2">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <button
                      type="button"
                      key={s}
                      onClick={() => setRating(s)}
                      className={`p-1.5 rounded-lg transition ${
                        rating >= s ? 'text-amber-500' : 'text-slate-300 dark:text-slate-700'
                      }`}
                    >
                      <Star className="w-6 h-6 fill-current" />
                    </button>
                  ))}
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300 ml-2">
                    {rating} of 5 Stars
                  </span>
                </div>
              </div>

              {/* Helpfulness & Outcome Achieved Toggles */}
              <div className="grid grid-cols-2 gap-3">
                <label className="flex items-center gap-2 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 cursor-pointer text-xs font-semibold text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={helpful}
                    onChange={(e) => setHelpful(e.target.checked)}
                    className="accent-brand-600"
                  />
                  <span>Was this resource helpful?</span>
                </label>

                <label className="flex items-center gap-2 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 cursor-pointer text-xs font-semibold text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={outcomeAchieved}
                    onChange={(e) => setOutcomeAchieved(e.target.checked)}
                    className="accent-brand-600"
                  />
                  <span>Target outcome achieved?</span>
                </label>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">
                  Student Review & Comments
                </label>
                <textarea
                  rows={3}
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder="Share feedback on curriculum relevance, difficulty, or how it helped your exam / interview prep..."
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 outline-none"
                />
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 shadow-sm transition"
                >
                  Submit Review
                </button>
              </div>
            </form>
          )}

          {activeTab === 'guidance' && (
            <div className="space-y-4">
              {recommendation.mentor_guidance_notes && (
                <div className="p-4 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-900 space-y-2">
                  <span className="text-xs font-bold text-indigo-900 dark:text-indigo-200 flex items-center gap-1.5">
                    <UserCheck className="w-4 h-4 text-indigo-600" />
                    Faculty Mentor Coaching Notes
                  </span>
                  <pre className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">
                    {recommendation.mentor_guidance_notes}
                  </pre>
                </div>
              )}

              {(userRole === 'mentor' || userRole === 'faculty' || userRole === 'admin') && (
                <form onSubmit={handleAddGuidance} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-3">
                  <span className="text-xs font-bold text-slate-900 dark:text-slate-100 block">
                    Add Personalized Coaching Guidance
                  </span>
                  <textarea
                    rows={3}
                    required
                    value={mentorGuidance}
                    onChange={(e) => setMentorGuidance(e.target.value)}
                    placeholder="Provide customized tips, specific chapters to focus on, or milestones for Alex..."
                    className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 outline-none"
                  />
                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={submitting}
                      className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm transition"
                    >
                      Save Mentor Guidance
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-xs">
          <span className="text-slate-400">
            Personalized Recommendation Engine · Module 3
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
