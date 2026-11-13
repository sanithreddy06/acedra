import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { api, errorMessage } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useApi } from '../lib/useApi';
import { cleanName, fmtDate, num, pct, titleCase } from '../lib/format';
import { PageHeader } from '../components/shell';
import { ChartContainer, ColumnChart, Distribution } from '../components/charts';
import type { AdminAnalytics, AdminDashboard, MentorDashboard, PlacementDashboard, Application, CareerRole, DepartmentSummary, FacultyAnalytics, Opportunity, PlacementReadiness, RiskAlertList, RiskStatistics, RoleDashboard, StudentProfile } from '../types/api';
import {
  Async, Badge, Button, cx, DataTable, Dialog, Drawer, EmptyState, Field, Input, Meter, Notice, Pagination, Panel, SearchInput, Select,
  Stat, StatStrip, StatusBadge, Textarea, Toolbar, useToast,
} from '../components/ui';

const words = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];
const say = (n: number) => (n <= 10 ? words[n] : String(n));
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

/* ------------------------------------------------------------------ faculty */
export function FacultyOverview() {
  const { me, hasModule } = useAuth();
  const nav = useNavigate();
  const a = useApi<FacultyAnalytics>('/students/analytics/faculty');
  const alerts = useApi<RiskAlertList>(hasModule('risk_identification') ? '/risk/alerts' : null, { status: 'ACTIVE', limit: 6 });
  const minAtt = me?.university?.academic_structure?.minimum_attendance_percent ?? 75;
  const below = (a.data?.students_summary || []).filter((s) => s.attendance < minAtt);
  return (
    <div>
      <PageHeader meta={a.data?.department_name}
        title={a.data ? `${cap(say(a.data.total_assigned_students))} students in ${say(a.data.assigned_courses?.length || 0)} ${a.data.assigned_courses?.length === 1 ? 'course' : 'courses'}.` : 'Your teaching'}
        lede={a.data ? (below.length ? `${cap(say(below.length))} ${below.length === 1 ? 'is' : 'are'} below the ${minAtt}% attendance requirement.` : 'Attendance in your sections is above the requirement.') : undefined} />
      <Async state={a} rows={3}>{(d) => !d.profile_configured ? (
        <Notice title="Your faculty profile hasn’t been set up yet">Your administrator links your account to a department and assigns the sections you teach. Your students will appear here once that is done.</Notice>
      ) : (
        <>
          <StatStrip className="mb-6">
            <Stat label="Average attendance" value={pct(d.average_cohort_attendance, 1)} tone={d.average_cohort_attendance < minAtt ? 'attention' : undefined} />
            {/* The API reports the cohort’s average CGPA scaled to 100 as `average_cohort_marks`. */}
            <Stat label="Average CGPA" value={num(d.average_cohort_marks / 10, 2)} />
            <Stat label="Below attendance requirement" value={below.length} tone={below.length ? 'attention' : undefined} />
            {alerts.data && <Stat label="Open alerts" value={alerts.data.total} />}
          </StatStrip>
          <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
            <Panel title="Sections you teach" padded={false}>
              <ul className="divide-y divide-line">
                {d.assigned_courses?.map((c) => (
                  <li key={c.assignment_id} className="px-4 py-2.5"><div className="font-medium">{c.subject_name}</div><div className="text-[12px] text-muted">{c.subject_code} · Section {c.section} · {c.academic_year}</div></li>
                ))}
                {!d.assigned_courses?.length && <li className="px-4 py-6"><EmptyState title="No teaching assignments yet">Your administrator assigns sections in Academic structure.</EmptyState></li>}
              </ul>
            </Panel>
            <Panel title="Students" description="Sorted by attendance, lowest first" padded={false} actions={<Link to="/app/students"><Button size="sm" variant="ghost">All students</Button></Link>}>
              <DataTable rows={d.students_summary || []} onRowClick={(s) => nav(`/app/students/${s.id}`)} initialSort={{ key: 'att', dir: 'asc' }}
                empty={<EmptyState title="No students assigned" />} columns={[
                  { key: 'n', header: 'Student', sort: (s) => s.name, render: (s) => <div><div className="font-medium">{cleanName(s.name)}</div><div className="text-[12px] text-muted">{s.usn} · Sec {s.section}</div></div> },
                  { key: 'cgpa', header: 'CGPA', align: 'right', sort: (s) => s.cgpa, render: (s) => num(s.cgpa, 2) },
                  { key: 'att', header: 'Attendance', sort: (s) => s.attendance, className: 'w-44', render: (s) => <div className="flex items-center gap-2"><Meter value={s.attendance} threshold={minAtt} className="w-20" /><span className={cx('tnum text-[12.5px]', s.attendance < minAtt && 'font-medium text-bronze')}>{pct(s.attendance)}</span></div> },
                ]} />
            </Panel>
          </div>
          {!!alerts.data?.items.length && (
            <Panel className="mt-6" title="Recent alerts for your students" padded={false} actions={<Link to="/app/alerts"><Button size="sm" variant="ghost">Review alerts</Button></Link>}>
              <DataTable rows={alerts.data.items} dense columns={[
                { key: 's', header: 'Student', render: (x) => cleanName(x.student_name) },
                { key: 'r', header: 'Rule', render: (x) => x.rule_name },
                { key: 'v', header: 'Severity', render: (x) => <StatusBadge status={x.severity} /> },
              ]} />
            </Panel>
          )}
        </>
      )}</Async>
    </div>
  );
}

/* ------------------------------------------------------------------ mentor */
export function MentorOverview() {
  const nav = useNavigate();
  const d = useApi<RoleDashboard<MentorDashboard['quick_stats'], MentorDashboard['details']>>('/dashboards/me');
  const q = d.data?.quick_stats;
  const needs = (d.data?.details.mentee_roster || []).filter((m) => m.status && m.status !== 'On Track');
  return (
    <div>
      <PageHeader title={q ? (q.pending_followups_count ? `${cap(say(q.pending_followups_count))} follow-up${q.pending_followups_count === 1 ? '' : 's'} coming up.` : 'No follow-ups due.') : 'Your caseload'}
        lede={q ? `${q.total_mentees} mentees · ${q.open_interventions} open intervention${q.open_interventions === 1 ? '' : 's'} · ${q.at_risk_count} flagged for support` : undefined}
        actions={<Link to="/app/interventions"><Button variant="primary">Open interventions</Button></Link>} />
      <Async state={d} rows={4}>{({ details: det }) => (
        <div className="grid gap-6 lg:grid-cols-[1fr_1.3fr]">
          <div className="space-y-6">
            <Panel title="Upcoming follow-ups" padded={false}>
              {det.pending_followups?.length ? <ul className="divide-y divide-line">{det.pending_followups.map((f) => (
                <li key={f.id} className="flex items-center justify-between gap-3 px-4 py-2.5"><div><div className="font-medium">{cleanName(f.student_name)}</div><div className="text-[12px] text-muted">{f.intervention_title || `Case #${f.intervention_id}`}</div></div><span className="text-[13px] tnum">{fmtDate(f.scheduled_date)}</span></li>
              ))}</ul> : <div className="px-4"><EmptyState title="Nothing scheduled" /></div>}
            </Panel>
            <Panel title="Active interventions" padded={false}>
              {det.active_interventions?.length ? <ul className="divide-y divide-line">{det.active_interventions.map((i) => (
                <li key={i.id} className="px-4 py-2.5"><div className="flex items-center justify-between gap-2"><span className="font-medium">{i.title}</span><StatusBadge status={i.status} /></div><div className="text-[12px] text-muted">{cleanName(i.student_name)} · updated {fmtDate(i.updated_at)}</div></li>
              ))}</ul> : <div className="px-4"><EmptyState title="No active interventions" /></div>}
            </Panel>
          </div>
          <Panel title="Mentees" description={needs.length ? `${needs.length} flagged for support appear first` : undefined} padded={false}>
            <DataTable rows={[...needs, ...(det.mentee_roster || []).filter((m) => !needs.includes(m))]} onRowClick={(m) => nav(`/app/students/${m.id}`)}
              empty={<EmptyState title="No mentees assigned yet" />} columns={[
                { key: 'n', header: 'Student', render: (m) => <div><div className="font-medium">{cleanName(m.name)}</div><div className="text-[12px] text-muted">{m.usn} · Sem {m.semester}</div></div> },
                { key: 'c', header: 'CGPA', align: 'right', render: (m) => num(m.cgpa, 2) },
                { key: 'a', header: 'Attendance', align: 'right', render: (m) => pct(m.attendance) },
                { key: 's', header: 'Status', render: (m) => <Badge tone={m.status === 'On Track' ? 'ok' : 'bronze'} dot>{m.status}</Badge> },
              ]} />
          </Panel>
        </div>
      )}</Async>
    </div>
  );
}

/* ------------------------------------------------------------------ administrator */
export function AdminOverview() {
  const { me, hasModule } = useAuth();
  const a = useApi<AdminAnalytics>('/students/analytics/admin');
  const risk = useApi<RiskStatistics>(hasModule('risk_identification') ? '/risk/statistics' : null);
  const dash = useApi<RoleDashboard<AdminDashboard['quick_stats'], AdminDashboard['details']>>('/dashboards/me');
  const s = a.data?.institutional_stats;
  return (
    <div>
      <PageHeader meta={me?.university?.name} title={s ? `${s.total_students} students in ${say(s.total_departments)} departments.` : 'Institution overview'}
        lede={risk.data ? `${risk.data.total_students_at_risk} students currently have open early alerts.` : undefined} />
      <Async state={a} rows={4}>{(d) => (
        <>
          <StatStrip className="mb-6">
            <Stat label="Average CGPA" value={num(d.institutional_stats.campus_average_cgpa, 2)} />
            <Stat label="Average attendance" value={pct(d.institutional_stats.campus_average_attendance, 1)} />
            <Stat label="Active students" value={d.institutional_stats.active_students} />
            <Stat label="Faculty" value={d.institutional_stats.total_faculty} />
            {risk.data && <Stat label="Open alerts" value={risk.data.total_active_alerts} tone={risk.data.total_active_alerts ? 'attention' : undefined} />}
          </StatStrip>
          <Panel title="Departments" padded={false} className="mb-6">
            <DataTable rows={d.department_wise_stats} rowKey={(r) => r.department_code} columns={[
              { key: 'n', header: 'Department', sort: (r) => r.department_name, render: (r) => <div><div className="font-medium">{r.department_name}</div><div className="text-[12px] text-muted">{r.hod_name ? `HOD ${r.hod_name}` : r.department_code}</div></div> },
              { key: 's', header: 'Students', align: 'right', sort: (r) => r.total_students, render: (r) => r.total_students },
              { key: 'c', header: 'Avg CGPA', align: 'right', sort: (r) => r.average_cgpa, render: (r) => num(r.average_cgpa, 2) },
              { key: 'a', header: 'Avg attendance', align: 'right', sort: (r) => r.average_attendance, render: (r) => pct(r.average_attendance, 1) },
              { key: 'r', header: 'With open alerts', align: 'right', sort: (r) => r.at_risk_count, render: (r) => <span className={r.at_risk_count ? 'font-medium text-bronze' : ''}>{r.at_risk_count}</span> },
            ]} />
          </Panel>
          <div className="grid gap-6 lg:grid-cols-3">
            <Panel title="Attendance">
              <Distribution rows={[{ label: '85% and above', value: d.attendance_distribution.above_85 }, { label: '75–85%', value: d.attendance_distribution.between_75_85 }, { label: 'Below 75%', value: d.attendance_distribution.below_75_at_risk, attention: true }]} />
            </Panel>
            <Panel title="CGPA">
              <Distribution rows={[{ label: '9 and above', value: d.cgpa_distribution.tier_1_above_9 }, { label: '8–9', value: d.cgpa_distribution.tier_2_8_to_9 }, { label: '7–8', value: d.cgpa_distribution.tier_3_7_to_8 }, { label: '6–7', value: d.cgpa_distribution.tier_4_6_to_7 }, { label: 'Below 6', value: d.cgpa_distribution.below_6_at_risk, attention: true }]} />
            </Panel>
            <Panel title={`Students by ${(me?.university?.academic_structure?.term_label || 'semester').toLowerCase()}`}>
              <ChartContainer height={150}><ColumnChart data={d.semester_wise_performance.map((x) => ({ ...x, label: `${x.semester.charAt(0)}${x.semester_number}` }))} x="label" y="student_count" name="Students" /></ChartContainer>
            </Panel>
          </div>
          {dash.data?.quick_stats?.intervention_stats && (
            <Panel title="Support activity" className="mt-6">
              <StatStrip className="border-0 py-0">
                <Stat label="Interventions" value={dash.data.quick_stats.intervention_stats.total} />
                <Stat label="In progress" value={dash.data.quick_stats.intervention_stats.in_progress + dash.data.quick_stats.intervention_stats.assigned} />
                <Stat label="Resolved" value={dash.data.quick_stats.intervention_stats.resolved} tone="good" />
                <Stat label="Recommendations issued" value={dash.data.quick_stats.recommendation_stats.total} />
                <Stat label="Recommendations completed" value={dash.data.quick_stats.recommendation_stats.completed} />
              </StatStrip>
            </Panel>
          )}
        </>
      )}</Async>
    </div>
  );
}

/* ------------------------------------------------------------------ placement */
export function PlacementOverview() {
  const d = useApi<RoleDashboard<PlacementDashboard['quick_stats'], PlacementDashboard['details']>>('/dashboards/me');
  const q = d.data?.quick_stats;
  return (
    <div>
      <PageHeader title={q ? `${q.eligible_count} of ${q.total_students} students meet placement eligibility.` : 'Placement overview'}
        lede={q ? `${q.opportunities_count} ${q.opportunities_count === 1 ? 'opportunity' : 'opportunities'} · ${q.placed_count} placed so far` : undefined}
        actions={<Link to="/app/opportunities"><Button variant="primary">Manage opportunities</Button></Link>} />
      <Async state={d} rows={4}>{(x) => (
        <>
          <Panel title="Application pipeline" className="mb-6">
            <ol className="grid gap-px overflow-hidden rounded border border-line bg-line sm:grid-cols-5">
              {x.quick_stats.pipeline.map((p, i) => (
                <li key={p.stage} className="bg-surface px-4 py-3">
                  <div className="text-[12px] text-muted">{i + 1}. {p.stage}</div>
                  <div className="mt-1 text-[22px] font-semibold tnum">{p.count}</div>
                </li>
              ))}
            </ol>
          </Panel>
          <div className="grid gap-6 lg:grid-cols-2">
            <Panel title="Open opportunities" padded={false}>
              <DataTable rows={x.details.opportunities} dense empty={<EmptyState title="No open opportunities" />} columns={[
                { key: 't', header: 'Opportunity', render: (o) => <div><div className="font-medium">{o.title}</div><div className="text-[12px] text-muted">{o.company} · {o.location}</div></div> },
                { key: 'p', header: 'Package', hideOnMobile: true, render: (o) => o.salary_package },
                { key: 'd', header: 'Deadline', render: (o) => fmtDate(o.application_deadline) },
              ]} />
            </Panel>
            <Panel title="Career roles" padded={false}>
              <DataTable rows={x.details.roles} dense columns={[
                { key: 't', header: 'Role', render: (r) => r.title },
                { key: 's', header: 'Skills', align: 'right', render: (r) => r.required_skills_count },
                { key: 'c', header: 'Experience', hideOnMobile: true, render: (r) => r.min_experience_level || '—' },
                { key: 'd', header: 'Demand', hideOnMobile: true, render: (r) => r.category },
              ]} />
            </Panel>
          </div>
        </>
      )}</Async>
    </div>
  );
}

export function PlacementReadinessPage() {
  const roles = useApi<CareerRole[]>('/placement/roles');
  const [role, setRole] = useState('');
  const [search, setSearchValue] = useState('');
  const [skip, setSkip] = useState(0);
  const limit = 25;
  const setSearch = (v: string) => { setSearchValue(v); setSkip(0); };
  const students = useApi<StudentProfile[]>('/students/', { search, skip, limit });
  const count = useApi<{ total: number }>('/students/count', { search });
  const [selected, setSelected] = useState<StudentProfile | null>(null);
  const rows = students.data || [];
  return (
    <div>
      <PageHeader title="Student readiness" lede="Readiness compares a student’s skills with a role’s requirements. It is an internal indicator — not a prediction of placement or an employer certification." />
      <Panel padded={false}>
        <Toolbar>
          <SearchInput value={search} onChange={setSearch} placeholder="Search students" className="w-full sm:w-64" />
          <Select value={role} onChange={(e) => setRole(e.target.value)} className="w-56" aria-label="Role"><option value="">Each student’s target role</option>{roles.data?.map((r) => <option key={r.code} value={r.code}>{r.title}</option>)}</Select>
        </Toolbar>
        <Async state={students}>{() => (<>
          <DataTable rows={rows} empty={<EmptyState title="No students match" />} onRowClick={(s) => setSelected(s)} columns={[
            { key: 'n', header: 'Student', sort: (s) => s.full_name, render: (s) => <div><div className="font-medium">{cleanName(s.full_name)}</div><div className="text-[12px] text-muted">{s.usn} · {s.department_code}</div></div> },
            { key: 'c', header: 'CGPA', align: 'right', sort: (s) => s.cgpa, render: (s) => num(s.cgpa, 2) },
            { key: 'a', header: 'Attendance', align: 'right', sort: (s) => s.attendance_percentage, render: (s) => pct(s.attendance_percentage) },
            { key: 'p', header: 'Eligibility', render: (s) => <StatusBadge status={s.placement_status === 'Placed' ? 'placed' : s.placement_status === 'Eligible' ? 'ready' : 'pending'} label={s.placement_status} /> },
          ]} />
          <Pagination total={count.data?.total ?? skip + rows.length} skip={skip} limit={limit} onChange={setSkip} />
        </>)}</Async>
      </Panel>
      {selected && <ReadinessDrawer student={selected} role={role} onClose={() => setSelected(null)} />}
    </div>
  );
}

function ReadinessDrawer({ student, role, onClose }: { student: StudentProfile; role: string; onClose: () => void }) {
  const r = useApi<PlacementReadiness>(`/placement/readiness/${student.id}`, role ? { role } : undefined);
  return (
    <Drawer open onClose={onClose} title={cleanName(student.full_name)} subtitle={`${student.usn} · CGPA ${num(student.cgpa, 2)}`}>
      <Async state={r}>{(x) => (
        <div className="space-y-5">
          <StatStrip><Stat label={`Readiness · ${x.target_role?.title}`} value={pct(x.readiness_score)} note={titleCase(x.readiness_tier)} /><Stat label="Matched" value={`${x.skills_matched_count}/${x.total_role_skills_count}`} /><Stat label="Core skills met" value={x.mandatory_skills_met ? 'Yes' : 'No'} /></StatStrip>
          <DataTable rows={x.skill_gaps || []} rowKey={(g) => g.skill_name} dense columns={[
            { key: 'n', header: 'Skill', render: (g) => g.skill_name }, { key: 'r', header: 'Needed', render: (g) => g.required_proficiency },
            { key: 's', header: 'Has', render: (g) => g.student_proficiency || '—' },
            { key: 'v', header: 'Status', render: (g) => <span className={g.status === 'MATCHED' ? 'text-ok' : 'text-bronze'}>{titleCase(g.status)}</span> },
          ]} />
          <p className="text-[12px] text-faint">{x.disclaimer}</p>
        </div>
      )}</Async>
    </Drawer>
  );
}

export function OpportunitiesPage() {
  const { me } = useAuth();
  const toast = useToast();
  const opps = useApi<Opportunity[]>('/placement/opportunities');
  const roles = useApi<CareerRole[]>('/placement/roles');
  const depts = useApi<DepartmentSummary[]>('/tenant/departments');
  const [open, setOpen] = useState(false);
  const blank = { company_name: '', title: '', opportunity_type: 'JOB', role_id: '', location: '', work_mode: 'ONSITE', ctc_stipend: '', min_cgpa: '6.5', max_backlogs: '0', min_attendance: '75', application_deadline: '', open_positions: '1', description: '', eligible_departments: [] as string[] };
  const [f, setF] = useState(blank);
  const [saving, setSaving] = useState(false);
  const save = async () => {
    setSaving(true);
    try {
      await api.post('/placement/opportunities', { ...f, role_id: f.role_id ? Number(f.role_id) : null, min_cgpa: Number(f.min_cgpa), max_backlogs: Number(f.max_backlogs), min_attendance: Number(f.min_attendance), open_positions: Number(f.open_positions), eligible_semesters: [5, 6, 7, 8], status: 'OPEN', requirements: [] });
      toast('Opportunity published'); setOpen(false); setF(blank); opps.reload();
    } catch (e) { toast(errorMessage(e), 'error'); } finally { setSaving(false); }
  };
  return (
    <div>
      <PageHeader title="Opportunities" lede="Placement drives and internships with clear eligibility. Students see every open opportunity; those they do not qualify for are marked “Not eligible”."
        actions={me?.role === 'placement_officer' && <Button variant="primary" icon={<Plus size={14} />} onClick={() => setOpen(true)}>New opportunity</Button>} />
      <Panel padded={false}>
        <Async state={opps}>{(list) => (
          <DataTable rows={list} empty={<EmptyState title="No opportunities yet" action={<Button onClick={() => setOpen(true)}>Add the first one</Button>} />} columns={[
            { key: 't', header: 'Opportunity', sort: (o) => o.company_name, render: (o) => <div><div className="font-medium">{o.title}</div><div className="text-[12px] text-muted">{o.company_name} · {o.location} · {titleCase(o.work_mode)}</div></div> },
            { key: 'ty', header: 'Type', hideOnMobile: true, render: (o) => titleCase(o.opportunity_type) },
            { key: 'e', header: 'Eligibility', hideOnMobile: true, render: (o) => <span className="text-[12.5px]">CGPA {o.min_cgpa}+ · att. {o.min_attendance}% · ≤{o.max_backlogs} backlogs</span> },
            { key: 'p', header: 'Package', hideOnMobile: true, render: (o) => o.ctc_stipend },
            { key: 'a', header: 'Applicants', align: 'right', render: (o) => o.application_count },
            { key: 'd', header: 'Deadline', sort: (o) => o.application_deadline, render: (o) => fmtDate(o.application_deadline) },
            { key: 's', header: 'Status', render: (o) => <StatusBadge status={o.status} /> },
          ]} />
        )}</Async>
      </Panel>
      <Dialog open={open} onClose={() => setOpen(false)} title="New opportunity" wide
        footer={<><Button onClick={() => setOpen(false)}>Cancel</Button><Button variant="primary" loading={saving} disabled={!f.company_name || !f.title || !f.application_deadline} onClick={save}>Publish opportunity</Button></>}>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Company" required><Input value={f.company_name} onChange={(e) => setF({ ...f, company_name: e.target.value })} /></Field>
          <Field label="Title" required><Input value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></Field>
          <Field label="Type"><Select value={f.opportunity_type} onChange={(e) => setF({ ...f, opportunity_type: e.target.value })}><option value="JOB">Full-time role</option><option value="INTERNSHIP">Internship</option></Select></Field>
          <Field label="Career role"><Select value={f.role_id} onChange={(e) => setF({ ...f, role_id: e.target.value })}><option value="">None</option>{roles.data?.map((r) => <option key={r.id} value={r.id}>{r.title}</option>)}</Select></Field>
          <Field label="Location"><Input value={f.location} onChange={(e) => setF({ ...f, location: e.target.value })} /></Field>
          <Field label="Work mode"><Select value={f.work_mode} onChange={(e) => setF({ ...f, work_mode: e.target.value })}><option value="ONSITE">On-site</option><option value="HYBRID">Hybrid</option><option value="REMOTE">Remote</option></Select></Field>
          <Field label="Package / stipend"><Input value={f.ctc_stipend} onChange={(e) => setF({ ...f, ctc_stipend: e.target.value })} placeholder="e.g. 8 LPA" /></Field>
          <Field label="Application deadline" required><Input type="date" value={f.application_deadline} onChange={(e) => setF({ ...f, application_deadline: e.target.value })} /></Field>
          <Field label="Minimum CGPA"><Input type="number" step="0.1" value={f.min_cgpa} onChange={(e) => setF({ ...f, min_cgpa: e.target.value })} /></Field>
          <Field label="Minimum attendance %"><Input type="number" value={f.min_attendance} onChange={(e) => setF({ ...f, min_attendance: e.target.value })} /></Field>
          <Field label="Maximum backlogs"><Input type="number" value={f.max_backlogs} onChange={(e) => setF({ ...f, max_backlogs: e.target.value })} /></Field>
          <Field label="Open positions"><Input type="number" value={f.open_positions} onChange={(e) => setF({ ...f, open_positions: e.target.value })} /></Field>
          <div className="sm:col-span-2"><span className="label mb-1.5 block">Eligible departments</span><div className="flex flex-wrap gap-1.5">
            {depts.data?.map((d) => { const on = f.eligible_departments.includes(d.code); return (
              <button key={d.code} type="button" aria-pressed={on} onClick={() => setF({ ...f, eligible_departments: on ? f.eligible_departments.filter((x) => x !== d.code) : [...f.eligible_departments, d.code] })}
                className={cx('rounded border px-2 py-1 text-[12.5px]', on ? 'border-forest bg-forest-soft text-forest' : 'border-line-strong text-muted')}>{d.code}</button>); })}
          </div></div>
          <Field label="Description" className="sm:col-span-2"><Textarea value={f.description} onChange={(e) => setF({ ...f, description: e.target.value })} /></Field>
        </div>
      </Dialog>
    </div>
  );
}

const APP_STATUSES = ['APPLIED', 'SHORTLISTED', 'INTERVIEW_SCHEDULED', 'OFFERED', 'PLACED', 'REJECTED', 'WITHDRAWN'];
export function ApplicationsPage() {
  const toast = useToast();
  const [status, setStatusValue] = useState('');
  const [skip, setSkip] = useState(0);
  const limit = 25;
  const setStatus = (s: string) => { setStatusValue(s); setSkip(0); };
  const apps = useApi<Application[]>('/placement/applications', { status, skip, limit });
  const count = useApi<{ total: number }>('/placement/applications/count', { status });
  const update = async (a: Application, s: string) => {
    try { await api.put(`/placement/applications/${a.id}/status`, { status: s }); toast(`Moved to ${titleCase(s).toLowerCase()}`); apps.reload(); count.reload(); } catch (e) { toast(errorMessage(e), 'error'); }
  };
  return (
    <div>
      <PageHeader title="Applications" lede="Track each application from submission to outcome. Students see status changes in their workspace." />
      <Panel padded={false}>
        <Toolbar><Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-52" aria-label="Status"><option value="">All statuses</option>{APP_STATUSES.map((s) => <option key={s} value={s}>{titleCase(s)}</option>)}</Select></Toolbar>
        <Async state={apps}>{(list) => (<>
          <DataTable rows={list} empty={<EmptyState title="No applications match" />} columns={[
            { key: 's', header: 'Student', render: (a) => <div><div className="font-medium">{cleanName(a.student_name)}</div><div className="text-[12px] text-muted">{a.student_srn}</div></div> },
            { key: 'o', header: 'Opportunity', render: (a) => <div><div>{a.opportunity_title}</div><div className="text-[12px] text-muted">{a.company_name}</div></div> },
            { key: 'r', header: 'Readiness at apply', align: 'right', hideOnMobile: true, render: (a) => pct(a.readiness_score_at_application) },
            { key: 'd', header: 'Applied', hideOnMobile: true, render: (a) => fmtDate(a.applied_at) },
            { key: 'st', header: 'Status', render: (a) => (
              <Select value={a.status} onChange={(e) => update(a, e.target.value)} className="h-8 w-48" aria-label="Application status">{APP_STATUSES.map((s) => <option key={s} value={s}>{titleCase(s)}</option>)}</Select>) },
          ]} />
          <Pagination total={count.data?.total ?? skip + list.length} skip={skip} limit={limit} onChange={setSkip} />
        </>)}</Async>
      </Panel>
    </div>
  );
}

export function CareerRolesPage() {
  const roles = useApi<CareerRole[]>('/placement/roles');
  return (
    <div>
      <PageHeader title="Career roles" lede="The skills each role requires. Readiness scores are calculated against these definitions, so keep them current with recruiters’ expectations." />
      <Async state={roles}>{(list) => (
        <div className="grid gap-4 md:grid-cols-2">
          {list.map((r) => (
            <Panel key={r.id} title={r.title} description={`${r.min_experience_level} · ${r.average_salary_range} · demand ${r.industry_demand?.toLowerCase()}`}>
              <p className="mb-3 text-[13px] text-muted">{r.description}</p>
              <div className="flex flex-wrap gap-1.5">{r.skills?.map((s) => <Badge key={s.id} tone={s.is_mandatory ? 'forest' : 'neutral'}>{s.skill_name} · {s.min_proficiency}</Badge>)}</div>
            </Panel>
          ))}
        </div>
      )}</Async>
    </div>
  );
}
