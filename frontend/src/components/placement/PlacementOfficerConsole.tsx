import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  Building2,
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  Plus,
  Search,
  Filter,
  ExternalLink,
  ChevronRight,
  AlertTriangle,
  Award,
  Layers,
  MapPin,
  Calendar,
  FileText,
  ShieldCheck,
  Check,
  X
} from 'lucide-react';
import { api } from '../../api/client';

export const PlacementOfficerConsole: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'OPPORTUNITIES' | 'APPLICATIONS' | 'ROLES' | 'VERIFICATION'>('OPPORTUNITIES');
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [applications, setApplications] = useState<any[]>([]);
  const [careerRoles, setCareerRoles] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // New Opportunity Modal
  const [isNewOppModalOpen, setIsNewOppModalOpen] = useState<boolean>(false);
  const [companyName, setCompanyName] = useState<string>('');
  const [jobTitle, setJobTitle] = useState<string>('');
  const [oppType, setOppType] = useState<string>('JOB');
  const [ctcStipend, setCtcStipend] = useState<string>('');
  const [location, setLocation] = useState<string>('Bangalore');
  const [workMode, setWorkMode] = useState<string>('HYBRID');
  const [minCgpa, setMinCgpa] = useState<number>(7.0);
  const [maxBacklogs, setMaxBacklogs] = useState<number>(0);
  const [deadline, setDeadline] = useState<string>('2026-12-31');
  const [openPositions, setOpenPositions] = useState<number>(5);
  const [description, setDescription] = useState<string>('');

  useEffect(() => {
    loadConsoleData();
  }, []);

  const loadConsoleData = async () => {
    setLoading(true);
    try {
      const [oppsRes, appsRes, rolesRes] = await Promise.all([
        api.getPlacementOpportunities(),
        api.getPlacementApplications(),
        api.getCareerRoles(),
      ]);
      setOpportunities(oppsRes);
      setApplications(appsRes);
      setCareerRoles(rolesRes);
    } catch (err: any) {
      console.error('Failed to load placement console data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (appId: number, newStatus: string) => {
    try {
      await api.updatePlacementApplicationStatus(appId, { status: newStatus });
      loadConsoleData();
    } catch (err: any) {
      alert('Failed to update status: ' + (err?.response?.data?.detail || err.message));
    }
  };

  const handleCreateOpportunity = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createPlacementOpportunity({
        company_name: companyName,
        title: jobTitle,
        opportunity_type: oppType,
        ctc_stipend: ctcStipend,
        location,
        work_mode: workMode,
        min_cgpa: minCgpa,
        max_backlogs: maxBacklogs,
        application_deadline: deadline,
        open_positions: openPositions,
        description,
        eligible_departments: ['CSE', 'AI_DS', 'ECE'],
        eligible_semesters: [6, 7, 8],
      });
      setIsNewOppModalOpen(false);
      loadConsoleData();
    } catch (err: any) {
      alert('Failed to create opportunity: ' + (err?.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Console Header */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-md shadow-blue-600/20">
                <Briefcase className="w-5 h-5" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Placement Cell Operations Console
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200 dark:border-blue-800/40">
                Module 4 Active
              </span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Manage corporate recruitment drives, internship postings, eligibility criteria, student applicant rosters, and skill benchmark taxonomies.
            </p>
          </div>

          <button
            onClick={() => setIsNewOppModalOpen(true)}
            className="px-4 py-2.5 text-xs font-semibold rounded-xl bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2 shadow-md shadow-blue-600/20 whitespace-nowrap"
          >
            <Plus className="w-4 h-4" />
            Post Corporate Drive / Opp
          </button>
        </div>

        {/* Top KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-100 dark:border-slate-800">
          <div>
            <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">Active Corporate Drives</span>
            <span className="text-2xl font-bold text-slate-900 dark:text-white">{opportunities.length}</span>
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">Total Applications</span>
            <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">{applications.length}</span>
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">Shortlisted / Interviews</span>
            <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              {applications.filter(a => a.status === 'SHORTLISTED' || a.status === 'INTERVIEW_SCHEDULED').length}
            </span>
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">Configured Roles</span>
            <span className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{careerRoles.length}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('OPPORTUNITIES')}
          className={`pb-3 px-2 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'OPPORTUNITIES'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-slate-500 hover:text-slate-900 dark:text-slate-400'
          }`}
        >
          <Building2 className="w-4 h-4" />
          Recruitment Drives & Internships ({opportunities.length})
        </button>
        <button
          onClick={() => setActiveTab('APPLICATIONS')}
          className={`pb-3 px-2 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'APPLICATIONS'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-slate-500 hover:text-slate-900 dark:text-slate-400'
          }`}
        >
          <Users className="w-4 h-4" />
          Applicant Tracking Roster ({applications.length})
        </button>
        <button
          onClick={() => setActiveTab('ROLES')}
          className={`pb-3 px-2 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'ROLES'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-slate-500 hover:text-slate-900 dark:text-slate-400'
          }`}
        >
          <Award className="w-4 h-4" />
          Career Roles & Skill Weights ({careerRoles.length})
        </button>
      </div>

      {/* Tab 1: Opportunities List */}
      {activeTab === 'OPPORTUNITIES' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {opportunities.map(opp => (
            <div
              key={opp.id}
              className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                    {opp.opportunity_type}
                  </span>
                  <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 font-mono">
                    {opp.ctc_stipend}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">{opp.title}</h3>
                <p className="text-xs font-semibold text-slate-600 dark:text-slate-300 flex items-center gap-1 mb-3">
                  <Building2 className="w-3.5 h-3.5 text-blue-500" />
                  {opp.company_name} &bull; {opp.location}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mb-4">
                  {opp.description}
                </p>

                <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 space-y-1 text-xs text-slate-600 dark:text-slate-400">
                  <div className="flex justify-between">
                    <span>Min CGPA:</span>
                    <strong className="text-slate-800 dark:text-slate-200">{opp.min_cgpa}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Max Backlogs:</span>
                    <strong className="text-slate-800 dark:text-slate-200">{opp.max_backlogs}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Deadline:</span>
                    <strong className="text-slate-800 dark:text-slate-200">{opp.application_deadline}</strong>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs mt-4">
                <span className="text-slate-500">
                  Applicants: <strong className="text-blue-600 dark:text-blue-400">{opp.application_count}</strong>
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
                  {opp.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 2: Applications Tracking Roster */}
      {activeTab === 'APPLICATIONS' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Candidate Applications Pipeline
            </h3>
            <span className="text-xs text-slate-500">
              Total submissions: {applications.length}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="p-3.5 font-semibold">Student Candidate</th>
                  <th className="p-3.5 font-semibold">Company & Role</th>
                  <th className="p-3.5 font-semibold">Readiness Score</th>
                  <th className="p-3.5 font-semibold">Application Status</th>
                  <th className="p-3.5 font-semibold">Applied Date</th>
                  <th className="p-3.5 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {applications.map(app => (
                  <tr key={app.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="p-3.5">
                      <span className="font-bold text-slate-900 dark:text-white block">{app.student_name}</span>
                      <span className="font-mono text-[11px] text-slate-400">{app.student_srn}</span>
                    </td>
                    <td className="p-3.5">
                      <span className="font-semibold text-slate-800 dark:text-slate-200 block">{app.company_name}</span>
                      <span className="text-[11px] text-slate-500">{app.opportunity_title}</span>
                    </td>
                    <td className="p-3.5">
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-indigo-600 dark:text-indigo-400 font-mono text-sm">
                          {app.readiness_score_at_application}%
                        </span>
                        <span className="text-[10px] text-slate-400">Match</span>
                      </div>
                    </td>
                    <td className="p-3.5">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
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
                    </td>
                    <td className="p-3.5 text-slate-500 font-mono text-[11px]">
                      {new Date(app.applied_at).toLocaleDateString()}
                    </td>
                    <td className="p-3.5 text-right space-x-1">
                      {app.status === 'APPLIED' && (
                        <button
                          onClick={() => handleUpdateStatus(app.id, 'SHORTLISTED')}
                          className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-emerald-600 hover:bg-emerald-700 text-white"
                        >
                          Shortlist
                        </button>
                      )}
                      {app.status === 'SHORTLISTED' && (
                        <button
                          onClick={() => handleUpdateStatus(app.id, 'INTERVIEW_SCHEDULED')}
                          className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-blue-600 hover:bg-blue-700 text-white"
                        >
                          Schedule Interview
                        </button>
                      )}
                      {app.status === 'INTERVIEW_SCHEDULED' && (
                        <button
                          onClick={() => handleUpdateStatus(app.id, 'OFFERED')}
                          className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-emerald-600 hover:bg-emerald-700 text-white"
                        >
                          Make Offer
                        </button>
                      )}
                      {app.status !== 'REJECTED' && app.status !== 'OFFERED' && (
                        <button
                          onClick={() => handleUpdateStatus(app.id, 'REJECTED')}
                          className="px-2 py-1 rounded-lg text-[11px] font-semibold border border-slate-300 dark:border-slate-700 text-slate-500 hover:text-red-600 hover:border-red-300"
                        >
                          Decline
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Career Roles & Benchmarks */}
      {activeTab === 'ROLES' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {careerRoles.map(role => (
            <div key={role.id} className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-blue-600 dark:text-blue-400">{role.code}</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                  {role.average_salary_range}
                </span>
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">{role.title}</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">{role.description}</p>

              <div>
                <span className="text-[11px] font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider block mb-2">
                  Role Benchmark Skills ({role.skills?.length || 0})
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {role.skills?.map((s: any) => (
                    <span
                      key={s.id}
                      className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 flex items-center gap-1"
                    >
                      <span>{s.skill_name}</span>
                      <span className="text-[10px] text-blue-600 font-mono">({s.min_proficiency})</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Post New Corporate Drive */}
      {isNewOppModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-900 dark:to-blue-950/30">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Post Recruitment / Internship Drive</h3>
              <button onClick={() => setIsNewOppModalOpen(false)} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleCreateOpportunity} className="p-6 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-500 uppercase">Company Name *</label>
                  <input type="text" value={companyName} onChange={e => setCompanyName(e.target.value)} required placeholder="e.g. Microsoft" className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800" />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-500 uppercase">Role Title *</label>
                  <input type="text" value={jobTitle} onChange={e => setJobTitle(e.target.value)} required placeholder="e.g. Cloud Engineer" className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800" />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-500 uppercase">Type</label>
                  <select value={oppType} onChange={e => setOppType(e.target.value)} className="w-full px-2 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800">
                    <option value="JOB">Full Time Job</option>
                    <option value="INTERNSHIP">Internship</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-500 uppercase">Package / Stipend *</label>
                  <input type="text" value={ctcStipend} onChange={e => setCtcStipend(e.target.value)} required placeholder="e.g. 18 LPA" className="w-full px-2 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800" />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-500 uppercase">Work Mode</label>
                  <select value={workMode} onChange={e => setWorkMode(e.target.value)} className="w-full px-2 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800">
                    <option value="HYBRID">Hybrid</option>
                    <option value="ONSITE">Onsite</option>
                    <option value="REMOTE">Remote</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-500 uppercase">Min CGPA</label>
                  <input type="number" step="0.1" value={minCgpa} onChange={e => setMinCgpa(parseFloat(e.target.value))} className="w-full px-2 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800" />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-500 uppercase">Max Backlogs</label>
                  <input type="number" value={maxBacklogs} onChange={e => setMaxBacklogs(parseInt(e.target.value))} className="w-full px-2 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800" />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-500 uppercase">Deadline</label>
                  <input type="date" value={deadline} onChange={e => setDeadline(e.target.value)} className="w-full px-2 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800" />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-500 uppercase">Job Description</label>
                <textarea rows={2} value={description} onChange={e => setDescription(e.target.value)} placeholder="Overview of responsibilities and team context..." className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800" />
              </div>

              <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2">
                <button type="button" onClick={() => setIsNewOppModalOpen(false)} className="px-4 py-1.5 text-xs rounded-lg border">Cancel</button>
                <button type="submit" className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white">Post Opportunity</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
