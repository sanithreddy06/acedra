import React, { useState, useEffect } from 'react';
import {
  X,
  BookOpen,
  Search,
  ExternalLink,
  Plus,
  Filter,
  CheckCircle2,
  Clock,
  Layers,
  GraduationCap
} from 'lucide-react';
import { api } from '../../api/client';

interface CatalogueBrowserModalProps {
  isOpen: boolean;
  onClose: () => void;
  userRole?: string;
  onSelectResource?: (item: any) => void;
}

const CATEGORIES = [
  'ALL',
  'SUBJECT_IMPROVEMENT',
  'STUDY_RESOURCES',
  'LEARNING_COURSES',
  'PROGRAMMING_PRACTICE',
  'TECHNICAL_CERTIFICATIONS',
  'SOFT_SKILLS',
  'EXAMINATION_PREPARATION',
  'PROJECT_SUGGESTIONS',
  'INTERNSHIP_PREPARATION',
  'PLACEMENT_PREPARATION',
  'HACKATHON_PARTICIPATION',
];

export const CatalogueBrowserModal: React.FC<CatalogueBrowserModalProps> = ({
  isOpen,
  onClose,
  userRole,
  onSelectResource,
}) => {
  if (!isOpen) return null;

  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCat, setSelectedCat] = useState('ALL');
  const [selectedDiff, setSelectedDiff] = useState('');
  const [showAddDrawer, setShowAddDrawer] = useState(false);

  // New Catalogue Item Form
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('LEARNING_COURSES');
  const [description, setDescription] = useState('');
  const [requiredSkill, setRequiredSkill] = useState('');
  const [provider, setProvider] = useState('');
  const [difficulty, setDifficulty] = useState('Intermediate');
  const [duration, setDuration] = useState('4 Weeks');
  const [resourceUrl, setResourceUrl] = useState('');
  const [outcome, setOutcome] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadCatalogue();
  }, [selectedCat, selectedDiff]);

  const loadCatalogue = async () => {
    setLoading(true);
    try {
      const data = await api.getRecommendationCatalogue({
        category: selectedCat === 'ALL' ? undefined : selectedCat,
        difficulty: selectedDiff || undefined,
      });
      setItems(data || []);
    } catch (err) {
      console.error('Failed to load catalogue:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateItem = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.createCatalogueItem({
        title,
        category,
        description,
        required_skill: requiredSkill,
        provider,
        difficulty_level: difficulty,
        estimated_duration: duration,
        resource_url: resourceUrl,
        expected_learning_outcome: outcome,
        status: 'Active',
      });
      setShowAddDrawer(false);
      setTitle('');
      setDescription('');
      setResourceUrl('');
      await loadCatalogue();
    } catch (err) {
      console.error('Failed to create catalogue item:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredItems = items.filter((item) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      item.title?.toLowerCase().includes(q) ||
      item.description?.toLowerCase().includes(q) ||
      item.required_skill?.toLowerCase().includes(q) ||
      item.provider?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-900">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Institutional Recommendation Catalogue
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Approved university, industry, and MOOC learning resources across 11 disciplines.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {(userRole === 'admin' || userRole === 'faculty') && (
              <button
                onClick={() => setShowAddDrawer(!showAddDrawer)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition"
              >
                <Plus className="w-3.5 h-3.5" />
                {showAddDrawer ? 'Close Form' : 'Add Resource'}
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Add Drawer */}
        {showAddDrawer && (
          <form onSubmit={handleCreateItem} className="p-6 bg-slate-50 dark:bg-slate-800/70 border-b border-slate-200 dark:border-slate-800 space-y-4">
            <span className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider block">
              Register New Learning Resource into Catalogue
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2">
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Title *</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Stanford CS229: Machine Learning"
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 outline-none"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 outline-none"
                >
                  {CATEGORIES.filter((c) => c !== 'ALL').map((c) => (
                    <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Skill Linked</label>
                <input
                  type="text"
                  value={requiredSkill}
                  onChange={(e) => setRequiredSkill(e.target.value)}
                  placeholder="e.g. PyTorch"
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 outline-none"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Provider</label>
                <input
                  type="text"
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  placeholder="e.g. Coursera / Stanford"
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 outline-none"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Difficulty</label>
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 outline-none"
                >
                  <option value="Beginner">Beginner</option>
                  <option value="Intermediate">Intermediate</option>
                  <option value="Advanced">Advanced</option>
                </select>
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Duration</label>
                <input
                  type="text"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                  placeholder="e.g. 4 Weeks"
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Resource URL *</label>
              <input
                type="url"
                required
                value={resourceUrl}
                onChange={(e) => setResourceUrl(e.target.value)}
                placeholder="https://..."
                className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 outline-none"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Description & Outcomes</label>
              <textarea
                rows={2}
                required
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Course curriculum summary and prerequisites..."
                className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 outline-none"
              />
            </div>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowAddDrawer(false)}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-1.5 rounded-lg text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition"
              >
                Save Resource
              </button>
            </div>
          </form>
        )}

        {/* Filter Controls */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 space-y-3 bg-white dark:bg-slate-900">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search catalogue by title, skill, or provider..."
                className="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 outline-none"
              />
            </div>

            <select
              value={selectedDiff}
              onChange={(e) => setSelectedDiff(e.target.value)}
              className="text-xs py-1.5 px-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none"
            >
              <option value="">All Difficulties</option>
              <option value="Beginner">Beginner</option>
              <option value="Intermediate">Intermediate</option>
              <option value="Advanced">Advanced</option>
            </select>
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCat(cat)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold whitespace-nowrap transition ${
                  selectedCat === cat
                    ? 'bg-brand-600 text-white'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                {cat === 'ALL' ? 'All Categories' : cat.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Resources Grid */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="text-center py-12 text-xs text-slate-400">Loading learning catalogue...</div>
          ) : filteredItems.length === 0 ? (
            <div className="text-center py-12 text-xs text-slate-400">
              No learning resources found matching your search.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredItems.map((item) => (
                <div
                  key={item.id}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between hover:shadow-md transition"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider">
                        {item.category?.replace(/_/g, ' ')}
                      </span>
                      <span className="px-2 py-0.5 rounded font-semibold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                        {item.difficulty_level}
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 line-clamp-2">
                      {item.title}
                    </h4>

                    <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-3">
                      {item.description}
                    </p>

                    <div className="flex flex-wrap items-center gap-2 pt-2 text-[10px] text-slate-400">
                      {item.provider && <span className="font-medium text-slate-600 dark:text-slate-300">🏢 {item.provider}</span>}
                      {item.estimated_duration && <span>⏱ {item.estimated_duration}</span>}
                      {item.required_skill && <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-mono">⚡ {item.required_skill}</span>}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4 mt-2 border-t border-slate-100 dark:border-slate-800">
                    {item.resource_url ? (
                      <a
                        href={item.resource_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline"
                      >
                        Visit Portal
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-[10px] text-slate-400">Internal Reference</span>
                    )}

                    {onSelectResource && (
                      <button
                        onClick={() => onSelectResource(item)}
                        className="px-3 py-1 rounded-lg text-xs font-bold text-white bg-brand-600 hover:bg-brand-700"
                      >
                        Select Resource
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-xs">
          <span className="text-slate-400">
            Showing {filteredItems.length} of {items.length} approved resources
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg font-semibold text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 transition"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
