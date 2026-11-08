import React, { useState } from 'react';
import { X, Target, Compass, Sparkles, Check } from 'lucide-react';
import { api } from '../../api/client';

interface CareerProfileModalProps {
  studentId: number;
  initialGoals: string[];
  initialInterests: string[];
  isOpen: boolean;
  onClose: () => void;
  onProfileUpdated: () => void;
}

const AVAILABLE_CAREER_GOALS = [
  'Full Stack Developer',
  'AI/ML Engineer',
  'Cloud Architect',
  'Data Engineer',
  'Cybersecurity Analyst',
  'DevOps Engineer',
  'Embedded IoT Specialist',
];

const AVAILABLE_INTERESTS = [
  'Deep Learning',
  'Distributed Systems',
  'Web Performance',
  'Cloud Native',
  'Natural Language Processing',
  'Computer Vision',
  'Ethical Hacking',
  'Competitive Programming',
  'IoT & Robotics',
  'Open Source',
  'Blockchain Architecture',
];

export const CareerProfileModal: React.FC<CareerProfileModalProps> = ({
  studentId,
  initialGoals,
  initialInterests,
  isOpen,
  onClose,
  onProfileUpdated,
}) => {
  if (!isOpen) return null;

  const [selectedGoals, setSelectedGoals] = useState<string[]>(initialGoals || []);
  const [selectedInterests, setSelectedInterests] = useState<string[]>(initialInterests || []);
  const [customGoal, setCustomGoal] = useState('');
  const [customInterest, setCustomInterest] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleGoal = (goal: string) => {
    setSelectedGoals((prev) =>
      prev.includes(goal) ? prev.filter((g) => g !== goal) : [...prev, goal]
    );
  };

  const toggleInterest = (interest: string) => {
    setSelectedInterests((prev) =>
      prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]
    );
  };

  const addCustomGoal = (e: React.FormEvent) => {
    e.preventDefault();
    if (customGoal.trim() && !selectedGoals.includes(customGoal.trim())) {
      setSelectedGoals([...selectedGoals, customGoal.trim()]);
      setCustomGoal('');
    }
  };

  const addCustomInterest = (e: React.FormEvent) => {
    e.preventDefault();
    if (customInterest.trim() && !selectedInterests.includes(customInterest.trim())) {
      setSelectedInterests([...selectedInterests, customInterest.trim()]);
      setCustomInterest('');
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updateStudentCareerProfile(studentId, {
        career_goals: selectedGoals,
        interests: selectedInterests,
      });
      onProfileUpdated();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to update career goals');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl max-h-[85vh] flex flex-col bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-brand-50 dark:bg-brand-950/50 text-brand-600 dark:text-brand-400 border border-brand-100 dark:border-brand-900">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Career Goals & Technical Interests
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Personalize your targets to automatically align learning recommendations.
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

        {error && (
          <div className="px-6 py-2.5 bg-rose-50 text-rose-800 dark:bg-rose-950 dark:text-rose-300 text-xs">
            {error}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* Target Career Roles */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-brand-600" />
                Target Professional Roles
              </label>
              <span className="text-[10px] text-slate-400">Select one or more</span>
            </div>

            <div className="flex flex-wrap gap-2">
              {AVAILABLE_CAREER_GOALS.map((goal) => {
                const isSelected = selectedGoals.includes(goal);
                return (
                  <button
                    key={goal}
                    type="button"
                    onClick={() => toggleGoal(goal)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                      isSelected
                        ? 'bg-brand-600 text-white shadow-sm'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3" />}
                    {goal}
                  </button>
                );
              })}
            </div>

            <form onSubmit={addCustomGoal} className="flex gap-2 pt-1">
              <input
                type="text"
                value={customGoal}
                onChange={(e) => setCustomGoal(e.target.value)}
                placeholder="Or type custom career goal (e.g. SRE)..."
                className="flex-1 text-xs px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 outline-none"
              />
              <button
                type="submit"
                className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200"
              >
                Add
              </button>
            </form>
          </div>

          {/* Technical Interests */}
          <div className="space-y-3 border-t border-slate-200 dark:border-slate-800 pt-5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
                Areas of Technical Interest & Specialization
              </label>
              <span className="text-[10px] text-slate-400">Drives project suggestions</span>
            </div>

            <div className="flex flex-wrap gap-2">
              {AVAILABLE_INTERESTS.map((interest) => {
                const isSelected = selectedInterests.includes(interest);
                return (
                  <button
                    key={interest}
                    type="button"
                    onClick={() => toggleInterest(interest)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                      isSelected
                        ? 'bg-indigo-600 text-white shadow-sm'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3" />}
                    {interest}
                  </button>
                );
              })}
            </div>

            <form onSubmit={addCustomInterest} className="flex gap-2 pt-1">
              <input
                type="text"
                value={customInterest}
                onChange={(e) => setCustomInterest(e.target.value)}
                placeholder="Or type custom interest (e.g. LLMs, AR/VR)..."
                className="flex-1 text-xs px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 outline-none"
              />
              <button
                type="submit"
                className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200"
              >
                Add
              </button>
            </form>
          </div>

        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-xs">
          <span className="text-slate-400 text-[11px]">
            Updating goals immediately regenerates your personalized roadmap.
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-1.5 rounded-lg font-bold text-white bg-brand-600 hover:bg-brand-700 shadow-sm transition disabled:opacity-50"
            >
              {saving ? 'Regenerating Plan...' : 'Save & Refresh Roadmap'}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
