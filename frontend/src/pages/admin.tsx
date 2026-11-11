import { useEffect, useRef, useState } from 'react';
import { Download, FileUp, Plus, RefreshCw, Trash2, Upload } from 'lucide-react';
import { api, errorMessage } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useApi } from '../lib/useApi';
import { cleanName, fmtDate, num, relTime, ROLE_LABEL, titleCase } from '../lib/format';
import { PageHeader } from '../components/shell';
import type { AuditLogEntry, PlatformAuditList, AssistantDocument, CatalogueItemInput, ImportPreview, MessageResult, RetrievalResult, RiskRuleInput, UniversityUser, AssistantStatus, CatalogueItem, DepartmentSummary, ImportJob, MentorSummary, ProvisioningRequest, ReportExport, RiskRule, Semester, StaffAccess, StudentProfile, Subject, TeachingAssignment, TenantProfile, UserList } from '../types/api';
import {
  Async, Badge, Button, Checkbox, ConfirmDialog, cx, DataTable, Dialog, EmptyState, Field, Input, KeyValues, Notice,
  Pagination, Panel, SearchInput, Select, StatusBadge, Tabs, Textarea, Toolbar, useToast,
} from '../components/ui';

/* ------------------------------------------------------------------ people & access */
export function PeoplePage() {
  const [tab, setTab] = useState('users');
  return (
    <div>
      <PageHeader title="People & access" lede="Everyone is invited by your university. A matching email domain is required but never grants access by itself." />
      <Tabs value={tab} onChange={setTab} className="mb-5" tabs={[
        { id: 'users', label: 'Users' }, { id: 'mentors', label: 'Mentor assignments' }, { id: 'access', label: 'Shared student access' }, { id: 'prov', label: 'Account provisioning' },
      ]} />
      {tab === 'users' && <UsersTab />}
      {tab === 'mentors' && <MentorsTab />}
      {tab === 'access' && <StaffAccessTab />}
      {tab === 'prov' && <ProvisioningTab />}
    </div>
  );
}

function UsersTab() {
  const toast = useToast();
  const { me } = useAuth();
  const [role, setRole] = useState(''); const [status, setStatus] = useState(''); const [search, setSearch] = useState(''); const [skip, setSkip] = useState(0);
  const users = useApi<UserList>('/users/', { role, status, search, skip, limit: 25 });
  const [inviting, setInviting] = useState(false);
  const [edit, setEdit] = useState<UniversityUser | null>(null);
  const resend = async (u: UniversityUser) => { try { const r = await api.post<MessageResult>(`/users/${u.id}/resend-invitation`); toast(r.message); } catch (e) { toast(errorMessage(e), 'error'); } };
  return (
    <Panel padded={false}>
      <Toolbar>
        <SearchInput value={search} onChange={(v) => { setSearch(v); setSkip(0); }} placeholder="Search name or email" className="w-full sm:w-64" />
        <Select value={role} onChange={(e) => { setRole(e.target.value); setSkip(0); }} className="w-48" aria-label="Role"><option value="">All roles</option>{['student', 'faculty', 'mentor', 'placement_officer', 'admin'].map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}</Select>
        <Select value={status} onChange={(e) => { setStatus(e.target.value); setSkip(0); }} className="w-40" aria-label="Status"><option value="">Any status</option><option value="active">Active</option><option value="invited">Invited</option><option value="disabled">Disabled</option></Select>
        <div className="ml-auto"><Button variant="primary" icon={<Plus size={14} />} onClick={() => setInviting(true)}>Invite people</Button></div>
      </Toolbar>
      <Async state={users}>{(d) => (
        <>
          <DataTable rows={d.items} empty={<EmptyState title="No users match these filters" />} columns={[
            { key: 'n', header: 'Name', render: (u) => <div><div className="font-medium">{cleanName(u.full_name)}</div><div className="text-[12px] text-muted">{u.email}</div></div> },
            { key: 'r', header: 'Role', render: (u) => ROLE_LABEL[u.role] },
            { key: 'd', header: 'Department', hideOnMobile: true, render: (u) => u.department_name || '—' },
            { key: 's', header: 'Status', render: (u) => <StatusBadge status={u.status} /> },
            { key: 'l', header: 'Last sign-in', hideOnMobile: true, render: (u) => u.last_login_at ? relTime(u.last_login_at) : '—' },
            { key: 'a', header: '', align: 'right', render: (u) => (
              <div className="flex justify-end gap-1">
                {u.status === 'invited' && <Button size="sm" variant="ghost" onClick={() => resend(u)}>Resend</Button>}
                {u.id !== me?.id && <Button size="sm" variant="ghost" onClick={() => setEdit(u)}>Edit</Button>}
              </div>) },
          ]} />
          <Pagination total={d.total} skip={skip} limit={25} onChange={setSkip} />
        </>
      )}</Async>
      {inviting && <InviteDialog onClose={() => setInviting(false)} onDone={users.reload} />}
      {edit && <EditUserDialog user={edit} onClose={() => setEdit(null)} onDone={users.reload} />}
    </Panel>
  );
}

function InviteDialog({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const depts = useApi<DepartmentSummary[]>('/tenant/departments');
  const profile = useApi<TenantProfile>('/tenant/profile');
  const [f, setF] = useState({ email: '', full_name: '', role: 'student', department_id: '', title: '', usn: '', current_semester: '1', section: 'A', employee_id: '' });
  const [saving, setSaving] = useState(false);
  const domains = (profile.data?.domains || []).map((d) => d.domain);
  const domainOk = !f.email.includes('@') || !domains.length || domains.includes(f.email.split('@')[1]?.toLowerCase());
  const save = async () => {
    setSaving(true);
    try {
      await api.post('/users/invite', { ...f, department_id: f.department_id ? Number(f.department_id) : null, current_semester: Number(f.current_semester), title: f.title || null, usn: f.usn || null, employee_id: f.employee_id || null });
      toast(`Invitation sent to ${f.email}`); onDone(); onClose();
    } catch (e) { toast(errorMessage(e), 'error'); } finally { setSaving(false); }
  };
  const needsDept = ['student', 'faculty', 'mentor'].includes(f.role);
  return (
    <Dialog open onClose={onClose} title="Invite a person" description="They’ll receive an email link to set their own password. Access starts only after they accept."
      footer={<><Button onClick={onClose}>Cancel</Button><Button variant="primary" loading={saving} disabled={!f.email || !f.full_name || !domainOk || (needsDept && !f.department_id) || (f.role === 'student' && !f.usn)} onClick={save}>Send invitation</Button></>}>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Full name" className="sm:col-span-2"><Input value={f.full_name} onChange={(e) => setF({ ...f, full_name: e.target.value })} /></Field>
        <Field label="Institutional email" className="sm:col-span-2" error={!domainOk ? `Use an approved domain: ${domains.join(', ')}` : null} hint={domains.length ? `Approved: ${domains.join(', ')}` : undefined}>
          <Input type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
        <Field label="Role"><Select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}>{['student', 'faculty', 'mentor', 'placement_officer', 'admin'].map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}</Select></Field>
        <Field label={needsDept ? 'Department' : 'Department (optional)'}><Select value={f.department_id} onChange={(e) => setF({ ...f, department_id: e.target.value })}><option value="">Choose…</option>{depts.data?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</Select></Field>
        {f.role === 'student' ? (<>
          <Field label="USN / registration no."><Input value={f.usn} onChange={(e) => setF({ ...f, usn: e.target.value.toUpperCase() })} /></Field>
          <div className="grid grid-cols-2 gap-3"><Field label="Semester"><Input type="number" min={1} max={12} value={f.current_semester} onChange={(e) => setF({ ...f, current_semester: e.target.value })} /></Field><Field label="Section"><Input value={f.section} onChange={(e) => setF({ ...f, section: e.target.value })} /></Field></div>
        </>) : (<>
          <Field label="Designation"><Input value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></Field>
          {['faculty', 'mentor'].includes(f.role) && <Field label="Employee ID (optional)"><Input value={f.employee_id} onChange={(e) => setF({ ...f, employee_id: e.target.value })} /></Field>}
        </>)}
      </div>
    </Dialog>
  );
}

const STAFF_ROLES = ['faculty', 'mentor', 'placement_officer', 'admin'] as const;

function EditUserDialog({ user, onClose, onDone }: { user: UniversityUser; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const [role, setRole] = useState(user.role); const [active, setActive] = useState(user.is_active); const [saving, setSaving] = useState(false);
  const save = async () => {
    setSaving(true);
    try { await api.patch(`/users/${user.id}`, { ...(role !== user.role ? { role } : {}), ...(active !== user.is_active ? { is_active: active } : {}) }); toast('User updated — their existing sessions have ended'); onDone(); onClose(); }
    catch (e) { toast(errorMessage(e), 'error'); } finally { setSaving(false); }
  };
  return (
    <Dialog open onClose={onClose} title={cleanName(user.full_name)} description={user.email}
      footer={<><Button onClick={onClose}>Cancel</Button><Button variant="primary" loading={saving} onClick={save}>Save changes</Button></>}>
      <div className="space-y-4">
        {user.role !== 'student' && <Field label="Role" hint="Student accounts can’t be converted to staff roles."><Select value={role} onChange={(e) => { const next = STAFF_ROLES.find((r) => r === e.target.value); if (next) setRole(next); }}>{STAFF_ROLES.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}</Select></Field>}
        {user.is_verified && <Checkbox label="Account active" description="Disabling signs the person out everywhere." checked={active} onChange={setActive} />}
      </div>
    </Dialog>
  );
}

function MentorsTab() {
  const toast = useToast();
  const mentors = useApi<MentorSummary[]>('/tenant/mentors');
  const students = useApi<StudentProfile[]>('/students/', { limit: 100 });
  const [mentor, setMentor] = useState(''); const [picked, setPicked] = useState<number[]>([]); const [search, setSearch] = useState('');
  const assign = async () => {
    try { const r = await api.post<MessageResult>('/tenant/mentor-assignments', { mentor_id: Number(mentor), student_ids: picked }); toast(r.message); setPicked([]); mentors.reload(); students.reload(); }
    catch (e) { toast(errorMessage(e), 'error'); }
  };
  const rows = (students.data || []).filter((s) => !search || s.full_name.toLowerCase().includes(search.toLowerCase()) || s.usn.toLowerCase().includes(search.toLowerCase()));
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.6fr]">
      <Panel title="Mentors" padded={false}>
        <Async state={mentors}>{(list) => <DataTable rows={list} empty={<EmptyState title="No mentors yet">Invite staff with the mentor role first.</EmptyState>} columns={[
          { key: 'n', header: 'Mentor', render: (m) => <div><div className="font-medium">{cleanName(m.full_name)}</div><div className="text-[12px] text-muted">{m.department}</div></div> },
          { key: 'c', header: 'Mentees', align: 'right', render: (m) => `${m.mentee_count} / ${m.max_mentees}` },
        ]} />}</Async>
      </Panel>
      <Panel title="Assign students" padded={false}>
        <Toolbar>
          <SearchInput value={search} onChange={setSearch} placeholder="Find students" className="w-full sm:w-56" />
          <Select value={mentor} onChange={(e) => setMentor(e.target.value)} className="w-56" aria-label="Mentor"><option value="">Choose mentor…</option>{mentors.data?.map((m) => <option key={m.id} value={m.id}>{cleanName(m.full_name)}</option>)}</Select>
          <Button variant="primary" disabled={!mentor || !picked.length} onClick={assign}>Assign {picked.length || ''}</Button>
        </Toolbar>
        <Async state={students}>{() => (
          <div className="max-h-[28rem] overflow-y-auto">
            <DataTable rows={rows} dense columns={[
              { key: 'p', header: <span className="sr-only">Select</span>, className: 'w-10', render: (s) => <Checkbox label={<span className="sr-only">Select {s.full_name}</span>} checked={picked.includes(s.id)} onChange={(c) => setPicked(c ? [...picked, s.id] : picked.filter((x) => x !== s.id))} /> },
              { key: 'n', header: 'Student', render: (s) => <div><span className="font-medium">{cleanName(s.full_name)}</span> <span className="text-[12px] text-muted">{s.usn}</span></div> },
              { key: 'm', header: 'Current mentor', render: (s) => cleanName(s.mentor_name) || <span className="text-faint">None</span> },
            ]} />
          </div>
        )}</Async>
      </Panel>
    </div>
  );
}

function StaffAccessTab() {
  const toast = useToast();
  const rows = useApi<StaffAccess[]>('/tenant/staff-access');
  const faculty = useApi<UserList>('/users/', { role: 'faculty', limit: 200 });
  const students = useApi<StudentProfile[]>('/students/', { limit: 100 });
  const [f, setF] = useState({ user_id: '', student_id: '', reason: '' });
  const grant = async () => {
    try { await api.post('/tenant/staff-access', { user_id: Number(f.user_id), student_id: Number(f.student_id), reason: f.reason }); toast('Access shared'); setF({ user_id: '', student_id: '', reason: '' }); rows.reload(); }
    catch (e) { toast(errorMessage(e), 'error'); }
  };
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.5fr]">
      <Panel title="Share a student with faculty" description="Faculty normally see only the sections they teach. Use this for advisers or project guides. Every grant is audited.">
        <div className="space-y-3">
          <Field label="Faculty member"><Select value={f.user_id} onChange={(e) => setF({ ...f, user_id: e.target.value })}><option value="">Choose…</option>{faculty.data?.items?.map((u) => <option key={u.id} value={u.id}>{cleanName(u.full_name)}</option>)}</Select></Field>
          <Field label="Student"><Select value={f.student_id} onChange={(e) => setF({ ...f, student_id: e.target.value })}><option value="">Choose…</option>{students.data?.map((s) => <option key={s.id} value={s.id}>{cleanName(s.full_name)} · {s.usn}</option>)}</Select></Field>
          <Field label="Reason"><Input value={f.reason} onChange={(e) => setF({ ...f, reason: e.target.value })} placeholder="e.g. Final-year project guide" /></Field>
          <Button variant="primary" disabled={!f.user_id || !f.student_id || f.reason.length < 3} onClick={grant}>Share access</Button>
        </div>
      </Panel>
      <Panel title="Current grants" padded={false}>
        <Async state={rows}>{(list) => <DataTable rows={list} empty={<EmptyState title="No shared access" />} columns={[
          { key: 'f', header: 'Faculty', render: (r) => cleanName(r.staff) }, { key: 's', header: 'Student', render: (r) => cleanName(r.student) },
          { key: 'r', header: 'Reason', hideOnMobile: true, render: (r) => r.reason }, { key: 'd', header: 'Since', hideOnMobile: true, render: (r) => fmtDate(r.created_at) },
          { key: 'x', header: '', align: 'right', render: (r) => <Button size="sm" variant="ghost" onClick={async () => { await api.del(`/tenant/staff-access/${r.id}`); toast('Access revoked'); rows.reload(); }}>Revoke</Button> },
        ]} />}</Async>
      </Panel>
    </div>
  );
}

function ProvisioningTab() {
  const toast = useToast();
  const list = useApi<ProvisioningRequest[]>('/tenant/provisioning');
  const [f, setF] = useState({ method: 'existing', accounts_requested: '', notes: '' });
  const submit = async () => {
    try { const r = await api.post<{ estimate?: unknown }>('/tenant/provisioning', { ...f, accounts_requested: Number(f.accounts_requested) }); toast(r.estimate ? 'Request recorded with an indicative estimate' : 'Request recorded'); list.reload(); setF({ method: 'existing', accounts_requested: '', notes: '' }); }
    catch (e) { toast(errorMessage(e), 'error'); }
  };
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.5fr]">
      <Panel title="Request account provisioning" description="Tell your ACEDRA contact how student accounts should be set up.">
        <div className="space-y-3">
          <Field label="Method"><Select value={f.method} onChange={(e) => setF({ ...f, method: e.target.value })}><option value="existing">Use our existing institutional emails</option><option value="rio_assisted">ACEDRA-assisted email creation (additional charge)</option></Select></Field>
          {f.method === 'rio_assisted' && <Notice tone="attention">ACEDRA-assisted creation is an additional, chargeable service outside the standard platform. This records your request and an indicative estimate; no mailboxes are created automatically.</Notice>}
          <Field label="Number of accounts"><Input type="number" min={1} value={f.accounts_requested} onChange={(e) => setF({ ...f, accounts_requested: e.target.value })} /></Field>
          <Field label="Notes"><Textarea value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} /></Field>
          <Button variant="primary" disabled={!(Number(f.accounts_requested) > 0)} onClick={submit}>Record request</Button>
        </div>
      </Panel>
      <Panel title="Requests" padded={false}>
        <Async state={list}>{(rows) => <DataTable rows={rows} empty={<EmptyState title="No provisioning requests" />} columns={[
          { key: 'm', header: 'Method', render: (p) => p.method === 'rio_assisted' ? <span>ACEDRA-assisted <Badge tone="bronze">chargeable</Badge></span> : 'Existing emails' },
          { key: 'a', header: 'Accounts', align: 'right', render: (p) => `${p.accounts_completed} / ${p.accounts_requested}` },
          { key: 'c', header: 'Estimate', align: 'right', hideOnMobile: true, render: (p) => p.estimated_cost ? `₹${p.estimated_cost.toLocaleString('en-IN')}/yr` : '—' },
          { key: 's', header: 'Status', render: (p) => <StatusBadge status={p.status} /> },
          { key: 'd', header: 'Requested', hideOnMobile: true, render: (p) => fmtDate(p.created_at) },
        ]} />}</Async>
      </Panel>
    </div>
  );
}

/* ------------------------------------------------------------------ academic structure */
/** Add a subject, term or teaching assignment. Inputs are validated here and again by the API. */
function StructureDialog({ kind, departments, onClose, onSaved }: {
  kind: 'subject' | 'term' | 'teaching'; departments: DepartmentSummary[]; onClose: () => void; onSaved: () => void;
}) {
  const toast = useToast();
  const faculty = useApi<UserList>(kind === 'teaching' ? '/users/' : null, { role: 'faculty', limit: 200 });
  const subjects = useApi<Subject[]>(kind === 'teaching' ? '/academics/subjects' : null);
  const terms = useApi<Semester[]>(kind === 'teaching' ? '/academics/semesters' : null);
  const [f, setF] = useState({ code: '', name: '', department_id: '', semester_number: '1', credits: '3', subject_type: 'Theory',
    academic_year: '', is_current: false, faculty_user_id: '', subject_id: '', semester_id: '', section: 'A' });
  const [saving, setSaving] = useState(false);
  const set = (patch: Partial<typeof f>) => setF((p) => ({ ...p, ...patch }));
  const valid = kind === 'subject' ? f.code.trim().length >= 2 && f.name.trim().length >= 2 && !!f.department_id && Number(f.semester_number) >= 1
    : kind === 'term' ? f.name.trim().length >= 1 && f.academic_year.trim().length >= 4 && Number(f.semester_number) >= 1
      : !!f.faculty_user_id && !!f.subject_id && !!f.semester_id && f.section.trim().length >= 1 && f.academic_year.trim().length >= 4;
  const save = async () => {
    setSaving(true);
    try {
      if (kind === 'subject') await api.post('/academics/subjects', { code: f.code.trim().toUpperCase(), name: f.name.trim(), department_id: Number(f.department_id), semester_number: Number(f.semester_number), credits: Number(f.credits), subject_type: f.subject_type });
      else if (kind === 'term') await api.post('/academics/semesters', { name: f.name.trim(), academic_year: f.academic_year.trim(), semester_number: Number(f.semester_number), is_current: f.is_current });
      else await api.post('/academics/assignments', { faculty_user_id: Number(f.faculty_user_id), subject_id: Number(f.subject_id), semester_id: Number(f.semester_id), section: f.section.trim().toUpperCase(), academic_year: f.academic_year.trim() });
      toast(kind === 'subject' ? 'Subject added' : kind === 'term' ? 'Term added' : 'Teaching assignment saved');
      onSaved(); onClose();
    } catch (e) { toast(errorMessage(e), 'error'); } finally { setSaving(false); }
  };
  const title = kind === 'subject' ? 'Add subject' : kind === 'term' ? 'Add term' : 'Assign teaching';
  return (
    <Dialog open onClose={onClose} title={title}
      description={kind === 'teaching' ? 'The faculty member will see every student in this section, in addition to students shared with them.' : undefined}
      footer={<><Button onClick={onClose}>Cancel</Button><Button variant="primary" loading={saving} disabled={!valid} onClick={save}>{title}</Button></>}>
      <div className="space-y-3">
        {kind === 'subject' && <>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Code"><Input value={f.code} onChange={(e) => set({ code: e.target.value.toUpperCase() })} placeholder="e.g. CS301" /></Field>
            <Field label="Department"><Select value={f.department_id} onChange={(e) => set({ department_id: e.target.value })}><option value="">Choose…</option>{departments.map((d) => <option key={d.id} value={d.id}>{d.code} · {d.name}</option>)}</Select></Field>
          </div>
          <Field label="Name"><Input value={f.name} onChange={(e) => set({ name: e.target.value })} /></Field>
          <div className="grid grid-cols-3 gap-3">
            <Field label="Term number"><Input type="number" min={1} max={24} value={f.semester_number} onChange={(e) => set({ semester_number: e.target.value })} /></Field>
            <Field label="Credits"><Input type="number" min={0} max={30} value={f.credits} onChange={(e) => set({ credits: e.target.value })} /></Field>
            <Field label="Type"><Select value={f.subject_type} onChange={(e) => set({ subject_type: e.target.value })}><option>Theory</option><option>Lab</option><option>Elective</option></Select></Field>
          </div>
        </>}
        {kind === 'term' && <>
          <Field label="Name"><Input value={f.name} onChange={(e) => set({ name: e.target.value })} placeholder="e.g. Semester 3" /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Term number"><Input type="number" min={1} max={24} value={f.semester_number} onChange={(e) => set({ semester_number: e.target.value })} /></Field>
            <Field label="Academic year"><Input value={f.academic_year} onChange={(e) => set({ academic_year: e.target.value })} placeholder="2026-2027" /></Field>
          </div>
          <Checkbox label="This is the current term" description="Attendance imports are recorded against the current term." checked={f.is_current} onChange={(v) => set({ is_current: v })} />
        </>}
        {kind === 'teaching' && <>
          <Field label="Faculty member"><Select value={f.faculty_user_id} onChange={(e) => set({ faculty_user_id: e.target.value })}><option value="">Choose…</option>{faculty.data?.items.map((u) => <option key={u.id} value={u.id}>{cleanName(u.full_name)}{u.status !== 'active' ? ` (${u.status})` : ''}</option>)}</Select></Field>
          <Field label="Subject"><Select value={f.subject_id} onChange={(e) => set({ subject_id: e.target.value })}><option value="">Choose…</option>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{s.code} · {s.name}</option>)}</Select></Field>
          <div className="grid grid-cols-3 gap-3">
            <Field label="Term"><Select value={f.semester_id} onChange={(e) => set({ semester_id: e.target.value })}><option value="">Choose…</option>{terms.data?.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}</Select></Field>
            <Field label="Section"><Input value={f.section} onChange={(e) => set({ section: e.target.value.toUpperCase() })} /></Field>
            <Field label="Academic year"><Input value={f.academic_year} onChange={(e) => set({ academic_year: e.target.value })} placeholder="2026-2027" /></Field>
          </div>
        </>}
      </div>
    </Dialog>
  );
}

export function StructurePage() {
  const toast = useToast();
  const [tab, setTab] = useState('departments');
  const depts = useApi<DepartmentSummary[]>('/tenant/departments');
  const subjects = useApi<Subject[]>(tab === 'subjects' ? '/academics/subjects' : null);
  const assigns = useApi<TeachingAssignment[]>(tab === 'teaching' ? '/academics/assignments' : null);
  const sems = useApi<Semester[]>(tab === 'terms' ? '/academics/semesters' : null);
  const [f, setF] = useState({ code: '', name: '', hod_name: '' });
  const [open, setOpen] = useState(false);
  const [adding, setAdding] = useState<'subject' | 'term' | 'teaching' | null>(null);
  const save = async () => {
    try { await api.post('/tenant/departments', f); toast('Department added'); setOpen(false); setF({ code: '', name: '', hod_name: '' }); depts.reload(); } catch (e) { toast(errorMessage(e), 'error'); }
  };
  const removeAssignment = async (id: number) => {
    try { await api.del(`/academics/assignments/${id}`); toast('Teaching assignment removed'); assigns.reload(); } catch (e) { toast(errorMessage(e), 'error'); }
  };
  const addLabel = { departments: 'Add department', subjects: 'Add subject', teaching: 'Assign teaching', terms: 'Add term' }[tab];
  const onAdd = () => { if (tab === 'departments') setOpen(true); else setAdding(tab === 'subjects' ? 'subject' : tab === 'terms' ? 'term' : 'teaching'); };
  const dname = (id: number) => depts.data?.find((d) => d.id === id)?.code || id;
  return (
    <div>
      <PageHeader title="Academic structure" lede="Departments, subjects, terms and teaching assignments for your university. Teaching assignments decide which students each faculty member can see."
        actions={addLabel && <Button variant="primary" icon={<Plus size={14} />} onClick={onAdd}>{addLabel}</Button>} />
      <Tabs value={tab} onChange={setTab} className="mb-5" tabs={[{ id: 'departments', label: 'Departments' }, { id: 'subjects', label: 'Subjects' }, { id: 'teaching', label: 'Teaching assignments' }, { id: 'terms', label: 'Terms' }]} />
      <Panel padded={false}>
        {tab === 'departments' && <Async state={depts}>{(list) => <DataTable rows={list} columns={[
          { key: 'c', header: 'Code', render: (d) => <span className="font-medium">{d.code}</span> }, { key: 'n', header: 'Name', render: (d) => d.name },
          { key: 'h', header: 'Head of department', hideOnMobile: true, render: (d) => d.hod_name || '—' },
          { key: 's', header: 'Students', align: 'right', render: (d) => d.student_count ?? 0 }, { key: 'f', header: 'Faculty', align: 'right', render: (d) => d.faculty_count },
        ]} />}</Async>}
        {tab === 'subjects' && <Async state={subjects}>{(list) => <DataTable rows={list} columns={[
          { key: 'c', header: 'Code', sort: (s) => s.code, render: (s) => <span className="font-medium">{s.code}</span> }, { key: 'n', header: 'Subject', render: (s) => s.name },
          { key: 'd', header: 'Department', render: (s) => dname(s.department_id) }, { key: 'sem', header: 'Semester', align: 'right', sort: (s) => s.semester_number, render: (s) => s.semester_number },
          { key: 'cr', header: 'Credits', align: 'right', render: (s) => s.credits }, { key: 't', header: 'Type', hideOnMobile: true, render: (s) => s.subject_type },
        ]} />}</Async>}
        {tab === 'teaching' && <Async state={assigns}>{(list) => <DataTable rows={list} empty={<EmptyState title="No teaching assignments" />} columns={[
          { key: 'f', header: 'Faculty', render: (a) => cleanName(a.faculty_name) }, { key: 's', header: 'Subject', render: (a) => `${a.subject_code} · ${a.subject_name}` },
          { key: 'sec', header: 'Section', render: (a) => a.section }, { key: 'y', header: 'Year', hideOnMobile: true, render: (a) => a.academic_year },
          { key: 'x', header: <span className="sr-only">Actions</span>, align: 'right', render: (a) => <Button size="sm" variant="ghost" onClick={() => removeAssignment(a.id)}>Remove</Button> },
        ]} />}</Async>}
        {tab === 'terms' && <Async state={sems}>{(list) => <DataTable rows={list} columns={[
          { key: 'n', header: 'Term', render: (s) => <span className="font-medium">{s.name}</span> }, { key: 'y', header: 'Academic year', render: (s) => s.academic_year },
          { key: 'd', header: 'Dates', hideOnMobile: true, render: (s) => s.start_date ? `${fmtDate(s.start_date)} – ${fmtDate(s.end_date)}` : '—' },
          { key: 'c', header: '', render: (s) => s.is_current ? <Badge tone="forest">Current</Badge> : null },
        ]} />}</Async>}
      </Panel>
      {adding && <StructureDialog kind={adding} departments={depts.data || []} onClose={() => setAdding(null)}
        onSaved={() => { subjects.reload(); assigns.reload(); sems.reload(); }} />}
      <Dialog open={open} onClose={() => setOpen(false)} title="Add department" footer={<><Button onClick={() => setOpen(false)}>Cancel</Button><Button variant="primary" disabled={f.code.length < 2 || f.name.length < 2} onClick={save}>Add department</Button></>}>
        <div className="space-y-3"><Field label="Code"><Input value={f.code} onChange={(e) => setF({ ...f, code: e.target.value.toUpperCase() })} placeholder="e.g. CSE" /></Field>
          <Field label="Name"><Input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
          <Field label="Head of department"><Input value={f.hod_name} onChange={(e) => setF({ ...f, hod_name: e.target.value })} /></Field></div>
      </Dialog>
    </div>
  );
}

/* ------------------------------------------------------------------ data import */
const IMPORT_FIELDS: Record<string, string[]> = {
  students: ['usn', 'srn', 'roll_number', 'full_name', 'email', 'department', 'semester', 'section', 'cgpa', 'attendance'],
  academic_records: ['usn', 'semester_number', 'subject_code', 'internal_marks', 'external_marks', 'total_marks', 'grade'],
  attendance: ['usn', 'subject_code', 'total_classes', 'attended_classes'],
};
export function ImportPage() {
  const toast = useToast();
  const jobs = useApi<ImportJob[]>('/imports/jobs');
  const [type, setType] = useState('students');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const form = (selected: File, m?: Record<string, string>) => { const fd = new FormData(); fd.append('file', selected); fd.append('import_type', type); if (m && Object.keys(m).length) fd.append('column_mapping', JSON.stringify(m)); return fd; };
  const runPreview = async (m = mapping) => {
    if (!file) return; setBusy('preview');
    try {
      const p = await api.post<ImportPreview>('/imports/preview', form(file, m)); setPreview(p);
      if (!Object.keys(m).length) {
        const auto: Record<string, string> = {};
        p.columns_detected.forEach((c) => { const k = c.trim().toLowerCase().replace(/\s+/g, '_'); if (IMPORT_FIELDS[type].includes(k)) auto[c] = k; });
        setMapping(auto);
      }
    } catch (e) { toast(errorMessage(e), 'error'); } finally { setBusy(null); }
  };
  const execute = async () => {
    setBusy('exec');
    if (!file) return;
    try { const j = await api.post<ImportJob>('/imports/execute', form(file, mapping)); toast(`Imported ${j.successful_rows} of ${j.total_rows} rows`); setPreview(null); setFile(null); jobs.reload(); }
    catch (e) { toast(errorMessage(e), 'error'); } finally { setBusy(null); }
  };
  useEffect(() => { setPreview(null); setMapping({}); }, [file, type]);
  return (
    <div>
      <PageHeader title="Data import" lede="Bring in students, results and attendance from CSV or Excel. Review the preview and fix errors before anything is saved. Imported students receive invitations." />
      <div className="grid gap-6 lg:grid-cols-[1fr_1.6fr]">
        <Panel title="1. Choose data and file">
          <div className="space-y-4">
            <Field label="What are you importing?"><Select value={type} onChange={(e) => setType(e.target.value)}><option value="students">Student records</option><option value="academic_records">Subject results</option><option value="attendance">Attendance</option></Select></Field>
            <div>
              <input ref={input} type="file" accept=".csv,.xlsx,.xls" className="sr-only" onChange={(e) => setFile(e.target.files?.[0] || null)} aria-label="Import file" />
              <button type="button" onClick={() => input.current?.click()} className="flex w-full flex-col items-center gap-1.5 rounded-lg border border-dashed border-line-strong px-4 py-7 text-center hover:bg-sunken/50">
                <FileUp size={20} className="text-muted" /><span className="text-[13.5px] font-medium">{file ? file.name : 'Select a CSV or Excel file'}</span><span className="text-[12px] text-muted">Up to 10 MB</span>
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="primary" disabled={!file} loading={busy === 'preview'} onClick={() => runPreview()}>Preview import</Button>
              <Button variant="ghost" icon={<Download size={14} />} onClick={() => api.download(`/imports/template/${type}`, `acedra_template_${type}.csv`)}>Download template</Button>
            </div>
          </div>
        </Panel>
        <Panel title="2. Map columns and review" description={preview ? `${preview.total_rows} rows · ${preview.valid_rows_count} valid · ${preview.invalid_rows_count} with errors` : 'The preview appears here.'}>
          {!preview ? <EmptyState title="No file previewed yet" /> : (
            <div className="space-y-5">
              <div className="grid gap-2 sm:grid-cols-2">
                {preview.columns_detected.map((c: string) => (
                  <div key={c} className="flex items-center gap-2 text-[13px]"><span className="w-32 truncate text-muted" title={c}>{c}</span><span className="text-faint">→</span>
                    <Select value={mapping[c] || ''} onChange={(e) => setMapping({ ...mapping, [c]: e.target.value })} className="h-8"><option value="">Keep as is</option>{IMPORT_FIELDS[type].map((f) => <option key={f} value={f}>{f}</option>)}</Select></div>
                ))}
              </div>
              <Button size="sm" icon={<RefreshCw size={13} />} loading={busy === 'preview'} onClick={() => runPreview(mapping)}>Apply mapping</Button>
              {preview.errors?.length > 0 && <Notice tone="attention" title={`${preview.errors.length} row(s) need attention`}>
                <ul className="mt-1 max-h-40 space-y-0.5 overflow-y-auto">{preview.errors.slice(0, 50).map((e) => <li key={e.row_number}>Row {e.row_number}: {e.error_message}</li>)}</ul></Notice>}
              {preview.preview_rows?.length > 0 && (
                <div className="overflow-x-auto rounded border border-line"><table className="w-full text-[12px]"><thead><tr className="border-b border-line bg-sunken/50">{Object.keys(preview.preview_rows[0]).slice(0, 8).map((k) => <th key={k} className="px-2.5 py-1.5 text-left font-medium text-muted">{k}</th>)}</tr></thead>
                  <tbody>{preview.preview_rows.slice(0, 8).map((r, i: number) => <tr key={i} className="border-b border-line last:border-0">{Object.keys(preview.preview_rows[0]).slice(0, 8).map((k) => <td key={k} className="px-2.5 py-1.5">{String(r[k] ?? '')}</td>)}</tr>)}</tbody></table></div>
              )}
              <div className="flex justify-end"><Button variant="primary" icon={<Upload size={14} />} disabled={!preview.valid_rows_count} loading={busy === 'exec'} onClick={execute}>Import {preview.valid_rows_count} valid row(s)</Button></div>
            </div>
          )}
        </Panel>
      </div>
      <Panel title="Import history" padded={false} className="mt-6">
        <Async state={jobs}>{(list) => <DataTable rows={list} empty={<EmptyState title="No imports yet" />} columns={[
          { key: 'f', header: 'File', render: (j) => <span className="font-medium">{j.filename}</span> }, { key: 't', header: 'Type', render: (j) => titleCase(j.import_type) },
          { key: 'r', header: 'Rows', align: 'right', render: (j) => `${j.successful_rows} / ${j.total_rows}` },
          { key: 'e', header: 'Failed', align: 'right', render: (j) => <span className={j.failed_rows ? 'text-bronze' : ''}>{j.failed_rows}</span> },
          { key: 's', header: 'Status', render: (j) => <StatusBadge status={j.status?.toLowerCase()} label={titleCase(j.status)} /> },
          { key: 'd', header: 'When', hideOnMobile: true, render: (j) => fmtDate(j.created_at, true) },
        ]} />}</Async>
      </Panel>
    </div>
  );
}

/* ------------------------------------------------------------------ rules */
// Must match RISK_INDICATOR_TYPES in backend/app/schemas/risk.py (composite rules are edited via the API).
const INDICATORS = ['attendance_percentage', 'assessment_percentage', 'sgpa_drop', 'backlog_count', 'missing_assessments'];
export function RulesPage() {
  const toast = useToast();
  const rules = useApi<RiskRule[]>('/risk/rules');
  const [edit, setEdit] = useState<(Omit<RiskRuleInput, 'threshold_value'> & { id?: number; threshold_value: number | string }) | null>(null);
  const save = async () => {
    if (!edit) return;
    const body = { name: edit.name, code: edit.code, description: edit.description, category: edit.category, severity: edit.severity, indicator_type: edit.indicator_type, operator: edit.operator, threshold_value: Number(edit.threshold_value), suggested_action: edit.suggested_action, is_active: edit.is_active, conditions_config: edit.conditions_config || null };
    try { if (edit.id) await api.put(`/risk/rules/${edit.id}`, body); else await api.post('/risk/rules', body); toast('Rule saved — it applies from the next evaluation'); setEdit(null); rules.reload(); }
    catch (e) { toast(errorMessage(e), 'error'); }
  };
  return (
    <div>
      <PageHeader title="Early-warning rules" lede="Transparent thresholds your university controls. ACEDRA uses these rules — not a trained predictive model — and alerts never trigger penalties."
        actions={<Button variant="primary" icon={<Plus size={14} />} onClick={() => setEdit({ name: '', code: '', category: 'ATTENDANCE', severity: 'MODERATE', indicator_type: 'attendance_percentage', operator: '<', threshold_value: 75, suggested_action: '', description: '', is_active: true })}>New rule</Button>} />
      <Panel padded={false}>
        <Async state={rules}>{(list) => <DataTable rows={list} onRowClick={(r) => setEdit({ ...r })} columns={[
          { key: 'n', header: 'Rule', render: (r) => <div><div className="font-medium">{r.name}</div><div className="text-[12px] text-muted">{r.description}</div></div> },
          { key: 'c', header: 'Condition', render: (r) => <span className="whitespace-nowrap tnum">{titleCase(r.indicator_type)} {r.operator} {r.threshold_value}</span> },
          { key: 's', header: 'Severity', render: (r) => <StatusBadge status={r.severity} /> },
          { key: 'a', header: 'Status', render: (r) => r.is_active ? <Badge tone="ok" dot>Active</Badge> : <Badge dot>Paused</Badge> },
        ]} />}</Async>
      </Panel>
      {edit && (
        <Dialog open onClose={() => setEdit(null)} title={edit.id ? 'Edit rule' : 'New rule'} wide footer={<><Button onClick={() => setEdit(null)}>Cancel</Button><Button variant="primary" disabled={!edit.name || !edit.code} onClick={save}>Save rule</Button></>}>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Name"><Input value={edit.name} onChange={(e) => setEdit({ ...edit, name: e.target.value })} /></Field>
            <Field label="Code"><Input value={edit.code} disabled={!!edit.id} onChange={(e) => setEdit({ ...edit, code: e.target.value.toUpperCase().replace(/\s/g, '_') })} /></Field>
            <Field label="Indicator"><Select value={edit.indicator_type} onChange={(e) => setEdit({ ...edit, indicator_type: e.target.value })}>{[...new Set([...INDICATORS, edit.indicator_type])].map((i) => <option key={i} value={i}>{titleCase(i)}</option>)}</Select></Field>
            <div className="grid grid-cols-[5rem_1fr] gap-2"><Field label="Operator"><Select value={edit.operator} onChange={(e) => setEdit({ ...edit, operator: e.target.value })}>{['<', '<=', '>', '>=', '=='].map((o) => <option key={o}>{o}</option>)}</Select></Field>
              <Field label="Threshold"><Input type="number" step="0.1" value={edit.threshold_value} onChange={(e) => setEdit({ ...edit, threshold_value: e.target.value })} /></Field></div>
            <Field label="Category"><Select value={edit.category} onChange={(e) => setEdit({ ...edit, category: e.target.value })}>{['ATTENDANCE', 'ASSESSMENT', 'ACADEMIC', 'BACKLOG', 'COMPOSITE'].map((c) => <option key={c} value={c}>{titleCase(c)}</option>)}</Select></Field>
            <Field label="Severity"><Select value={edit.severity} onChange={(e) => setEdit({ ...edit, severity: e.target.value })}>{['MODERATE', 'HIGH', 'CRITICAL'].map((c) => <option key={c} value={c}>{titleCase(c)}</option>)}</Select></Field>
            <Field label="Description" className="sm:col-span-2"><Input value={edit.description || ''} onChange={(e) => setEdit({ ...edit, description: e.target.value })} /></Field>
            <Field label="Suggested support action" className="sm:col-span-2"><Textarea value={edit.suggested_action || ''} onChange={(e) => setEdit({ ...edit, suggested_action: e.target.value })} /></Field>
            <Checkbox label="Rule is active" checked={edit.is_active} onChange={(v) => setEdit({ ...edit, is_active: v })} />
          </div>
        </Dialog>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ catalogue */
export function CataloguePage() {
  const toast = useToast();
  const items = useApi<CatalogueItem[]>('/recommendations/catalogue');
  const [edit, setEdit] = useState<(Partial<CatalogueItemInput> & { id?: number }) | null>(null);
  const save = async () => {
    if (!edit) return;
    try { if (edit.id) await api.put(`/recommendations/catalogue/${edit.id}`, edit); else await api.post('/recommendations/catalogue', { ...edit, resources: [] }); toast('Catalogue item saved'); setEdit(null); items.reload(); }
    catch (e) { toast(errorMessage(e), 'error'); }
  };
  return (
    <div>
      <PageHeader title="Recommendation catalogue" lede="Approved courses, practice sets and programmes ACEDRA can suggest. Recommendations always cite the gap they address."
        actions={<Button variant="primary" icon={<Plus size={14} />} onClick={() => setEdit({ title: '', category: 'SUBJECT_IMPROVEMENT', description: '', difficulty_level: 'Intermediate', provider: '', resource_url: '', estimated_duration: '', expected_learning_outcome: '', status: 'Active' })}>Add item</Button>} />
      <Panel padded={false}>
        <Async state={items}>{(list) => <DataTable rows={list} onRowClick={(r) => setEdit({ ...r })} columns={[
          { key: 't', header: 'Item', render: (r) => <div><div className="font-medium">{r.title}</div><div className="line-clamp-1 text-[12px] text-muted">{r.description}</div></div> },
          { key: 'c', header: 'Category', hideOnMobile: true, render: (r) => titleCase(r.category) },
          { key: 'p', header: 'Provider', hideOnMobile: true, render: (r) => r.provider || '—' },
          { key: 'd', header: 'Duration', hideOnMobile: true, render: (r) => r.estimated_duration || '—' },
          { key: 's', header: 'Status', render: (r) => <StatusBadge status={r.status?.toLowerCase()} label={r.status} /> },
        ]} />}</Async>
      </Panel>
      {edit && (
        <Dialog open onClose={() => setEdit(null)} title={edit.id ? 'Edit catalogue item' : 'Add catalogue item'} wide footer={<><Button onClick={() => setEdit(null)}>Cancel</Button><Button variant="primary" disabled={!edit.title || !edit.description} onClick={save}>Save item</Button></>}>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Title" className="sm:col-span-2"><Input value={edit.title} onChange={(e) => setEdit({ ...edit, title: e.target.value })} /></Field>
            <Field label="Category"><Select value={edit.category} onChange={(e) => setEdit({ ...edit, category: e.target.value })}>{['SUBJECT_IMPROVEMENT', 'ATTENDANCE_RECOVERY', 'EXAMINATION_PREPARATION', 'CERTIFICATION', 'PROGRAMMING_PRACTICE', 'PROJECT', 'INTERNSHIP', 'PLACEMENT_PREPARATION', 'SKILL_DEVELOPMENT', 'CAREER_DEVELOPMENT'].map((c) => <option key={c} value={c}>{titleCase(c)}</option>)}</Select></Field>
            <Field label="Difficulty"><Select value={edit.difficulty_level} onChange={(e) => setEdit({ ...edit, difficulty_level: e.target.value })}>{['Beginner', 'Intermediate', 'Advanced'].map((c) => <option key={c}>{c}</option>)}</Select></Field>
            <Field label="Provider"><Input value={edit.provider || ''} onChange={(e) => setEdit({ ...edit, provider: e.target.value })} /></Field>
            <Field label="Estimated duration"><Input value={edit.estimated_duration || ''} onChange={(e) => setEdit({ ...edit, estimated_duration: e.target.value })} placeholder="e.g. 3 weeks" /></Field>
            <Field label="Resource link" className="sm:col-span-2"><Input value={edit.resource_url || ''} onChange={(e) => setEdit({ ...edit, resource_url: e.target.value })} /></Field>
            <Field label="Description" className="sm:col-span-2"><Textarea value={edit.description} onChange={(e) => setEdit({ ...edit, description: e.target.value })} /></Field>
            <Field label="Expected outcome" className="sm:col-span-2"><Input value={edit.expected_learning_outcome || ''} onChange={(e) => setEdit({ ...edit, expected_learning_outcome: e.target.value })} /></Field>
            <Field label="Status"><Select value={edit.status} onChange={(e) => setEdit({ ...edit, status: e.target.value })}><option>Active</option><option>Inactive</option></Select></Field>
          </div>
        </Dialog>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ knowledge base */
const DOC_CATS = ['ACADEMIC_REGULATIONS', 'ATTENDANCE_GUIDELINES', 'EXAMINATION_GUIDELINES', 'DEPARTMENT_INFO', 'COURSE_INFO', 'INTERNSHIP_GUIDELINES', 'PLACEMENT_GUIDELINES', 'CAMPUS_HANDBOOK', 'GENERAL_POLICY'];
const ACCESS: Record<string, string> = { PUBLIC: 'Everyone at the university', AUTHENTICATED_STUDENT: 'Students and staff', FACULTY_ONLY: 'Faculty and mentors', ADMIN_ONLY: 'Administrators only' };
export function DocumentsPage() {
  const toast = useToast();
  const docs = useApi<AssistantDocument[]>('/ai/documents');
  const status = useApi<AssistantStatus>('/ai/status');
  const [open, setOpen] = useState(false);
  const [del, setDel] = useState<AssistantDocument | null>(null);
  const [q, setQ] = useState(''); const [results, setResults] = useState<RetrievalResult | null>(null);
  const [f, setF] = useState<{ title: string; category: string; access_permission: string; description: string; file: File | null }>({ title: '', category: 'GENERAL_POLICY', access_permission: 'PUBLIC', description: '', file: null });
  const [saving, setSaving] = useState(false);
  const upload = async () => {
    setSaving(true);
    if (!f.file) return;
    const fd = new FormData(); fd.append('file', f.file); fd.append('title', f.title); fd.append('category', f.category); fd.append('access_permission', f.access_permission); if (f.description) fd.append('description', f.description);
    try { await api.post('/ai/documents/upload', fd); toast('Document indexed'); setOpen(false); docs.reload(); } catch (e) { toast(errorMessage(e), 'error'); } finally { setSaving(false); }
  };
  return (
    <div>
      <PageHeader title="Knowledge base" lede="Approved documents the university assistant answers from. Access levels control who can retrieve each document."
        actions={<Button variant="primary" icon={<Upload size={14} />} onClick={() => setOpen(true)}>Upload document</Button>} />
      {status.data && <div className="mb-5"><Notice>Retrieval: {status.data.retrieval}. {status.data.llm_configured ? `Answers are written by ${status.data.llm_model}.` : 'No language model is connected, so answers quote documents directly.'}</Notice></div>}
      <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <Panel padded={false}>
          <Async state={docs}>{(list) => <DataTable rows={list} empty={<EmptyState title="No documents yet" />} columns={[
            { key: 't', header: 'Document', render: (d) => <div><div className="font-medium">{d.title}</div><div className="text-[12px] text-muted">{d.file_name} · {d.chunk_count} passages</div></div> },
            { key: 'c', header: 'Category', hideOnMobile: true, render: (d) => titleCase(d.category) },
            { key: 'a', header: 'Who can retrieve', hideOnMobile: true, render: (d) => ACCESS[d.access_permission] || d.access_permission },
            { key: 'i', header: 'Indexed', hideOnMobile: true, render: (d) => fmtDate(d.indexed_at) },
            { key: 'x', header: '', align: 'right', render: (d) => <div className="flex justify-end gap-1">
              <Button size="sm" variant="ghost" onClick={async () => { await api.post(`/ai/documents/${d.id}/reindex`); toast('Reindexed'); docs.reload(); }}>Reindex</Button>
              <Button size="sm" variant="quiet" aria-label={`Delete ${d.title}`} onClick={() => setDel(d)}><Trash2 size={13} /></Button></div> },
          ]} />}</Async>
        </Panel>
        <Panel title="Test retrieval" description="See which passages a question would retrieve.">
          <form onSubmit={async (e) => { e.preventDefault(); setResults(await api.get('/ai/rag/search', { q, top_k: 4 })); }} className="flex gap-2">
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. condonation of attendance" /><Button type="submit" disabled={!q.trim()}>Search</Button>
          </form>
          {results && <ul className="mt-4 space-y-3">{results.results.length ? results.results.map((r, i) => (
            <li key={i} className="text-[12.5px]"><div className="flex justify-between gap-2"><span className="font-medium">{r.document_title}</span><span className="tnum text-faint">{num(r.score, 2)}</span></div><p className="mt-0.5 line-clamp-3 text-muted">{r.chunk?.content}</p></li>
          )) : <li className="text-[13px] text-muted">No passages matched.</li>}</ul>}
        </Panel>
      </div>
      <Dialog open={open} onClose={() => setOpen(false)} title="Upload document" description="PDF, DOCX, TXT or Markdown, up to 10 MB. Text is extracted, split into passages and indexed for your university only."
        footer={<><Button onClick={() => setOpen(false)}>Cancel</Button><Button variant="primary" loading={saving} disabled={!f.file || !f.title} onClick={upload}>Upload and index</Button></>}>
        <div className="space-y-4">
          <Field label="File"><Input type="file" accept=".pdf,.docx,.txt,.md" onChange={(e) => { const file = e.target.files?.[0] || null; setF({ ...f, file, title: f.title || (file?.name.replace(/\.[^.]+$/, '') ?? '') }); }} className="py-1.5" /></Field>
          <Field label="Title"><Input value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Category"><Select value={f.category} onChange={(e) => setF({ ...f, category: e.target.value })}>{DOC_CATS.map((c) => <option key={c} value={c}>{titleCase(c)}</option>)}</Select></Field>
            <Field label="Who can retrieve it"><Select value={f.access_permission} onChange={(e) => setF({ ...f, access_permission: e.target.value })}>{Object.entries(ACCESS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</Select></Field>
          </div>
          <Field label="Description"><Textarea value={f.description} onChange={(e) => setF({ ...f, description: e.target.value })} /></Field>
        </div>
      </Dialog>
      <ConfirmDialog open={!!del} onClose={() => setDel(null)} danger title="Delete document?" confirmLabel="Delete document"
        onConfirm={async () => { if (!del) return; await api.del(`/ai/documents/${del.id}`); toast('Document deleted'); setDel(null); docs.reload(); }}>
        “{del?.title}” and its indexed passages will be removed. The assistant will no longer cite it.
      </ConfirmDialog>
    </div>
  );
}

/* ------------------------------------------------------------------ reports */
const REPORTS: [string, string, string][] = [
  ['STUDENT_PROGRESS', 'Student progress', 'CGPA, attendance and alerts for each student.'],
  ['RISK_SUMMARY', 'Early-warning summary', 'Open and resolved alerts by rule and severity.'],
  ['MENTOR_INTERVENTIONS', 'Interventions', 'Cases, follow-ups and outcomes by mentor.'],
  ['DEPARTMENT_SUMMARY', 'Department summary', 'Performance and attendance by department.'],
  ['PLACEMENT_READINESS', 'Placement readiness', 'Eligibility, readiness and applications.'],
];
export function ReportsPage() {
  const toast = useToast();
  const reports = useApi<ReportExport[]>('/reports');
  const [busy, setBusy] = useState<string | null>(null);
  const gen = async (t: string) => {
    setBusy(t);
    try { await api.post('/reports/export', { report_type: t, file_format: 'CSV' }); toast('Report generated'); reports.reload(); } catch (e) { toast(errorMessage(e), 'error'); } finally { setBusy(null); }
  };
  return (
    <div>
      <PageHeader title="Reports" lede="CSV exports generated from current records. Each export is logged in the audit trail." />
      <div className="grid gap-6 lg:grid-cols-[1fr_1.5fr]">
        <Panel title="Generate" padded={false}>
          <ul className="divide-y divide-line">{REPORTS.map(([t, n, d]) => (
            <li key={t} className="flex items-center justify-between gap-3 px-4 py-3"><div><div className="font-medium">{n}</div><div className="text-[12.5px] text-muted">{d}</div></div><Button size="sm" loading={busy === t} onClick={() => gen(t)}>Generate</Button></li>
          ))}</ul>
        </Panel>
        <Panel title="Recent exports" padded={false}>
          <Async state={reports}>{(list) => <DataTable rows={list} empty={<EmptyState title="No reports yet" />} columns={[
            { key: 't', header: 'Report', render: (r) => <div><div className="font-medium">{r.title}</div><div className="text-[12px] text-muted">{cleanName(r.generated_by_name)}</div></div> },
            { key: 'd', header: 'Generated', hideOnMobile: true, render: (r) => fmtDate(r.created_at, true) },
            { key: 'x', header: '', align: 'right', render: (r) => <Button size="sm" variant="ghost" icon={<Download size={13} />} onClick={() => api.download(`/reports/${r.id}/download`, r.file_name)}>CSV</Button> },
          ]} />}</Async>
        </Panel>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ audit */
type AuditRow = Pick<AuditLogEntry, 'id' | 'action' | 'resource_type' | 'resource_id' | 'ip_address' | 'created_at'> & {
  actor?: string | null; user_name?: string | null; university?: string | null;
};

export function AuditPage({ platform }: { platform?: boolean }) {
  const [skip, setSkip] = useState(0);
  const [action, setAction] = useState('');
  // The platform log is paginated ({ total, items }); a university's log is a plain list.
  const logs = useApi<PlatformAuditList | AuditLogEntry[]>(platform ? '/platform/audit-logs' : '/audit-logs/', platform ? { skip, limit: 50, action } : { limit: 200 });
  const rows: AuditRow[] = !logs.data ? [] : Array.isArray(logs.data) ? logs.data : logs.data.items;
  const total = logs.data && !Array.isArray(logs.data) ? logs.data.total : 0;
  return (
    <div>
      <PageHeader title="Audit log" lede={platform ? 'Security and configuration events across the platform, including every student-data access under a grant.' : 'Sign-ins, invitations, configuration changes and data access in your university.'} />
      <Panel padded={false}>
        {platform && <Toolbar><Select value={action} onChange={(e) => { setAction(e.target.value); setSkip(0); }} className="w-64" aria-label="Action">
          <option value="">All events</option>{['LOGIN_SUCCESS', 'LOGIN_FAILED', 'TENANT_CREATED', 'TENANT_STATUS_CHANGED', 'PRIMARY_EMPLOYEE_ASSIGNED', 'STUDENT_DATA_GRANT_CREATED', 'STUDENT_DATA_ACCESSED', 'ENQUIRY_STATUS_CHANGED', 'USER_INVITED'].map((a) => <option key={a} value={a}>{titleCase(a)}</option>)}</Select></Toolbar>}
        <Async state={logs}>{() => (
          <>
            <DataTable rows={rows} dense empty={<EmptyState title="No events recorded" />} columns={[
              { key: 'w', header: 'When', render: (a) => <span className="whitespace-nowrap">{fmtDate(a.created_at, true)}</span> },
              { key: 'a', header: 'Event', render: (a) => titleCase(a.action) },
              { key: 'u', header: 'By', render: (a) => cleanName(a.actor || a.user_name) || <span className="text-faint">System</span> },
              ...(platform ? [{ key: 'un', header: 'University', render: (a: AuditRow) => a.university || '—' }] : []),
              { key: 'r', header: 'Resource', hideOnMobile: true, render: (a) => a.resource_type ? `${a.resource_type}${a.resource_id ? ` #${a.resource_id}` : ''}` : '—' },
              { key: 'ip', header: 'IP', hideOnMobile: true, render: (a) => a.ip_address || '—' },
            ]} />
            {platform && logs.data && <Pagination total={total} skip={skip} limit={50} onChange={setSkip} />}
          </>
        )}</Async>
      </Panel>
    </div>
  );
}

/* ------------------------------------------------------------------ settings */
export function SettingsPage() {
  const toast = useToast();
  const p = useApi<TenantProfile>('/tenant/profile');
  // Numeric fields are edited as text and converted on save.
  const [f, setF] = useState<{ tagline: string; att: string; ia: string; term: string; cats: string; notif: Record<string, unknown> } | null>(null);
  useEffect(() => { if (p.data) setF({ tagline: p.data.tagline || '', att: String(p.data.academic_structure?.minimum_attendance_percent ?? 75), ia: String(p.data.academic_structure?.internal_assessment_max ?? 50), term: p.data.academic_structure?.term_label || 'Semester', cats: (p.data.document_categories || []).join('\n'), notif: p.data.notification_settings || {} }); }, [p.data]);
  const save = async () => {
    if (!f) return;
    try {
      await api.patch('/tenant/settings', { tagline: f.tagline, academic_structure: { minimum_attendance_percent: Number(f.att), internal_assessment_max: Number(f.ia), term_label: f.term }, document_categories: f.cats.split('\n'), notification_settings: f.notif });
      toast('Settings saved'); p.reload();
    } catch (e) { toast(errorMessage(e), 'error'); }
  };
  return (
    <div>
      <PageHeader title="University settings" lede="Settings within your authority. Identity, email domains and enabled modules are managed with your dedicated ACEDRA contact under your service agreement." />
      <Async state={p}>{(d) => f && (
        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="space-y-6">
            <Panel title="Academic policy" description="Used by dashboards and default attendance rules.">
              <div className="grid gap-4 sm:grid-cols-3">
                <Field label="Minimum attendance %"><Input type="number" min={40} max={100} value={f.att} onChange={(e) => setF({ ...f, att: e.target.value })} /></Field>
                <Field label="Internal assessment maximum"><Input type="number" value={f.ia} onChange={(e) => setF({ ...f, ia: e.target.value })} /></Field>
                <Field label="Term label"><Select value={f.term} onChange={(e) => setF({ ...f, term: e.target.value })}><option>Semester</option><option>Term</option><option>Trimester</option></Select></Field>
              </div>
            </Panel>
            <Panel title="Workspace">
              <div className="space-y-4">
                <Field label="Tagline shown to members"><Input value={f.tagline} onChange={(e) => setF({ ...f, tagline: e.target.value })} /></Field>
                <Field label="Document categories" hint="One per line"><Textarea value={f.cats} onChange={(e) => setF({ ...f, cats: e.target.value })} /></Field>
              </div>
            </Panel>
            <Panel title="Notifications">
              <div className="space-y-3">
                {[['risk_alerts', 'Notify mentors when an early alert is raised'], ['intervention_updates', 'Notify staff when interventions change status'], ['weekly_digest', 'Weekly summary for administrators']].map(([k, l]) => (
                  <Checkbox key={k} label={l} checked={!!f.notif[k]} onChange={(v) => setF({ ...f, notif: { ...f.notif, [k]: v } })} />
                ))}
              </div>
            </Panel>
            <div className="flex justify-end"><Button variant="primary" onClick={save}>Save settings</Button></div>
          </div>
          <div className="space-y-6">
            <Panel title="Your ACEDRA contact" description="Your dedicated point of contact for onboarding, configuration and service changes.">
              {d.acedra_contact ? <KeyValues cols={1} items={[['Name', d.acedra_contact.full_name], ['Role', d.acedra_contact.title], ['Email', <a className="link" href={`mailto:${d.acedra_contact.email}`}>{d.acedra_contact.email}</a>], ['Phone', d.acedra_contact.phone]]} /> : <EmptyState title="No contact assigned" />}
            </Panel>
            <Panel title="Managed by ACEDRA">
              <KeyValues cols={1} items={[
                ['University', d.name], ['Status', <StatusBadge status={d.status} />],
                ['Email domains', d.domains?.map((x) => x.domain).join(', ') || '—'],
                ['Student email accounts', d.student_email_mode === 'rio_assisted' ? 'ACEDRA-assisted (additional service)' : 'Provided by the university'],
                ['Enabled modules', <span>{d.enabled_modules.length} of 6</span>], ['Service agreement', d.agreement_reference || '—'],
              ]} />
            </Panel>
          </div>
        </div>
      )}</Async>
    </div>
  );
}

export { cx };
