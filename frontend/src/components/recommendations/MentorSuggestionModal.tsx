import React, { useState, useEffect } from 'react';
import {
  X,
  Lightbulb,
  Send,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';
import { api } from '../../api/client';

interface MentorSuggestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  studentId?: number;
  studentName?: string;
  onSuccess?: () => void;
}

export const MentorSuggestionModal: React.FC<MentorSuggestionModalProps> = ({
  isOpen,
  onClose,
  studentId,
  studentName,
  onSuccess
}) => {
  const [catalogue, setCatalogue] = useState<any[]>([]);
  const [selectedCatalogueId, setSelectedCatalogueId] = useState<number | ''>('');
  const [useCatalogue, setUseCatalogue] = useState<boolean>(true);

  // Form fields
  const [targetStudentId, setTargetStudentId] = useState<number | ''>(studentId || '');
  const [category, setCategory] = useState<string>('LEARNING_COURSES');
  const [title, setTitle] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [relatedGap, setRelatedGap] = useState<string>('');
  const [expectedOutcome, setExpectedOutcome] = useState<string>('');
  const [priority, setPriority] = useState<string>('MEDIUM');
  const [resourceUrl, setResourceUrl] = useState<string>('');
  const [suggestedTime, setSuggestedTime] = useState<string>('2-4 weeks');
  const [mentorGuidance, setMentorGuidance] = useState<string>('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      if (studentId) setTargetStudentId(studentId);
      loadCatalogue();
      setError(null);
      setSuccess(null);
    }
  }, [isOpen, studentId]);

  const loadCatalogue = async () => {
    try {
      const items = await api.getRecommendationCatalogue();
      setCatalogue(items.filter((item: any) => item.is_active));
    } catch (err: any) {
      console.error('Failed to load catalogue', err);
    }
  };

  const handleCatalogueSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const rawVal = e.target.value;
    if (!rawVal) {
      setSelectedCatalogueId('');
      return;
    }
    const id = parseInt(rawVal, 10);
    setSelectedCatalogueId(id);

    const selected = catalogue.find(c => c.id === id);
    if (selected) {
      setTitle(selected.title);
      setCategory(selected.category);
      setResourceUrl(selected.resource_url || '');
      setExpectedOutcome(selected.description);
      setSuggestedTime(selected.estimated_duration || '2-4 weeks');
      setRelatedGap(`Curated resource for ${selected.required_skill || 'skill enhancement'}`);
      setReason(`Recommended by mentor from certified catalogue based on academic progression review.`);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetStudentId) {
      setError('Please select or specify a student ID');
      return;
    }
    if (!title.trim() || !reason.trim()) {
      setError('Title and justification/reason are required.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await api.suggestMentorRecommendation({
        student_id: Number(targetStudentId),
        catalogue_id: selectedCatalogueId ? Number(selectedCatalogueId) : undefined,
        category,
        title,
        reason,
        related_gap: relatedGap || 'Faculty mentor academic consultation',
        expected_outcome: expectedOutcome || 'Skill enhancement & knowledge mastery',
        priority,
        resource_url: resourceUrl || undefined,
        suggested_completion_time: suggestedTime,
        mentor_guidance: mentorGuidance || undefined
      });

      setSuccess('Recommendation successfully submitted and assigned to student!');
      setTimeout(() => {
        if (onSuccess) onSuccess();
        onClose();
      }, 1200);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to submit suggestion');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-slate-900 dark:to-indigo-950/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-md shadow-indigo-600/20">
              <Lightbulb className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                Suggest Personalized Resource
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-indigo-100 text-indigo-700 dark:bg-indigo-900/60 dark:text-indigo-300">
                  Mentor Coaching
                </span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {studentName ? `For student: ${studentName}` : 'Assign targeted guidance and approved learning materials'}
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
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/40 rounded-xl flex items-center gap-3 text-red-700 dark:text-red-300 text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {success && (
            <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/40 rounded-xl flex items-center gap-3 text-emerald-700 dark:text-emerald-300 text-sm">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
              <span>{success}</span>
            </div>
          )}

          {/* Student ID if not fixed */}
          {!studentId && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
                Student ID *
              </label>
              <input
                type="number"
                value={targetStudentId}
                onChange={(e) => setTargetStudentId(e.target.value ? parseInt(e.target.value, 10) : '')}
                placeholder="ID of student (e.g. 1)"
                required
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          )}

          {/* Source Selection Mode */}
          <div className="flex items-center gap-4 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700">
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">Suggestion Source:</span>
            <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-600 dark:text-slate-300">
              <input
                type="radio"
                checked={useCatalogue}
                onChange={() => setUseCatalogue(true)}
                className="text-indigo-600 focus:ring-indigo-500"
              />
              Select from Approved Catalogue
            </label>
            <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-600 dark:text-slate-300">
              <input
                type="radio"
                checked={!useCatalogue}
                onChange={() => {
                  setUseCatalogue(false);
                  setSelectedCatalogueId('');
                }}
                className="text-indigo-600 focus:ring-indigo-500"
              />
              Custom Academic Guidance
            </label>
          </div>

          {useCatalogue && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
                Approved Resource Catalogue
              </label>
              <select
                value={selectedCatalogueId}
                onChange={handleCatalogueSelect}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">-- Choose verified catalogue resource --</option>
                {catalogue.map((cat: any) => (
                  <option key={cat.id} value={cat.id}>
                    [{cat.category.replace(/_/g, ' ')}] {cat.title} ({cat.difficulty_level})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Title & Category */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
                Resource / Plan Title *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Advanced Operating Systems Lab Prep"
                required
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
                Category *
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="SUBJECT_IMPROVEMENT">Subject Improvement</option>
                <option value="STUDY_RESOURCES">Study Resources</option>
                <option value="LEARNING_COURSES">Learning Courses</option>
                <option value="PROGRAMMING_PRACTICE">Programming Practice</option>
                <option value="TECHNICAL_CERTIFICATIONS">Technical Certifications</option>
                <option value="SOFT_SKILL_DEVELOPMENT">Soft Skill Development</option>
                <option value="EXAMINATION_PREPARATION">Examination Preparation</option>
                <option value="PROJECT_SUGGESTIONS">Project Suggestions</option>
                <option value="INTERNSHIP_PREPARATION">Internship Preparation</option>
                <option value="PLACEMENT_PREPARATION">Placement Preparation</option>
                <option value="HACKATHON_PARTICIPATION">Hackathon Participation</option>
              </select>
            </div>
          </div>

          {/* Reason / Why it is recommended */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
              Why It Is Recommended (Transparent Justification) *
            </label>
            <textarea
              rows={2}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why this student specifically benefits from this action based on observations or records..."
              required
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Related Gap & Expected Outcome */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
                Academic / Skill Gap
              </label>
              <input
                type="text"
                value={relatedGap}
                onChange={(e) => setRelatedGap(e.target.value)}
                placeholder="e.g. Memory Management & Multi-threading"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
                Expected Learning Outcome
              </label>
              <input
                type="text"
                value={expectedOutcome}
                onChange={(e) => setExpectedOutcome(e.target.value)}
                placeholder="e.g. Clears backlog exam with Grade B or higher"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Resource URL, Priority, Suggested Time */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
                Est. Duration
              </label>
              <input
                type="text"
                value={suggestedTime}
                onChange={(e) => setSuggestedTime(e.target.value)}
                placeholder="e.g. 3 weeks, 10 hours"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
                External Resource URL
              </label>
              <input
                type="url"
                value={resourceUrl}
                onChange={(e) => setResourceUrl(e.target.value)}
                placeholder="https://..."
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Mentor Guidance Note */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
              Personalized Mentor Guidance & Instructions
            </label>
            <textarea
              rows={2}
              value={mentorGuidance}
              onChange={(e) => setMentorGuidance(e.target.value)}
              placeholder="Direct coaching advice for the student on how to approach this task..."
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Footer actions */}
          <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 rounded-xl text-sm font-medium border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-md shadow-indigo-600/20 flex items-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Assign Recommendation
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
