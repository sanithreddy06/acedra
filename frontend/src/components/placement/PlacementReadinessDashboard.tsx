import React, { useState, useEffect } from 'react';
import {
  Compass,
  Award,
  Briefcase,
  Building2,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ChevronRight,
  ExternalLink,
  Plus,
  Search,
  Filter,
  Check,
  X,
  Clock,
  Sparkles,
  TrendingUp,
  FileText,
  UploadCloud,
  ShieldCheck,
  ShieldAlert,
  UserCheck,
  Info
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { api } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { SkillEvidenceModal } from './SkillEvidenceModal';
import { ApplyOpportunityModal } from './ApplyOpportunityModal';

export const PlacementReadinessDashboard: React.FC = () => {
  const { user } = useAuth();
  const isStudent = user?.role === 'student';
  const isPlacementOfficer = user?.role === 'placement_officer';

  // State
  const [studentId, setStudentId] = useState<number>(user?.student_id || 1);
  const [studentsList, setStudentsList] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [selectedRoleCode, setSelectedRoleCode] = useState<string>('SOFTWARE_DEVELOPER');
  const [readinessData, setReadinessData] = useState<any | null>(null);
  const [matchingOpps, setMatchingOpps] = useState<any[]>([]);
  const [applications, setApplications] = useState<any[]>([]);
  const [studentSkills, setStudentSkills] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'SKILL_GAP' | 'PROFICIENCY_CHART' | 'MATCHING_OPPS' | 'APPLICATIONS' | 'EVIDENCES'>('SKILL_GAP');

  // Modals state
  const [isEvidenceModalOpen, setIsEvidenceModalOpen] = useState<boolean>(false);
  const [selectedSkillForEvidence, setSelectedSkillForEvidence] = useState<{ id: number; name: string } | null>(null);
  const [isApplyModalOpen, setIsApplyModalOpen] = useState<boolean>(false);
  const [selectedOppForApply, setSelectedOppForApply] = useState<any | null>(null);

  // Add skill inline modal
  const [isAddSkillModalOpen, setIsAddSkillModalOpen] = useState<boolean>(false);
  const [newSkillName, setNewSkillName] = useState<string>('');
  const [newSkillCategory, setNewSkillCategory] = useState<string>('programming');
  const [newSkillProficiency, setNewSkillProficiency] = useState<string>('Intermediate');

  useEffect(() => {
    initializeDashboard();
  }, [user]);

  useEffect(() => {
    if (studentId) {
      loadReadinessAndMatches(studentId, selectedRoleCode);
    }
  }, [studentId, selectedRoleCode]);

  const initializeDashboard = async () => {
    setLoading(true);
    try {
      const [rolesRes] = await Promise.all([
        api.getCareerRoles(),
      ]);
      setRoles(rolesRes);
      if (rolesRes.length > 0 && !selectedRoleCode) {
        setSelectedRoleCode(rolesRes[0].code);
      }

      if (!isStudent) {
        const students = await api.getStudents();
        setStudentsList(students);
        if (students.length > 0) {
          setStudentId(students[0].id);
        }
      }
    } catch (err: any) {
      console.error('Failed to initialize dashboard', err);
    } finally {
      setLoading(false);
    }
  };

  const loadReadinessAndMatches = async (sId: number, rCode: string) => {
    try {
      const [readinessRes, oppsRes, appsRes, skillsRes] = await Promise.all([
        api.getPlacementReadiness(sId, rCode),
        api.getStudentMatchingOpportunities(sId),
        api.getPlacementApplications({ student_id: sId }),
        api.getStudentPlacementSkills(sId),
      ]);
      setReadinessData(readinessRes);
      setMatchingOpps(oppsRes);
      setApplications(appsRes);
      setStudentSkills(skillsRes);
    } catch (err: any) {
      console.error('Failed to fetch readiness data', err);
    }
  };

  const handleAddSkillSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSkillName.trim()) return;
    try {
      await api.addOrUpdateStudentPlacementSkill(studentId, {
        skill_name: newSkillName.trim(),
        category: newSkillCategory,
        proficiency_level: newSkillProficiency,
      });
      setIsAddSkillModalOpen(false);
      setNewSkillName('');
      loadReadinessAndMatches(studentId, selectedRoleCode);
    } catch (err: any) {
      alert('Failed to add skill: ' + (err?.response?.data?.detail || err.message));
    }
  };

  const openEvidenceModal = (sId: number, sName: string) => {
    setSelectedSkillForEvidence({ id: sId, name: sName });
    setIsEvidenceModalOpen(true);
  };

  const openApplyModal = (opp: any) => {
    setSelectedOppForApply(opp);
    setIsApplyModalOpen(true);
  };

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'READY':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800';
      case 'NEAR_READY':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-950/80 dark:text-blue-300 border-blue-300 dark:border-blue-800';
      case 'DEVELOPING':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300 border-amber-300 dark:border-amber-800';
      case 'EARLY_STAGE':
      default:
        return 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300 border-rose-300 dark:border-rose-800';
    }
  };

  // Prepare chart comparison data
  const chartData = (readinessData?.skill_gaps || []).map((g: any) => ({
    skill: g.skill_name,
    studentLevel: g.student_level_val,
    requiredLevel: g.required_level_val,
  }));

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Top Banner & Header */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-blue-500/10 via-teal-500/5 to-transparent rounded-full -mr-20 -mt-20 pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-teal-500 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
                <Briefcase className="w-5 h-5" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Skill Gap & Placement Readiness Hub
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200 dark:border-blue-800/40">
                Module 4 Active
              </span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-3xl">
              Compare verified and self-reported competencies against corporate career role benchmarks. Identify missing skills, submit verifiable artifacts, and match with active campus placement drives.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsAddSkillModalOpen(true)}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-1.5 shadow-md shadow-teal-600/20"
            >
              <Plus className="w-4 h-4" />
              Add Skill & Evidence
            </button>
          </div>
        </div>

        {/* Prototype Indicator Disclaimer */}
        <div className="mt-4 p-3 rounded-xl bg-amber-50/80 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40 flex items-center gap-2.5 text-xs text-amber-800 dark:text-amber-300">
          <Info className="w-4 h-4 flex-shrink-0 text-amber-600 dark:text-amber-400" />
          <span>
            <strong>Disclaimer:</strong> {readinessData?.disclaimer || 'Internal prototype readiness indicator. Does not guarantee corporate hiring or selection.'}
          </span>
        </div>

        {/* Multi-student selector for Staff / Placement Officers */}
        {!isStudent && studentsList.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center gap-3 text-xs">
            <label className="font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <UserCheck className="w-4 h-4 text-blue-600" />
              Reviewing Student:
            </label>
            <select
              value={studentId}
              onChange={(e) => setStudentId(parseInt(e.target.value, 10))}
              className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
            >
              {studentsList.map(s => (
                <option key={s.id} value={s.id}>
                  {s.first_name} {s.last_name} ({s.srn}) &bull; Sem {s.semester} {s.department_code || ''}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Career Role Comparison Bar */}
        <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-800">
          <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-2">
            Target Career Role Benchmark:
          </span>
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {roles.map(r => {
              const isSelected = selectedRoleCode === r.code;
              return (
                <button
                  key={r.id}
                  onClick={() => setSelectedRoleCode(r.code)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all border ${
                    isSelected
                      ? 'bg-blue-600 text-white border-blue-600 shadow-sm shadow-blue-600/20'
                      : 'bg-slate-50 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700'
                  }`}
                >
                  {r.title}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* KPI Stats Cards */}
      {readinessData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-between justify-between text-slate-500 dark:text-slate-400 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider">Placement Readiness</span>
              <Award className="w-4 h-4 text-blue-500" />
            </div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-3xl font-bold text-blue-600 dark:text-blue-400 font-mono">
                {readinessData.readiness_score}%
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getTierBadge(readinessData.readiness_tier)}`}>
                {readinessData.readiness_tier}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Weighted competency score</p>
          </div>

          <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-between justify-between text-slate-500 dark:text-slate-400 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider">Skill Coverage</span>
              <Layers className="w-4 h-4 text-teal-500" />
            </div>
            <div className="text-3xl font-bold text-teal-600 dark:text-teal-400 font-mono mt-1">
              {readinessData.skill_coverage_percentage}%
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              {readinessData.skills_matched_count} of {readinessData.total_role_skills_count} role skills matched
            </p>
          </div>

          <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-between justify-between text-slate-500 dark:text-slate-400 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider">Mandatory Skills</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="flex items-center gap-1.5 mt-2">
              {readinessData.mandatory_skills_met ? (
                <>
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  <span className="text-base font-bold text-emerald-600 dark:text-emerald-400">All Benchmarks Met</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-5 h-5 text-amber-500" />
                  <span className="text-base font-bold text-amber-600 dark:text-amber-400">Core Deficits Pending</span>
                </>
              )}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Prerequisite core competencies</p>
          </div>

          <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-between justify-between text-slate-500 dark:text-slate-400 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider">Active Applications</span>
              <Briefcase className="w-4 h-4 text-purple-500" />
            </div>
            <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 font-mono mt-1">
              {applications.length}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Campus drive pipelines</p>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-3 border border-slate-200 dark:border-slate-800 flex items-center gap-2 overflow-x-auto shadow-sm">
        <button
          onClick={() => setActiveTab('SKILL_GAP')}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap flex items-center gap-1.5 transition-colors ${
            activeTab === 'SKILL_GAP'
              ? 'bg-blue-600 text-white'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Skill Gap Analysis ({readinessData?.skill_gaps?.length || 0})
        </button>

        <button
          onClick={() => setActiveTab('PROFICIENCY_CHART')}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap flex items-center gap-1.5 transition-colors ${
            activeTab === 'PROFICIENCY_CHART'
              ? 'bg-blue-600 text-white'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <TrendingUp className="w-3.5 h-3.5" />
          Benchmark Comparison Chart
        </button>

        <button
          onClick={() => setActiveTab('MATCHING_OPPS')}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap flex items-center gap-1.5 transition-colors ${
            activeTab === 'MATCHING_OPPS'
              ? 'bg-blue-600 text-white'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          Matching Corporate Opportunities ({matchingOpps.length})
        </button>

        <button
          onClick={() => setActiveTab('APPLICATIONS')}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap flex items-center gap-1.5 transition-colors ${
            activeTab === 'APPLICATIONS'
              ? 'bg-blue-600 text-white'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Briefcase className="w-3.5 h-3.5" />
          Application Tracking ({applications.length})
        </button>

        <button
          onClick={() => setActiveTab('EVIDENCES')}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap flex items-center gap-1.5 transition-colors ${
            activeTab === 'EVIDENCES'
              ? 'bg-blue-600 text-white'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          My Verified Skills & Artifacts ({studentSkills.length})
        </button>
      </div>

      {/* Tab 1: Skill Gap Analysis Grid */}
      {activeTab === 'SKILL_GAP' && readinessData && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {readinessData.skill_gaps.map((item: any, idx: number) => {
              const isMatched = item.status === 'MATCHED';
              const isBelow = item.status === 'BELOW_PROFICIENCY';
              const isMissing = item.status === 'MISSING';
              const isUnverified = item.status === 'REQUIRES_VERIFICATION';

              return (
                <div
                  key={idx}
                  className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-1.5 mb-2">
                      <span className="text-xs font-bold text-slate-900 dark:text-white">
                        {item.skill_name}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        isMatched
                          ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                          : isBelow
                          ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                          : isUnverified
                          ? 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300'
                          : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                      }`}>
                        {item.status.replace(/_/g, ' ')}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-1.5 text-xs text-slate-600 dark:text-slate-400 mb-3">
                      <div className="flex justify-between">
                        <span>Required Level:</span>
                        <strong className="text-slate-800 dark:text-slate-200">{item.required_proficiency}</strong>
                      </div>
                      <div className="flex justify-between">
                        <span>Student Level:</span>
                        <strong className="text-blue-600 dark:text-blue-400">
                          {item.student_proficiency || 'Not acquired'}
                        </strong>
                      </div>
                      <div className="flex justify-between">
                        <span>Importance:</span>
                        <span className={`font-semibold ${item.importance === 'CRITICAL' ? 'text-rose-600' : 'text-slate-600'}`}>
                          {item.importance}
                        </span>
                      </div>
                      <div className="flex justify-between items-center pt-1 border-t border-slate-200 dark:border-slate-700">
                        <span>Verification:</span>
                        {item.is_verified ? (
                          <span className="text-emerald-600 flex items-center gap-1 font-semibold text-[11px]">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Verified
                          </span>
                        ) : (
                          <span className="text-amber-600 flex items-center gap-1 font-medium text-[11px]">
                            <AlertTriangle className="w-3.5 h-3.5" /> Self-Reported
                          </span>
                        )}
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed mb-3">
                      {item.suggested_improvement}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                    {item.recommended_resource_url ? (
                      <a
                        href={item.recommended_resource_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 font-semibold text-[11px]"
                      >
                        Recommended Course <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-[11px] text-slate-400">Core Curriculum</span>
                    )}

                    {(!isMatched || isUnverified) && (
                      <button
                        onClick={() => openEvidenceModal(idx + 1, item.skill_name)}
                        className="text-[11px] font-semibold text-teal-600 hover:underline flex items-center gap-1"
                      >
                        Submit Evidence <UploadCloud className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 2: Recharts Proficiency Benchmark Chart */}
      {activeTab === 'PROFICIENCY_CHART' && readinessData && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Skill Proficiency vs. Role Benchmark
              </h3>
              <p className="text-xs text-slate-500">
                Levels: 1 = Beginner, 2 = Intermediate, 3 = Advanced, 4 = Expert
              </p>
            </div>
            <span className="px-3 py-1 rounded-lg text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300">
              Target: {readinessData.target_role.title}
            </span>
          </div>

          <div className="h-80 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="skill" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 4]} ticks={[1, 2, 3, 4]} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px', border: 'none', color: '#fff', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <Bar dataKey="studentLevel" name="Student Acquired Level" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="requiredLevel" name="Role Benchmark Level" fill="#94a3b8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Tab 3: Matching Corporate Opportunities */}
      {activeTab === 'MATCHING_OPPS' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {matchingOpps.map(opp => (
            <div
              key={opp.id}
              className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                    {opp.opportunity_type}
                  </span>
                  <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                    {opp.ctc_stipend}
                  </span>
                </div>

                <h3 className="text-base font-bold text-slate-900 dark:text-white mb-0.5">
                  {opp.title}
                </h3>
                <p className="text-xs font-semibold text-slate-600 dark:text-slate-300 flex items-center gap-1 mb-3">
                  <Building2 className="w-3.5 h-3.5 text-blue-500" />
                  {opp.company_name} &bull; {opp.location} ({opp.work_mode})
                </p>

                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-1 text-xs text-slate-600 dark:text-slate-400 mb-3">
                  <div className="flex justify-between items-center">
                    <span>Role Skill Match:</span>
                    <strong className="text-blue-600 dark:text-blue-400 font-mono">{opp.readiness_score}%</strong>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Eligibility:</span>
                    {opp.is_eligible ? (
                      <span className="text-emerald-600 font-bold flex items-center gap-1 text-[11px]">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Fully Eligible
                      </span>
                    ) : (
                      <span className="text-amber-600 font-medium text-[11px]">
                        Criteria Shortfall
                      </span>
                    )}
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Deadline:</span>
                    <span className="font-mono text-slate-700 dark:text-slate-300 text-[11px]">{opp.application_deadline}</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                {opp.application_status ? (
                  <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300">
                    Applied: {opp.application_status}
                  </span>
                ) : (
                  <button
                    onClick={() => openApplyModal(opp)}
                    disabled={!opp.is_eligible}
                    className="w-full py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center gap-1.5 disabled:opacity-50"
                  >
                    <Briefcase className="w-3.5 h-3.5" />
                    {opp.is_eligible ? 'Apply for Drive' : 'Ineligible for Criteria'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 4: Application Pipeline */}
      {activeTab === 'APPLICATIONS' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              My Corporate Drive Submissions
            </h3>
            <span className="text-xs text-slate-500">Total: {applications.length}</span>
          </div>

          {applications.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-400">
              No placement or internship applications submitted yet. Browse matching opportunities above.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {applications.map(app => (
                <div key={app.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-slate-900 dark:text-white text-sm">{app.company_name}</span>
                      <span className="text-slate-400">&bull;</span>
                      <span className="font-semibold text-slate-700 dark:text-slate-300">{app.opportunity_title}</span>
                    </div>
                    <p className="text-slate-500 text-[11px]">
                      Applied on {new Date(app.applied_at).toLocaleDateString()} &bull; Package: {app.ctc_stipend} &bull; Match at submission: {app.readiness_score_at_application}%
                    </p>
                    {app.reviewer_notes && (
                      <p className="text-[11px] text-blue-600 dark:text-blue-400 mt-1 font-medium">
                        Placement Note: {app.reviewer_notes}
                      </p>
                    )}
                  </div>

                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase self-start sm:self-auto ${
                    app.status === 'SHORTLISTED' || app.status === 'OFFERED'
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                      : app.status === 'INTERVIEW_SCHEDULED'
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                      : app.status === 'REJECTED'
                      ? 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
                      : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                  }`}>
                    {app.status.replace(/_/g, ' ')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 5: My Verified Skills & Evidences */}
      {activeTab === 'EVIDENCES' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Acquired Skill Dossier & Verifiable Artifacts
              </h3>
              <p className="text-xs text-slate-500">
                Skills verified by faculty or placement coordinators carry verified confidence in corporate matching.
              </p>
            </div>
            <button
              onClick={() => setIsAddSkillModalOpen(true)}
              className="px-3.5 py-1.5 rounded-xl bg-teal-600 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Skill
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {studentSkills.map((s: any) => (
              <div key={s.id} className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900 dark:text-white">{s.skill_name}</span>
                  {s.is_verified ? (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Verified
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                      Self-Reported
                    </span>
                  )}
                </div>

                <div className="flex justify-between text-xs text-slate-500">
                  <span>Proficiency: <strong className="text-slate-700 dark:text-slate-300">{s.proficiency_level}</strong></span>
                  <span>Category: <span className="font-mono text-[11px]">{s.category}</span></span>
                </div>

                {s.evidences?.length > 0 && (
                  <div className="pt-2 border-t border-slate-200 dark:border-slate-700 space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Supporting Evidence ({s.evidences.length})</span>
                    {s.evidences.map((ev: any) => (
                      <div key={ev.id} className="text-xs flex items-center justify-between text-slate-600 dark:text-slate-300">
                        <span className="truncate max-w-[180px] font-medium">{ev.title}</span>
                        {ev.url && (
                          <a href={ev.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline flex items-center gap-0.5 text-[11px]">
                            Artifact <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                <div className="pt-2">
                  <button
                    onClick={() => openEvidenceModal(s.id, s.skill_name)}
                    className="w-full py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-teal-600 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-950/30 flex items-center justify-center gap-1"
                  >
                    <UploadCloud className="w-3 h-3" /> Attach Evidence
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modals */}
      {/* 1. Skill Evidence Modal */}
      {selectedSkillForEvidence && (
        <SkillEvidenceModal
          isOpen={isEvidenceModalOpen}
          onClose={() => {
            setIsEvidenceModalOpen(false);
            setSelectedSkillForEvidence(null);
          }}
          studentId={studentId}
          studentSkillId={selectedSkillForEvidence.id}
          skillName={selectedSkillForEvidence.name}
          onEvidenceSubmitted={() => loadReadinessAndMatches(studentId, selectedRoleCode)}
        />
      )}

      {/* 2. Apply Opportunity Modal */}
      {selectedOppForApply && (
        <ApplyOpportunityModal
          isOpen={isApplyModalOpen}
          onClose={() => {
            setIsApplyModalOpen(false);
            setSelectedOppForApply(null);
          }}
          opportunity={selectedOppForApply}
          studentId={studentId}
          readinessScore={selectedOppForApply.readiness_score}
          onApplicationSubmitted={() => loadReadinessAndMatches(studentId, selectedRoleCode)}
        />
      )}

      {/* 3. Add Skill Modal */}
      {isAddSkillModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-gradient-to-r from-teal-50 to-blue-50 dark:from-slate-900 dark:to-teal-950/30">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Add New Competency</h3>
              <button onClick={() => setIsAddSkillModalOpen(false)} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleAddSkillSubmit} className="p-6 space-y-3">
              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Skill Name *</label>
                <input
                  type="text"
                  value={newSkillName}
                  onChange={e => setNewSkillName(e.target.value)}
                  placeholder="e.g. PyTorch, Docker, System Design"
                  required
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Category</label>
                <select
                  value={newSkillCategory}
                  onChange={e => setNewSkillCategory(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                >
                  <option value="programming">Programming Language</option>
                  <option value="framework">Framework / Library</option>
                  <option value="database">Database</option>
                  <option value="cloud">Cloud & DevOps</option>
                  <option value="data_science">Data Science</option>
                  <option value="artificial_intelligence">Artificial Intelligence</option>
                  <option value="cybersecurity">Cybersecurity</option>
                  <option value="problem_solving">Problem Solving & Algorithms</option>
                  <option value="communication">Communication</option>
                  <option value="teamwork">Teamwork & Leadership</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Self-Reported Proficiency</label>
                <select
                  value={newSkillProficiency}
                  onChange={e => setNewSkillProficiency(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                >
                  <option value="Beginner">Beginner (Level 1)</option>
                  <option value="Intermediate">Intermediate (Level 2)</option>
                  <option value="Advanced">Advanced (Level 3)</option>
                  <option value="Expert">Expert (Level 4)</option>
                </select>
              </div>

              <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2">
                <button type="button" onClick={() => setIsAddSkillModalOpen(false)} className="px-4 py-1.5 text-xs rounded-xl border">Cancel</button>
                <button type="submit" className="px-4 py-1.5 text-xs font-semibold rounded-xl bg-teal-600 text-white">Save Skill</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
