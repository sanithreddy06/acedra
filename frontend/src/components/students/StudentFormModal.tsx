import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import { Department } from '../../types';
import { Modal } from '../common/Modal';
import { ErrorAlert } from '../common/ErrorAlert';

interface StudentFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  student: any | null; // null if creating, populated if editing
  departments: Department[];
  onSaved: () => void;
}

export const StudentFormModal: React.FC<StudentFormModalProps> = ({
  isOpen,
  onClose,
  student,
  departments,
  onSaved,
}) => {
  const isEditing = !!student;
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: 'StudentPass123!',
    usn: '',
    srn: '',
    roll_number: '',
    department_id: departments[0]?.id || 1,
    program: 'B.Tech Computer Science & Engineering',
    current_semester: 5,
    section: 'A',
    batch_year: 2024,
    admission_year: 2022,
    status: 'Active',
    placement_status: 'Eligible',
    gender: 'Male',
    blood_group: 'O+',
    guardian_name: '',
    guardian_contact: '',
    address: '',
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (student) {
      setFormData({
        full_name: student.full_name || '',
        email: student.email || '',
        password: '',
        usn: student.usn || '',
        srn: student.srn || '',
        roll_number: student.roll_number || '',
        department_id: student.department_id || (departments[0]?.id || 1),
        program: student.program || 'B.Tech Computer Science & Engineering',
        current_semester: student.current_semester || 5,
        section: student.section || 'A',
        batch_year: student.batch_year || 2024,
        admission_year: student.admission_year || 2022,
        status: student.status || 'Active',
        placement_status: student.placement_status || 'Eligible',
        gender: student.gender || 'Male',
        blood_group: student.blood_group || 'O+',
        guardian_name: student.guardian_name || '',
        guardian_contact: student.guardian_contact || '',
        address: student.address || '',
      });
    }
  }, [student, departments]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      if (isEditing) {
        await api.updateStudent(student.id, {
          full_name: formData.full_name,
          program: formData.program,
          current_semester: formData.current_semester,
          section: formData.section,
          status: formData.status,
          placement_status: formData.placement_status,
          gender: formData.gender,
          blood_group: formData.blood_group,
          guardian_name: formData.guardian_name,
          guardian_contact: formData.guardian_contact,
          address: formData.address,
        });
      } else {
        await api.createStudent(formData);
      }
      onSaved();
    } catch (err: any) {
      setError(err.message || 'Error saving student profile');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? `Edit Student — ${student?.usn}` : 'Enroll New Student Profile'}
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4 text-xs max-h-[75vh] overflow-y-auto pr-1">
        {error && <ErrorAlert message={error} />}

        {/* Basic Identifiers */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Full Name *
            </label>
            <input
              type="text"
              required
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Institutional Email *
            </label>
            <input
              type="email"
              required
              disabled={isEditing}
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 disabled:opacity-60"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              USN *
            </label>
            <input
              type="text"
              required
              disabled={isEditing}
              placeholder="e.g. 1RV22CS099"
              value={formData.usn}
              onChange={(e) => setFormData({ ...formData, usn: e.target.value.toUpperCase() })}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 font-mono disabled:opacity-60"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              SRN
            </label>
            <input
              type="text"
              disabled={isEditing}
              placeholder="e.g. SRN-2022-099"
              value={formData.srn}
              onChange={(e) => setFormData({ ...formData, srn: e.target.value.toUpperCase() })}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 font-mono disabled:opacity-60"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Roll Number *
            </label>
            <input
              type="text"
              required
              disabled={isEditing}
              placeholder="e.g. CS22B099"
              value={formData.roll_number}
              onChange={(e) => setFormData({ ...formData, roll_number: e.target.value.toUpperCase() })}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 font-mono disabled:opacity-60"
            />
          </div>
        </div>

        {/* Academic Program & Branch */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Department *
            </label>
            <select
              disabled={isEditing}
              value={formData.department_id}
              onChange={(e) => setFormData({ ...formData, department_id: Number(e.target.value) })}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 disabled:opacity-60"
            >
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.code} - {d.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Degree Program *
            </label>
            <input
              type="text"
              required
              value={formData.program}
              onChange={(e) => setFormData({ ...formData, program: e.target.value })}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Current Semester
            </label>
            <select
              value={formData.current_semester}
              onChange={(e) => setFormData({ ...formData, current_semester: Number(e.target.value) })}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            >
              {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                <option key={s} value={s}>Sem {s}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Section
            </label>
            <select
              value={formData.section}
              onChange={(e) => setFormData({ ...formData, section: e.target.value })}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            >
              <option value="A">Section A</option>
              <option value="B">Section B</option>
              <option value="C">Section C</option>
            </select>
          </div>
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Status
            </label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            >
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
              <option value="Graduated">Graduated</option>
              <option value="Suspended">Suspended</option>
            </select>
          </div>
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Placement Status
            </label>
            <select
              value={formData.placement_status}
              onChange={(e) => setFormData({ ...formData, placement_status: e.target.value })}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            >
              <option value="Eligible">Eligible</option>
              <option value="Placed">Placed</option>
              <option value="Ineligible">Ineligible</option>
            </select>
          </div>
        </div>

        {/* Guardian and Personal Info */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Guardian Name
            </label>
            <input
              type="text"
              value={formData.guardian_name}
              onChange={(e) => setFormData({ ...formData, guardian_name: e.target.value })}
              placeholder="Parent or Guardian"
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Guardian Contact
            </label>
            <input
              type="text"
              value={formData.guardian_contact}
              onChange={(e) => setFormData({ ...formData, guardian_contact: e.target.value })}
              placeholder="+91-9844000000"
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
        </div>

        <div>
          <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Residential Address
          </label>
          <textarea
            rows={2}
            value={formData.address}
            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            placeholder="Permanent or campus residential address"
            className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100"
          />
        </div>

        {/* Modal Action Buttons */}
        <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex justify-end space-x-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold shadow-sm disabled:opacity-50"
          >
            {isLoading ? 'Saving...' : isEditing ? 'Update Profile' : 'Enroll Student'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
