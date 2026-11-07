import React, { useState, useEffect } from 'react';
import {
  Users,
  Search,
  Filter,
  Plus,
  Eye,
  Edit,
  GraduationCap,
  CalendarCheck,
  Building2,
  FileSpreadsheet,
  Download
} from 'lucide-react';
import { api } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { Department } from '../../types';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import { StudentProfileModal } from './StudentProfileModal';
import { StudentFormModal } from './StudentFormModal';

export const StudentDirectory: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [students, setStudents] = useState<any[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedDept, setSelectedDept] = useState<number | undefined>(undefined);
  const [selectedSemester, setSelectedSemester] = useState<number | undefined>(undefined);
  const [selectedSection, setSelectedSection] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');

  // Modals
  const [viewingStudentId, setViewingStudentId] = useState<number | null>(null);
  const [isFormModalOpen, setIsFormModalOpen] = useState<boolean>(false);
  const [editingStudent, setEditingStudent] = useState<any | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [studentsRes, deptsRes] = await Promise.all([
        api.getStudents({
          search: searchTerm || undefined,
          department_id: selectedDept,
          semester: selectedSemester,
          section: selectedSection || undefined,
          status: selectedStatus,
        }),
        api.getDepartments(),
      ]);
      setStudents(studentsRes);
      setDepartments(deptsRes);
    } catch (err: any) {
      setError(err.message || 'Failed to load students directory');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadData();
    }, 250);
    return () => clearTimeout(timer);
  }, [searchTerm, selectedDept, selectedSemester, selectedSection, selectedStatus]);

  const handleEdit = (student: any, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingStudent(student);
    setIsFormModalOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Directory Title Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center">
            <Users className="w-5 h-5 mr-2 text-brand-600" />
            Student Intelligence Directory
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Consolidated directory of students, academic standing, and attendance dossiers across all departments.
          </p>
        </div>

        {isAdmin && (
          <button
            onClick={() => {
              setEditingStudent(null);
              setIsFormModalOpen(true);
            }}
            className="px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs flex items-center shadow-sm shadow-brand-500/20 transition"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            Add Student Profile
          </button>
        )}
      </div>

      {error && <ErrorAlert message={error} onRetry={loadData} />}

      {/* Search and Filters Bar */}
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3 text-xs">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by name, USN, SRN, or roll number..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Department */}
          <select
            value={selectedDept || ''}
            onChange={(e) => setSelectedDept(e.target.value ? Number(e.target.value) : undefined)}
            className="px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>{d.code} - {d.name}</option>
            ))}
          </select>

          {/* Semester */}
          <select
            value={selectedSemester || ''}
            onChange={(e) => setSelectedSemester(e.target.value ? Number(e.target.value) : undefined)}
            className="px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All Semesters</option>
            {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
              <option key={s} value={s}>Semester {s}</option>
            ))}
          </select>

          {/* Section */}
          <select
            value={selectedSection}
            onChange={(e) => setSelectedSection(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All Sections</option>
            <option value="A">Section A</option>
            <option value="B">Section B</option>
            <option value="C">Section C</option>
          </select>

          {/* Status */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="all">All Statuses</option>
            <option value="Active">Active</option>
            <option value="Inactive">Inactive</option>
            <option value="Graduated">Graduated</option>
            <option value="Suspended">Suspended</option>
          </select>
        </div>
      </div>

      {/* Students Data Table */}
      {isLoading ? (
        <LoadingSpinner label="Loading student records & analytics..." />
      ) : (
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-400">
                  <th className="py-3 px-4 font-semibold">Student Name & Identifiers</th>
                  <th className="py-3 px-4 font-semibold">Department & Program</th>
                  <th className="py-3 px-4 font-semibold text-center">Sem / Sec</th>
                  <th className="py-3 px-4 font-semibold text-center">CGPA</th>
                  <th className="py-3 px-4 font-semibold text-center">Attendance</th>
                  <th className="py-3 px-4 font-semibold text-center">Status</th>
                  <th className="py-3 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {students.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-400 italic">
                      No matching student profiles found for the selected criteria.
                    </td>
                  </tr>
                ) : (
                  students.map((st) => (
                    <tr
                      key={st.id}
                      onClick={() => setViewingStudentId(st.id)}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition cursor-pointer"
                    >
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-300 flex items-center justify-center font-bold text-xs uppercase flex-shrink-0">
                            {st.full_name.charAt(0)}
                          </div>
                          <div>
                            <p className="font-semibold text-slate-900 dark:text-slate-100">{st.full_name}</p>
                            <p className="text-[10px] text-slate-400 font-mono">
                              USN: {st.usn} &bull; SRN: {st.srn}
                            </p>
                          </div>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <span className="font-semibold text-brand-600 dark:text-brand-400">{st.department_code}</span>
                        <p className="text-[10px] text-slate-400 truncate max-w-[200px]">{st.program}</p>
                      </td>

                      <td className="py-3 px-4 text-center font-medium">
                        Sem {st.current_semester} - {st.section}
                      </td>

                      <td className="py-3 px-4 text-center font-bold font-mono text-slate-900 dark:text-slate-100">
                        {st.cgpa.toFixed(2)}
                      </td>

                      <td className="py-3 px-4 text-center">
                        <span className={`font-mono font-bold ${st.attendance_percentage < 75 ? 'text-rose-600' : 'text-emerald-600'}`}>
                          {st.attendance_percentage.toFixed(1)}%
                        </span>
                      </td>

                      <td className="py-3 px-4 text-center">
                        <Badge
                          variant={st.status === 'Active' ? 'success' : 'slate'}
                          size="sm"
                        >
                          {st.status}
                        </Badge>
                      </td>

                      <td className="py-3 px-4 text-right space-x-1" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => setViewingStudentId(st.id)}
                          title="View Intelligence Dossier"
                          className="p-1.5 rounded-lg text-slate-400 hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-950 transition"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {isAdmin && (
                          <button
                            onClick={(e) => handleEdit(st, e)}
                            title="Edit Student Profile"
                            className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950 transition"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Student Profile Intelligence Modal */}
      {viewingStudentId && (
        <StudentProfileModal
          studentId={viewingStudentId}
          isOpen={!!viewingStudentId}
          onClose={() => setViewingStudentId(null)}
          onStudentUpdated={loadData}
        />
      )}

      {/* Admin Student Form Modal (Create / Edit) */}
      {isFormModalOpen && (
        <StudentFormModal
          isOpen={isFormModalOpen}
          onClose={() => setIsFormModalOpen(false)}
          student={editingStudent}
          departments={departments}
          onSaved={() => {
            setIsFormModalOpen(false);
            loadData();
          }}
        />
      )}
    </div>
  );
};
