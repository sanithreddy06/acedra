import React, { useState, useEffect } from 'react';
import {
  Compass,
  Sparkles,
  BookOpen,
  GraduationCap,
  Briefcase,
  Layers,
  CheckCircle2,
  Clock,
  TrendingUp,
  AlertTriangle,
  ExternalLink,
  Filter,
  Search,
  Plus,
  RefreshCw,
  Award,
  ChevronRight,
  Eye,
  Sliders,
  Check,
  X,
  Target,
  UserCheck,
  HelpCircle
} from 'lucide-react';
import { api } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { RecommendationDetailModal } from './RecommendationDetailModal';
import { CareerProfileModal } from './CareerProfileModal';
import { CatalogueBrowserModal } from './CatalogueBrowserModal';
import { MentorSuggestionModal } from './MentorSuggestionModal';

export const RecommendationsView: React.FC = () => {
  const { user } = useAuth();
  const isStudent = user?.role === 'student';

  // State
  const [learningPath, setLearningPath] = useState<any | null>(null);
  const [studentsList, setStudentsList] = useState<any[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<number>(user?.student_id || 1);
  const [loading, setLoading] = useState<boolean>(true);
  const [regenerating, setRegenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Tabs & Filters
  const [activeTab, setActiveTab] = useState<'ALL' | 'ACADEMIC' | 'CAREER' | 'ACTIVE' | 'COMPLETED'>('ALL');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedPriority, setSelectedPriority] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals state
  const [activeRec, setActiveRec] = useState<any | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);
  const [isCareerModalOpen, setIsCareerModalOpen] = useState<boolean>(false);
  const [isCatalogueModalOpen, setIsCatalogueModalOpen] = useState<boolean>(false);
  const [isMentorModalOpen, setIsMentorModalOpen] = useState<boolean>(false);

  // Initial load
  useEffect(() => {
    initializeView();
  }, [user]);

  const initializeView = async () => {
    setLoading(true);
    setError(null);
    try {
      if (isStudent) {
        const studentId = user?.student_id || 1;
        setSelectedStudentId(studentId);
        await loadStudentLearningPath(studentId);
      } else {
        // Load students list for faculty/mentors/admins to choose from
        const students = await api.getStudents();
        setStudentsList(students);
        if (students.length > 0) {
          const firstId = students[0].id;
          setSelectedStudentId(firstId);
          await loadStudentLearningPath(firstId);
        }
      }
    } catch (err: any) {
      console.error('Failed to initialize recommendations view', err);
      setError('Unable to load student data or recommendations.');
    } finally {
      setLoading(false);
    }
  };

  const loadStudentLearningPath = async (studentId: number) => {
    try {
      const data = await api.getStudentLearningPath(studentId);
      setLearningPath(data);
    } catch (err: any) {
      console.error('Failed to fetch student learning path', err);
      setError('Failed to fetch recommendations.');
    }
  };

  const handleStudentChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const studentId = parseInt(e.target.value, 10);
    setSelectedStudentId(studentId);
    setLoading(true);
    await loadStudentLearningPath(studentId);
    setLoading(false);
  };

  const handleRegenerate = async () => {
    if (!selectedStudentId) return;
    setRegenerating(true);
    try {
      await api.generateRecommendations(selectedStudentId, true);
      await loadStudentLearningPath(selectedStudentId);
    } catch (err: any) {
      console.error('Failed to regenerate recommendations', err);
      alert('Failed to regenerate: ' + (err?.response?.data?.detail || err.message));
    } finally {
      setRegenerating(false);
    }
  };

  const handleQuickAccept = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.acceptRecommendation(id);
      if (selectedStudentId) loadStudentLearningPath(selectedStudentId);
    } catch (err: any) {
      alert('Error accepting recommendation');
    }
  };

  const handleQuickReject = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.rejectRecommendation(id, 'Declined by student');
      if (selectedStudentId) loadStudentLearningPath(selectedStudentId);
    } catch (err: any) {
      alert('Error rejecting recommendation');
    }
  };

  const openDetail = (rec: any) => {
    setActiveRec(rec);
    setIsDetailModalOpen(true);
  };

  // Compile list based on active tab
  const getTabRecommendations = (): any[] => {
    if (!learningPath) return [];
    const all = [
      ...(learningPath.academic_improvement_plan || []),
      ...(learningPath.career_development_plan || [])
    ];

    // Deduplicate in case
    const map = new Map<number, any>();
    all.forEach(item => map.set(item.id, item));
    const unique = Array.from(map.values());

    switch (activeTab) {
      case 'ACADEMIC':
        return learningPath.academic_improvement_plan || [];
      case 'CAREER':
        return learningPath.career_development_plan || [];
      case 'ACTIVE':
        return unique.filter(i => i.status === 'ACCEPTED' || i.status === 'IN_PROGRESS');
      case 'COMPLETED':
        return unique.filter(i => i.status === 'COMPLETED');
      case 'ALL':
      default:
        return unique;
    }
  };

  // Filter recommendations
  const filteredRecommendations = getTabRecommendations().filter(rec => {
    if (selectedCategory !== 'ALL' && rec.category !== selectedCategory) return false;
    if (selectedPriority !== 'ALL' && rec.priority !== selectedPriority) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = rec.title?.toLowerCase().includes(q);
      const matchReason = rec.reason?.toLowerCase().includes(q);
      const matchGap = rec.related_gap?.toLowerCase().includes(q);
      if (!matchTitle && !matchReason && !matchGap) return false;
    }
    return true;
  });

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300 border-red-200 dark:border-red-800/40';
      case 'HIGH':
        return 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border-amber-200 dark:border-amber-800/40';
      case 'MEDIUM':
        return 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800/40';
      case 'LOW':
      default:
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300';
      case 'IN_PROGRESS':
        return 'bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300';
      case 'ACCEPTED':
        return 'bg-purple-100 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300';
      case 'REJECTED':
        return 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300';
      case 'EXPIRED':
        return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400';
      case 'SUGGESTED':
      default:
        return 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300';
    }
  };

  const formatCategory = (cat: string) => {
    return (cat || '').replace(/_/g, ' ');
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Top Banner & Header */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-indigo-500/10 via-purple-500/5 to-transparent rounded-full -mr-20 -mt-20 pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center shadow-md shadow-indigo-500/20">
                <Compass className="w-5 h-5" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Personalized Recommendation Engine
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/40">
                Module 3 Grounded
              </span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-2xl">
              Transparent, rule-based recommendations tailored to individual student performance, verified gaps, and aspirations. Split into Academic Improvement and Career Development plans.
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={() => setIsCatalogueModalOpen(true)}
              className="px-3.5 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/60 transition-colors flex items-center gap-2 shadow-sm"
            >
              <BookOpen className="w-4 h-4 text-indigo-500" />
              Resource Catalogue
            </button>

            {isStudent && (
              <button
                onClick={() => setIsCareerModalOpen(true)}
                className="px-3.5 py-2 text-xs font-semibold rounded-xl border border-indigo-200 dark:border-indigo-800/50 bg-indigo-50/50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100/50 transition-colors flex items-center gap-2 shadow-sm"
              >
                <Target className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                Edit Career Goals
              </button>
            )}

            {!isStudent && (
              <button
                onClick={() => setIsMentorModalOpen(true)}
                className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-purple-600 hover:bg-purple-700 text-white transition-colors flex items-center gap-2 shadow-sm shadow-purple-600/20"
              >
                <Plus className="w-4 h-4" />
                Suggest Resource
              </button>
            )}

            <button
              onClick={handleRegenerate}
              disabled={regenerating || !selectedStudentId}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white transition-colors flex items-center gap-2 shadow-sm shadow-indigo-600/20 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${regenerating ? 'animate-spin' : ''}`} />
              {regenerating ? 'Regenerating...' : 'Evaluate & Refresh'}
            </button>
          </div>
        </div>

        {/* Multi-student selector for Staff / Mentors / Admins */}
        {!isStudent && studentsList.length > 0 && (
          <div className="mt-6 pt-5 border-t border-slate-100 dark:border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <UserCheck className="w-4 h-4 text-indigo-500" />
                Select Student Context:
              </label>
              <select
                value={selectedStudentId}
                onChange={handleStudentChange}
                className="px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              >
                {studentsList.map((s: any) => (
                  <option key={s.id} value={s.id}>
                    {s.first_name} {s.last_name} ({s.srn}) — Sem {s.semester} {s.department_code || ''}
                  </option>
                ))}
              </select>
            </div>

            {learningPath && (
              <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                <span>Selected:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {learningPath.student_name}
                </span>
                <span>({learningPath.srn})</span>
                <span className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono text-[11px]">
                  Sem {learningPath.semester}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Current Career Goal & Interests Bar */}
        {learningPath && (
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold text-slate-600 dark:text-slate-400">Target Career:</span>
              {learningPath.career_goals && learningPath.career_goals.length > 0 ? (
                learningPath.career_goals.map((g: any, idx: number) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-lg font-medium bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/40 flex items-center gap-1.5"
                  >
                    <Briefcase className="w-3.5 h-3.5" />
                    {String(g)}
                  </span>
                ))
              ) : (
                <span className="text-slate-400 italic">No career goal set (Default: General Engineering)</span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-1.5">
              <span className="font-semibold text-slate-600 dark:text-slate-400">Key Interests:</span>
              {learningPath.interests && learningPath.interests.length > 0 ? (
                learningPath.interests.map((int: any, idx: number) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-[11px]"
                  >
                    #{String(int)}
                  </span>
                ))
              ) : (
                <span className="text-slate-400 italic">No tags</span>
              )}
              {isStudent && (
                <button
                  onClick={() => setIsCareerModalOpen(true)}
                  className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium ml-1"
                >
                  Change
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* KPI Cards */}
      {learningPath && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Total Roadmap</span>
              <Compass className="w-4 h-4 text-indigo-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {learningPath.total_recommendations || 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Grounded recommendation items</p>
          </div>

          <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Academic Plan</span>
              <GraduationCap className="w-4 h-4 text-amber-500" />
            </div>
            <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
              {learningPath.academic_improvement_plan?.length || 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Remedial, CIA & exam prep</p>
          </div>

          <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Career Plan</span>
              <Briefcase className="w-4 h-4 text-indigo-500" />
            </div>
            <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
              {learningPath.career_development_plan?.length || 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Skills, certs & placement tracks</p>
          </div>

          <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">In Progress / Done</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              {
                [...(learningPath.academic_improvement_plan || []), ...(learningPath.career_development_plan || [])].filter(
                  i => i.status === 'IN_PROGRESS' || i.status === 'COMPLETED'
                ).length
              }
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Active student engagement</p>
          </div>
        </div>
      )}

      {/* Tabs and Controls */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Main Navigation Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0">
            <button
              onClick={() => setActiveTab('ALL')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-2 ${
                activeTab === 'ALL'
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/20'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <Compass className="w-3.5 h-3.5" />
              All Recommendations ({learningPath?.total_recommendations || 0})
            </button>
            <button
              onClick={() => setActiveTab('ACADEMIC')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-2 ${
                activeTab === 'ACADEMIC'
                  ? 'bg-amber-600 text-white shadow-sm shadow-amber-600/20'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <GraduationCap className="w-3.5 h-3.5" />
              Academic Improvement Plan ({learningPath?.academic_improvement_plan?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('CAREER')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-2 ${
                activeTab === 'CAREER'
                  ? 'bg-purple-600 text-white shadow-sm shadow-purple-600/20'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <Briefcase className="w-3.5 h-3.5" />
              Career Development Plan ({learningPath?.career_development_plan?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('ACTIVE')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-2 ${
                activeTab === 'ACTIVE'
                  ? 'bg-sky-600 text-white shadow-sm shadow-sky-600/20'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              Accepted / In Progress
            </button>
            <button
              onClick={() => setActiveTab('COMPLETED')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-2 ${
                activeTab === 'COMPLETED'
                  ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-600/20'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              Completed
            </button>
          </div>

          {/* Search bar */}
          <div className="relative min-w-[240px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search title, gap or skill..."
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Secondary filters row */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-400">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-medium flex items-center gap-1">
              <Filter className="w-3.5 h-3.5 text-indigo-500" /> Filter by:
            </span>

            {/* Category filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200"
            >
              <option value="ALL">All 11 Categories</option>
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

            {/* Priority filter */}
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200"
            >
              <option value="ALL">All Priorities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          <div className="text-slate-400">
            Showing <span className="font-semibold text-slate-700 dark:text-slate-200">{filteredRecommendations.length}</span> recommendations
          </div>
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="py-20 flex flex-col items-center justify-center text-slate-400">
          <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-sm font-medium">Generating verified student learning roadmap...</p>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="p-6 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/40 rounded-2xl text-center">
          <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-2" />
          <h3 className="text-base font-semibold text-red-800 dark:text-red-300">
            Error loading recommendations
          </h3>
          <p className="text-xs text-red-600 dark:text-red-400 mt-1">{error}</p>
          <button
            onClick={initializeView}
            className="mt-4 px-4 py-1.5 text-xs font-semibold rounded-lg bg-red-600 text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && filteredRecommendations.length === 0 && (
        <div className="p-12 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 text-center shadow-sm">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mx-auto mb-3">
            <Sparkles className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200">
            No Recommendations Matching Current Filters
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto mt-1">
            Try resetting your category or priority filters, or click "Evaluate & Refresh" to run rule evaluation against this student's latest records.
          </p>
          <button
            onClick={handleRegenerate}
            className="mt-4 px-4 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white inline-flex items-center gap-2"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Evaluate Recommendations
          </button>
        </div>
      )}

      {/* Cards Grid */}
      {!loading && !error && filteredRecommendations.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredRecommendations.map((rec: any) => {
            const progressPercent = rec.latest_progress || (rec.status === 'COMPLETED' ? 100 : 0);

            return (
              <div
                key={rec.id}
                onClick={() => openDetail(rec)}
                className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm hover:shadow-md hover:border-indigo-300 dark:hover:border-indigo-700 transition-all cursor-pointer flex flex-col justify-between group relative overflow-hidden"
              >
                {/* Top badges */}
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase border ${getPriorityBadge(rec.priority)}`}>
                        {rec.priority}
                      </span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                        {formatCategory(rec.category)}
                      </span>
                      {rec.source === 'MENTOR' && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-100 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300">
                          Mentor Pick
                        </span>
                      )}
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${getStatusBadge(rec.status)}`}>
                      {(rec.status || '').replace(/_/g, ' ')}
                    </span>
                  </div>

                  {/* Title */}
                  <h3 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2 mb-2">
                    {rec.title}
                  </h3>

                  {/* Grounded Reason (Transparent rationale) */}
                  <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 mb-3 text-xs text-slate-600 dark:text-slate-300">
                    <span className="font-semibold text-slate-800 dark:text-slate-200 block mb-0.5">
                      Why Recommended:
                    </span>
                    <p className="line-clamp-2 leading-relaxed">{rec.reason}</p>
                  </div>

                  {/* Gaps and outcomes */}
                  <div className="space-y-1.5 text-xs text-slate-500 dark:text-slate-400 mb-4">
                    {rec.related_gap && (
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-slate-700 dark:text-slate-300">Target Gap:</span>
                        <span className="truncate text-slate-600 dark:text-slate-400 font-mono text-[11px]">
                          {rec.related_gap}
                        </span>
                      </div>
                    )}
                    {rec.suggested_completion_time && (
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>Est. Duration: {rec.suggested_completion_time}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Footer: Progress / Action buttons */}
                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 space-y-3">
                  {(rec.status === 'ACCEPTED' || rec.status === 'IN_PROGRESS' || rec.status === 'COMPLETED') && (
                    <div>
                      <div className="flex justify-between items-center text-[11px] mb-1">
                        <span className="font-medium text-slate-600 dark:text-slate-400">Progress</span>
                        <span className="font-bold text-indigo-600 dark:text-indigo-400">{progressPercent}%</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-indigo-600 rounded-full transition-all duration-300"
                          style={{ width: `${progressPercent}%` }}
                        />
                      </div>
                    </div>
                  )}

                  <div className="flex items-center justify-between gap-2">
                    {rec.resource_url ? (
                      <a
                        href={rec.resource_url}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
                      >
                        Access Resource
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    ) : (
                      <span className="text-[11px] text-slate-400">Curated Plan</span>
                    )}

                    {/* Quick Accept/Reject if SUGGESTED and Student */}
                    {isStudent && rec.status === 'SUGGESTED' ? (
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={(e) => handleQuickReject(rec.id, e)}
                          title="Decline"
                          className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-500 hover:text-rose-600 hover:border-rose-300 dark:hover:border-rose-800 transition-colors"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={(e) => handleQuickAccept(rec.id, e)}
                          className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition-colors flex items-center gap-1 shadow-sm shadow-indigo-600/20"
                        >
                          <Check className="w-3.5 h-3.5" />
                          Accept
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => openDetail(rec)}
                        className="text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 flex items-center gap-1"
                      >
                        Details
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* MODALS */}
      {/* 1. Detail & Progress & Feedback Modal */}
      {activeRec && (
        <RecommendationDetailModal
          isOpen={isDetailModalOpen}
          onClose={() => {
            setIsDetailModalOpen(false);
            setActiveRec(null);
          }}
          recommendation={activeRec}
          userRole={user?.role}
          onUpdated={() => {
            if (selectedStudentId) loadStudentLearningPath(selectedStudentId);
          }}
        />
      )}

      {/* 2. Career Profile Goal & Interest Modal */}
      <CareerProfileModal
        isOpen={isCareerModalOpen}
        onClose={() => setIsCareerModalOpen(false)}
        studentId={selectedStudentId}
        initialGoals={learningPath?.career_goals || []}
        initialInterests={learningPath?.interests || []}
        onProfileUpdated={async () => {
          if (selectedStudentId) {
            await handleRegenerate();
          }
        }}
      />

      {/* 3. Catalogue Browser Modal */}
      <CatalogueBrowserModal
        isOpen={isCatalogueModalOpen}
        onClose={() => setIsCatalogueModalOpen(false)}
      />

      {/* 4. Mentor Suggestion Modal */}
      <MentorSuggestionModal
        isOpen={isMentorModalOpen}
        onClose={() => setIsMentorModalOpen(false)}
        studentId={selectedStudentId}
        studentName={learningPath?.student_name}
        onSuccess={() => {
          if (selectedStudentId) loadStudentLearningPath(selectedStudentId);
        }}
      />
    </div>
  );
};
