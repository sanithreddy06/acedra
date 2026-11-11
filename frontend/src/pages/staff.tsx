import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, RefreshCw } from 'lucide-react';
import { api, errorMessage } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useApi } from '../lib/useApi';
import { cleanName, fmtDate, isBelow, num, pct, relTime, titleCase } from '../lib/format';
import { PageHeader } from '../components/shell';
import {
  Async, Avatar, Badge, Button, cx, DataTable, Dialog, Drawer, EmptyState, Field, Input, KeyValues, Meter, Notice, Pagination,
  Panel, SearchInput, Select, Stat, StatStrip, StatusBadge, Tabs, Textarea, Timeline, Toolbar, useToast,
} from '../components/ui';
import { StudentAcademics } from './student';
import type { DepartmentSummary, RiskAlert, RiskEvaluation, Intervention, InterventionDetail, MentorSummary, PlacementReadiness, Recommendation, RiskAlertDetail, RiskAlertList, RiskStatistics, StudentAnalytics, StudentProfile, StudentRiskProfile } from '../types/api';

/* ------------------------------------------------------------------ student directory */
export function StudentsPage() {
  const { me } = useAuth();
  const nav = useNavigate();
  const [search, setSearch] = useState('');
  const [semester, setSemester] = useState('');
  const [dept, setDept] = useState('');
  const [skip, setSkip] = useState(0);
  const limit = 50;
  const depts = useApi<DepartmentSummary[]>(me?.role === 'admin' || me?.role === 'placement_officer' ? '/tenant/departments' : null);
  const st = useApi<StudentProfile[]>('/students/', { search, semester, department_id: dept, skip, limit });
  const minAtt = me?.university?.academic_structure?.minimum_attendance_percent ?? 75;
  const title = me?.role === 'mentor' ? 'Mentees' : me?.role === 'faculty' ? 'My students' : 'Students';
  const lede = me?.role === 'faculty' ? 'Students in the sections you teach, plus any your administrator has explicitly shared with you.'
    : me?.role === 'mentor' ? 'Students assigned to you for mentoring.' : `Every student enrolled at ${me?.university?.short_name}.`;
  return (
    <div>
      <PageHeader title={title} lede={lede} />
      <Panel padded={false}>
        <Toolbar>
          <SearchInput value={search} onChange={(v) => { setSearch(v); setSkip(0); }} placeholder="Search name, USN or email" className="w-full sm:w-72" />
          <Select value={semester} onChange={(e) => { setSemester(e.target.value); setSkip(0); }} className="w-36" aria-label="Semester">
            <option value="">All semesters</option>{[1, 2, 3, 4, 5, 6, 7, 8].map((s) => <option key={s} value={s}>Semester {s}</option>)}
          </Select>
          {depts.data && <Select value={dept} onChange={(e) => { setDept(e.target.value); setSkip(0); }} className="w-52" aria-label="Department">
            <option value="">All departments</option>{depts.data.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</Select>}
        </Toolbar>
        <Async state={st}>{(rows) => (
          <>
            <DataTable rows={rows} onRowClick={(r) => nav(`/app/students/${r.id}`)}
              empty={<EmptyState title={search ? 'No students match your search' : 'No students to show'}>{me?.role === 'faculty' ? 'Students appear here once you are assigned to teach a section.' : undefined}</EmptyState>}
              columns={[
                { key: 'name', header: 'Student', sort: (r) => r.full_name, render: (r) => (
                  <div className="flex items-center gap-2.5"><Avatar name={cleanName(r.full_name)} size={26} /><div className="min-w-0"><div className="truncate font-medium">{cleanName(r.full_name)}</div><div className="text-[12px] text-muted">{r.usn}</div></div></div>) },
                { key: 'dept', header: 'Department', hideOnMobile: true, render: (r) => r.department_code || r.department_name },
                { key: 'sem', header: 'Sem · Sec', hideOnMobile: true, sort: (r) => r.current_semester, render: (r) => `${r.current_semester} · ${r.section}` },
                { key: 'cgpa', header: 'CGPA', align: 'right', sort: (r) => r.cgpa, render: (r) => num(r.cgpa, 2) },
                { key: 'att', header: 'Attendance', sort: (r) => r.attendance_percentage, className: 'w-40', render: (r) => (
                  <div className="flex items-center gap-2"><Meter value={r.attendance_percentage} threshold={minAtt} className="w-20" /><span className={cx('tnum text-[12.5px]', r.attendance_percentage < minAtt && 'text-bronze font-medium')}>{pct(r.attendance_percentage)}</span></div>) },
                { key: 'status', header: 'Status', hideOnMobile: true, render: (r) => <StatusBadge status={r.status === 'Active' ? 'active' : r.status} label={r.status} /> },
              ]} />
            <Pagination total={rows.length < limit && skip === 0 ? rows.length : skip + rows.length + (rows.length === limit ? 1 : 0)} skip={skip} limit={limit} onChange={setSkip} />
          </>
        )}</Async>
      </Panel>
    </div>
  );
}

/* ------------------------------------------------------------------ student detail (staff view) */
export function StudentDetailPage() {
  const { id } = useParams();
  const sid = Number(id);
  const { me, hasModule } = useAuth();
  const [tab, setTab] = useState('overview');
  const profile = useApi<StudentProfile>(`/students/${sid}`);
  const analytics = useApi<StudentAnalytics>(`/students/${sid}/analytics`);
  const risk = useApi<StudentRiskProfile>(hasModule('risk_identification') && me?.role !== 'placement_officer' ? `/risk/students/${sid}` : null);
  const recs = useApi<Recommendation[]>(hasModule('recommendations') && tab === 'plan' ? '/recommendations/' : null, { student_id: sid });
  const readiness = useApi<PlacementReadiness>(hasModule('placement_readiness') && tab === 'readiness' ? `/placement/readiness/${sid}` : null);
  const ints = useApi<Intervention[]>(hasModule('interventions') && me?.role !== 'placement_officer' ? '/interventions' : null, { student_id: sid });
  const [newInt, setNewInt] = useState(false);
  const minAtt = me?.university?.academic_structure?.minimum_attendance_percent ?? 75;

  if (profile.error) return <Notice tone="danger" title="This student record isn’t available">{profile.error}</Notice>;
  const p = profile.data;
  const tabs = [
    { id: 'overview', label: 'Overview' }, { id: 'academics', label: 'Academics' },
    ...(hasModule('recommendations') ? [{ id: 'plan', label: 'Plan' }] : []),
    ...(hasModule('placement_readiness') ? [{ id: 'readiness', label: 'Readiness' }] : []),
  ];
  return (
    <div>
      <PageHeader meta={p ? `${p.usn} · ${p.department_name} · Semester ${p.current_semester}, section ${p.section}` : ' '}
        title={p ? cleanName(p.full_name) : 'Loading…'}
        actions={hasModule('interventions') && !!me && ['mentor', 'faculty', 'admin'].includes(me.role) && <Button variant="primary" icon={<Plus size={14} />} onClick={() => setNewInt(true)}>Start intervention</Button>} />
      <Tabs value={tab} onChange={setTab} tabs={tabs} className="mb-5" />
      {tab === 'overview' && (
        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="space-y-6">
            <Async state={analytics} rows={2}>{(a) => (
              <StatStrip>
                <Stat label="CGPA" value={num(a.metrics?.cgpa, 2)} />
                <Stat label="Attendance" value={pct(a.metrics?.calculated_attendance_percentage, 1)} tone={isBelow(a.metrics.calculated_attendance_percentage, minAtt) ? 'attention' : undefined} note={`${minAtt}% required`} />
                <Stat label="Internal average" value={pct(a.metrics?.internal_assessment_average, 0)} />
                <Stat label="Backlogs" value={a.metrics?.total_backlogs ?? 0} tone={a.metrics?.total_backlogs ? 'attention' : undefined} />
              </StatStrip>
            )}</Async>
            {hasModule('risk_identification') && (
              <Panel title="Early alerts" padded={false}>
                <Async state={risk}>{(r) => <AlertList alerts={r.alerts} />}</Async>
              </Panel>
            )}
          </div>
          <div className="space-y-6">
            <Panel title="Profile">
              {p && <KeyValues cols={1} items={[
                ['Programme', p.program], ['Mentor', p.mentor_name || 'Not assigned'], ['Email', p.email],
                ['Batch', p.batch_year], ['Placement status', p.placement_status],
              ]} />}
            </Panel>
            {hasModule('interventions') && me?.role !== 'placement_officer' && (
              <Panel title="Interventions">
                <Async state={ints}>{(list) => list.length ? (
                  <ul className="divide-y divide-line">{list.map((i) => (
                    <li key={i.id} className="flex items-center justify-between gap-2 py-2 first:pt-0 last:pb-0"><div className="min-w-0"><div className="truncate font-medium">{i.title}</div><div className="text-[12px] text-muted">{titleCase(i.intervention_type)} · updated {relTime(i.updated_at)}</div></div><StatusBadge status={i.status} /></li>
                  ))}</ul>
                ) : <EmptyState title="No interventions yet" />}</Async>
              </Panel>
            )}
          </div>
        </div>
      )}
      {tab === 'academics' && <StudentAcademics studentId={sid} />}
      {tab === 'plan' && (
        <Panel padded={false} title="Recommendations" description="Students accept, decline and track these from their own plan.">
          <Async state={recs}>{(list) => <DataTable rows={list} empty={<EmptyState title="No recommendations for this student" />} columns={[
            { key: 't', header: 'Recommendation', render: (r) => <div><div className="font-medium">{r.title}</div><div className="text-[12px] text-muted">{r.reason}</div></div> },
            { key: 'p', header: 'Priority', hideOnMobile: true, render: (r) => titleCase(r.priority) },
            { key: 's', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
          ]} />}</Async>
        </Panel>
      )}
      {tab === 'readiness' && (
        <Async state={readiness}>{(r) => (
          <Panel padded={false} title={`Readiness for ${r.target_role?.title}`} description={r.disclaimer}>
            <div className="px-4 py-3"><StatStrip className="border-0 py-0"><Stat label="Score" value={pct(r.readiness_score)} /><Stat label="Matched" value={`${r.skills_matched_count}/${r.total_role_skills_count}`} /><Stat label="Missing" value={r.skills_missing_count} /></StatStrip></div>
            <DataTable rows={r.skill_gaps || []} rowKey={(g) => g.skill_name} columns={[
              { key: 'n', header: 'Skill', render: (g) => g.skill_name }, { key: 'r', header: 'Needed', render: (g) => g.required_proficiency },
              { key: 's', header: 'Student', render: (g) => g.student_proficiency || '—' },
              { key: 'v', header: 'Evidence', hideOnMobile: true, render: (g) => g.is_verified ? <Badge tone="ok">Verified</Badge> : g.student_proficiency ? <Badge>Self-reported</Badge> : '—' },
              { key: 'st', header: 'Status', render: (g) => titleCase(g.status) },
            ]} />
          </Panel>
        )}</Async>
      )}
      {newInt && <InterventionDialog studentId={sid} studentName={p ? cleanName(p.full_name) : ''} onClose={() => setNewInt(false)} onSaved={() => ints.reload()} />}
    </div>
  );
}

function AlertList({ alerts, onOpen }: { alerts: RiskAlert[]; onOpen?: (a: RiskAlert) => void }) {
  if (!alerts?.length) return <EmptyState title="No alerts for this student" />;
  return (
    <ul className="divide-y divide-line">
      {alerts.map((a) => (
        <li key={a.id} className={cx('px-4 py-3', onOpen && 'cursor-pointer hover:bg-sunken/60')} onClick={onOpen ? () => onOpen(a) : undefined}>
          <div className="flex flex-wrap items-center justify-between gap-2"><span className="font-medium">{a.rule_name}</span><div className="flex gap-1.5"><StatusBadge status={a.severity} /><StatusBadge status={a.status} /></div></div>
          <div className="mt-0.5 text-[12.5px] text-muted">Observed {a.observed_display || a.observed_value} · threshold {a.threshold_display || a.threshold_value} · {fmtDate(a.detected_date)}</div>
        </li>
      ))}
    </ul>
  );
}

/* ------------------------------------------------------------------ early alerts */
export function AlertsPage() {
  const { me } = useAuth();
  const toast = useToast();
  const [severity, setSeverity] = useState('');
  const [status, setStatus] = useState('ACTIVE');
  const [skip, setSkip] = useState(0);
  const [openId, setOpenId] = useState<number | null>(null);
  const [running, setRunning] = useState(false);
  const limit = 25;
  const alerts = useApi<RiskAlertList>('/risk/alerts', { severity, status, skip, limit });
  const stats = useApi<RiskStatistics>(me?.role === 'admin' ? '/risk/statistics' : null);
  const evaluate = async () => {
    setRunning(true);
    try { const r = await api.post<RiskEvaluation>('/risk/evaluate', { run_type: 'MANUAL' }); toast(`Evaluation complete — ${r.alerts_generated_count ?? 0} new alert(s)`); alerts.reload(); stats.reload(); }
    catch (e) { toast(errorMessage(e), 'error'); } finally { setRunning(false); }
  };
  return (
    <div>
      <PageHeader title="Early alerts" lede="Rule-based signals with the evidence behind them. They prompt a conversation; they never decide outcomes."
        actions={!!me && ['admin', 'faculty'].includes(me.role) && <Button icon={<RefreshCw size={14} />} loading={running} onClick={evaluate}>Re-run rules</Button>} />
      {stats.data && (
        <StatStrip className="mb-6">
          <Stat label="Active alerts" value={stats.data.total_active_alerts} />
          <Stat label="Students affected" value={stats.data.total_students_at_risk} />
          <Stat label="Critical or high" value={(stats.data.severity_distribution?.critical || 0) + (stats.data.severity_distribution?.high || 0)} tone="attention" />
          <Stat label="Last evaluation" value={<span className="text-[15px] font-medium">{relTime(stats.data.recent_evaluations?.[0]?.completed_at || stats.data.recent_evaluations?.[0]?.created_at) || '—'}</span>} />
        </StatStrip>
      )}
      <Panel padded={false}>
        <Toolbar>
          <Select value={status} onChange={(e) => { setStatus(e.target.value); setSkip(0); }} className="w-44" aria-label="Status">
            <option value="ACTIVE">Open alerts</option><option value="FLAGGED">New</option><option value="UNDER_REVIEW">Under review</option><option value="RESOLVED">Resolved</option><option value="">All</option>
          </Select>
          <Select value={severity} onChange={(e) => { setSeverity(e.target.value); setSkip(0); }} className="w-40" aria-label="Severity">
            <option value="">Any severity</option><option value="CRITICAL">Critical</option><option value="HIGH">High</option><option value="MODERATE">Moderate</option>
          </Select>
        </Toolbar>
        <Async state={alerts}>{(d) => (
          <>
            <DataTable rows={d.items} onRowClick={(a) => setOpenId(a.id)} empty={<EmptyState title="No alerts match these filters" />} columns={[
              { key: 's', header: 'Student', render: (a) => <div><div className="font-medium">{cleanName(a.student_name)}</div><div className="text-[12px] text-muted">{a.student_usn} · Sem {a.student_semester}</div></div> },
              { key: 'r', header: 'Rule', render: (a) => <div><div>{a.rule_name}</div><div className="text-[12px] text-muted">{a.observed_display || a.observed_value} vs {a.threshold_display || a.threshold_value}</div></div> },
              { key: 'sev', header: 'Severity', render: (a) => <StatusBadge status={a.severity} /> },
              { key: 'st', header: 'Status', hideOnMobile: true, render: (a) => <StatusBadge status={a.status} /> },
              { key: 'm', header: 'Mentor', hideOnMobile: true, render: (a) => a.assigned_mentor_name ? cleanName(a.assigned_mentor_name) : <span className="text-faint">Unassigned</span> },
              { key: 'd', header: 'Raised', hideOnMobile: true, render: (a) => fmtDate(a.detected_date) },
            ]} />
            <Pagination total={d.total} skip={skip} limit={limit} onChange={setSkip} />
          </>
        )}</Async>
      </Panel>
      {openId && <AlertDrawer id={openId} onClose={() => setOpenId(null)} onChanged={() => { alerts.reload(); stats.reload(); }} />}
    </div>
  );
}

function AlertDrawer({ id, onClose, onChanged }: { id: number; onClose: () => void; onChanged: () => void }) {
  const { me, hasModule } = useAuth();
  const toast = useToast();
  const a = useApi<RiskAlertDetail>(`/risk/alerts/${id}`);
  const mentors = useApi<MentorSummary[]>(me?.role === 'admin' ? '/tenant/mentors' : null);
  const [note, setNote] = useState('');
  const [mentor, setMentor] = useState('');
  const [busy, setBusy] = useState<string | null>(null);
  const [newInt, setNewInt] = useState(false);
  const run = async (key: string, fn: () => Promise<unknown>, msg: string) => {
    setBusy(key);
    try { await fn(); toast(msg); setNote(''); a.reload(); onChanged(); } catch (e) { toast(errorMessage(e), 'error'); } finally { setBusy(null); }
  };
  // The detail endpoint returns { alert, history, assignments }.
  const al = a.data?.alert;
  const closed = !!al && ['RESOLVED', 'CLOSED'].includes(al.status);
  return (
    <Drawer open onClose={onClose} title={al?.rule_name || 'Alert'} subtitle={al && <>{cleanName(al.student_name)} · {al.student_usn}</>}>
      <Async state={a}>{({ alert: x, history }) => (
        <div className="space-y-6">
          <div className="flex gap-1.5"><StatusBadge status={x.severity} /><StatusBadge status={x.status} /></div>
          <KeyValues items={[['Observed', x.observed_display || x.observed_value], ['Configured threshold', x.threshold_display || x.threshold_value],
            ['Period', x.academic_period], ['Raised', fmtDate(x.detected_date, true)], ['Subject', x.subject_name || 'All subjects'], ['Mentor', x.assigned_mentor_name ? cleanName(x.assigned_mentor_name) : 'Unassigned']]} />
          {x.ai_explanation && (
            <div><div className="label mb-1">Explanation of the evidence</div><p className="whitespace-pre-line text-[13px] text-ink">{x.ai_explanation}</p>
              <p className="mt-1 text-[11.5px] text-faint">Composed from the rule and recorded values. It is not a prediction.</p></div>
          )}
          {x.suggested_action && <div><div className="label mb-1">Suggested support</div><p className="text-[13px]">{x.suggested_action}</p></div>}
          {!closed && (
            <div className="space-y-3 rounded-lg border border-line p-3.5">
              <Field label="Note"><Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="What did you observe or agree with the student?" /></Field>
              <div className="flex flex-wrap gap-2">
                {x.status === 'FLAGGED' && <Button size="sm" loading={busy === 'ack'} onClick={() => run('ack', () => api.post(`/risk/alerts/${id}/acknowledge`, { notes: note || null }), 'Alert acknowledged')}>Acknowledge</Button>}
                <Button size="sm" disabled={!note.trim()} loading={busy === 'note'} onClick={() => run('note', () => api.post(`/risk/alerts/${id}/notes`, { notes: note }), 'Note added')}>Add note</Button>
                <Button size="sm" variant="primary" disabled={note.trim().length < 2} loading={busy === 'res'} onClick={() => run('res', () => api.post(`/risk/alerts/${id}/resolve`, { resolution_reason: note }), 'Alert resolved')}>Resolve with note</Button>
                {hasModule('interventions') && !!me && ['mentor', 'faculty', 'admin'].includes(me.role) && <Button size="sm" variant="ghost" onClick={() => setNewInt(true)}>Start intervention</Button>}
              </div>
              {mentors.data && (
                <div className="flex items-end gap-2 border-t border-line pt-3">
                  <Field label="Assign mentor" className="flex-1"><Select value={mentor} onChange={(e) => setMentor(e.target.value)}><option value="">Choose…</option>{mentors.data.map((m) => <option key={m.id} value={m.id}>{cleanName(m.full_name)} · {m.mentee_count} mentees</option>)}</Select></Field>
                  <Button size="sm" disabled={!mentor} loading={busy === 'asg'} onClick={() => run('asg', () => api.post(`/risk/alerts/${id}/assign`, { mentor_id: Number(mentor), notes: note || null }), 'Mentor assigned')}>Assign</Button>
                </div>
              )}
            </div>
          )}
          {closed && <Button size="sm" disabled={note.trim().length < 2} onClick={() => run('re', () => api.post(`/risk/alerts/${id}/reopen`, { reason: note }), 'Alert reopened')}>Reopen</Button>}
          {closed && <Field label="Reason for reopening"><Textarea value={note} onChange={(e) => setNote(e.target.value)} /></Field>}
          <div><div className="section-title mb-3">History</div>
            <Timeline items={history.slice().reverse().map((h) => ({ id: h.id, title: <>{titleCase(h.action)}{h.new_status && h.new_status !== h.old_status ? <span className="text-muted"> → {titleCase(h.new_status)}</span> : null}</>, meta: `${cleanName(h.performed_by_name)} · ${fmtDate(h.created_at, true)}`, body: h.notes }))} />
          </div>
          {newInt && <InterventionDialog studentId={x.student_id} studentName={cleanName(x.student_name)} alertId={x.id} defaultTitle={`Follow-up: ${x.rule_name}`} onClose={() => setNewInt(false)} onSaved={() => { a.reload(); onChanged(); }} />}
        </div>
      )}</Async>
    </Drawer>
  );
}

/* ------------------------------------------------------------------ interventions */
const INT_TYPES = ['ACADEMIC_REMEDIAL', 'ATTENDANCE_CONDONATION_COUNSELING', 'EXAMINATION_PREPARATION', 'CAREER_SKILL_COACHING', 'PLACEMENT_INTERVIEW_PREPARATION', 'BEHAVIORAL_WELLBEING'];
const LANES = ['OPEN', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'];

export function InterventionDialog({ studentId, studentName, alertId, defaultTitle, onClose, onSaved }: {
  studentId?: number; studentName?: string; alertId?: number; defaultTitle?: string; onClose: () => void; onSaved: () => void;
}) {
  const toast = useToast();
  const { me } = useAuth();
  const students = useApi<StudentProfile[]>(studentId ? null : '/students/', { limit: 100 });
  const mentors = useApi<MentorSummary[]>(me?.role === 'admin' ? '/tenant/mentors' : null);
  const [f, setF] = useState({ student_id: studentId ? String(studentId) : '', mentor_id: '', title: defaultTitle || '', intervention_type: 'ACADEMIC_REMEDIAL', priority: 'MEDIUM', initial_notes: '', target_resolution_date: '' });
  const [saving, setSaving] = useState(false);
  const save = async () => {
    setSaving(true);
    try {
      await api.post('/interventions', { ...f, student_id: Number(f.student_id), mentor_id: f.mentor_id ? Number(f.mentor_id) : null, risk_alert_id: alertId || null, target_resolution_date: f.target_resolution_date || null, initial_notes: f.initial_notes || null });
      toast('Intervention started'); onSaved(); onClose();
    } catch (e) { toast(errorMessage(e), 'error'); } finally { setSaving(false); }
  };
  return (
    <Dialog open onClose={onClose} title="Start an intervention" description={studentName ? `For ${studentName}` : 'Plan support for a student'}
      footer={<><Button onClick={onClose}>Cancel</Button><Button variant="primary" loading={saving} disabled={!f.student_id || f.title.trim().length < 3} onClick={save}>Start intervention</Button></>}>
      <div className="space-y-4">
        {!studentId && <Field label="Student"><Select value={f.student_id} onChange={(e) => setF({ ...f, student_id: e.target.value })}><option value="">Choose…</option>{students.data?.map((s) => <option key={s.id} value={s.id}>{cleanName(s.full_name)} · {s.usn}</option>)}</Select></Field>}
        <Field label="Title"><Input value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} placeholder="e.g. Attendance recovery plan" /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Type"><Select value={f.intervention_type} onChange={(e) => setF({ ...f, intervention_type: e.target.value })}>{INT_TYPES.map((t) => <option key={t} value={t}>{titleCase(t)}</option>)}</Select></Field>
          <Field label="Priority"><Select value={f.priority} onChange={(e) => setF({ ...f, priority: e.target.value })}>{['LOW', 'MEDIUM', 'HIGH', 'URGENT'].map((t) => <option key={t} value={t}>{titleCase(t)}</option>)}</Select></Field>
        </div>
        {mentors.data && <Field label="Mentor" hint="Leave as default to use the student’s assigned mentor."><Select value={f.mentor_id} onChange={(e) => setF({ ...f, mentor_id: e.target.value })}><option value="">Student’s assigned mentor</option>{mentors.data.map((m) => <option key={m.id} value={m.id}>{cleanName(m.full_name)} · {m.mentee_count} mentees</option>)}</Select></Field>}
        <Field label="Target date"><Input type="date" value={f.target_resolution_date} onChange={(e) => setF({ ...f, target_resolution_date: e.target.value })} /></Field>
        <Field label="Initial notes" hint="Visible to staff only."><Textarea value={f.initial_notes} onChange={(e) => setF({ ...f, initial_notes: e.target.value })} /></Field>
      </div>
    </Dialog>
  );
}

export function InterventionsPage() {
  const { me } = useAuth();
  const list = useApi<Intervention[]>('/interventions', { limit: 100 });
  const [openId, setOpenId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const [view, setView] = useState<'lanes' | 'table'>('lanes');
  const grouped = useMemo(() => Object.fromEntries(LANES.map((l) => [l, (list.data || []).filter((i) => i.status === l)])), [list.data]);
  return (
    <div>
      <PageHeader title="Interventions" lede={me?.role === 'mentor' ? 'Your support cases, from first conversation to outcome.' : 'Support cases across the students you can see.'}
        actions={<><Tabs value={view} onChange={setView} tabs={[{ id: 'lanes', label: 'By status' }, { id: 'table', label: 'List' }]} className="border-0" />
          <Button variant="primary" icon={<Plus size={14} />} onClick={() => setCreating(true)}>New intervention</Button></>} />
      <Async state={list}>{(rows) => view === 'lanes' ? (
        <div className="grid gap-4 overflow-x-auto pb-2 md:grid-cols-5">
          {LANES.map((l) => (
            <section key={l} className="min-w-[14rem]">
              <h2 className="mb-2 flex items-center justify-between text-[12.5px] font-medium text-muted"><span>{titleCase(l)}</span><span className="tnum text-faint">{grouped[l].length}</span></h2>
              <div className="space-y-2">
                {grouped[l].map((i) => (
                  <button key={i.id} type="button" onClick={() => setOpenId(i.id)} className="block w-full rounded-lg border border-line bg-surface p-3 text-left hover:border-line-strong">
                    <div className="text-[13px] font-medium leading-snug">{i.title}</div>
                    <div className="mt-1 text-[12px] text-muted">{cleanName(i.student_name)}</div>
                    <div className="mt-2 flex items-center justify-between text-[11.5px] text-faint"><span>{i.target_resolution_date ? `Due ${fmtDate(i.target_resolution_date)}` : 'No target date'}</span>{['HIGH', 'URGENT'].includes(i.priority) && <Badge tone="bronze">{titleCase(i.priority)}</Badge>}</div>
                  </button>
                ))}
                {!grouped[l].length && <div className="rounded-lg border border-dashed border-line px-3 py-4 text-center text-[12px] text-faint">None</div>}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <Panel padded={false}><DataTable rows={rows} onRowClick={(i) => setOpenId(i.id)} empty={<EmptyState title="No interventions yet" />} columns={[
          { key: 't', header: 'Intervention', render: (i) => <div><div className="font-medium">{i.title}</div><div className="text-[12px] text-muted">{titleCase(i.intervention_type)}</div></div> },
          { key: 's', header: 'Student', render: (i) => cleanName(i.student_name) },
          { key: 'm', header: 'Mentor', hideOnMobile: true, render: (i) => cleanName(i.mentor_name) || '—' },
          { key: 'p', header: 'Priority', hideOnMobile: true, render: (i) => titleCase(i.priority) },
          { key: 'st', header: 'Status', render: (i) => <StatusBadge status={i.status} /> },
          { key: 'd', header: 'Updated', hideOnMobile: true, sort: (i) => i.updated_at, render: (i) => relTime(i.updated_at) },
        ]} /></Panel>
      )}</Async>
      {openId && <InterventionDrawer id={openId} onClose={() => setOpenId(null)} onChanged={list.reload} />}
      {creating && <InterventionDialog onClose={() => setCreating(false)} onSaved={list.reload} />}
    </div>
  );
}

function InterventionDrawer({ id, onClose, onChanged }: { id: number; onClose: () => void; onChanged: () => void }) {
  const toast = useToast();
  const d = useApi<InterventionDetail>(`/interventions/${id}`);
  const [note, setNote] = useState('');
  const [fdate, setFdate] = useState('');
  const [summary, setSummary] = useState('');
  const [busy, setBusy] = useState<string | null>(null);
  const run = async (key: string, fn: () => Promise<unknown>, msg: string) => {
    setBusy(key);
    try { await fn(); toast(msg); d.reload(); onChanged(); } catch (e) { toast(errorMessage(e), 'error'); } finally { setBusy(null); }
  };
  const x = d.data;
  const next: Record<string, string[]> = { OPEN: ['IN_PROGRESS'], ASSIGNED: ['IN_PROGRESS'], IN_PROGRESS: ['RESOLVED'], RESOLVED: ['CLOSED', 'IN_PROGRESS'], CLOSED: ['IN_PROGRESS'] };
  return (
    <Drawer open onClose={onClose} title={x?.title || 'Intervention'} subtitle={x && <>{cleanName(x.student_name)} · {x.student_usn}</>} width="max-w-2xl">
      <Async state={d}>{(x) => (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center gap-2"><StatusBadge status={x.status} /><Badge>{titleCase(x.intervention_type)}</Badge><Badge tone={['HIGH', 'URGENT'].includes(x.priority) ? 'bronze' : 'neutral'}>{titleCase(x.priority)} priority</Badge></div>
          <KeyValues items={[['Mentor', cleanName(x.mentor_name) || 'Unassigned'], ['Started by', cleanName(x.assigned_by_name)], ['Target date', fmtDate(x.target_resolution_date)], ['Linked alert', x.risk_alert_id ? `#${x.risk_alert_id}` : 'None']]} />
          {x.initial_notes && <div><div className="label mb-1">Initial notes</div><p className="whitespace-pre-line text-[13px]">{x.initial_notes}</p></div>}
          {x.resolution_summary && <Notice tone="ok" title="Outcome">{x.resolution_summary}</Notice>}
          <div className="rounded-lg border border-line p-3.5">
            <div className="section-title mb-2">Update status</div>
            {['IN_PROGRESS'].includes(x.status) && <Field label="Outcome summary (required to resolve)" className="mb-2"><Textarea value={summary} onChange={(e) => setSummary(e.target.value)} /></Field>}
            <div className="flex flex-wrap gap-2">
              {(next[x.status] || []).map((s) => (
                <Button key={s} size="sm" variant={s === 'RESOLVED' ? 'primary' : 'secondary'} disabled={s === 'RESOLVED' && summary.trim().length < 3} loading={busy === s}
                  onClick={() => run(s, () => api.put(`/interventions/${id}/status`, { status: s, resolution_summary: s === 'RESOLVED' ? summary : undefined }), `Marked ${titleCase(s).toLowerCase()}`)}>
                  {s === 'IN_PROGRESS' && x.status !== 'OPEN' && x.status !== 'ASSIGNED' ? 'Reopen' : `Mark ${titleCase(s).toLowerCase()}`}
                </Button>
              ))}
            </div>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <div className="section-title mb-2">Notes</div>
              <Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Record a conversation, observation or agreed action" />
              <Button size="sm" className="mt-2" disabled={note.trim().length < 2} loading={busy === 'note'} onClick={() => run('note', async () => { await api.post(`/interventions/${id}/notes`, { note_text: note, note_type: 'GENERAL' }); setNote(''); }, 'Note added')}>Add note</Button>
              <div className="mt-4"><Timeline items={(x.notes || []).slice().reverse().map((n) => ({ id: n.id, title: cleanName(n.author_name) || 'Staff', meta: `${titleCase(n.note_type)} · ${fmtDate(n.created_at, true)}`, body: n.note_text }))} /></div>
            </div>
            <div>
              <div className="section-title mb-2">Follow-ups</div>
              <div className="flex gap-2"><Input type="date" value={fdate} onChange={(e) => setFdate(e.target.value)} aria-label="Follow-up date" />
                <Button size="sm" className="h-9" disabled={!fdate} loading={busy === 'f'} onClick={() => run('f', async () => { await api.post(`/interventions/${id}/followups`, { scheduled_date: fdate }); setFdate(''); }, 'Follow-up scheduled')}>Schedule</Button></div>
              <ul className="mt-3 divide-y divide-line">
                {(x.followups || []).map((f) => (
                  <li key={f.id} className="py-2.5">
                    <div className="flex items-center justify-between gap-2"><span className="text-[13px] font-medium">{fmtDate(f.scheduled_date)}</span><StatusBadge status={f.followup_status === 'SCHEDULED' ? 'pending' : f.followup_status === 'COMPLETED' ? 'completed' : 'closed'} label={titleCase(f.followup_status)} /></div>
                    {f.outcome_notes && <p className="mt-0.5 text-[12.5px] text-muted">{f.outcome_notes}</p>}
                    {f.followup_status === 'SCHEDULED' && (
                      <div className="mt-1.5 flex gap-1.5">
                        <Button size="sm" variant="ghost" onClick={() => run(`c${f.id}`, () => api.put(`/interventions/followups/${f.id}`, { followup_status: 'COMPLETED', outcome_notes: note || 'Follow-up held.' }), 'Follow-up recorded')}>Mark held</Button>
                        <Button size="sm" variant="quiet" onClick={() => run(`m${f.id}`, () => api.put(`/interventions/followups/${f.id}`, { followup_status: 'MISSED' }), 'Marked as missed')}>Missed</Button>
                      </div>
                    )}
                  </li>
                ))}
                {!x.followups?.length && <li className="py-2 text-[12.5px] text-muted">No follow-ups scheduled.</li>}
              </ul>
            </div>
          </div>
        </div>
      )}</Async>
    </Drawer>
  );
}
