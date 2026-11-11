import { FormEvent, ReactNode, useEffect, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Check, Menu as MenuIcon, X } from 'lucide-react';
import { api, ApiError, errorMessage } from '../lib/api';
import { homeFor, useAuth } from '../lib/auth';
import { MODULES, ROLE_LABEL } from '../lib/format';
import { AcedraWordmark } from '../components/brand';
import { LegalLinks } from '../components/legal';
import { openCookiePreferences } from '../lib/consent';
import { PLACEHOLDER, SITE } from '../lib/site';
import { Button, Checkbox, cx, Field, Input, Notice, Select, Textarea } from '../components/ui';
import type { EnquiryOptions, EnquiryReceipt, InvitationInfo, LegalDocumentSummary, TokenResponse } from '../types/api';

/* ------------------------------------------------------------------ public frame */
const SITE_NAV: [string, string][] = [
  ['/solutions', 'Platform'], ['/about', 'About'], ['/security', 'Security'], ['/faq', 'FAQ'], ['/contact', 'Contact'],
];

function PublicNav() {
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  useEffect(() => setOpen(false), [loc.pathname]);
  const navCls = ({ isActive }: { isActive: boolean }) => cx('hover:text-ink', isActive && 'text-ink font-medium');
  return (
    <header className="border-b border-line">
      <a href="#content" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-2">Skip to content</a>
      <div className="mx-auto flex h-14 max-w-content items-center gap-6 px-5 sm:px-8">
        <Link to="/" aria-label="ACEDRA home"><AcedraWordmark size={24} /></Link>
        <nav className="hidden items-center gap-5 text-[13.5px] text-muted md:flex" aria-label="Site">
          {SITE_NAV.map(([to, label]) => <NavLink key={to} to={to} className={navCls}>{label}</NavLink>)}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <Link to="/login" className="hidden px-2 text-[13.5px] text-muted hover:text-ink sm:inline">Sign in</Link>
          <Link to="/enquire" className="hidden sm:inline-flex"><Button variant="primary" size="sm">Request a consultation</Button></Link>
          <button type="button" className="inline-flex h-9 w-9 items-center justify-center rounded text-muted hover:bg-sunken hover:text-ink md:hidden"
            aria-expanded={open} aria-controls="site-menu" aria-label={open ? 'Close menu' : 'Open menu'} onClick={() => setOpen((o) => !o)}>
            {open ? <X size={18} /> : <MenuIcon size={18} />}
          </button>
        </div>
      </div>
      {open && (
        <nav id="site-menu" aria-label="Site" className="border-t border-line px-5 pb-4 pt-2 md:hidden">
          <ul className="space-y-1 text-[14px]">
            {[...SITE_NAV, ['/login', 'Sign in'] as [string, string], ['/enquire', 'Request a consultation'] as [string, string]].map(([to, label]) => (
              <li key={to}><NavLink to={to} className={({ isActive }) => cx('block rounded px-2 py-2', isActive ? 'bg-sunken text-ink' : 'text-muted hover:bg-sunken hover:text-ink')}>{label}</NavLink></li>
            ))}
          </ul>
        </nav>
      )}
    </header>
  );
}

const FOOTER: [string, [string, string][]][] = [
  ['Platform', [['/solutions', 'Capabilities'], ['/about', 'About ACEDRA'], ['/security', 'Security'], ['/faq', 'FAQ']]],
  ['Institutions', [['/enquire', 'Institutional enquiry'], ['/contact', 'Contact'], ['/login', 'Institutional sign-in']]],
  ['Legal', [['/legal/terms', 'Terms and conditions'], ['/legal/privacy', 'Privacy policy'], ['/legal/cookies', 'Cookie policy'], ['/accessibility', 'Accessibility']]],
];

function PublicFooter() {
  return (
    <footer className="border-t border-line bg-paper">
      <div className="mx-auto grid max-w-content gap-8 px-5 py-10 text-[13px] sm:px-8 md:grid-cols-[1.3fr_repeat(3,1fr)]">
        <div>
          <AcedraWordmark size={20} tagline />
          <p className="mt-3 max-w-xs text-[12.5px] leading-relaxed text-muted">A university intelligence platform for student support. Accounts are created by institutions; there is no public sign-up.</p>
        </div>
        {FOOTER.map(([title, links]) => (
          <nav key={title} aria-label={title}>
            <h2 className="text-[12px] font-semibold uppercase tracking-[0.06em] text-faint">{title}</h2>
            <ul className="mt-3 space-y-2">
              {links.map(([to, label]) => <li key={to}><Link to={to} className="text-muted hover:text-ink">{label}</Link></li>)}
              {title === 'Legal' && <li><button type="button" onClick={openCookiePreferences} className="text-muted hover:text-ink">Cookie preferences</button></li>}
            </ul>
          </nav>
        ))}
      </div>
      <div className="border-t border-line">
        <div className="mx-auto max-w-content px-5 py-4 text-[12px] text-faint sm:px-8">
          © {new Date().getFullYear()} {SITE.operator ?? PLACEHOLDER('operating entity name')}. Legal documents are drafts pending legal review.
        </div>
      </div>
    </footer>
  );
}
export function PublicFrame({ children }: { children: ReactNode }) {
  return <div className="flex min-h-screen flex-col bg-paper"><PublicNav /><main id="content" className="flex-1">{children}</main><PublicFooter /></div>;
}

/* ------------------------------------------------------------------ home */
function ExampleAlert() {
  return (
    <figure className="rounded-lg border border-line bg-surface shadow-pop" aria-label="Illustrative early-warning alert">
      <div className="flex items-center justify-between border-b border-line px-5 py-3">
        <span className="text-[13px] font-semibold">Attendance below requirement</span>
        <span className="rounded bg-bronze-soft px-1.5 py-[1px] text-[12px] font-medium text-bronze">Needs follow-up</span>
      </div>
      <div className="space-y-4 px-5 py-4 text-[13px]">
        <div className="grid grid-cols-3 gap-4">
          <div><div className="label">Observed</div><div className="mt-0.5 text-[20px] font-semibold tnum">68.9%</div></div>
          <div><div className="label">Required</div><div className="mt-0.5 text-[20px] font-semibold tnum">75%</div></div>
          <div><div className="label">Subject</div><div className="mt-0.5 text-[13.5px]">Database Systems</div></div>
        </div>
        <div>
          <div className="label">Why this was raised</div>
          <p className="mt-0.5 text-muted">14 of 45 classes missed this semester under the university’s configured attendance rule. Two internal assessments were completed on time.</p>
        </div>
        <div>
          <div className="label">Suggested support</div>
          <p className="mt-0.5 text-muted">Mentor conversation within a week; check eligibility for condonation under the attendance policy.</p>
        </div>
      </div>
      <figcaption className="border-t border-line px-5 py-2.5 text-[11.5px] text-faint">Illustrative example with synthetic data. Alerts inform support — they never trigger penalties.</figcaption>
    </figure>
  );
}

const STEPS = [
  ['Enquiry', 'Your institution shares its context and the capabilities it is interested in.'],
  ['Conversation', 'An ACEDRA team member contacts you, meets your academic office and documents requirements.'],
  ['Agreement', 'Scope, modules and any additional services are recorded in a service agreement.'],
  ['Workspace set-up', 'We create your university’s workspace and assign a dedicated ACEDRA contact who configures it with you.'],
  ['Administrator access', 'Your initial administrator is invited on your official email domain and configures users and rules.'],
  ['Go live', 'Students and staff are invited. Each person sees only what their role permits.'],
];

export function HomePage() {
  return (
    <PublicFrame>
      <section className="mx-auto grid max-w-content items-center gap-12 px-5 py-14 sm:px-8 lg:grid-cols-[1.05fr_1fr] lg:py-20">
        <div>
          <h1 className="font-serif text-[40px] font-medium leading-[1.08] tracking-[-0.015em] sm:text-[52px]">
            Notice which students need support — and see exactly why.
          </h1>
          <p className="mt-5 max-w-[34rem] text-[16px] leading-relaxed text-muted">
            ACEDRA brings a university’s academic records, early-warning rules, mentoring and placement readiness into one
            workspace. Every alert and recommendation shows the evidence behind it, so faculty and mentors can act early and fairly.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link to="/enquire"><Button variant="primary">Request a consultation</Button></Link>
            <Link to="/solutions"><Button>Explore the platform</Button></Link>
          </div>
          <p className="mt-6 text-[12.5px] text-faint">For universities and colleges. Student and staff accounts are created by your institution — there is no public sign-up.</p>
        </div>
        <ExampleAlert />
      </section>

      <section id="platform" className="border-t border-line bg-surface">
        <div className="mx-auto max-w-content px-5 py-16 sm:px-8">
          <div className="grid gap-10 lg:grid-cols-[1fr_2fr]">
            <div>
              <h2 className="font-serif text-[30px] font-medium leading-tight">Six capabilities, one connected workflow</h2>
              <p className="mt-3 text-[14px] text-muted">Records feed early warning; alerts lead to interventions; recommendations and readiness close the loop. Universities enable the capabilities they need.</p>
            </div>
            <dl className="grid gap-x-10 gap-y-7 sm:grid-cols-2">
              {Object.entries(MODULES).map(([k, m]) => (
                <div key={k} className="border-t border-line pt-4">
                  <dt className="text-[14.5px] font-semibold">{m.name}</dt>
                  <dd className="mt-1 text-[13.5px] leading-relaxed text-muted">{m.summary}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-content px-5 py-16 sm:px-8">
        <div className="grid gap-10 lg:grid-cols-[1fr_2fr]">
          <h2 className="font-serif text-[30px] font-medium leading-tight">Built for each role in the university</h2>
          <div className="grid gap-x-10 gap-y-6 sm:grid-cols-2">
            {[
              ['Students', 'A personal workspace: their own records, alerts explained in plain language, a plan they can act on, and an assistant that only sees their data.'],
              ['Faculty', 'Subject and section performance for the students they teach, with alerts for those who need attention.'],
              ['Mentors', 'A caseload of assigned mentees with interventions, follow-up dates, notes and outcomes.'],
              ['Administrators', 'Institutional analytics, users and access, rules, documents, imports and reports — for their university only.'],
              ['Placement officers', 'Explainable readiness against career roles, eligibility, opportunities and application progress.'],
            ].map(([t, d]) => (
              <div key={t}><h3 className="text-[14.5px] font-semibold">{t}</h3><p className="mt-1 text-[13.5px] leading-relaxed text-muted">{d}</p></div>
            ))}
          </div>
        </div>
      </section>

      <section id="onboarding" className="border-t border-line bg-surface">
        <div className="mx-auto max-w-content px-5 py-16 sm:px-8">
          <div className="grid gap-10 lg:grid-cols-[1fr_2fr]">
            <div>
              <h2 className="font-serif text-[30px] font-medium leading-tight">How a university joins ACEDRA</h2>
              <p className="mt-3 text-[14px] text-muted">Each university gets its own configured workspace on the shared platform: its own departments, rules, documents and branding, with data kept separate from every other institution.</p>
            </div>
            <ol className="grid gap-x-10 gap-y-6 sm:grid-cols-2">
              {STEPS.map(([t, d], i) => (
                <li key={t} className="flex gap-4">
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-line-strong text-[12px] font-semibold tnum text-muted">{i + 1}</span>
                  <div><h3 className="text-[14.5px] font-semibold">{t}</h3><p className="mt-1 text-[13.5px] leading-relaxed text-muted">{d}</p></div>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </section>

      <section id="privacy" className="mx-auto max-w-content px-5 py-16 sm:px-8">
        <div className="grid gap-10 lg:grid-cols-[1fr_2fr]">
          <h2 className="font-serif text-[30px] font-medium leading-tight">Student data stays with the university</h2>
          <ul className="grid gap-x-10 gap-y-5 sm:grid-cols-2">
            {[
              ['Separate workspaces', 'Every record belongs to exactly one university. Access across institutions is blocked at the data layer and tested.'],
              ['Least privilege', 'Students see only themselves; faculty see the sections they teach; mentors see assigned mentees.'],
              ['ACEDRA staff don’t browse records', 'Configuring your workspace does not grant access to student records. Any support access needs your named approval, is time-limited and audited.'],
              ['Invitation-only accounts', 'An approved email domain is required, but it is never enough by itself — every account is invited.'],
              ['Explainable by design', 'Rules, thresholds and evidence are visible. ACEDRA does not claim predictive models it does not use.'],
              ['Support, not sanction', 'Alerts and readiness indicators guide support. They are never used for automatic penalties or placement guarantees.'],
            ].map(([t, d]) => (
              <li key={t} className="flex gap-3"><Check size={16} className="mt-0.5 shrink-0 text-forest" /><div><div className="text-[14px] font-semibold">{t}</div><p className="mt-0.5 text-[13.5px] leading-relaxed text-muted">{d}</p></div></li>
            ))}
          </ul>
        </div>
      </section>

      <section className="border-t border-line bg-forest text-on-forest">
        <div className="mx-auto flex max-w-content flex-col gap-5 px-5 py-14 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <div>
            <h2 className="font-serif text-[28px] font-medium text-on-forest">Talk to the ACEDRA team</h2>
            <p className="mt-1.5 max-w-xl text-[14px] opacity-80">Tell us about your institution. We’ll respond by your preferred contact method and arrange a conversation with your academic office.</p>
          </div>
          <Link to="/enquire"><Button className="border-0 bg-paper text-forest hover:bg-paper/90">Start an enquiry</Button></Link>
        </div>
      </section>
    </PublicFrame>
  );
}

/* ------------------------------------------------------------------ enquiry */
function Section({ title, help, children }: { title: string; help: string; children: ReactNode }) {
  return (
    <fieldset className="grid gap-6 border-t border-line py-8 lg:grid-cols-[16rem_1fr]">
      <legend className="sr-only">{title}</legend>
      <div><h2 className="text-[15px] font-semibold">{title}</h2><p className="mt-1 text-[13px] text-muted">{help}</p></div>
      <div className="grid gap-4 sm:grid-cols-2">{children}</div>
    </fieldset>
  );
}
const INITIAL = {
  university_name: '', official_website: '', institution_type: '', location: '', student_population: '', department_count: '', campus_count: '',
  contact_name: '', contact_designation: '', contact_email: '', contact_phone: '', preferred_contact_method: 'email',
  requested_modules: [] as string[], existing_sis: '', existing_academic_systems: '', has_student_emails: true,
  email_provisioning: 'existing', accounts_required: '', institutional_requirements: '', expected_outcomes: '', additional_information: '',
  consent_to_contact: false, website: '',
};
type EnquiryForm = typeof INITIAL;

export function EnquiryPage() {
  const [f, setF] = useState(INITIAL);
  const [opts, setOpts] = useState<EnquiryOptions | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState<EnquiryReceipt | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  useEffect(() => { api.get<EnquiryOptions>('/public/enquiry-options').then(setOpts).catch(() => {}); }, []);
  const set = <K extends keyof EnquiryForm>(k: K, v: EnquiryForm[K]) => { setF((p) => ({ ...p, [k]: v })); setErrors((e) => ({ ...e, [k]: '' })); };

  const validate = () => {
    const e: Record<string, string> = {};
    if (f.university_name.trim().length < 3) e.university_name = 'Enter the university’s full name.';
    if (!f.institution_type) e.institution_type = 'Choose the institution type.';
    if (!f.location.trim()) e.location = 'Enter the city and state.';
    if (!f.student_population) e.student_population = 'Choose an approximate size.';
    if (!f.contact_name.trim()) e.contact_name = 'Enter a contact name.';
    if (!f.contact_designation.trim()) e.contact_designation = 'Enter the contact’s designation.';
    if (!/^\S+@\S+\.\S+$/.test(f.contact_email)) e.contact_email = 'Enter a valid official email address.';
    if (!f.requested_modules.length) e.requested_modules = 'Select at least one capability.';
    if (f.email_provisioning === 'rio_assisted' && !(Number(f.accounts_required) > 0)) e.accounts_required = 'Enter the approximate number of accounts.';
    if (!f.consent_to_contact) e.consent_to_contact = 'Please confirm we may contact you.';
    setErrors(e);
    return !Object.keys(e).length;
  };

  const submit = async (ev: FormEvent) => {
    ev.preventDefault(); setFormError(null);
    if (!validate()) { setFormError('Some details need attention before you can send the enquiry.'); return; }
    setSubmitting(true);
    try {
      const body: Record<string, unknown> = { ...f, department_count: f.department_count ? Number(f.department_count) : null, campus_count: f.campus_count ? Number(f.campus_count) : null,
        accounts_required: f.accounts_required ? Number(f.accounts_required) : null };
      Object.keys(body).forEach((k) => { if (body[k] === '') body[k] = null; });  // blank optional fields are sent as null
      setDone(await api.post<EnquiryReceipt>('/public/enquiries', body));
      window.scrollTo({ top: 0 });
    } catch (e) { setFormError(errorMessage(e)); } finally { setSubmitting(false); }
  };

  if (done) {
    return (
      <PublicFrame>
        <div className="mx-auto max-w-prose px-5 py-20">
          <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-ok-soft text-ok"><Check size={20} /></div>
          <h1 className="font-serif text-[34px] font-medium">Thank you — your enquiry has been received</h1>
          <p className="mt-3 text-[15px] text-muted">Your reference is <strong className="text-ink tnum">{done.reference}</strong>. A member of the ACEDRA team will review the details and contact you by your preferred method. We’ve sent an acknowledgement to the address you provided.</p>
          {done.email_service_estimate && (
            <Notice tone="info" title="ACEDRA-assisted student email accounts">
              Recorded for {done.email_service_estimate.accounts.toLocaleString('en-IN')} accounts. This is an additional, chargeable service and is not part of the standard platform; pricing is confirmed in the service agreement.
            </Notice>
          )}
          <Link to="/" className="mt-8 inline-flex items-center gap-1.5 text-[13.5px] text-forest hover:underline"><ArrowLeft size={14} />Back to the ACEDRA website</Link>
        </div>
      </PublicFrame>
    );
  }

  return (
    <PublicFrame>
      <div className="mx-auto max-w-content px-5 py-12 sm:px-8">
        <div className="max-w-prose">
          <h1 className="font-serif text-[36px] font-medium leading-tight">Request a consultation</h1>
          <p className="mt-2 text-[15px] text-muted">Tell us about your institution and what you hope to achieve. This takes about five minutes; fields marked * are required.</p>
        </div>
        <form onSubmit={submit} noValidate className="mt-6">
          {formError && <div className="mb-2"><Notice tone="danger">{formError}</Notice></div>}
          <Section title="Institution" help="So we understand your scale and structure.">
            <Field label="University name" required error={errors.university_name} className="sm:col-span-2"><Input value={f.university_name} onChange={(e) => set('university_name', e.target.value)} autoComplete="organization" /></Field>
            <Field label="Official website"><Input value={f.official_website} onChange={(e) => set('official_website', e.target.value)} placeholder="https://" inputMode="url" /></Field>
            <Field label="Institution type" required error={errors.institution_type}>
              <Select value={f.institution_type} onChange={(e) => set('institution_type', e.target.value)}><option value="">Select…</option>{opts?.institution_types?.map((t) => <option key={t}>{t}</option>)}</Select>
            </Field>
            <Field label="Location" required error={errors.location}><Input value={f.location} onChange={(e) => set('location', e.target.value)} placeholder="City, state" /></Field>
            <Field label="Approximate student population" required error={errors.student_population}>
              <Select value={f.student_population} onChange={(e) => set('student_population', e.target.value)}><option value="">Select…</option>{opts?.population_bands?.map((t) => <option key={t}>{t}</option>)}</Select>
            </Field>
            <Field label="Number of departments"><Input type="number" min={1} value={f.department_count} onChange={(e) => set('department_count', e.target.value)} /></Field>
            <Field label="Number of campuses" hint="If more than one"><Input type="number" min={1} value={f.campus_count} onChange={(e) => set('campus_count', e.target.value)} /></Field>
          </Section>

          <Section title="Contact" help="The person we should speak to first.">
            <Field label="Full name" required error={errors.contact_name}><Input value={f.contact_name} onChange={(e) => set('contact_name', e.target.value)} autoComplete="name" /></Field>
            <Field label="Designation" required error={errors.contact_designation}><Input value={f.contact_designation} onChange={(e) => set('contact_designation', e.target.value)} placeholder="e.g. Dean, Academic Affairs" /></Field>
            <Field label="Official email" required error={errors.contact_email} hint="Please use your institutional address."><Input type="email" value={f.contact_email} onChange={(e) => set('contact_email', e.target.value)} autoComplete="email" /></Field>
            <Field label="Phone"><Input type="tel" value={f.contact_phone} onChange={(e) => set('contact_phone', e.target.value)} autoComplete="tel" /></Field>
            <Field label="Preferred contact method">
              <Select value={f.preferred_contact_method} onChange={(e) => set('preferred_contact_method', e.target.value)}>
                <option value="email">Email</option><option value="phone">Phone call</option><option value="video_call">Video call</option>
              </Select>
            </Field>
          </Section>

          <Section title="Requirements" help="Which capabilities interest you and what you use today.">
            <div className="sm:col-span-2">
              <span className="label mb-2 block">Capabilities of interest <span className="text-bronze">*</span></span>
              <div className="grid gap-3 sm:grid-cols-2">
                {Object.entries(MODULES).map(([k, m]) => (
                  <Checkbox key={k} label={m.name} description={m.summary} checked={f.requested_modules.includes(k)}
                    onChange={(c) => set('requested_modules', c ? [...f.requested_modules, k] : f.requested_modules.filter((x) => x !== k))} />
                ))}
              </div>
              {errors.requested_modules && <span className="mt-1 block text-[12px] text-danger">{errors.requested_modules}</span>}
            </div>
            <Field label="Existing student-management system"><Input value={f.existing_sis} onChange={(e) => set('existing_sis', e.target.value)} placeholder="e.g. in-house ERP, spreadsheets" /></Field>
            <Field label="Existing academic data systems"><Input value={f.existing_academic_systems} onChange={(e) => set('existing_academic_systems', e.target.value)} placeholder="e.g. LMS, examination portal" /></Field>
            <Field label="Institutional requirements" className="sm:col-span-2"><Textarea value={f.institutional_requirements} onChange={(e) => set('institutional_requirements', e.target.value)} placeholder="Regulations, integrations or constraints we should know about" /></Field>
            <Field label="Expected outcomes" className="sm:col-span-2"><Textarea value={f.expected_outcomes} onChange={(e) => set('expected_outcomes', e.target.value)} placeholder="What would success look like in your first year?" /></Field>
          </Section>

          <Section title="Student email accounts" help="ACEDRA accounts are invited on your institutional email domain.">
            <div className="space-y-3 sm:col-span-2">
              <Checkbox label="Our students already have institutional email addresses" checked={f.has_student_emails} onChange={(v) => set('has_student_emails', v)} />
              <div role="radiogroup" aria-label="Email provisioning" className="grid gap-3 sm:grid-cols-2">
                {[
                  ['existing', 'We’ll provide existing addresses', 'Included in the standard service.'],
                  ['rio_assisted', 'Request ACEDRA-assisted account creation', 'An additional, chargeable service — not part of the standard platform.'],
                ].map(([v, t, d]) => (
                  <label key={v} className={cx('cursor-pointer rounded-lg border p-3.5', f.email_provisioning === v ? 'border-forest bg-forest-soft/40' : 'border-line-strong bg-surface')}>
                    <input type="radio" className="sr-only" name="prov" checked={f.email_provisioning === v} onChange={() => set('email_provisioning', v)} />
                    <div className="text-[13.5px] font-medium">{t}</div><div className="mt-0.5 text-[12.5px] text-muted">{d}</div>
                  </label>
                ))}
              </div>
              {f.email_provisioning === 'rio_assisted' && (
                <div className="grid gap-3 sm:grid-cols-2">
                  <Field label="Approximate number of accounts" required error={errors.accounts_required}><Input type="number" min={1} value={f.accounts_required} onChange={(e) => set('accounts_required', e.target.value)} /></Field>
                  {Number(f.accounts_required) > 0 && opts && (
                    <div className="self-end rounded border border-line bg-sunken/50 px-3 py-2 text-[12.5px] text-muted">
                      Indicative estimate: <strong className="text-ink tnum">₹{(Number(f.accounts_required) * opts.email_service_unit_cost_inr).toLocaleString('en-IN')}</strong> per year. Final pricing is agreed with you.
                    </div>
                  )}
                </div>
              )}
            </div>
          </Section>

          <Section title="Anything else" help="Optional context for our team.">
            <Field label="Additional information" className="sm:col-span-2"><Textarea value={f.additional_information} onChange={(e) => set('additional_information', e.target.value)} /></Field>
            <input tabIndex={-1} autoComplete="off" aria-hidden className="hidden" value={f.website} onChange={(e) => set('website', e.target.value)} />
            <div className="sm:col-span-2">
              <Checkbox label="ACEDRA may contact me about this enquiry" description="We use these details only to respond to your enquiry." checked={f.consent_to_contact} onChange={(v) => set('consent_to_contact', v)} />
              {errors.consent_to_contact && <span className="mt-1 block text-[12px] text-danger">{errors.consent_to_contact}</span>}
            </div>
          </Section>
          <div className="flex justify-end border-t border-line pt-6"><Button type="submit" variant="primary" loading={submitting}>Send enquiry</Button></div>
        </form>
      </div>
    </PublicFrame>
  );
}

/* ------------------------------------------------------------------ auth pages */
function AuthFrame({ title, lede, children, footer }: { title: string; lede?: ReactNode; children: ReactNode; footer?: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-paper">
      <header className="mx-auto flex h-16 w-full max-w-content items-center px-5 sm:px-8"><Link to="/" aria-label="ACEDRA home"><AcedraWordmark size={26} tagline /></Link></header>
      <main className="flex flex-1 items-start justify-center px-5 pt-10 sm:pt-20">
        <div className="w-full max-w-[22rem]">
          <h1 className="font-serif text-[30px] font-medium leading-tight">{title}</h1>
          {lede && <p className="mt-1.5 text-[13.5px] text-muted">{lede}</p>}
          <div className="mt-6">{children}</div>
          {footer && <div className="mt-6 text-[12.5px] text-muted">{footer}</div>}
        </div>
      </main>
      <footer className="mx-auto w-full max-w-content px-5 py-6 sm:px-8"><LegalLinks className="justify-center" /></footer>
    </div>
  );
}

export function LoginPage() {
  const { signIn } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    try { const me = await signIn(email, password); nav(homeFor(me.role), { replace: true }); }
    catch (err) { setError(errorMessage(err)); } finally { setLoading(false); }
  };
  return (
    <AuthFrame title="Sign in" lede="Use the account your institution invited you to."
      footer={<>New to ACEDRA? Accounts are created by your university — ask your administrator for an invitation. Institutions can <Link to="/enquire" className="link">request a consultation</Link>.</>}>
      <form onSubmit={submit} className="space-y-4">
        {error && <Notice tone="danger">{error}</Notice>}
        <Field label="Email"><Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" required autoFocus /></Field>
        <Field label="Password"><Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></Field>
        <Button type="submit" variant="primary" className="w-full" loading={loading}>Sign in</Button>
        <div className="text-center"><Link to="/forgot-password" className="text-[12.5px] text-muted hover:text-ink">Forgot your password?</Link></div>
      </form>
      <DemoAccounts onPick={(e, p) => { setEmail(e); setPassword(p); }} />
    </AuthFrame>
  );
}

function DemoAccounts({ onPick }: { onPick: (e: string, p: string) => void }) {
  const [open, setOpen] = useState(false);
  const rows: [string, string, string][] = [
    ['ACEDRA super administrator', 'superadmin@acedra.example', 'PlatformPass123!'],
    ['ACEDRA employee (REVA, Deccan)', 'arjun.rao@acedra.example', 'PlatformPass123!'],
    ['REVA · administrator', 'admin@reva-demo.example', 'AdminPass123!'],
    ['REVA · faculty', 'faculty@reva-demo.example', 'FacultyPass123!'],
    ['REVA · mentor', 'mentor@reva-demo.example', 'MentorPass123!'],
    ['REVA · placement officer', 'placement@reva-demo.example', 'PlacementPass123!'],
    ['REVA · student', 'student@reva-demo.example', 'StudentPass123!'],
    ['Northfield · administrator', 'admin@northfield.example', 'AdminPass123!'],
    ['Northfield · student', 'student@northfield.example', 'StudentPass123!'],
    ['Deccan Tech · mentor', 'mentor@deccan-tech.example', 'MentorPass123!'],
  ];
  if (import.meta.env.PROD && import.meta.env.VITE_SHOW_DEMO_ACCOUNTS !== 'true') return null;
  return (
    <div className="mt-8 border-t border-line pt-4">
      <button type="button" className="text-[12.5px] text-muted hover:text-ink" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        {open ? 'Hide' : 'Show'} synthetic demo accounts
      </button>
      {open && (
        <ul className="mt-2 divide-y divide-line rounded border border-line bg-surface">
          {rows.map(([l, e, p]) => (
            <li key={e}><button type="button" onClick={() => onPick(e, p)} className="w-full px-3 py-2 text-left hover:bg-sunken">
              <div className="text-[12.5px] font-medium text-ink">{l}</div><div className="text-[12px] text-muted">{e}</div>
            </button></li>
          ))}
        </ul>
      )}
    </div>
  );
}

function PasswordRules({ pw }: { pw: string }) {
  const rules = [
    [pw.length >= 10, 'At least 10 characters'],
    [[/[a-z]/, /[A-Z]/, /\d/, /[^A-Za-z0-9]/].filter((r) => r.test(pw)).length >= 3, 'Three of: lowercase, uppercase, number, symbol'],
  ] as const;
  return <ul className="mt-1.5 space-y-0.5 text-[12px]">{rules.map(([ok, t]) => <li key={t} className={ok ? 'text-ok' : 'text-faint'}>{ok ? '✓' : '·'} {t}</li>)}</ul>;
}

/** Terms and privacy versions the person is shown; the server records exactly these on acceptance. */
function useRequiredLegalVersions() {
  const [docs, setDocs] = useState<LegalDocumentSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = () => {
    setError(null);
    api.get<LegalDocumentSummary[]>('/public/legal')
      .then((d) => setDocs(d.filter((x) => x.doc_type === 'terms' || x.doc_type === 'privacy')))
      .catch((e) => setError(errorMessage(e, 'The terms could not be loaded.')));
  };
  useEffect(load, []);
  const versions = Object.fromEntries((docs || []).map((d) => [d.doc_type, d.version]));
  return { docs, error, versions, reload: load };
}

export function AcceptInvitationPage() {
  const [params] = useSearchParams();
  const token = params.get('token') || '';
  const { acceptTokens } = useAuth();
  const nav = useNavigate();
  const [info, setInfo] = useState<InvitationInfo | null>(null);
  const [invalid, setInvalid] = useState<string | null>(null);
  const [pw, setPw] = useState(''); const [pw2, setPw2] = useState('');
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const legal = useRequiredLegalVersions();
  useEffect(() => { api.get<InvitationInfo>(`/auth/invitations/${encodeURIComponent(token)}`).then(setInfo).catch((e) => setInvalid(errorMessage(e))); }, [token]);
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setError(null);
    if (pw !== pw2) { setError('The two passwords do not match.'); return; }
    if (!agreed) { setError('Please review and accept the Terms and Privacy Policy to continue.'); return; }
    setLoading(true);
    try {
      const d = await api.post<TokenResponse>('/auth/invitations/accept', { token, password: pw, accepted_versions: legal.versions });
      acceptTokens(d); nav(homeFor(d.user.role), { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) { setAgreed(false); legal.reload(); }
      setError(errorMessage(err));
    } finally { setLoading(false); }
  };
  if (invalid) return <AuthFrame title="This invitation can’t be used" lede={invalid} footer={<>Ask your administrator to send a new invitation. <Link to="/login" className="link">Go to sign in</Link></>}><span /></AuthFrame>;
  if (!info) return <AuthFrame title="Checking your invitation…"><span /></AuthFrame>;
  const label = (t: string) => legal.docs?.find((d) => d.doc_type === t);
  return (
    <AuthFrame title="Set up your account" lede={<>You’ve been invited to <strong className="text-ink">{info.university_name}</strong> as {ROLE_LABEL[info.role]?.toLowerCase()}.</>}>
      <form onSubmit={submit} className="space-y-4" noValidate>
        {error && <Notice tone="danger">{error}</Notice>}
        <Field label="Email"><Input value={info.email} disabled /></Field>
        <Field label="Create a password"><Input type="password" value={pw} onChange={(e) => setPw(e.target.value)} autoComplete="new-password" required /><PasswordRules pw={pw} /></Field>
        <Field label="Confirm password"><Input type="password" value={pw2} onChange={(e) => setPw2(e.target.value)} autoComplete="new-password" required /></Field>
        {legal.error ? (
          <Notice tone="danger" action={<Button size="sm" onClick={legal.reload}>Try again</Button>}>{legal.error}</Notice>
        ) : (
          <div className="rounded border border-line bg-surface p-3">
            <Checkbox checked={agreed} onChange={setAgreed} label={<>I have read and accept the{' '}
              <Link to="/legal/terms" target="_blank" className="link">Terms and Conditions</Link>{label('terms') && <> (v{label('terms')?.version})</>} and the{' '}
              <Link to="/legal/privacy" target="_blank" className="link">Privacy Policy</Link>{label('privacy') && <> (v{label('privacy')?.version})</>}.</>}
              description="Your acceptance, with these version numbers and the time, is recorded against your account." />
          </div>
        )}
        <Button type="submit" variant="primary" className="w-full" loading={loading} disabled={!legal.docs}>Activate account</Button>
      </form>
    </AuthFrame>
  );
}

export function ForgotPasswordPage() {
  const [email, setEmail] = useState(''); const [sent, setSent] = useState(false); const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setLoading(true); setError(null);
    try { await api.post('/auth/password-reset-request', { email }); setSent(true); } catch (err) { setError(errorMessage(err)); } finally { setLoading(false); }
  };
  return (
    <AuthFrame title="Reset your password" lede="We’ll email a link that works for 30 minutes." footer={<Link to="/login" className="link">Back to sign in</Link>}>
      {sent ? <Notice tone="ok" title="Check your inbox">If an active account exists for {email}, a reset link is on its way.</Notice> : (
        <form onSubmit={submit} className="space-y-4">
          {error && <Notice tone="danger">{error}</Notice>}
          <Field label="Email"><Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus /></Field>
          <Button type="submit" variant="primary" className="w-full" loading={loading}>Send reset link</Button>
        </form>
      )}
    </AuthFrame>
  );
}

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const nav = useNavigate();
  const [pw, setPw] = useState(''); const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setLoading(true); setError(null);
    try { await api.post('/auth/password-reset-confirm', { token: params.get('token'), new_password: pw }); nav('/login?reset=1'); }
    catch (err) { setError(errorMessage(err)); } finally { setLoading(false); }
  };
  return (
    <AuthFrame title="Choose a new password">
      <form onSubmit={submit} className="space-y-4">
        {error && <Notice tone="danger">{error}</Notice>}
        <Field label="New password"><Input type="password" value={pw} onChange={(e) => setPw(e.target.value)} autoComplete="new-password" required /><PasswordRules pw={pw} /></Field>
        <Button type="submit" variant="primary" className="w-full" loading={loading}>Update password</Button>
      </form>
    </AuthFrame>
  );
}

export function NotFoundPage() {
  return <AuthFrame title="Page not found" lede="The page you’re looking for doesn’t exist or you don’t have access to it." footer={<Link to="/" className="link">Go to the ACEDRA website</Link>}><span /></AuthFrame>;
}
