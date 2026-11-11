import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ExternalLink, Plus } from 'lucide-react';
import { api, errorMessage } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useApi } from '../lib/useApi';
import { cleanName, fmtDate, isBelow, num, pct, titleCase } from '../lib/format';
import { PageHeader } from '../components/shell';
import { ChartContainer, TrendLine } from '../components/charts';
import type { Application, CareerRole, Intervention, OpportunityMatch, PlacementReadiness, Recommendation, StudentAnalytics, StudentRiskProfile } from '../types/api';
import {
  Async, Badge, Button, DataTable, Dialog, EmptyState, Field, Input, KeyValues, LoadingBlock, Meter, Notice, Panel,
  Select, Stat, StatStrip, StatusBadge, Tabs, Textarea, useToast,
} from '../components/ui';

export function useStudentId() {
  const { me } = useAuth();
  return me?.student_id as number;
}

const firstName = (n?: string) => cleanName(n).split(' ')[0];

/* ------------------------------------------------------------------ overview */
export function StudentOverview() {
  const { me, hasModule } = useAuth();
  const sid = useStudentId();
  const analytics = useApi<StudentAnalytics>(`/students/${sid}/analytics`);
  const risk = useApi<StudentRiskProfile>(hasModule('risk_identification') ? `/risk/students/${sid}` : null);
  const recs = useApi<Recommendation[]>(hasModule('recommendations') ? '/recommendations/' : null);
  const readiness = useApi<PlacementReadiness>(hasModule('placement_readiness') ? `/placement/readiness/${sid}` : null);
  const minAtt = me?.university?.academic_structure?.minimum_attendance_percent ?? 75;

  const alerts = (risk.data?.alerts || []).filter((a) => !['RESOLVED', 'CLOSED'].includes(a.status));
  const openRecs = (recs.data || []).filter((r) => ['SUGGESTED', 'ACCEPTED', 'IN_PROGRESS'].includes(r.status));
  const att = analytics.data?.metrics?.calculated_attendance_percentage ?? analytics.data?.student_profile?.attendance_percentage;
  const lowSubjects = (analytics.data?.attendance_breakdown || []).filter((s) => s.attendance_percentage < minAtt);

  const attention = alerts.length + lowSubjects.length;
  const headline = !analytics.data ? `Welcome back, ${firstName(me?.full_name)}`
    : attention === 0 ? 'You’re on track this semester.'
      : attention === 1 ? 'One thing needs your attention.'
        : `${['', '', 'Two', 'Three', 'Four', 'Five'][attention] || attention} things need your attention.`;

  return (
    <div>
      <PageHeader meta={`${me?.university?.academic_structure?.term_label || 'Semester'} ${me?.current_semester ?? ''} · ${me?.department_name ?? ''}`}
        title={headline}
        lede={analytics.data ? (attention ? 'Each item below explains what was observed and what support is available. None of it is a penalty.' : 'Keep an eye on attendance and your plan — your mentor is here if you need anything.') : undefined} />

      <Async state={analytics} rows={3}>{(a) => (
        <StatStrip className="mb-8">
          <Stat label="CGPA" value={num(a.metrics?.cgpa, 2)} note={`out of ${me?.university?.academic_structure?.cgpa_max ?? 10}`} />
          <div className="min-w-[10rem]">
            <Stat label="Attendance" value={pct(att, 1)} tone={isBelow(att, minAtt) ? 'attention' : undefined} note={`${minAtt}% required`} />
            <Meter value={att || 0} threshold={minAtt} className="mt-2 max-w-[10rem]" label="Attendance against requirement" />
          </div>
          <Stat label="Credits earned" value={a.metrics?.total_credits_earned ?? '—'} />
          {readiness.data && <Stat label="Placement readiness" value={pct(readiness.data.readiness_score)} note={readiness.data.target_role?.title} />}
        </StatStrip>
      )}</Async>

      <div className="grid gap-6 lg:grid-cols-[1.25fr_1fr]">
        <div className="space-y-6">
          <Panel title="Needs attention" description="Raised by your university’s published rules">
            {(risk.loading || analytics.loading) && !alerts.length ? <LoadingBlock rows={3} /> : (alerts.length || lowSubjects.length) ? (
              <ul className="divide-y divide-line">
                {lowSubjects.map((s) => (
                  <li key={`att-${s.subject_id}`} className="py-3 first:pt-0 last:pb-0">
                    <div className="flex items-baseline justify-between gap-3"><span className="font-medium">Attendance in {s.subject_name}</span><span className="tnum text-bronze">{pct(s.attendance_percentage, 1)}</span></div>
                    <p className="mt-0.5 text-[13px] text-muted">{s.attended_classes} of {s.total_classes} classes attended. The requirement is {minAtt}%; attending the next classes will raise it.</p>
                  </li>
                ))}
                {alerts.map((a) => (
                  <li key={a.id} className="py-3 first:pt-0 last:pb-0">
                    <div className="flex items-baseline justify-between gap-3"><span className="font-medium">{a.rule_name}</span><StatusBadge status={a.severity} /></div>
                    <p className="mt-0.5 text-[13px] text-muted">Observed {a.observed_display || a.observed_value} against a threshold of {a.threshold_display || a.threshold_value}. {a.suggested_action}</p>
                  </li>
                ))}
              </ul>
            ) : <EmptyState title="Nothing needs attention right now">Alerts appear here if attendance or assessments fall below your university’s thresholds.</EmptyState>}
            {hasModule('risk_identification') && <Link to="/app/support" className="link mt-3 inline-block text-[13px]">See support and alert history</Link>}
          </Panel>

          {hasModule('recommendations') && (
            <Panel title="Your plan" description="Suggested from your records and your university’s catalogue"
              actions={<Link to="/app/plan"><Button size="sm" variant="ghost">Open plan</Button></Link>}>
              {recs.loading && !recs.data ? <LoadingBlock /> : openRecs.length ? (
                <ul className="divide-y divide-line">
                  {openRecs.slice(0, 4).map((r) => (
                    <li key={r.id} className="flex items-start justify-between gap-3 py-2.5 first:pt-0 last:pb-0">
                      <div className="min-w-0"><div className="truncate font-medium">{r.title}</div><div className="text-[12.5px] text-muted">{titleCase(r.category)} · {r.suggested_completion_time || 'Self-paced'}</div></div>
                      <StatusBadge status={r.status} />
                    </li>
                  ))}
                </ul>
              ) : <EmptyState title="No open items in your plan" />}
            </Panel>
          )}
        </div>

        <div className="space-y-6">
          <Panel title="Semester trend">
            <Async state={analytics}>{(a) => a.sgpa_trend?.length ? (
              <ChartContainer height={190}><TrendLine data={a.sgpa_trend.map((s) => ({ ...s, label: `S${s.semester_number}` }))} x="label" y="sgpa" domain={[4, 10]} names={['SGPA']} /></ChartContainer>
            ) : <EmptyState title="No completed semesters yet" />}</Async>
          </Panel>
          <Panel title="Your support">
            <Async state={analytics}>{(a) => (
              <KeyValues cols={1} items={[
                ['Mentor', a.student_profile?.mentor_name || 'Not assigned yet'],
                ['Section', `${a.student_profile?.section} · ${a.student_profile?.program}`],
              ]} />
            )}</Async>
          </Panel>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ academics */
export function StudentAcademics({ studentId }: { studentId?: number }) {
  const own = useStudentId();
  const sid = studentId ?? own;
  const { me } = useAuth();
  const [tab, setTab] = useState('subjects');
  const a = useApi<StudentAnalytics>(`/students/${sid}/analytics`);
  const minAtt = me?.university?.academic_structure?.minimum_attendance_percent ?? 75;
  return (
    <div>
      {!studentId && <PageHeader title="Academics" lede="Your attendance, assessments and results as recorded by your university." />}
      <Tabs value={tab} onChange={setTab} className="mb-5" tabs={[
        { id: 'subjects', label: 'This semester' }, { id: 'assessments', label: 'Assessments' },
        { id: 'semesters', label: 'Semester history' }, { id: 'skills', label: 'Skills & portfolio' },
      ]} />
      <Async state={a}>{(d) => (
        <>
          {tab === 'subjects' && (
            <Panel padded={false} title="Attendance by subject" description={`The vertical mark shows the ${minAtt}% requirement.`}>
              <DataTable rows={d.attendance_breakdown || []} rowKey={(r) => r.subject_id}
                empty={<EmptyState title="No attendance recorded yet" />}
                columns={[
                  { key: 'subject', header: 'Subject', render: (r) => <div><div className="font-medium">{r.subject_name}</div><div className="text-[12px] text-muted">{r.subject_code}</div></div> },
                  { key: 'classes', header: 'Attended', align: 'right', render: (r) => `${r.attended_classes} / ${r.total_classes}` },
                  { key: 'bar', header: <span className="sr-only">Progress</span>, className: 'w-48 hidden sm:table-cell', render: (r) => <Meter value={r.attendance_percentage} threshold={minAtt} /> },
                  { key: 'pct', header: '%', align: 'right', sort: (r) => r.attendance_percentage, render: (r) => <span className={r.attendance_percentage < minAtt ? 'text-bronze font-medium' : ''}>{pct(r.attendance_percentage, 1)}</span> },
                ]} />
            </Panel>
          )}
          {tab === 'assessments' && (
            <Panel padded={false} title="Internal assessments">
              <DataTable rows={d.assessment_history || []} empty={<EmptyState title="No assessments recorded yet" />}
                columns={[
                  { key: 'subject_name', header: 'Subject', sort: (r) => r.subject_name },
                  { key: 'assessment_type', header: 'Assessment' },
                  { key: 'date', header: 'Date', hideOnMobile: true, sort: (r) => r.assessment_date, render: (r) => fmtDate(r.assessment_date) },
                  { key: 'marks', header: 'Marks', align: 'right', render: (r) => `${num(r.marks_obtained)} / ${num(r.max_marks, 0)}` },
                  { key: 'pct', header: '%', align: 'right', sort: (r) => r.percentage, render: (r) => <span className={r.percentage < 40 ? 'text-bronze font-medium' : ''}>{pct(r.percentage)}</span> },
                ]} />
            </Panel>
          )}
          {tab === 'semesters' && (
            <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
              <Panel title="SGPA by semester">{d.sgpa_trend?.length ? <ChartContainer height={220}><TrendLine data={d.sgpa_trend.map((s) => ({ ...s, label: `S${s.semester_number}` }))} x="label" y="sgpa" domain={[4, 10]} names={['SGPA']} /></ChartContainer> : <EmptyState title="No completed semesters yet" />}</Panel>
              <Panel padded={false} title="Semester records">
                <DataTable rows={d.sgpa_trend || []} rowKey={(r) => r.semester_number} columns={[
                  { key: 'semester', header: 'Semester' }, { key: 'sgpa', header: 'SGPA', align: 'right', render: (r) => num(r.sgpa, 2) },
                  { key: 'credits', header: 'Credits', align: 'right', render: (r) => `${r.credits_earned}/${r.credits_registered}` },
                  { key: 'backlogs', header: 'Backlogs', align: 'right' }, { key: 'status', header: 'Result', render: (r) => <StatusBadge status={r.status === 'Pass' ? 'completed' : 'pending'} label={r.status} /> },
                ]} />
              </Panel>
            </div>
          )}
          {tab === 'skills' && <SkillsPortfolio data={d} sid={sid} editable={!studentId} onChange={a.reload} />}
        </>
      )}</Async>
    </div>
  );
}

function PortfolioList<T extends { id: number }>({ label, items, describe }: { label: string; items: T[]; describe: (item: T) => string }) {
  return (
    <div><div className="label mb-1">{label}</div>
      {items.length ? <ul className="space-y-1">{items.map((x) => <li key={x.id}>{describe(x)}</li>)}</ul> : <p className="text-muted">None recorded</p>}</div>
  );
}

function SkillsPortfolio({ data, sid, editable, onChange }: { data: StudentAnalytics; sid: number; editable: boolean; onChange: () => void }) {
  const [open, setOpen] = useState(false);
  const skills = Object.values(data.skills_by_category || {}).flat();
  return (
    <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
      <Panel title="Skills" description="Verified skills have been confirmed by faculty; others are self-reported."
        actions={editable && <Button size="sm" icon={<Plus size={14} />} onClick={() => setOpen(true)}>Add skill</Button>}>
        {skills.length ? (
          <ul className="divide-y divide-line">
            {skills.map((s) => (
              <li key={s.id} className="flex items-center justify-between gap-3 py-2 first:pt-0 last:pb-0">
                <div><span className="font-medium">{s.skill_name}</span><span className="ml-2 text-[12px] text-muted">{titleCase(s.category)}</span></div>
                <div className="flex items-center gap-2"><span className="text-[12.5px] text-muted">{s.proficiency_level}</span>
                  {s.is_verified ? <Badge tone="ok">Verified</Badge> : <Badge>Self-reported</Badge>}</div>
              </li>
            ))}
          </ul>
        ) : <EmptyState title="No skills recorded yet" />}
      </Panel>
      <Panel title="Portfolio">
        <div className="space-y-4 text-[13px]">
          <PortfolioList label="Projects" items={data.projects} describe={(p) => p.title + (p.tech_stack ? ` · ${p.tech_stack}` : '')} />
          <PortfolioList label="Certifications" items={data.certifications} describe={(c) => `${c.title} · ${c.issuing_organization}`} />
          <PortfolioList label="Internships" items={data.internships} describe={(i) => `${i.role || 'Intern'} · ${i.company_name || ''}`} />
        </div>
      </Panel>
      {editable && <AddSkillDialog open={open} onClose={() => setOpen(false)} sid={sid} onSaved={onChange} />}
    </div>
  );
}

function AddSkillDialog({ open, onClose, sid, onSaved }: { open: boolean; onClose: () => void; sid: number; onSaved: () => void }) {
  const toast = useToast();
  const [f, setF] = useState({ skill_name: '', category: 'programming', proficiency_level: 'Intermediate' });
  const [saving, setSaving] = useState(false);
  const save = async () => {
    setSaving(true);
    try { await api.post(`/placement/students/${sid}/skills`, f); toast('Skill added'); onSaved(); onClose(); }
    catch (e) { toast(errorMessage(e), 'error'); } finally { setSaving(false); }
  };
  return (
    <Dialog open={open} onClose={onClose} title="Add a skill" description="It will show as self-reported until faculty verify it."
      footer={<><Button onClick={onClose}>Cancel</Button><Button variant="primary" loading={saving} disabled={!f.skill_name.trim()} onClick={save}>Add skill</Button></>}>
      <div className="space-y-4">
        <Field label="Skill"><Input value={f.skill_name} onChange={(e) => setF({ ...f, skill_name: e.target.value })} placeholder="e.g. SQL" /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Category"><Select value={f.category} onChange={(e) => setF({ ...f, category: e.target.value })}>
            {['programming', 'framework', 'database', 'core_cs', 'ai_ml', 'cloud', 'tools', 'soft_skill'].map((c) => <option key={c} value={c}>{titleCase(c)}</option>)}</Select></Field>
          <Field label="Level"><Select value={f.proficiency_level} onChange={(e) => setF({ ...f, proficiency_level: e.target.value })}>
            {['Beginner', 'Intermediate', 'Advanced', 'Expert'].map((c) => <option key={c}>{c}</option>)}</Select></Field>
        </div>
      </div>
    </Dialog>
  );
}

/* ------------------------------------------------------------------ support & alerts */
export function StudentSupport() {
  const sid = useStudentId();
  const { hasModule } = useAuth();
  const risk = useApi<StudentRiskProfile>(`/risk/students/${sid}`);
  const ints = useApi<Intervention[]>(hasModule('interventions') ? '/interventions' : null);
  return (
    <div>
      <PageHeader title="Support & alerts" lede="Alerts come from rules your university publishes. They exist so that someone can help early — they are never used to penalise you." />
      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Panel title="Alerts">
          <Async state={risk}>{(r) => r.alerts?.length ? (
            <ul className="divide-y divide-line">
              {r.alerts.map((a) => (
                <li key={a.id} className="py-3.5 first:pt-0 last:pb-0">
                  <div className="flex flex-wrap items-center justify-between gap-2"><span className="font-medium">{a.rule_name}</span><div className="flex gap-1.5"><StatusBadge status={a.severity} /><StatusBadge status={a.status} /></div></div>
                  <div className="mt-2 grid grid-cols-3 gap-3 text-[13px]">
                    <div><div className="label">Observed</div>{a.observed_display || a.observed_value}</div>
                    <div><div className="label">Threshold</div>{a.threshold_display || a.threshold_value}</div>
                    <div><div className="label">Raised</div>{fmtDate(a.detected_date)}</div>
                  </div>
                  {a.suggested_action && <p className="mt-2 text-[13px] text-muted"><span className="font-medium text-ink">Suggested support: </span>{a.suggested_action}</p>}
                </li>
              ))}
            </ul>
          ) : <EmptyState title="No alerts on your record" />}</Async>
        </Panel>
        {hasModule('interventions') && (
          <Panel title="Support from your mentor">
            <Async state={ints}>{(list) => list.length ? (
              <ul className="divide-y divide-line">{list.map((i) => (
                <li key={i.id} className="py-2.5 first:pt-0 last:pb-0"><div className="flex items-center justify-between gap-2"><span className="font-medium">{i.title}</span><StatusBadge status={i.status} /></div>
                  <div className="text-[12.5px] text-muted">{i.mentor_name ? `With ${cleanName(i.mentor_name)}` : 'Mentor to be assigned'}{i.target_resolution_date ? ` · target ${fmtDate(i.target_resolution_date)}` : ''}</div></li>
              ))}</ul>
            ) : <EmptyState title="No support sessions planned">Your mentor will reach out if a check-in would help. You can also contact them directly.</EmptyState>}</Async>
          </Panel>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ plan (recommendations) */
export function StudentPlan() {
  const toast = useToast();
  const recs = useApi<Recommendation[]>('/recommendations/');
  const [filter, setFilter] = useState('open');
  const [active, setActive] = useState<{ r: Recommendation; kind: 'reject' | 'feedback' } | null>(null);
  const list = useMemo(() => (recs.data || []).filter((r) => filter === 'all' ? true : filter === 'open' ? ['SUGGESTED', 'ACCEPTED', 'IN_PROGRESS'].includes(r.status) : r.status === 'COMPLETED'), [recs.data, filter]);
  const act = async (r: Recommendation, kind: 'accept' | 'start' | 'complete') => {
    try {
      if (kind === 'accept') await api.post(`/recommendations/${r.id}/accept`);
      else await api.post(`/recommendations/${r.id}/progress`, { status: kind === 'start' ? 'IN_PROGRESS' : 'COMPLETED', percent_complete: kind === 'start' ? 10 : 100 });
      toast(kind === 'accept' ? 'Added to your plan' : kind === 'start' ? 'Marked as in progress' : 'Marked as completed');
      recs.reload();
    } catch (e) { toast(errorMessage(e), 'error'); }
  };
  const counts = { open: (recs.data || []).filter((r) => ['SUGGESTED', 'ACCEPTED', 'IN_PROGRESS'].includes(r.status)).length, done: (recs.data || []).filter((r) => r.status === 'COMPLETED').length };
  return (
    <div>
      <PageHeader title="My plan" lede="Each suggestion says why it was made and what it should improve. Accept the ones that suit you, or decline with a reason." />
      <Tabs value={filter} onChange={setFilter} className="mb-5" tabs={[{ id: 'open', label: 'Open', count: counts.open }, { id: 'done', label: 'Completed', count: counts.done }, { id: 'all', label: 'All' }]} />
      <Async state={recs}>{() => list.length ? (
        <div className="divide-y divide-line rounded-lg border border-line bg-surface">
          {list.map((r) => (
            <article key={r.id} className="grid gap-3 p-4 sm:grid-cols-[1fr_auto]">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2"><h3 className="text-[14.5px] font-semibold">{r.title}</h3><StatusBadge status={r.status} />{r.priority === 'HIGH' && <Badge tone="bronze">High priority</Badge>}</div>
                <p className="mt-1 text-[13px] text-muted"><span className="text-ink">Why: </span>{r.reason}</p>
                <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-[12.5px] text-muted">
                  <span>Addresses: {r.gap_detail || titleCase(r.gap_type)}</span><span>Expected: {r.expected_outcome}</span><span>Time: {r.suggested_completion_time || 'Self-paced'}</span>
                  {r.source === 'MENTOR' && <span>Suggested by {cleanName(r.created_by_name)}</span>}
                </div>
              </div>
              <div className="flex flex-wrap items-start gap-2 sm:flex-col sm:items-end">
                {r.resource_url && <a href={r.resource_url} target="_blank" rel="noreferrer noopener"><Button size="sm" variant="ghost" icon={<ExternalLink size={13} />}>Resource</Button></a>}
                {r.status === 'SUGGESTED' && <><Button size="sm" variant="primary" onClick={() => act(r, 'accept')}>Accept</Button><Button size="sm" onClick={() => setActive({ r, kind: 'reject' })}>Decline</Button></>}
                {r.status === 'ACCEPTED' && <Button size="sm" variant="primary" onClick={() => act(r, 'start')}>Start</Button>}
                {r.status === 'IN_PROGRESS' && <Button size="sm" variant="primary" onClick={() => act(r, 'complete')}>Mark complete</Button>}
                {r.status === 'COMPLETED' && !r.feedback && <Button size="sm" onClick={() => setActive({ r, kind: 'feedback' })}>Give feedback</Button>}
              </div>
            </article>
          ))}
        </div>
      ) : <EmptyState title={filter === 'done' ? 'Nothing completed yet' : 'Your plan is clear'}>New suggestions appear when your records change or your mentor adds one.</EmptyState>}</Async>
      {active && <PlanDialog {...active} onClose={() => setActive(null)} onDone={recs.reload} />}
    </div>
  );
}

function PlanDialog({ r, kind, onClose, onDone }: { r: Recommendation; kind: 'reject' | 'feedback'; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const [text, setText] = useState(''); const [rating, setRating] = useState(4); const [saving, setSaving] = useState(false);
  const save = async () => {
    setSaving(true);
    try {
      if (kind === 'reject') await api.post(`/recommendations/${r.id}/reject`, { reason: text });
      else await api.post(`/recommendations/${r.id}/feedback`, { rating, helpful: rating >= 3, relevance_score: rating, comments: text || null, outcome_achieved: rating >= 4 });
      toast(kind === 'reject' ? 'Suggestion declined' : 'Feedback saved'); onDone(); onClose();
    } catch (e) { toast(errorMessage(e), 'error'); } finally { setSaving(false); }
  };
  return (
    <Dialog open onClose={onClose} title={kind === 'reject' ? 'Decline suggestion' : 'How useful was this?'} description={r.title}
      footer={<><Button onClick={onClose}>Cancel</Button><Button variant="primary" loading={saving} disabled={kind === 'reject' && text.trim().length < 3} onClick={save}>{kind === 'reject' ? 'Decline' : 'Save feedback'}</Button></>}>
      {kind === 'feedback' && (
        <Field label="Rating" className="mb-4"><div className="flex gap-1.5">{[1, 2, 3, 4, 5].map((n) => (
          <button key={n} type="button" onClick={() => setRating(n)} aria-pressed={rating === n}
            className={`h-8 w-8 rounded border text-[13px] ${rating >= n ? 'border-forest bg-forest-soft text-forest' : 'border-line-strong text-muted'}`}>{n}</button>
        ))}</div></Field>
      )}
      <Field label={kind === 'reject' ? 'Reason' : 'Comments (optional)'}><Textarea value={text} onChange={(e) => setText(e.target.value)} placeholder={kind === 'reject' ? 'e.g. Already completed a similar course' : ''} /></Field>
    </Dialog>
  );
}

/* ------------------------------------------------------------------ career readiness */
function notEligibleReason(o: OpportunityMatch) {
  const b = o.eligibility_breakdown || {};
  const r: string[] = [];
  if (b.cgpa_eligible === false) r.push(`CGPA ${o.min_cgpa}+ required`);
  if (b.attendance_eligible === false) r.push(`attendance ${o.min_attendance}%+ required`);
  if (b.backlogs_eligible === false) r.push(`at most ${o.max_backlogs} backlogs`);
  if (b.department_eligible === false) r.push('department not eligible');
  if (b.semester_eligible === false) r.push(`open to semesters ${(o.eligible_semesters || []).join(', ')}`);
  return r.join('; ') || 'Not eligible';
}
export function StudentCareer() {
  const sid = useStudentId();
  const toast = useToast();
  const roles = useApi<CareerRole[]>('/placement/roles');
  const [role, setRole] = useState('');
  const readiness = useApi<PlacementReadiness>(`/placement/readiness/${sid}`, role ? { role } : undefined);
  const opps = useApi<OpportunityMatch[]>(`/placement/students/${sid}/matching-opportunities`);
  const apps = useApi<Application[]>('/placement/applications');
  const [applyTo, setApplyTo] = useState<OpportunityMatch | null>(null);
  const [notes, setNotes] = useState('');
  const appliedIds = new Set((apps.data || []).map((a) => a.opportunity_id));
  const apply = async () => {
    if (!applyTo) return;
    try { await api.post('/placement/applications', { opportunity_id: applyTo.id, cover_notes: notes || null }); toast('Application submitted'); setApplyTo(null); setNotes(''); apps.reload(); }
    catch (e) { toast(errorMessage(e), 'error'); }
  };
  return (
    <div>
      <PageHeader title="Career readiness" lede="How your verified and self-reported skills compare with what a role needs. This is guidance, not a guarantee of placement or an employer certification."
        actions={<Select value={role} onChange={(e) => setRole(e.target.value)} className="w-56" aria-label="Career role">
          <option value="">My target role</option>{roles.data?.map((r) => <option key={r.code} value={r.code}>{r.title}</option>)}</Select>} />
      <Async state={readiness}>{(r) => (
        <>
          <StatStrip className="mb-6">
            <Stat label="Readiness" value={pct(r.readiness_score)} note={titleCase(r.readiness_tier)} />
            <Stat label="Skills matched" value={`${r.skills_matched_count} / ${r.total_role_skills_count}`} />
            <Stat label="Below level" value={r.skills_below_proficiency_count} tone={r.skills_below_proficiency_count ? 'attention' : undefined} />
            <Stat label="Missing" value={r.skills_missing_count} tone={r.skills_missing_count ? 'attention' : undefined} />
            <Stat label="Core skills met" value={r.mandatory_skills_met ? 'Yes' : 'Not yet'} />
          </StatStrip>
          <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
            <Panel padded={false} title={`What ${r.target_role?.title || 'this role'} needs`} description="Score weights critical skills more heavily; unverified skills count partially.">
              <DataTable rows={r.skill_gaps || []} rowKey={(g) => g.skill_name} columns={[
                { key: 'skill', header: 'Skill', render: (g) => <div><span className="font-medium">{g.skill_name}</span>{g.is_mandatory && <span className="ml-1.5 text-[11.5px] text-muted">core</span>}</div> },
                { key: 'need', header: 'Needed', render: (g) => g.required_proficiency },
                { key: 'have', header: 'You', render: (g) => g.student_proficiency || '—' },
                { key: 'status', header: 'Status', render: (g) => <StatusBadge status={g.status === 'MATCHED' ? 'ready' : g.status === 'MISSING' ? 'open' : 'pending'} label={titleCase(g.status)} /> },
              ]} />
            </Panel>
            <Panel title="Next steps">
              <ul className="space-y-3 text-[13px]">
                {(r.skill_gaps || []).filter((g) => g.status !== 'MATCHED').slice(0, 5).map((g) => (
                  <li key={g.skill_name}><div className="font-medium">{g.skill_name}</div><p className="text-muted">{g.suggested_improvement}</p>
                    {g.recommended_resource_url && <a className="link text-[12.5px]" href={g.recommended_resource_url} target="_blank" rel="noreferrer noopener">Suggested resource</a>}</li>
                ))}
                {!(r.skill_gaps || []).some((g) => g.status !== 'MATCHED') && <EmptyState title="You meet every listed skill for this role" />}
              </ul>
            </Panel>
          </div>
        </>
      )}</Async>
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Panel padded={false} title="Open opportunities" description="Eligibility uses your current CGPA, attendance, backlogs, department and semester.">
          <Async state={opps}>{(list) => (
            <DataTable rows={[...list].sort((a, b) => Number(b.is_eligible) - Number(a.is_eligible))} empty={<EmptyState title="No open opportunities right now" />} columns={[
              { key: 'company', header: 'Opportunity', render: (o) => <div><div className="font-medium">{o.title}</div><div className="text-[12px] text-muted">{o.company_name} · {o.location} · {o.ctc_stipend}</div></div> },
              { key: 'deadline', header: 'Deadline', hideOnMobile: true, render: (o) => fmtDate(o.application_deadline) },
              { key: 'a', header: '', align: 'right', render: (o) => appliedIds.has(o.id) ? <Badge tone="ok">Applied</Badge>
                : o.is_eligible ? <Button size="sm" onClick={() => setApplyTo(o)}>Apply</Button>
                : <span title={notEligibleReason(o)}><Badge>Not eligible</Badge></span> },
            ]} />
          )}</Async>
        </Panel>
        <Panel padded={false} title="My applications">
          <Async state={apps}>{(list) => (
            <DataTable rows={list} empty={<EmptyState title="You haven’t applied anywhere yet" />} columns={[
              { key: 'o', header: 'Opportunity', render: (a) => <div><div className="font-medium">{a.opportunity_title}</div><div className="text-[12px] text-muted">{a.company_name}</div></div> },
              { key: 'applied', header: 'Applied', hideOnMobile: true, render: (a) => fmtDate(a.applied_at) },
              { key: 's', header: 'Status', render: (a) => <StatusBadge status={a.status} /> },
            ]} />
          )}</Async>
        </Panel>
      </div>
      <Dialog open={!!applyTo} onClose={() => setApplyTo(null)} title={`Apply to ${applyTo?.company_name || ''}`} description={applyTo?.title}
        footer={<><Button onClick={() => setApplyTo(null)}>Cancel</Button><Button variant="primary" onClick={apply}>Submit application</Button></>}>
        <Notice>Eligibility: CGPA {applyTo?.min_cgpa}+, attendance {applyTo?.min_attendance}%+, up to {applyTo?.max_backlogs} backlogs. The placement office reviews every application.</Notice>
        <Field label="Note to the placement office (optional)" className="mt-4"><Textarea value={notes} onChange={(e) => setNotes(e.target.value)} /></Field>
      </Dialog>
    </div>
  );
}
