import React, { useState } from 'react';
import {
  X,
  Send,
  Building2,
  Briefcase,
  MapPin,
  Calendar,
  CheckCircle2,
  AlertCircle,
  FileText,
  DollarSign,
  Award
} from 'lucide-react';
import { api } from '../../api/client';

interface ApplyOpportunityModalProps {
  isOpen: boolean;
  onClose: () => void;
  opportunity: any;
  studentId: number;
  readinessScore: number;
  onApplicationSubmitted: () => void;
}

export const ApplyOpportunityModal: React.FC<ApplyOpportunityModalProps> = ({
  isOpen,
  onClose,
  opportunity,
  studentId,
  readinessScore,
  onApplicationSubmitted,
}) => {
  const [resumeUrl, setResumeUrl] = useState<string>('https://campus-drives.edu/resumes/my_resume.pdf');
  const [coverNotes, setCoverNotes] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  if (!isOpen || !opportunity) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.applyToOpportunity({
        opportunity_id: opportunity.id,
        resume_url: resumeUrl.trim() || undefined,
        cover_notes: coverNotes.trim() || undefined,
      });

      setSuccess('Application successfully submitted to the corporate recruitment pipeline!');
      setTimeout(() => {
        onApplicationSubmitted();
        onClose();
      }, 1200);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to submit application');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-900 dark:to-blue-950/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-md shadow-blue-600/20">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Submit Campus Placement Application
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {opportunity.company_name} &bull; {opportunity.title}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/40 rounded-xl flex items-center gap-2 text-red-700 dark:text-red-300 text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {success && (
            <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/40 rounded-xl flex items-center gap-2 text-emerald-700 dark:text-emerald-300 text-xs">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>{success}</span>
            </div>
          )}

          {/* Quick Opportunity Stats */}
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 grid grid-cols-3 gap-2 text-xs">
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">Package / Stipend</span>
              <span className="font-bold text-emerald-600 dark:text-emerald-400">{opportunity.ctc_stipend}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">Location</span>
              <span className="font-medium text-slate-700 dark:text-slate-300">{opportunity.location} ({opportunity.work_mode})</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">Skill Readiness</span>
              <span className="font-bold text-indigo-600 dark:text-indigo-400">{readinessScore}% Match</span>
            </div>
          </div>

          {/* Resume link */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
              Verified Dossier / Resume Link *
            </label>
            <div className="relative">
              <FileText className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="url"
                value={resumeUrl}
                onChange={(e) => setResumeUrl(e.target.value)}
                placeholder="https://..."
                required
                className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Links your verified institutional portfolio, academic SGPA progression, and project matrix.
            </p>
          </div>

          {/* Cover Pitch */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
              Candidate Statement / Pitch
            </label>
            <textarea
              rows={3}
              value={coverNotes}
              onChange={(e) => setCoverNotes(e.target.value)}
              placeholder="Highlight key projects, hackathons, or core competencies that make you an ideal match for this opening..."
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Actions */}
          <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 rounded-xl text-xs font-semibold border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-600/20 flex items-center gap-1.5 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  Confirm Application
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
