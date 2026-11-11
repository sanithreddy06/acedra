import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Check, Circle, Plus, X } from 'lucide-react';
import { api, errorMessage } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useApi } from '../lib/useApi';
import { fmtDate, MODULES, relTime, titleCase } from '../lib/format';
import { PageHeader } from '../components/shell';
import type { DataAccessGrant, EnquiryDetail, UniversityDetail, OutboxMessage, StudentDirectory, Enquiry, EnquiryList, Outbox, PlatformEmployee, PlatformOverview, ProvisioningRequest, UniversitySummary } from '../types/api';

const isEnquiry = (v: unknown): v is EnquiryDetail => !!v && typeof v === 'object' && 'reference' in v && 'id' in v;
const isUniversity = (v: unknown): v is UniversityDetail => !!v && typeof v === 'object' && 'slug' in v && 'id' in v;
import {
  Async, Badge, Button, Checkbox, ConfirmDialog, cx, DataTable, Dialog, EmptyState, Field, Input, KeyValues, Notice, Panel,
  SearchInput, Select, Stat, StatStrip, StatusBadge, Tabs, Textarea, Timeline, Toolbar, useToast,
} from '../components/ui';

const STAGES: [string, string][] = [
  ['new', 'New'], ['under_review', 'Under review'], ['contacted', 'Contacted'], ['meeting_scheduled', 'Meeting scheduled'],
  ['requirements_gathering', 'Requirements'], ['proposal_agreement', 'Proposal / agreement'], ['approved', 'Approved'],
  ['onboarding', 'Onboarding'], ['active', 'Active'], ['rejected', 'Rejected'], ['closed', 'Closed'],
];
const stageLabel = (s?: string | null) => STAGES.find(([k]) => k === s)?.[1] || titleCase(s);

/* ------------------------------------------------------------------ overview */
export function PlatformOverview() {
  const { me } = useAuth();
  const d = useApi<PlatformOverview>('/platform/overview');
  return (
    <div>
      <PageHeader meta="ACEDRA internal operations" title={d.data ? `${d.data.open_enquiries} open enquiries · ${d.data.tenants_by_status?.active || 0} active universities` : 'Platform'}
        lede="Platform staff manage onboarding and configuration. Student records are not visible here without an explicit, audited grant." />
      <Async state={d} rows={4}>{(x) => (
        <>
          <StatStrip className="mb-6">
            {['active', 'onboarding', 'suspended'].map((s) => <Stat key={s} label={`${titleCase(s)} universities`} value={x.tenants_by_status?.[s] || 0} />)}
            <Stat label="New enquiries" value={x.enquiries_by_status?.new || 0} tone={x.enquiries_by_status?.new ? 'attention' : undefined} />
            <Stat label="Provisioning requests open" value={x.pending_provisioning} />
          </StatStrip>
          <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
            <Panel title="Latest enquiries" padded={false} actions={<Link to="/platform/enquiries"><Button size="sm" variant="ghost">All enquiries</Button></Link>}>
              <EnquiryTable rows={x.recent_enquiries} />
            </Panel>
            <Panel title={me?.role === 'platform_admin' ? 'Universities you’re assigned to' : 'Your universities'} padded={false}>
              {x.my_universities.length ? <ul className="divide-y divide-line">{x.my_universities.map((u) => (
                <li key={u.id}><Link to={`/platform/universities/${u.id}`} className="flex items-center justify-between gap-2 px-4 py-2.5 hover:bg-sunken/60"><div><div className="font-medium">{u.name}</div><div className="text-[12px] text-muted">{u.domains.map((d) => d.domain).join(', ')}</div></div><StatusBadge status={u.status} /></Link></li>
              ))}</ul> : <div className="px-4"><EmptyState title="No assignments yet" /></div>}
            </Panel>
          </div>
        </>
      )}</Async>
    </div>
  );
}

/** Runs a mutation, shows a toast and refreshes; resolves to whether it succeeded. */
type RunAction = (fn: () => Promise<unknown>, msg: string) => Promise<boolean>;

function EnquiryTable({ rows }: { rows: Enquiry[] }) {
  const nav = useNavigate();
  return <DataTable rows={rows} onRowClick={(e) => nav(`/platform/enquiries/${e.id}`)} empty={<EmptyState title="No enquiries" />} columns={[
    { key: 'u', header: 'Institution', render: (e) => <div><div className="font-medium">{e.university_name}</div><div className="text-[12px] text-muted">{e.reference} · {e.location}</div></div> },
    { key: 'c', header: 'Contact', hideOnMobile: true, render: (e) => <div><div>{e.contact_name}</div><div className="text-[12px] text-muted">{e.contact_designation}</div></div> },
    { key: 'o', header: 'Owner', hideOnMobile: true, render: (e) => e.owner?.full_name || <span className="text-faint">Unassigned</span> },
    { key: 's', header: 'Stage', render: (e) => <StatusBadge status={e.status} label={stageLabel(e.status)} /> },
    { key: 'd', header: 'Received', hideOnMobile: true, render: (e) => relTime(e.created_at) },
  ]} />;
}

/* ------------------------------------------------------------------ enquiries */
export function EnquiriesPage() {
  const [status, setStatus] = useState('open'); const [search, setSearch] = useState('');
  const list = useApi<EnquiryList>('/platform/enquiries', { status, search, limit: 100 });
  return (
    <div>
      <PageHeader title="Enquiries" lede="Every institutional enquiry from the public website, from first contact to an active workspace." />
      <Panel padded={false}>
        <Toolbar>
          <SearchInput value={search} onChange={setSearch} placeholder="Search institution, reference or contact" className="w-full sm:w-80" />
          <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-52" aria-label="Stage"><option value="open">Open enquiries</option><option value="">All</option>{STAGES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</Select>
        </Toolbar>
        <Async state={list}>{(d) => <EnquiryTable rows={d.items} />}</Async>
      </Panel>
    </div>
  );
}

function StageTrack({ status }: { status: string }) {
  const order = STAGES.slice(0, 9).map(([k]) => k);
  const idx = order.indexOf(status);
  const terminal = status === 'rejected' || status === 'closed';
  return (
    <ol className="flex flex-wrap gap-x-1 gap-y-2 text-[12px]" aria-label="Enquiry progress">
      {STAGES.slice(0, 9).map(([k, l], i) => (
        <li key={k} className={cx('flex items-center gap-1 rounded px-1.5 py-0.5', i === idx ? 'bg-forest text-on-forest' : i < idx ? 'text-forest' : 'text-faint')}>
          {i < idx ? <Check size={12} /> : <Circle size={8} className={i === idx ? 'fill-current' : ''} />}{l}
        </li>
      ))}
      {terminal && <li className="rounded bg-danger-soft px-1.5 py-0.5 text-danger">{stageLabel(status)}</li>}
    </ol>
  );
}

export function EnquiryDetailPage() {
  const { id } = useParams();
  const { me } = useAuth();
  const toast = useToast();
  const nav = useNavigate();
  const e = useApi<EnquiryDetail>(`/platform/enquiries/${id}`);
  const team = useApi<PlatformEmployee[]>('/platform/employees');
  const [act, setAct] = useState({ kind: 'note', body: '', meeting_at: '' });
  const [statusTo, setStatusTo] = useState(''); const [statusNote, setStatusNote] = useState('');
  const [agreement, setAgreement] = useState<{ reference: string; agreed_modules: string[]; notes: string } | null>(null);
  const [tenant, setTenant] = useState<{ short_name: string; slug: string; domain: string; primary_employee_id: number | string } | null>(null);
  const run = async (fn: () => Promise<unknown>, msg: string) => { try { const r = await fn(); if (isEnquiry(r)) e.setData(r); else e.reload(); toast(msg); return true; } catch (er) { toast(errorMessage(er), 'error'); return false; } };
  const isAdmin = me?.role === 'platform_admin';
  return (
    <Async state={e}>{(x) => (
      <div>
        <PageHeader meta={`${x.reference} · received ${fmtDate(x.created_at)}`} title={x.university_name}
          actions={x.university_id ? <Link to={`/platform/universities/${x.university_id}`}><Button>Open workspace</Button></Link>
            : x.status === 'approved' && isAdmin ? <Button variant="primary" onClick={() => setTenant({ short_name: '', slug: '', domain: x.contact_email.split('@')[1] || '', primary_employee_id: x.owner?.id || '' })}>Create university workspace</Button> : null} />
        <div className="mb-6"><StageTrack status={x.status} /></div>
        <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <div className="space-y-6">
            <Panel title="Institution & contact">
              <KeyValues items={[['Type', x.institution_type], ['Location', x.location], ['Students', x.student_population], ['Departments / campuses', `${x.department_count ?? '—'} / ${x.campus_count ?? '—'}`],
                ['Website', x.official_website ? <a className="link" href={x.official_website} target="_blank" rel="noreferrer noopener">{x.official_website}</a> : '—'],
                ['Contact', `${x.contact_name}, ${x.contact_designation}`], ['Email', <a className="link" href={`mailto:${x.contact_email}`}>{x.contact_email}</a>], ['Phone', x.contact_phone || '—'],
                ['Prefers', titleCase(x.preferred_contact_method)]]} />
            </Panel>
            <Panel title="Requirements">
              <div className="mb-4 flex flex-wrap gap-1.5">{x.requested_modules.map((m: string) => <Badge key={m} tone="forest">{MODULES[m]?.short || m}</Badge>)}</div>
              <KeyValues cols={1} items={[['Current systems', [x.existing_sis, x.existing_academic_systems].filter(Boolean).join(' · ') || '—'],
                ['Institutional requirements', x.institutional_requirements || '—'], ['Expected outcomes', x.expected_outcomes || '—'], ['Additional information', x.additional_information || '—'],
                ['Finalised requirements', x.finalized_requirements || <span className="text-faint">Not recorded yet</span>]]} />
            </Panel>
            <Panel title="Student email accounts">
              {x.email_provisioning === 'rio_assisted' ? (
                <Notice tone="attention" title={`ACEDRA-assisted creation requested for ${x.accounts_required?.toLocaleString('en-IN') ?? '—'} accounts`}>
                  Additional chargeable service.{x.email_service_estimate ? ` Indicative estimate ₹${x.email_service_estimate.estimated_total_inr_per_year?.toLocaleString('en-IN')} per year.` : ''} Mailboxes are not created by ACEDRA automatically.
                </Notice>
              ) : <p className="text-[13px]">The university will provide existing institutional addresses{x.has_student_emails ? '' : ' (they indicated students do not yet have addresses)'}.</p>}
            </Panel>
            <Panel title="Activity">
              <div className="mb-5 space-y-3 rounded-lg border border-line p-3.5">
                <div className="grid gap-3 sm:grid-cols-[10rem_1fr]">
                  <Field label="Type"><Select value={act.kind} onChange={(ev) => setAct({ ...act, kind: ev.target.value })}><option value="note">Internal note</option><option value="contact">Contact made</option><option value="meeting">Meeting</option><option value="requirements">Finalised requirements</option></Select></Field>
                  {act.kind === 'meeting' && <Field label="Meeting date and time"><Input type="datetime-local" value={act.meeting_at} onChange={(ev) => setAct({ ...act, meeting_at: ev.target.value })} /></Field>}
                </div>
                <Textarea value={act.body} onChange={(ev) => setAct({ ...act, body: ev.target.value })} placeholder={act.kind === 'requirements' ? 'The agreed scope, inputs and outputs' : 'What happened or what was agreed'} aria-label="Activity details" />
                <Button size="sm" disabled={act.body.trim().length < 2} onClick={async () => { if (await run(() => api.post(`/platform/enquiries/${id}/activities`, { kind: act.kind, body: act.body, meeting_at: act.meeting_at || null }), 'Activity recorded')) setAct({ kind: 'note', body: '', meeting_at: '' }); }}>Record</Button>
              </div>
              <Timeline items={x.activities.slice().reverse().map((a) => ({
                id: a.id, tone: a.kind === 'status_change' ? 'forest' : a.kind === 'system' ? 'muted' : 'bronze',
                title: a.kind === 'status_change' ? <>Stage → {stageLabel(a.to_status)}</> : titleCase(a.kind),
                meta: `${a.author?.full_name || 'System'} · ${fmtDate(a.created_at, true)}${a.meeting_at ? ` · meeting ${fmtDate(a.meeting_at, true)}` : ''}`, body: a.body,
              }))} />
            </Panel>
          </div>
          <div className="space-y-6">
            <Panel title="Move stage">
              <div className="space-y-3">
                <Select value={statusTo} onChange={(ev) => setStatusTo(ev.target.value)} aria-label="New stage"><option value="">Choose stage…</option>
                  {STAGES.filter(([k]) => !['onboarding', 'active', x.status].includes(k)).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</Select>
                <Textarea value={statusNote} onChange={(ev) => setStatusNote(ev.target.value)} placeholder="Note (optional)" className="min-h-[60px]" aria-label="Stage note" />
                <Button disabled={!statusTo} onClick={async () => { if (await run(() => api.post(`/platform/enquiries/${id}/status`, { status: statusTo, note: statusNote || null }), `Moved to ${stageLabel(statusTo)}`)) { setStatusTo(''); setStatusNote(''); } }}>Update stage</Button>
                <p className="text-[12px] text-muted">Approval needs a recorded agreement. Onboarding and Active are set when the workspace is created and activated.</p>
              </div>
            </Panel>
            <Panel title="Owner">
              <Select value={x.owner?.id || ''} onChange={(ev) => run(() => api.post(`/platform/enquiries/${id}/owner`, { owner_id: ev.target.value ? Number(ev.target.value) : null }), 'Owner updated')} aria-label="Owner">
                <option value="">Unassigned</option>{team.data?.filter((t) => t.is_active).map((t) => <option key={t.id} value={t.id}>{t.full_name}</option>)}
              </Select>
            </Panel>
            <Panel title="Service agreement">
              {x.agreement_reference ? <KeyValues cols={1} items={[['Reference', x.agreement_reference], ['Recorded', fmtDate(x.agreement_recorded_at)], ['Agreed modules', x.agreed_modules.map((m: string) => MODULES[m]?.short).join(', ')]]} />
                : <p className="mb-3 text-[13px] text-muted">No agreement recorded yet.</p>}
              <Button size="sm" className="mt-3" onClick={() => setAgreement({ reference: x.agreement_reference || '', agreed_modules: x.agreed_modules.length ? x.agreed_modules : x.requested_modules, notes: '' })}>{x.agreement_reference ? 'Update agreement' : 'Record agreement'}</Button>
            </Panel>
          </div>
        </div>
        {agreement && (
          <Dialog open onClose={() => setAgreement(null)} title="Record service agreement" footer={<><Button onClick={() => setAgreement(null)}>Cancel</Button>
            <Button variant="primary" disabled={agreement.reference.length < 3 || !agreement.agreed_modules.length} onClick={async () => { if (await run(() => api.post(`/platform/enquiries/${id}/agreement`, agreement), 'Agreement recorded')) setAgreement(null); }}>Save agreement</Button></>}>
            <div className="space-y-4">
              <Field label="Agreement reference"><Input value={agreement.reference} onChange={(ev) => setAgreement({ ...agreement, reference: ev.target.value })} placeholder="e.g. ACEDRA-SA-2026-014" /></Field>
              <div><span className="label mb-2 block">Agreed modules</span><div className="space-y-2">{Object.entries(MODULES).map(([k, m]) => (
                <Checkbox key={k} label={m.name} checked={agreement.agreed_modules.includes(k)} onChange={(c) => setAgreement({ ...agreement, agreed_modules: c ? [...agreement.agreed_modules, k] : agreement.agreed_modules.filter((v: string) => v !== k) })} />
              ))}</div></div>
              <Field label="Notes"><Textarea value={agreement.notes} onChange={(ev) => setAgreement({ ...agreement, notes: ev.target.value })} /></Field>
            </div>
          </Dialog>
        )}
        {tenant && (
          <Dialog open onClose={() => setTenant(null)} title="Create university workspace" description="Creates the tenant with the agreed modules, default rules and catalogue, and assigns the dedicated ACEDRA employee."
            footer={<><Button onClick={() => setTenant(null)}>Cancel</Button><Button variant="primary" disabled={!tenant.short_name || !tenant.slug || !tenant.primary_employee_id}
              onClick={async () => { try { const u = await api.post<UniversitySummary>(`/platform/enquiries/${id}/create-tenant`, { short_name: tenant.short_name, slug: tenant.slug, domains: tenant.domain ? [tenant.domain] : [], primary_employee_id: Number(tenant.primary_employee_id) }); toast('Workspace created'); nav(`/platform/universities/${u.id}`); } catch (er) { toast(errorMessage(er), 'error'); } }}>Create workspace</Button></>}>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Short name"><Input value={tenant.short_name} onChange={(ev) => setTenant({ ...tenant, short_name: ev.target.value, slug: tenant.slug || ev.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-') })} /></Field>
              <Field label="Workspace slug" hint="Lowercase letters, digits and hyphens"><Input value={tenant.slug} onChange={(ev) => setTenant({ ...tenant, slug: ev.target.value.toLowerCase() })} /></Field>
              <Field label="Primary email domain"><Input value={tenant.domain} onChange={(ev) => setTenant({ ...tenant, domain: ev.target.value })} /></Field>
              <Field label="Dedicated ACEDRA employee"><Select value={tenant.primary_employee_id} onChange={(ev) => setTenant({ ...tenant, primary_employee_id: ev.target.value })}><option value="">Choose…</option>{team.data?.filter((t) => t.is_active).map((t) => <option key={t.id} value={t.id}>{t.full_name}</option>)}</Select></Field>
            </div>
          </Dialog>
        )}
      </div>
    )}</Async>
  );
}

/* ------------------------------------------------------------------ universities */
export function UniversitiesPage() {
  const nav = useNavigate();
  const list = useApi<UniversitySummary[]>('/platform/universities');
  return (
    <div>
      <PageHeader title="Universities" lede="Each university is an isolated workspace on the shared platform, with its own configuration and a dedicated ACEDRA contact." />
      <Panel padded={false}>
        <Async state={list}>{(rows) => <DataTable rows={rows} onRowClick={(u) => nav(`/platform/universities/${u.id}`)} columns={[
          { key: 'n', header: 'University', render: (u) => <div className="flex items-center gap-2.5"><span className="h-6 w-1.5 rounded-full" style={{ background: u.brand_color }} aria-hidden /><div><div className="font-medium">{u.name}</div><div className="text-[12px] text-muted">{u.slug} · {u.location}</div></div></div> },
          { key: 'd', header: 'Domains', hideOnMobile: true, render: (u) => u.domains.map((d) => d.domain).join(', ') || '—' },
          { key: 'e', header: 'ACEDRA contact', render: (u) => u.primary_employee?.full_name || <span className="text-bronze">Unassigned</span> },
          { key: 'm', header: 'Modules', align: 'right', hideOnMobile: true, render: (u) => `${u.enabled_modules.length}/6` },
          { key: 's', header: 'Status', render: (u) => <div className="flex gap-1.5"><StatusBadge status={u.status} />{u.is_synthetic && <Badge>Synthetic</Badge>}</div> },
        ]} />}</Async>
      </Panel>
    </div>
  );
}

export function UniversityDetailPage() {
  const { id } = useParams();
  const { me } = useAuth();
  const toast = useToast();
  const u = useApi<UniversityDetail>(`/platform/universities/${id}`);
  const team = useApi<PlatformEmployee[]>('/platform/employees');
  const [tab, setTab] = useState('setup');
  const isAdmin = me?.role === 'platform_admin';
  const run = async (fn: () => Promise<unknown>, msg: string) => { try { const r = await fn(); if (isUniversity(r)) u.setData(r); else u.reload(); toast(msg); return true; } catch (e) { toast(errorMessage(e), 'error'); return false; } };
  return (
    <Async state={u}>{(x) => (
      <div>
        <PageHeader meta={<span className="inline-flex items-center gap-2"><StatusBadge status={x.status} />{x.is_synthetic && <Badge>Synthetic demo data</Badge>}<span>{x.slug}</span></span>} title={x.name}
          lede={x.primary_employee ? `Dedicated ACEDRA contact: ${x.primary_employee.full_name}` : 'No dedicated ACEDRA contact assigned'}
          actions={isAdmin && <StatusActions x={x} run={run} />} />
        <Tabs value={tab} onChange={setTab} className="mb-5" tabs={[{ id: 'setup', label: 'Onboarding' }, { id: 'config', label: 'Configuration' }, { id: 'team', label: 'ACEDRA team' }, { id: 'access', label: 'Student-data access' }, { id: 'prov', label: 'Provisioning' }]} />
        {tab === 'setup' && <SetupTab x={x} run={run} />}
        {tab === 'config' && <ConfigTab x={x} run={run} />}
        {tab === 'team' && <TeamTab x={x} team={team.data || []} run={run} isAdmin={isAdmin} />}
        {tab === 'access' && <GrantsTab x={x} team={team.data || []} isAdmin={isAdmin} />}
        {tab === 'prov' && <ProvTab uid={x.id} />}
      </div>
    )}</Async>
  );
}

function StatusActions({ x, run }: { x: UniversityDetail; run: RunAction }) {
  const [confirm, setConfirm] = useState<string | null>(null);
  return (
    <>
      {x.status !== 'active' && <Button variant="primary" disabled={!x.readiness?.ready} onClick={() => setConfirm('active')}>Activate workspace</Button>}
      {x.status === 'active' && <Button onClick={() => setConfirm('suspended')}>Suspend</Button>}
      <ConfirmDialog open={!!confirm} onClose={() => setConfirm(null)} danger={confirm !== 'active'} title={confirm === 'active' ? 'Activate this workspace?' : 'Suspend this workspace?'}
        confirmLabel={confirm === 'active' ? 'Activate' : 'Suspend workspace'} onConfirm={async () => { await run(() => api.post(`/platform/universities/${x.id}/status`, { status: confirm }), confirm === 'active' ? 'Workspace activated' : 'Workspace suspended'); setConfirm(null); }}>
        {confirm === 'active' ? 'All invited members of this university will be able to sign in.' : 'Every user at this university will be signed out and unable to sign in until it is reactivated.'}
      </ConfirmDialog>
    </>
  );
}

function SetupTab({ x, run }: { x: UniversityDetail; run: RunAction }) {
  const [admin, setAdmin] = useState({ email: '', full_name: '', title: '' });
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
      <Panel title="Go-live checklist">
        <ul className="space-y-2.5">{x.readiness.checks.map((c) => (
          <li key={c.key} className="flex items-center gap-2.5 text-[13.5px]">
            <span className={cx('flex h-5 w-5 items-center justify-center rounded-full', c.done ? 'bg-ok-soft text-ok' : 'border border-line-strong text-faint')}>{c.done ? <Check size={12} /> : null}</span>
            <span className={c.done ? 'text-ink' : 'text-muted'}>{c.label}</span>
          </li>))}</ul>
        {x.enquiry_id && <Link className="link mt-4 inline-block text-[13px]" to={`/platform/enquiries/${x.enquiry_id}`}>View the originating enquiry</Link>}
      </Panel>
      <div className="space-y-6">
        <Panel title="University administrators" description="The initial administrator is invited on an approved domain and then manages their own users.">
          {x.admins.length ? <ul className="mb-4 divide-y divide-line">{x.admins.map((a) => (
            <li key={a.id} className="flex items-center justify-between py-2"><div><div className="font-medium">{a.full_name}</div><div className="text-[12px] text-muted">{a.email}</div></div><StatusBadge status={a.is_verified ? 'active' : 'invited'} /></li>
          ))}</ul> : null}
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Full name"><Input value={admin.full_name} onChange={(e) => setAdmin({ ...admin, full_name: e.target.value })} /></Field>
            <Field label="Designation"><Input value={admin.title} onChange={(e) => setAdmin({ ...admin, title: e.target.value })} /></Field>
            <Field label="Institutional email" className="sm:col-span-2" hint={`Approved: ${x.domains.map((d) => d.domain).join(', ') || 'add a domain first'}`}><Input type="email" value={admin.email} onChange={(e) => setAdmin({ ...admin, email: e.target.value })} /></Field>
          </div>
          <Button className="mt-3" variant="primary" disabled={!admin.email || admin.full_name.length < 2}
            onClick={async () => { if (await run(() => api.post(`/platform/universities/${x.id}/admins`, admin), 'Invitation sent to the administrator')) setAdmin({ email: '', full_name: '', title: '' }); }}>Invite administrator</Button>
        </Panel>
        <Panel title="Accounts in this workspace" description="Counts only — ACEDRA staff don’t see individual student records.">
          <div className="flex flex-wrap gap-x-8 gap-y-2">{['admin', 'faculty', 'mentor', 'placement_officer', 'student'].map((r) => <Stat key={r} label={titleCase(r)} value={x.user_counts?.[r] || 0} />)}</div>
        </Panel>
      </div>
    </div>
  );
}

function ConfigTab({ x, run }: { x: UniversityDetail; run: RunAction }) {
  const [f, setF] = useState({ name: x.name, short_name: x.short_name, official_website: x.official_website || '', location: x.location || '', brand_color: x.brand_color, tagline: x.tagline || '',
    enabled_modules: x.enabled_modules, enforce_email_domains: x.enforce_email_domains, student_email_mode: x.student_email_mode || 'existing',
    // Numeric inputs are edited as text and converted on save.
    att: String(x.academic_structure?.minimum_attendance_percent ?? 75), term: x.academic_structure?.term_label || 'Semester',
    terms: String(x.academic_structure?.terms_per_year ?? 2), cgpa: String(x.academic_structure?.cgpa_max ?? 10) });
  const [domain, setDomain] = useState('');
  const save = () => run(() => api.patch(`/platform/universities/${x.id}`, {
    name: f.name, short_name: f.short_name, official_website: f.official_website || null, location: f.location, brand_color: f.brand_color, tagline: f.tagline,
    enabled_modules: f.enabled_modules, enforce_email_domains: f.enforce_email_domains, student_email_mode: f.student_email_mode,
    academic_structure: { minimum_attendance_percent: Number(f.att), term_label: f.term, terms_per_year: Number(f.terms), cgpa_max: Number(f.cgpa) },
  }), 'Configuration saved');
  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
      <div className="space-y-6">
        <Panel title="Identity & branding">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Name"><Input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
            <Field label="Short name"><Input value={f.short_name} onChange={(e) => setF({ ...f, short_name: e.target.value })} /></Field>
            <Field label="Website"><Input value={f.official_website} onChange={(e) => setF({ ...f, official_website: e.target.value })} /></Field>
            <Field label="Location"><Input value={f.location} onChange={(e) => setF({ ...f, location: e.target.value })} /></Field>
            <Field label="Brand colour"><div className="flex gap-2"><input type="color" value={f.brand_color} onChange={(e) => setF({ ...f, brand_color: e.target.value })} className="h-9 w-12 rounded border border-line-strong bg-surface" aria-label="Brand colour" /><Input value={f.brand_color} onChange={(e) => setF({ ...f, brand_color: e.target.value })} /></div></Field>
            <Field label="Tagline"><Input value={f.tagline} onChange={(e) => setF({ ...f, tagline: e.target.value })} /></Field>
          </div>
        </Panel>
        <Panel title="Academic structure">
          <div className="grid gap-4 sm:grid-cols-4">
            <Field label="Term label"><Select value={f.term} onChange={(e) => setF({ ...f, term: e.target.value })}><option>Semester</option><option>Term</option><option>Trimester</option></Select></Field>
            <Field label="Terms per year"><Input type="number" min={1} max={4} value={f.terms} onChange={(e) => setF({ ...f, terms: e.target.value })} /></Field>
            <Field label="CGPA scale"><Input type="number" value={f.cgpa} onChange={(e) => setF({ ...f, cgpa: e.target.value })} /></Field>
            <Field label="Min. attendance %"><Input type="number" value={f.att} onChange={(e) => setF({ ...f, att: e.target.value })} /></Field>
          </div>
        </Panel>
        <Panel title="Enabled modules" description="Modules a university hasn’t agreed to are blocked server-side for all its users.">
          <div className="grid gap-3 sm:grid-cols-2">{Object.entries(MODULES).map(([k, m]) => (
            <Checkbox key={k} label={m.name} checked={f.enabled_modules.includes(k)} onChange={(c) => setF({ ...f, enabled_modules: c ? [...f.enabled_modules, k] : f.enabled_modules.filter((v) => v !== k) })} />
          ))}</div>
        </Panel>
        <div className="flex justify-end"><Button variant="primary" onClick={save}>Save configuration</Button></div>
      </div>
      <div className="space-y-6">
        <Panel title="Email domains" description="Invitations are only accepted on these domains. A domain never grants access by itself.">
          <ul className="mb-3 divide-y divide-line">{x.domains.map((d) => (
            <li key={d.id} className="flex items-center justify-between py-2"><span className="font-medium">{d.domain}{d.is_primary && <span className="ml-2 text-[12px] font-normal text-muted">primary</span>}</span>
              <Button size="sm" variant="quiet" aria-label={`Remove ${d.domain}`} onClick={() => run(() => api.del(`/platform/universities/${x.id}/domains/${d.id}`), 'Domain removed')}><X size={13} /></Button></li>
          ))}{!x.domains.length && <li className="py-2 text-[13px] text-muted">No domains yet.</li>}</ul>
          <div className="flex gap-2"><Input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="university.edu.in" aria-label="New domain" /><Button disabled={!domain} onClick={async () => { if (await run(() => api.post(`/platform/universities/${x.id}/domains`, { domain }), 'Domain added')) setDomain(''); }}>Add</Button></div>
          <div className="mt-4"><Checkbox label="Require an approved domain for every invitation" checked={f.enforce_email_domains} onChange={(v) => setF({ ...f, enforce_email_domains: v })} /></div>
        </Panel>
        <Panel title="Student email accounts">
          <Select value={f.student_email_mode} onChange={(e) => setF({ ...f, student_email_mode: e.target.value })} aria-label="Student email mode"><option value="existing">University provides existing addresses</option><option value="rio_assisted">ACEDRA-assisted creation (additional service)</option></Select>
        </Panel>
      </div>
    </div>
  );
}

function TeamTab({ x, team, run, isAdmin }: { x: UniversityDetail; team: PlatformEmployee[]; run: RunAction; isAdmin: boolean }) {
  const [emp, setEmp] = useState(''); const [notes, setNotes] = useState('');
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
      <Panel title="Dedicated ACEDRA employee" description="The university’s point of contact for onboarding, requirements and changes. Assignment grants configuration — never student-record — access.">
        {x.primary_employee ? <KeyValues cols={1} items={[['Name', x.primary_employee.full_name], ['Role', x.primary_employee.title], ['Email', x.primary_employee.email], ['Phone', x.primary_employee.phone]]} /> : <Notice tone="attention">No dedicated employee assigned.</Notice>}
        {isAdmin && (
          <div className="mt-5 space-y-3 border-t border-line pt-4">
            <Field label="Reassign to"><Select value={emp} onChange={(e) => setEmp(e.target.value)}><option value="">Choose…</option>{team.filter((t) => t.is_active && t.id !== x.primary_employee?.id).map((t) => <option key={t.id} value={t.id}>{t.full_name}</option>)}</Select></Field>
            <Field label="Handover note"><Input value={notes} onChange={(e) => setNotes(e.target.value)} /></Field>
            <Button disabled={!emp} onClick={async () => { if (await run(() => api.post(`/platform/universities/${x.id}/primary-employee`, { employee_id: Number(emp), notes: notes || null }), 'Primary employee reassigned')) { setEmp(''); setNotes(''); } }}>Reassign</Button>
          </div>
        )}
      </Panel>
      <Panel title="Assignment history" padded={false}>
        <DataTable rows={x.assignments} columns={[
          { key: 'e', header: 'Employee', render: (a) => a.employee?.full_name }, { key: 'r', header: 'Role', render: (a) => titleCase(a.assignment_role) },
          { key: 'p', header: 'Period', render: (a) => `${fmtDate(a.started_at)} – ${a.ended_at ? fmtDate(a.ended_at) : 'present'}` },
          { key: 's', header: '', render: (a) => a.is_active ? <Badge tone="ok">Current</Badge> : null },
        ]} />
      </Panel>
    </div>
  );
}

function GrantsTab({ x, team, isAdmin }: { x: UniversityDetail; team: PlatformEmployee[]; isAdmin: boolean }) {
  const toast = useToast();
  const grants = useApi<DataAccessGrant[]>(`/platform/universities/${x.id}/grants`);
  const [f, setF] = useState({ employee_id: '', reason: '', university_authorised_by: '', days: '7' });
  const [dir, setDir] = useState<StudentDirectory | null>(null);
  const create = async () => {
    try { await api.post(`/platform/universities/${x.id}/grants`, { ...f, employee_id: Number(f.employee_id), days: Number(f.days) }); toast('Grant recorded'); setF({ employee_id: '', reason: '', university_authorised_by: '', days: '7' }); grants.reload(); }
    catch (e) { toast(errorMessage(e), 'error'); }
  };
  const openDir = async () => { try { setDir(await api.get<StudentDirectory>(`/platform/universities/${x.id}/student-directory`)); } catch (e) { toast(errorMessage(e), 'error'); } };
  return (
    <div className="space-y-6">
      <Notice title="Student records are off-limits by default">Configuration and coordination permissions never include student data. A super administrator can record a time-limited grant, named and approved by the university, for a specific support task. Every read is audited.</Notice>
      <div className="grid gap-6 lg:grid-cols-[1fr_1.4fr]">
        {isAdmin ? (
          <Panel title="Record a grant">
            <div className="space-y-3">
              <Field label="Employee"><Select value={f.employee_id} onChange={(e) => setF({ ...f, employee_id: e.target.value })}><option value="">Choose…</option>{team.filter((t) => t.is_active).map((t) => <option key={t.id} value={t.id}>{t.full_name}</option>)}</Select></Field>
              <Field label="Approved by (university)" hint="Name and designation of the approving official"><Input value={f.university_authorised_by} onChange={(e) => setF({ ...f, university_authorised_by: e.target.value })} /></Field>
              <Field label="Reason"><Textarea value={f.reason} onChange={(e) => setF({ ...f, reason: e.target.value })} placeholder="The specific support task requiring access" /></Field>
              <Field label="Duration"><Select value={f.days} onChange={(e) => setF({ ...f, days: e.target.value })}>{[1, 3, 7, 14, 30].map((d) => <option key={d} value={d}>{d} day{d > 1 ? 's' : ''}</option>)}</Select></Field>
              <Button variant="primary" disabled={!f.employee_id || f.reason.length < 10 || f.university_authorised_by.length < 3} onClick={create}>Record grant</Button>
            </div>
          </Panel>
        ) : (
          <Panel title="Your access"><p className="mb-3 text-[13px] text-muted">If a super administrator has recorded an active grant for you, you can open the minimal student directory for the approved task.</p><Button onClick={openDir}>Open student directory</Button></Panel>
        )}
        <Panel title="Grants" padded={false}>
          <Async state={grants}>{(list) => <DataTable rows={list} empty={<EmptyState title="No grants recorded" />} columns={[
            { key: 'e', header: 'Employee', render: (g) => <div><div className="font-medium">{g.employee?.full_name}</div><div className="line-clamp-1 text-[12px] text-muted">{g.reason}</div></div> },
            { key: 'a', header: 'Approved by', hideOnMobile: true, render: (g) => g.university_authorised_by },
            { key: 'x', header: 'Expires', render: (g) => fmtDate(g.expires_at) },
            { key: 's', header: 'Status', render: (g) => g.revoked_at ? <Badge>Revoked</Badge> : g.is_active ? <Badge tone="caution" dot>Active</Badge> : <Badge>Expired</Badge> },
            { key: 'r', header: '', align: 'right', render: (g) => isAdmin && g.is_active ? <Button size="sm" variant="ghost" onClick={async () => { await api.post(`/platform/grants/${g.id}/revoke`); toast('Grant revoked'); grants.reload(); }}>Revoke</Button> : null },
          ]} />}</Async>
        </Panel>
      </div>
      {dir && (
        <Panel title="Student directory (read-only)" description={`Access recorded in the audit log · grant expires ${fmtDate(dir.grant_expires_at, true)}`} padded={false}>
          <DataTable rows={dir.students} dense columns={[{ key: 'n', header: 'Name', render: (s) => s.full_name }, { key: 'u', header: 'USN', render: (s) => s.usn }, { key: 'd', header: 'Dept', render: (s) => s.department }, { key: 's', header: 'Semester', render: (s) => s.semester }]} />
        </Panel>
      )}
    </div>
  );
}

function ProvTab({ uid }: { uid: number }) {
  const toast = useToast();
  const list = useApi<ProvisioningRequest[]>(`/platform/universities/${uid}/provisioning`);
  const update = async (p: ProvisioningRequest, data: Partial<ProvisioningRequest>) => { try { await api.patch(`/platform/provisioning/${p.id}`, data); toast('Request updated'); list.reload(); } catch (e) { toast(errorMessage(e), 'error'); } };
  return (
    <Panel title="Account provisioning requests" description="Recorded requirements. This build does not create real mailboxes — completed counts are tracked manually." padded={false}>
      <Async state={list}>{(rows) => <DataTable rows={rows} empty={<EmptyState title="No requests" />} columns={[
        { key: 'm', header: 'Method', render: (p) => p.method === 'rio_assisted' ? <span>ACEDRA-assisted <Badge tone="bronze">chargeable</Badge></span> : 'Existing emails' },
        { key: 'a', header: 'Accounts', align: 'right', render: (p) => `${p.accounts_completed} / ${p.accounts_requested}` },
        { key: 'c', header: 'Estimate', align: 'right', render: (p) => p.estimated_cost ? `₹${p.estimated_cost.toLocaleString('en-IN')}/yr` : '—' },
        { key: 'n', header: 'Notes', hideOnMobile: true, render: (p) => <span className="line-clamp-2 text-[12.5px] text-muted">{p.notes}</span> },
        { key: 's', header: 'Status', render: (p) => <Select value={p.status} onChange={(e) => update(p, { status: e.target.value })} className="h-8 w-36" aria-label="Status">{['requested', 'estimated', 'approved', 'in_progress', 'completed', 'cancelled'].map((s) => <option key={s} value={s}>{titleCase(s)}</option>)}</Select> },
      ]} />}</Async>
    </Panel>
  );
}

/* ------------------------------------------------------------------ team */
export function TeamPage() {
  const { me } = useAuth();
  const toast = useToast();
  const team = useApi<PlatformEmployee[]>('/platform/employees');
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({ email: '', full_name: '', title: '', phone: '', role: 'platform_employee', permissions: ['tenant.configure', 'tenant.coordinate'] });
  const isAdmin = me?.role === 'platform_admin';
  const save = async () => { try { await api.post('/platform/employees', f); toast(`Invitation sent to ${f.email}`); setOpen(false); team.reload(); } catch (e) { toast(errorMessage(e), 'error'); } };
  const toggle = async (t: PlatformEmployee, perm: string) => {
    const perms = t.permissions.includes(perm) ? t.permissions.filter((p: string) => p !== perm) : [...t.permissions, perm];
    try { await api.patch(`/platform/employees/${t.id}`, { permissions: perms }); team.reload(); } catch (e) { toast(errorMessage(e), 'error'); }
  };
  return (
    <div>
      <PageHeader title="ACEDRA team" lede="Internal staff and their permissions. Configuration and coordination are separate permissions; student-data access is never a standing permission."
        actions={isAdmin && <Button variant="primary" icon={<Plus size={14} />} onClick={() => setOpen(true)}>Invite team member</Button>} />
      <Panel padded={false}>
        <Async state={team}>{(rows) => <DataTable rows={rows} columns={[
          { key: 'n', header: 'Name', render: (t) => <div><div className="font-medium">{t.full_name}</div><div className="text-[12px] text-muted">{t.email} · {t.employee_code}</div></div> },
          { key: 'r', header: 'Role', render: (t) => t.role === 'platform_admin' ? 'Super administrator' : t.title || 'Employee' },
          { key: 'p', header: 'Permissions', render: (t) => t.role === 'platform_admin' ? <Badge tone="forest">All platform permissions</Badge> : (
            <div className="flex flex-wrap gap-1.5">{[['tenant.configure', 'Configure'], ['tenant.coordinate', 'Coordinate']].map(([k, l]) => (
              <button key={k} type="button" disabled={!isAdmin} onClick={() => toggle(t, k)} aria-pressed={t.permissions.includes(k)}
                className={cx('rounded border px-1.5 py-[1px] text-[12px]', t.permissions.includes(k) ? 'border-forest/40 bg-forest-soft text-forest' : 'border-line text-faint', !isAdmin && 'cursor-default')}>{l}</button>))}</div>) },
          { key: 'a', header: 'Universities', hideOnMobile: true, render: (t) => t.assignments.map((a) => a.university).join(', ') || '—' },
          { key: 's', header: 'Status', render: (t) => <StatusBadge status={!t.is_verified ? 'invited' : t.is_active ? 'active' : 'disabled'} /> },
        ]} />}</Async>
      </Panel>
      <Dialog open={open} onClose={() => setOpen(false)} title="Invite an ACEDRA team member" footer={<><Button onClick={() => setOpen(false)}>Cancel</Button><Button variant="primary" disabled={!f.email || f.full_name.length < 2} onClick={save}>Send invitation</Button></>}>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Full name" className="sm:col-span-2"><Input value={f.full_name} onChange={(e) => setF({ ...f, full_name: e.target.value })} /></Field>
          <Field label="Email" className="sm:col-span-2"><Input type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
          <Field label="Job title"><Input value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></Field>
          <Field label="Phone"><Input value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} /></Field>
          <Field label="Role" className="sm:col-span-2"><Select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}><option value="platform_employee">Employee</option><option value="platform_admin">Super administrator</option></Select></Field>
        </div>
      </Dialog>
    </div>
  );
}

/* ------------------------------------------------------------------ outbox */
export function OutboxPage() {
  const o = useApi<Outbox>('/platform/email-outbox');
  const [open, setOpen] = useState<OutboxMessage | null>(null);
  return (
    <div>
      <PageHeader title="Email outbox" lede="Messages ACEDRA has generated: invitations, password resets and enquiry acknowledgements." />
      <Async state={o}>{(d) => (
        <>
          <div className="mb-5"><Notice tone={d.provider === 'log' ? 'attention' : 'info'} title={d.provider === 'log' ? 'Development mode: emails are logged, not sent' : `Delivered through ${d.provider.toUpperCase()}`}>
            {d.provider === 'log' ? 'Configure EMAIL_PROVIDER=smtp to deliver mail. Message bodies contain single-use links and are hidden in production.' : 'Message bodies are hidden in production.'}</Notice></div>
          <Panel padded={false}><DataTable rows={d.items} onRowClick={d.bodies_visible ? (m) => setOpen(m) : undefined} columns={[
            { key: 't', header: 'To', render: (m) => m.to_email }, { key: 's', header: 'Subject', render: (m) => m.subject },
            { key: 'k', header: 'Type', hideOnMobile: true, render: (m) => titleCase(m.template) }, { key: 'st', header: 'Status', render: (m) => <StatusBadge status={m.status} /> },
            { key: 'd', header: 'When', hideOnMobile: true, render: (m) => relTime(m.created_at) },
          ]} /></Panel>
        </>
      )}</Async>
      <Dialog open={!!open} onClose={() => setOpen(null)} title={open?.subject} description={`To ${open?.to_email}`} wide>
        <pre className="whitespace-pre-wrap break-words font-sans text-[13px] leading-relaxed">{open?.body_text}</pre>
      </Dialog>
    </div>
  );
}
