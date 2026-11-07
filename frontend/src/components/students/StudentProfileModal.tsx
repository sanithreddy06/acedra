import React, { useState, useEffect } from 'react';
import {
  GraduationCap,
  CalendarCheck,
  BookOpen,
  Award,
  Briefcase,
  Layers,
  Code,
  ShieldCheck,
  Mail,
  Phone,
  MapPin,
  ExternalLink,
  Github,
  Plus,
  CheckCircle,
  AlertTriangle,
  FileText,
  User,
  Clock
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend
} from 'recharts';
import { api } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import { Modal } from '../common/Modal';

interface StudentProfileModalProps {
  studentId: number;
  isOpen: boolean;
  onClose: () => void;
  onStudentUpdated?: () => void;
}

export const StudentProfileModal: React.FC<StudentProfileModalProps> = ({
  studentId,
  isOpen,
  onClose,
  onStudentUpdated,
}) => {
  const { user } = useAuth();
  const [data, setData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'academics' | 'attendance' | 'assessments' | 'skills' | 'portfolio'>('overview');

  // Add Skill Form state
  const [isAddSkillOpen, setIsAddSkillOpen] = useState(false);
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillCategory, setNewSkillCategory] = useState('programming');
  const [newSkillProficiency, setNewSkillProficiency] = useState('Intermediate');

  const loadStudentAnalytics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getStudentAnalytics(studentId);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch student intelligence profile');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && studentId) {
      loadStudentAnalytics();
    }
  }, [isOpen, studentId]);

  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.addStudentSkill(studentId, {
        skill_name: newSkillName,
        category: newSkillCategory,
        proficiency_level: newSkillProficiency,
      });
      setIsAddSkillOpen(false);
      setNewSkillName('');
      loadStudentAnalytics();
      if (onStudentUpdated) onStudentUpdated();
    } catch (err: any) {
      alert(err.message || 'Error adding skill');
    }
  };

  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Student Intelligence & Comprehensive Dossier" maxWidth="xl">
      {isLoading ? (
        <LoadingSpinner label="Compiling academic, attendance, and skill intelligence..." />
      ) : error || !data ? (
        <ErrorAlert message={error || 'Failed to load profile'} onRetry={loadStudentAnalytics} />
      ) : (
        <div className="space-y-5 max-h-[80vh] overflow-y-auto pr-1">
          {/* Header Card */}
          <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 to-indigo-950 text-white shadow-md flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
              <div className="w-14 h-14 rounded-2xl bg-brand-600 text-white flex items-center justify-center text-xl font-bold uppercase shadow-md shadow-brand-500/20">
                {data.student_profile.full_name.charAt(0)}
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-lg font-bold text-white tracking-tight">
                    {data.student_profile.full_name}
                  </h3>
                  <Badge variant="brand" size="sm">
                    {data.student_profile.status}
                  </Badge>
                </div>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-300 mt-1">
                  <span>USN: <strong className="font-mono text-white">{data.student_profile.usn}</strong></span>
                  <span>&bull;</span>
                  <span>SRN: <strong className="font-mono text-white">{data.student_profile.srn}</strong></span>
                  <span>&bull;</span>
                  <span>Roll: <strong className="font-mono text-white">{data.student_profile.roll_number}</strong></span>
                </div>
                <p className="text-xs text-brand-200 mt-0.5">
                  {data.student_profile.program} &bull; Semester {data.student_profile.current_semester} (Sec {data.student_profile.section})
                </p>
              </div>
            </div>

            <div className="flex sm:flex-col items-center sm:items-end justify-between w-full sm:w-auto gap-2 border-t sm:border-t-0 border-slate-800 pt-3 sm:pt-0">
              <div className="text-left sm:text-right">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">Cumulative CGPA</span>
                <span className="text-2xl font-black text-emerald-400 font-mono">
                  {data.metrics.cgpa.toFixed(2)}
                </span>
              </div>
              <Badge variant={data.metrics.calculated_attendance_percentage >= 75 ? 'success' : 'danger'} size="sm">
                {data.metrics.calculated_attendance_percentage}% Attendance
              </Badge>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="border-b border-slate-200 dark:border-slate-800 flex space-x-1 overflow-x-auto text-xs font-semibold">
            {[
              { id: 'overview', label: 'Overview & Metrics', icon: User },
              { id: 'academics', label: 'Academic & SGPA Progression', icon: Award },
              { id: 'attendance', label: 'Attendance Intelligence', icon: CalendarCheck },
              { id: 'assessments', label: 'Continuous Evaluations', icon: BookOpen },
              { id: 'skills', label: 'Skill Matrix', icon: Code },
              { id: 'portfolio', label: 'Projects & Experience', icon: Briefcase },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-3 py-2.5 border-b-2 whitespace-nowrap transition ${
                    isActive
                      ? 'border-brand-600 text-brand-600 dark:text-brand-400 dark:border-brand-400'
                      : 'border-transparent text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Tab 1: Overview & Metrics */}
          {activeTab === 'overview' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
                  <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">Total Credits</span>
                  <p className="text-xl font-bold text-slate-900 dark:text-white mt-0.5">{data.metrics.total_credits_earned}</p>
                  <span className="text-[10px] text-slate-400">Earned towards degree</span>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
                  <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">Active Backlogs</span>
                  <p className="text-xl font-bold text-rose-600 dark:text-rose-400 mt-0.5">{data.metrics.total_backlogs}</p>
                  <span className="text-[10px] text-slate-400">{data.metrics.total_backlogs === 0 ? 'Clear academic standing' : 'Intervention suggested'}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
                  <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">CIA Test Average</span>
                  <p className="text-xl font-bold text-brand-600 dark:text-brand-400 mt-0.5">{data.metrics.internal_assessment_average}%</p>
                  <span className="text-[10px] text-slate-400">Internal exams aggregate</span>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
                  <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">Placement Eligibility</span>
                  <p className="text-base font-bold text-emerald-600 dark:text-emerald-400 mt-1">{data.student_profile.placement_status}</p>
                  <span className="text-[10px] text-slate-400">Campus recruitments</span>
                </div>
              </div>

              {/* Personal Information & Department Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                  <h4 className="font-bold text-slate-900 dark:text-slate-100 flex items-center">
                    <User className="w-4 h-4 mr-1.5 text-brand-600" />
                    Identity & Contact
                  </h4>
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Email</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{data.student_profile.email}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Phone</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{data.student_profile.phone || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Gender & Blood Group</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{data.student_profile.gender || 'Not specified'} ({data.student_profile.blood_group || 'O+'})</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Residential Address</span>
                    <span className="font-medium text-slate-800 dark:text-slate-200 truncate max-w-[200px]">{data.student_profile.address || 'Campus Residency'}</span>
                  </div>
                </div>

                <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                  <h4 className="font-bold text-slate-900 dark:text-slate-100 flex items-center">
                    <GraduationCap className="w-4 h-4 mr-1.5 text-brand-600" />
                    Institutional Affiliation
                  </h4>
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Department</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{data.student_profile.department_name}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Admission Year / Batch</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{data.student_profile.admission_year} / {data.student_profile.batch_year}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Faculty Mentor</span>
                    <span className="font-semibold text-brand-600 dark:text-brand-400">{data.student_profile.mentor_name || 'Prof. David K. Sterling'}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Guardian Contact</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{data.student_profile.guardian_name} ({data.student_profile.guardian_contact})</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Academic Progression & SGPA */}
          {activeTab === 'academics' && (
            <div className="space-y-5">
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                  Semester SGPA Progression Trend
                </h4>
                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data.sgpa_trend}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis dataKey="semester" tick={{ fontSize: 11 }} />
                      <YAxis domain={[0, 10]} tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff', fontSize: '11px' }} />
                      <Line type="monotone" dataKey="sgpa" stroke="#4f46e5" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Subject Results Table */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                  Current Term Course Results & Marks Breakdown
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400">
                        <th className="pb-2 font-semibold">Code</th>
                        <th className="pb-2 font-semibold">Subject Title</th>
                        <th className="pb-2 font-semibold text-center">CIA (50)</th>
                        <th className="pb-2 font-semibold text-center">SEE (50)</th>
                        <th className="pb-2 font-semibold text-center">Total (100)</th>
                        <th className="pb-2 font-semibold text-center">Grade</th>
                        <th className="pb-2 font-semibold text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {data.subject_performance?.map((sub: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                          <td className="py-2.5 font-mono font-bold text-brand-600">{sub.subject_code}</td>
                          <td className="py-2.5 font-medium text-slate-800 dark:text-slate-200">{sub.subject_name}</td>
                          <td className="py-2.5 text-center font-mono">{sub.internal_marks.toFixed(1)}</td>
                          <td className="py-2.5 text-center font-mono">{sub.external_marks.toFixed(1)}</td>
                          <td className="py-2.5 text-center font-bold text-slate-900 dark:text-slate-100">{sub.total_marks.toFixed(1)}</td>
                          <td className="py-2.5 text-center font-bold text-brand-600">{sub.letter_grade}</td>
                          <td className="py-2.5 text-center">
                            <Badge variant={sub.is_backlog ? 'danger' : 'success'} size="sm">
                              {sub.is_backlog ? 'Backlog' : 'Pass'}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Tab 3: Attendance Intelligence */}
          {activeTab === 'attendance' && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Subject-Wise Attendance Breakdown (Calculated from Counts)
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Statutory requirement: Minimum 75% attendance per registered subject
                    </p>
                  </div>
                  <Badge variant={data.metrics.calculated_attendance_percentage >= 75 ? 'success' : 'danger'} size="md">
                    Aggregate: {data.metrics.calculated_attendance_percentage}%
                  </Badge>
                </div>

                <div className="space-y-3">
                  {data.attendance_breakdown?.map((att: any) => {
                    const pct = att.attendance_percentage;
                    const isDanger = pct < 75;
                    const isWarning = pct >= 75 && pct < 85;

                    return (
                      <div key={att.id} className="p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-850">
                        <div className="flex items-center justify-between text-xs">
                          <div>
                            <span className="font-mono font-bold text-brand-600 mr-2">{att.subject_code}</span>
                            <span className="font-medium text-slate-800 dark:text-slate-200">{att.subject_name}</span>
                          </div>
                          <div className="flex items-center space-x-3">
                            <span className="text-slate-500">
                              {att.attended_classes} / {att.total_classes} classes ({att.missed_classes} missed)
                            </span>
                            <span className={`font-bold font-mono ${isDanger ? 'text-rose-600' : isWarning ? 'text-amber-600' : 'text-emerald-600'}`}>
                              {pct}%
                            </span>
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full mt-2 overflow-hidden">
                          <div
                            className={`h-full transition-all duration-500 rounded-full ${
                              isDanger ? 'bg-rose-500' : isWarning ? 'bg-amber-500' : 'bg-emerald-500'
                            }`}
                            style={{ width: `${Math.min(100, pct)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Tab 4: Continuous Evaluations */}
          {activeTab === 'assessments' && (
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                Continuous Internal Assessments (CIA), Quizzes & Lab Evaluations
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400">
                      <th className="pb-2 font-semibold">Subject</th>
                      <th className="pb-2 font-semibold">Assessment Type</th>
                      <th className="pb-2 font-semibold text-center">Score</th>
                      <th className="pb-2 font-semibold text-center">Percentage</th>
                      <th className="pb-2 font-semibold">Remarks</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {data.assessment_history?.map((ass: any) => (
                      <tr key={ass.id}>
                        <td className="py-2.5 font-mono font-bold text-brand-600">{ass.subject_code}</td>
                        <td className="py-2.5 font-medium text-slate-800 dark:text-slate-200">{ass.assessment_type}</td>
                        <td className="py-2.5 text-center font-mono font-semibold">
                          {ass.marks_obtained} / {ass.max_marks}
                        </td>
                        <td className="py-2.5 text-center">
                          <Badge variant={ass.percentage >= 70 ? 'success' : 'warning'} size="sm">
                            {ass.percentage}%
                          </Badge>
                        </td>
                        <td className="py-2.5 text-slate-500">{ass.remarks || 'Standard evaluation'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 5: Skill Matrix */}
          {activeTab === 'skills' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Technical & Professional Competency Matrix
                  </h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Categorized taxonomy compatible with Placement Eligibility (Module 4)
                  </p>
                </div>
                <button
                  onClick={() => setIsAddSkillOpen(true)}
                  className="px-3 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs flex items-center shadow-sm"
                >
                  <Plus className="w-3.5 h-3.5 mr-1" /> Add Skill
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(data.skills_by_category || {}).map(([cat, skills]: [string, any]) => {
                  if (!skills || skills.length === 0) return null;
                  return (
                    <div key={cat} className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                      <h5 className="text-xs font-bold text-slate-700 dark:text-slate-300 capitalize mb-2">
                        {cat.replace('_', ' ')}
                      </h5>
                      <div className="flex flex-wrap gap-2">
                        {skills.map((sk: any) => (
                          <div
                            key={sk.id}
                            className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center space-x-1.5 text-xs"
                          >
                            <span className="font-semibold text-slate-800 dark:text-slate-200">{sk.skill_name}</span>
                            <span className="text-[10px] text-brand-600 font-mono">({sk.proficiency_level})</span>
                            {sk.is_verified && <CheckCircle className="w-3 h-3 text-emerald-500" />}
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Add Skill Modal */}
              {isAddSkillOpen && (
                <div className="p-4 rounded-xl border border-brand-200 dark:border-brand-900 bg-brand-50/50 dark:bg-brand-950/30">
                  <h5 className="text-xs font-bold text-brand-900 dark:text-brand-300 mb-2">Record Skill Competency</h5>
                  <form onSubmit={handleAddSkill} className="flex flex-wrap items-center gap-2 text-xs">
                    <input
                      type="text"
                      required
                      placeholder="e.g. PyTorch, Rust, AWS..."
                      value={newSkillName}
                      onChange={(e) => setNewSkillName(e.target.value)}
                      className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                    />
                    <select
                      value={newSkillCategory}
                      onChange={(e) => setNewSkillCategory(e.target.value)}
                      className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                    >
                      <option value="programming">Programming Language</option>
                      <option value="framework">Framework / Library</option>
                      <option value="database">Database</option>
                      <option value="cloud">Cloud / DevOps</option>
                      <option value="tool">Tool</option>
                      <option value="soft_skill">Soft Skill</option>
                    </select>
                    <select
                      value={newSkillProficiency}
                      onChange={(e) => setNewSkillProficiency(e.target.value)}
                      className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                    >
                      <option value="Beginner">Beginner</option>
                      <option value="Intermediate">Intermediate</option>
                      <option value="Advanced">Advanced</option>
                      <option value="Expert">Expert</option>
                    </select>
                    <button
                      type="submit"
                      className="px-4 py-1.5 rounded-lg bg-brand-600 text-white font-semibold shadow-sm hover:bg-brand-700"
                    >
                      Save Skill
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsAddSkillOpen(false)}
                      className="px-3 py-1.5 rounded-lg text-slate-500 hover:text-slate-800"
                    >
                      Cancel
                    </button>
                  </form>
                </div>
              )}
            </div>
          )}

          {/* Tab 6: Portfolio & Experience */}
          {activeTab === 'portfolio' && (
            <div className="space-y-4">
              {/* Projects */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center">
                  <Code className="w-4 h-4 mr-1.5 text-brand-600" />
                  Engineering & Research Projects ({data.projects?.length || 0})
                </h4>
                <div className="space-y-2.5">
                  {data.projects?.map((p: any) => (
                    <div key={p.id} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 text-xs">
                      <div className="flex items-center justify-between">
                        <h5 className="font-bold text-slate-900 dark:text-slate-100">{p.title}</h5>
                        <span className="font-mono text-[10px] text-brand-600">{p.role} &bull; Sem {p.semester_number}</span>
                      </div>
                      <p className="text-slate-600 dark:text-slate-400 mt-1">{p.description}</p>
                      <div className="mt-2 flex items-center space-x-2">
                        <span className="text-[10px] font-semibold text-slate-500">Tech Stack:</span>
                        <span className="text-[11px] font-mono text-brand-600 dark:text-brand-400">{p.tech_stack}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Internships & Certifications */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {/* Internships */}
                <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                  <h4 className="font-bold text-slate-900 dark:text-slate-100 flex items-center">
                    <Briefcase className="w-4 h-4 mr-1.5 text-brand-600" />
                    Internships & Industry Engagements
                  </h4>
                  {data.internships?.length === 0 ? (
                    <p className="text-slate-400 italic py-2">No completed internships recorded yet.</p>
                  ) : (
                    data.internships?.map((i: any) => (
                      <div key={i.id} className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60">
                        <p className="font-bold text-slate-900 dark:text-slate-100">{i.company_name}</p>
                        <p className="text-brand-600 font-semibold mt-0.5">{i.role} &bull; {i.stipend || 'Stipend undisclosed'}</p>
                        <p className="text-slate-500 mt-1">{i.description}</p>
                      </div>
                    ))
                  )}
                </div>

                {/* Certifications */}
                <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                  <h4 className="font-bold text-slate-900 dark:text-slate-100 flex items-center">
                    <ShieldCheck className="w-4 h-4 mr-1.5 text-emerald-600" />
                    Verified Certifications & Credentials
                  </h4>
                  {data.certifications?.length === 0 ? (
                    <p className="text-slate-400 italic py-2">No external certifications linked.</p>
                  ) : (
                    data.certifications?.map((c: any) => (
                      <div key={c.id} className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 flex items-center justify-between">
                        <div>
                          <p className="font-bold text-slate-900 dark:text-slate-100">{c.title}</p>
                          <p className="text-slate-500">{c.issuing_organization}</p>
                        </div>
                        <Badge variant="success" size="sm">Verified</Badge>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
};
