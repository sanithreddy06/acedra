import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  PlusCircle,
  Search,
  Filter,
  AlertTriangle,
  Calendar,
  Clock,
  User,
  CheckCircle2,
  ChevronRight,
  BookOpen,
  ArrowUpRight,
  Activity
} from 'lucide-react';
import { api } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { InterventionDetailModal } from './InterventionDetailModal';

export const InterventionHub: React.FC = () => {
  const { user } = useAuth();
  const [interventions, setInterventions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Selected intervention for Detail Modal
  const [selectedInterventionId, setSelectedInterventionId] = useState<number | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);

  // Create Intervention Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [createStudentId, setCreateStudentId] = useState<number>(1);
  const [createTitle, setCreateTitle] = useState<string>('');
  const [createType, setCreateType] = useState<string>('ACADEMIC_REMEDIAL');
  const [createPriority, setCreatePriority] = useState<string>('HIGH');
  const [createNotes, setCreateNotes] = useState<string>('');
  const [createTargetDate, setCreateTargetDate] = useState<string>('');
  const [isCreating, setIsCreating] = useState<boolean>(false);

  const loadInterventions = async () => {
    setIsLoading(true);
    try {
      const params: Record<string, any> = {};
      if (statusFilter) params.status = statusFilter;
      if (priorityFilter) params.priority = priorityFilter;
      const res = await api.getInterventions(params);
      setInterventions(res || []);
    } catch {
      setInterventions([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadInterventions();
  }, [statusFilter, priorityFilter]);

  const handleOpenDetail = (id: number) => {
    setSelectedInterventionId(id);
    setIsDetailModalOpen(true);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createTitle.trim()) return;
    setIsCreating(true);
    try {
      await api.createIntervention({
        student_id: createStudentId,
        title: createTitle.trim(),
        intervention_type: createType,
        priority: createPriority,
        initial_notes: createNotes.trim() || undefined,
        target_resolution_date: createTargetDate || undefined,
      });
      setIsCreateModalOpen(false);
      setCreateTitle('');
      setCreateNotes('');
      setCreateTargetDate('');
      await loadInterventions();
    } catch (err: any) {
      alert(err.message || 'Failed to create intervention case');
    } finally {
      setIsCreating(false);
    }
  };

  const filteredInterventions = interventions.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.title?.toLowerCase().includes(q) ||
      item.student_name?.toLowerCase().includes(q) ||
      item.student_usn?.toLowerCase().includes(q) ||
      item.mentor_name?.toLowerCase().includes(q)
    );
  });

  const activeCount = interventions.filter((i) => ['OPEN', 'ASSIGNED', 'IN_PROGRESS'].includes(i.status)).length;
  const highPriorityCount = interventions.filter((i) => ['HIGH', 'URGENT'].includes(i.priority)).length;
  const resolvedCount = interventions.filter((i) => ['RESOLVED', 'CLOSED'].includes(i.status)).length;

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-brand-700 via-indigo-700 to-slate-900 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-brand-200">
              Module 6 &bull; Intervention & Mentorship Central
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight mt-1">
            Student Support & Action Plans
          </h1>
          <p className="text-xs text-brand-100 max-w-2xl mt-1">
            End-to-end multi-tier intervention tracking: schedule 1-on-1 counseling, log auditable clinical observations, coordinate parent communications, and measure academic recovery.
          </p>
        </div>

        {user?.role !== 'student' && (
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-5 py-2.5 rounded-2xl bg-white text-brand-700 hover:bg-brand-50 font-bold text-xs shadow-md flex items-center space-x-2 transition"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Initiate Support Case</span>
          </button>
        )}
      </div>

      {/* KPI Counters Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-400">Total Cases</span>
            <div className="text-2xl font-extrabold text-slate-900 dark:text-white mt-0.5">{interventions.length}</div>
          </div>
          <div className="p-3 bg-brand-50 dark:bg-brand-950/50 text-brand-600 rounded-2xl">
            <BookOpen className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-400">Active / In Progress</span>
            <div className="text-2xl font-extrabold text-amber-600 dark:text-amber-400 mt-0.5">{activeCount}</div>
          </div>
          <div className="p-3 bg-amber-50 dark:bg-amber-950/50 text-amber-600 rounded-2xl">
            <Activity className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-400">High / Urgent Priority</span>
            <div className="text-2xl font-extrabold text-rose-600 dark:text-rose-400 mt-0.5">{highPriorityCount}</div>
          </div>
          <div className="p-3 bg-rose-50 dark:bg-rose-950/50 text-rose-600 rounded-2xl">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-400">Successfully Resolved</span>
            <div className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-0.5">{resolvedCount}</div>
          </div>
          <div className="p-3 bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 rounded-2xl">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search student, USN, mentor or topic..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-900 dark:text-slate-100"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-200"
          >
            <option value="">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-200"
          >
            <option value="">All Priorities</option>
            <option value="URGENT">Urgent</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      {/* Interventions Roster */}
      {isLoading ? (
        <LoadingSpinner label="Querying intervention records..." />
      ) : filteredInterventions.length === 0 ? (
        <div className="p-12 text-center rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-400">
          <ShieldCheck className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">No matching interventions found</h3>
          <p className="text-xs text-slate-500 mt-1">Adjust filters or create a new student support case.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredInterventions.map((it) => (
            <div
              key={it.id}
              onClick={() => handleOpenDetail(it.id)}
              className="p-5 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-brand-500 dark:hover:border-brand-500 hover:shadow-lg transition cursor-pointer flex flex-col justify-between group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Badge
                    variant={
                      it.priority === 'HIGH' || it.priority === 'URGENT'
                        ? 'danger'
                        : it.priority === 'MEDIUM'
                        ? 'warning'
                        : 'slate'
                    }
                    size="sm"
                  >
                    {it.priority} Priority
                  </Badge>
                  <Badge
                    variant={
                      it.status === 'RESOLVED' || it.status === 'CLOSED'
                        ? 'success'
                        : it.status === 'IN_PROGRESS'
                        ? 'brand'
                        : 'slate'
                    }
                    size="sm"
                  >
                    {it.status}
                  </Badge>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-brand-600 dark:group-hover:text-brand-400 transition line-clamp-2">
                    {it.title}
                  </h3>
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider block mt-0.5">
                    {it.intervention_type?.replace(/_/g, ' ')}
                  </span>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Student:</span>
                    <strong className="text-slate-800 dark:text-slate-200">{it.student_name}</strong>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">USN & Dept:</span>
                    <span className="text-slate-600 dark:text-slate-400">{it.student_usn} &bull; {it.student_department || 'CSE'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Assigned Mentor:</span>
                    <span className="font-semibold text-brand-600 dark:text-brand-400">{it.mentor_name || 'Unassigned'}</span>
                  </div>
                </div>

                {it.initial_notes && (
                  <p className="text-xs text-slate-500 line-clamp-2 italic">
                    "{it.initial_notes}"
                  </p>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span>{it.notes_count || 0} notes &bull; {it.followups_count || 0} followups</span>
                <span className="font-semibold text-brand-600 group-hover:translate-x-1 transition flex items-center">
                  Open Dossier <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Intervention Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden">
            <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/30">
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center">
                <PlusCircle className="w-5 h-5 mr-2 text-brand-600" />
                Initiate Student Intervention Plan
              </h2>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-semibold"
              >
                Cancel
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="p-6 space-y-4 text-xs">
              <div>
                <label className="block text-slate-500 mb-1 font-medium">Target Student ID</label>
                <input
                  type="number"
                  required
                  min={1}
                  value={createStudentId}
                  onChange={(e) => setCreateStudentId(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-500 mb-1 font-medium">Case Title / Focus</label>
                <input
                  type="text"
                  required
                  placeholder="E.g., Operating Systems Remedial Tutoring & Lab Support"
                  value={createTitle}
                  onChange={(e) => setCreateTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-500 mb-1 font-medium">Intervention Type</label>
                  <select
                    value={createType}
                    onChange={(e) => setCreateType(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs"
                  >
                    <option value="ACADEMIC_REMEDIAL">ACADEMIC_REMEDIAL</option>
                    <option value="ATTENDANCE_CONDONATION_COUNSELING">ATTENDANCE_CONDONATION_COUNSELING</option>
                    <option value="CAREER_SKILL_COACHING">CAREER_SKILL_COACHING</option>
                    <option value="EXAM_PREPARATION_SUPPORT">EXAM_PREPARATION_SUPPORT</option>
                    <option value="PARENT_TEACHER_CONFERENCE">PARENT_TEACHER_CONFERENCE</option>
                    <option value="WELLNESS_COUNSELING">WELLNESS_COUNSELING</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-500 mb-1 font-medium">Priority Level</label>
                  <select
                    value={createPriority}
                    onChange={(e) => setCreatePriority(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs"
                  >
                    <option value="URGENT">URGENT</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-500 mb-1 font-medium">Target Resolution Date</label>
                <input
                  type="date"
                  value={createTargetDate}
                  onChange={(e) => setCreateTargetDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-500 mb-1 font-medium">Initial Diagnosis / Notes</label>
                <textarea
                  rows={3}
                  value={createNotes}
                  onChange={(e) => setCreateNotes(e.target.value)}
                  placeholder="Observed risk factors, mid-term results, faculty referral notes..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-500 text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreating}
                  className="px-5 py-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-xl text-xs transition shadow-sm"
                >
                  {isCreating ? 'Creating Case...' : 'Create Intervention Case'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Intervention Detail Modal */}
      <InterventionDetailModal
        interventionId={selectedInterventionId}
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false);
          setSelectedInterventionId(null);
        }}
        onUpdated={loadInterventions}
        userRole={user?.role}
      />
    </div>
  );
};
