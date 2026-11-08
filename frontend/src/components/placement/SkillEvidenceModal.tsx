import React, { useState } from 'react';
import {
  X,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  Link as LinkIcon,
  FileText,
  Github,
  Award,
  Layers,
  Sparkles
} from 'lucide-react';
import { api } from '../../api/client';

interface SkillEvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  studentId: number;
  studentSkillId: number;
  skillName: string;
  onEvidenceSubmitted: () => void;
}

export const SkillEvidenceModal: React.FC<SkillEvidenceModalProps> = ({
  isOpen,
  onClose,
  studentId,
  studentSkillId,
  skillName,
  onEvidenceSubmitted,
}) => {
  const [evidenceType, setEvidenceType] = useState<string>('PROJECT');
  const [title, setTitle] = useState<string>('');
  const [url, setUrl] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Evidence title is required.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await api.submitSkillEvidence(studentId, {
        student_skill_id: studentSkillId,
        evidence_type: evidenceType,
        title: title.trim(),
        url: url.trim() || undefined,
        description: description.trim() || undefined,
      });

      setSuccess('Evidence submitted for faculty & placement officer verification!');
      setTimeout(() => {
        onEvidenceSubmitted();
        onClose();
      }, 1000);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to submit skill evidence');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-gradient-to-r from-teal-50 to-emerald-50 dark:from-slate-900 dark:to-teal-950/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-md shadow-teal-600/20">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Submit Skill Verification Evidence
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Back self-reported <span className="font-semibold text-teal-600 dark:text-teal-400">{skillName}</span> with verified projects or credentials
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

          {/* Evidence Type */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1.5">
              Evidence Type
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'PROJECT', label: 'Course Project', icon: Layers },
                { id: 'GITHUB_REPO', label: 'GitHub Repository', icon: Github },
                { id: 'CERTIFICATION', label: 'Certification', icon: Award },
              ].map(t => {
                const Icon = t.icon;
                const isSel = evidenceType === t.id;
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setEvidenceType(t.id)}
                    className={`p-2.5 rounded-xl border text-xs font-semibold flex flex-col items-center justify-center gap-1.5 transition-all ${
                      isSel
                        ? 'border-teal-500 bg-teal-50 text-teal-700 dark:bg-teal-950/50 dark:text-teal-300'
                        : 'border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{t.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Evidence Title */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
              Title / Project Name *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Distributed Task Queue in Python & Redis"
              required
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-teal-500"
            />
          </div>

          {/* Artifact Link / URL */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
              Artifact Link / Repository URL
            </label>
            <div className="relative">
              <LinkIcon className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://github.com/..."
                className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-teal-500"
              />
            </div>
          </div>

          {/* Implementation Description */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
              Technical Description & Contribution
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Summarize algorithms, architectural patterns, and libraries utilized to demonstrate proficiency..."
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-teal-500"
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
              className="px-5 py-2 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-md shadow-teal-600/20 flex items-center gap-1.5 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <UploadCloud className="w-3.5 h-3.5" />
                  Submit Evidence
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
