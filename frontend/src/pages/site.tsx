/**
 * Public information pages and legal documents. Content here describes what the software actually does;
 * organisation details come from `lib/site.ts` and show as marked placeholders until configured.
 */
import { FormEvent, ReactNode, useEffect, useMemo, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { Check } from 'lucide-react';
import { api, errorMessage } from '../lib/api';
import { useApi } from '../lib/useApi';
import { fmtDate, MODULES } from '../lib/format';
import { openCookiePreferences } from '../lib/consent';
import { PLACEHOLDER, SITE } from '../lib/site';
import { LegalMarkdown, parseHeadings } from '../components/legal';
import { Async, Button, Field, Input, Notice, Textarea } from '../components/ui';
import { PublicFrame } from './public';
import type { LegalDocType, LegalDocument, LegalDocumentSummary } from '../types/api';

/* ------------------------------------------------------------------ shared layout */
function useTitle(title: string) {
  useEffect(() => { const prev = document.title; document.title = `${title} — ACEDRA`; return () => { document.title = prev; }; }, [title]);
}

function Breadcrumbs({ trail }: { trail: [string, string?][] }) {
  return (
    <nav aria-label="Breadcrumb" className="text-[12.5px] text-muted">
      <ol className="flex flex-wrap items-center gap-1.5">
        <li><Link to="/" className="hover:text-ink">Home</Link></li>
        {trail.map(([label, to], i) => (
          <li key={label} className="flex items-center gap-1.5">
            <span aria-hidden className="text-faint">/</span>
            {to && i < trail.length - 1 ? <Link to={to} className="hover:text-ink">{label}</Link> : <span aria-current="page" className="text-ink">{label}</span>}
          </li>
        ))}
      </ol>
    </nav>
  );
}

export function InfoPage({ title, lede, trail, children, aside }: { title: string; lede?: ReactNode; trail: [string, string?][]; children: ReactNode; aside?: ReactNode }) {
  useTitle(title);
  return (
    <PublicFrame>
      <div className="mx-auto max-w-content px-5 pb-20 pt-8 sm:px-8">
        <Breadcrumbs trail={trail} />
        <header className="mt-6 max-w-3xl">
          <h1 className="font-serif text-[36px] font-medium leading-[1.1] tracking-[-0.01em] sm:text-[44px]">{title}</h1>
          {lede && <p className="mt-4 text-[16px] leading-relaxed text-muted">{lede}</p>}
        </header>
        <div className={aside ? 'mt-10 grid gap-10 lg:grid-cols-[minmax(0,1fr)_17rem]' : 'mt-10'}>
          <div className="min-w-0 max-w-3xl">{children}</div>
          {aside && <aside className="min-w-0">{aside}</aside>}
        </div>
      </div>
    </PublicFrame>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-t border-line py-8 first:border-0 first:pt-0">
      <h2 className="font-serif text-[24px] font-medium leading-snug">{title}</h2>
      <div className="mt-3 space-y-3 text-[14.5px] leading-[1.7] text-ink">{children}</div>
    </section>
  );
}

function Bullets({ items }: { items: ReactNode[] }) {
  return <ul className="space-y-2">{items.map((t, i) => <li key={i} className="flex gap-2.5"><Check size={15} className="mt-[5px] shrink-0 text-forest" aria-hidden /><span>{t}</span></li>)}</ul>;
}

const Placeholder = ({ children }: { children: string }) => <span className="rounded bg-bronze-soft px-1.5 py-[1px] text-[13px] text-bronze">{children}</span>;
const configured = (v: string | null, what: string) => v ?? <Placeholder>{PLACEHOLDER(what)}</Placeholder>;

/* ------------------------------------------------------------------ about */
export function AboutPage() {
  return (
    <InfoPage title="About ACEDRA" trail={[['About']]}
      lede="ACEDRA is software that helps a university notice which students need support, understand why, and follow that support through to an outcome.">
      <Section title="What ACEDRA does">
        <p>Universities already hold the information that shows when a student is starting to struggle: attendance, internal assessments, examination results, backlogs and mentoring notes. It is usually spread across spreadsheets and systems, and reviewed too late.</p>
        <p>ACEDRA brings those records into one workspace for each institution, applies the institution’s own early-warning rules, and gives faculty and mentors a clear list of who may need attention — with the evidence behind every alert.</p>
      </Section>
      <Section title="Principles we build to">
        <Bullets items={[
          <><strong>Explainable, not predictive.</strong> Alerts and readiness indicators come from rules and calculations an institution can read and change. ACEDRA does not claim to use predictive models it does not use.</>,
          <><strong>Support, not sanction.</strong> Alerts are prompts for a supportive conversation. They are not designed for automatic penalties or consequential decisions.</>,
          <><strong>Each institution’s data stays separate.</strong> Every record belongs to one university, and access across institutions is blocked in the data layer and covered by automated tests.</>,
          <><strong>Least privilege.</strong> Students see only their own records; faculty see the sections they teach; mentors see their mentees. ACEDRA team members configure workspaces but do not browse student records.</>,
        ]} />
      </Section>
      <Section title="How institutions work with us">
        <p>ACEDRA is offered to universities and colleges, not to individuals. An institution starts with an <Link to="/enquire" className="link">enquiry</Link>; an ACEDRA team member then meets its academic office, agrees scope in a service agreement and configures the workspace with the institution’s first administrator.</p>
        <p>We do not list customers, partners or certifications on this website. If you need references or details of our security arrangements for a procurement process, ask us through the <Link to="/contact" className="link">contact form</Link>.</p>
      </Section>
      <Section title="Who operates ACEDRA">
        <p>ACEDRA is operated by {configured(SITE.operator, 'registered name of the operating entity')}.</p>
        <p>Registered address: {configured(SITE.address, 'registered office address')}{SITE.demoContact && ' (demonstration placeholder)'}.</p>
      </Section>
    </InfoPage>
  );
}

/* ------------------------------------------------------------------ solutions */
const MODULE_DETAIL: Record<string, string[]> = {
  student_intelligence: ['Import students, attendance, assessments and results from CSV or Excel with row-by-row validation.', 'Term-by-term views that follow each university’s own academic structure.', 'Faculty see the sections they teach; administrators see their whole institution.'],
  risk_identification: ['Rules for attendance, CGPA, backlogs and assessment performance, with thresholds the institution sets.', 'Each alert records the observed value, the rule and the evidence used.', 'Alerts can be acknowledged, resolved or dismissed with a reason.'],
  recommendations: ['Improvement plans drawn from the institution’s own catalogue of resources and actions.', 'Students record progress and give feedback on each recommendation.', 'Staff can regenerate suggestions without losing ones a student has started.'],
  placement_readiness: ['Readiness against career roles, based on skills, certifications, projects and academic standing.', 'Opportunities with eligibility criteria, and application tracking.', 'Indicators guide preparation; they are not placement guarantees.'],
  ai_assistant: ['Answers questions from the institution’s approved documents and cites the passages used.', 'In personal mode, uses only records the person is already allowed to see.', 'Without a configured language model, returns relevant passages rather than generated text, and says so.'],
  interventions: ['Mentors open interventions from alerts, set follow-up dates and record notes.', 'Resolving an intervention requires an outcome summary.', 'Reports for administrators on alerts, interventions and outcomes.'],
};

export function SolutionsPage() {
  return (
    <InfoPage title="The ACEDRA platform" trail={[['Platform']]}
      lede="Six capabilities that share one set of records. Each institution chooses which to enable, and configures them to its own rules and academic structure.">
      <div className="grid gap-x-10 gap-y-2 md:grid-cols-2">
        {Object.entries(MODULES).map(([key, m]) => (
          <section key={key} className="border-t border-line py-6">
            <h2 className="text-[16px] font-semibold">{m.name}</h2>
            <p className="mt-1 text-[14px] text-muted">{m.summary}</p>
            <ul className="mt-3 space-y-1.5 text-[13.5px] leading-relaxed">
              {(MODULE_DETAIL[key] || []).map((d) => <li key={d} className="flex gap-2"><span aria-hidden className="mt-[9px] h-1 w-1 shrink-0 rounded-full bg-forest" />{d}</li>)}
            </ul>
          </section>
        ))}
      </div>
      <Section title="From a university’s records to a supported student">
        <ol className="list-decimal space-y-1.5 pl-5">
          <li>The university administrator configures departments, terms, subjects and teaching assignments.</li>
          <li>Faculty, mentors and students are invited on the institution’s approved email domains.</li>
          <li>Records are imported and validated; rows with problems are reported, not silently changed.</li>
          <li>Early-warning rules identify students who meet the institution’s criteria.</li>
          <li>A mentor opens an intervention, follows up and records the outcome.</li>
          <li>Administrators review progress and outcomes across the institution.</li>
        </ol>
      </Section>
      <div className="mt-4 flex flex-wrap gap-3">
        <Link to="/enquire"><Button variant="primary">Request a consultation</Button></Link>
        <Link to="/security"><Button>How data is protected</Button></Link>
      </div>
    </InfoPage>
  );
}

/* ------------------------------------------------------------------ FAQ */
const FAQS: [string, ReactNode][] = [
  ['Can I sign up as a student or faculty member?', 'No. There is no public registration. Your university creates your account and sends you an invitation to your institutional email address.'],
  ['How does a university start using ACEDRA?', <>Submit an <Link to="/enquire" className="link">institutional enquiry</Link>. An ACEDRA team member reviews it, contacts your institution, and once a service agreement is in place sets up your workspace and invites your first administrator.</>],
  ['Can ACEDRA staff see our student records?', 'Not by default. ACEDRA team members can configure your workspace (structure, modules, branding) but cannot open student records. If support needs that access, your institution must approve a specific, time-limited grant, and each access is written to the audit log.'],
  ['Does ACEDRA predict which students will fail?', 'No. Alerts come from rules your institution configures, such as attendance or CGPA thresholds, and each alert shows the evidence. They indicate who may benefit from support, not a prediction about outcomes.'],
  ['Does the AI assistant send our data to an AI company?', 'Only if your deployment enables a language-model provider. By default none is configured and the assistant returns passages from your approved documents. If a provider is enabled, the Privacy Policy explains what is sent.'],
  ['Does ACEDRA create email accounts for our staff or students?', 'No. ACEDRA invites people on your existing institutional email domains. Requests for help with email accounts are handled separately under your agreement.'],
  ['Where is our data stored?', 'This depends on the hosting arrangements agreed for your deployment and is set out in your service agreement. We do not claim on this website that data is stored only in India.'],
  ['Which cookies does the website use?', <>None. The application uses browser storage to keep you signed in and, if you allow it, to remember your appearance setting. See the <Link to="/legal/cookies" className="link">Cookie policy</Link>.</>],
  ['How do I report a security issue?', <>See <Link to="/security" className="link">Security</Link> for how to report a vulnerability.</>],
];

export function FaqPage() {
  return (
    <InfoPage title="Frequently asked questions" trail={[['FAQ']]} lede="Answers about how ACEDRA works for institutions and the people in them.">
      <div className="divide-y divide-line border-y border-line">
        {FAQS.map(([q, a]) => (
          <details key={q} className="group py-4">
            <summary className="flex cursor-pointer list-none items-start justify-between gap-4 rounded text-[15px] font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-forest">
              {q}<span aria-hidden className="mt-0.5 text-faint transition-transform group-open:rotate-45">+</span>
            </summary>
            <div className="mt-2 max-w-2xl text-[14.5px] leading-[1.7] text-muted">{a}</div>
          </details>
        ))}
      </div>
      <p className="mt-6 text-[14px] text-muted">Didn’t find your answer? <Link to="/contact" className="link">Contact us</Link>.</p>
    </InfoPage>
  );
}

/* ------------------------------------------------------------------ security */
export function SecurityPage() {
  return (
    <InfoPage title="Security information" trail={[['Security']]}
      lede="How the ACEDRA software protects accounts and keeps each institution’s data separate. Hosting-specific measures depend on each deployment and are confirmed in the service agreement.">
      <Section title="Accounts and sign-in">
        <Bullets items={[
          'Invitation-only accounts on email domains the institution has approved.',
          'Passwords are stored only as salted bcrypt hashes, and must meet a minimum length and complexity rule.',
          'Invitation and password-reset links are single-use, expire, and are stored only as hashes.',
          'Sign-in tokens are short-lived and are revoked when you sign out, change your password, or your role or status changes.',
          'Sign-in, password reset and public forms are rate-limited.',
        ]} />
      </Section>
      <Section title="Separation between institutions">
        <Bullets items={[
          'Every record carries the institution it belongs to. Queries are filtered by institution in the data layer, and writes that cross institutions are rejected.',
          'Role-based permission checks run on the server for every request; the interface only hides what you cannot use.',
          'Automated tests cover access across institutions and between roles.',
        ]} />
      </Section>
      <Section title="ACEDRA team access">
        <p>Configuration permissions are separate from student-data permissions. ACEDRA employees can configure the workspaces assigned to them but cannot read student records unless the institution approves a time-limited access grant. Grants and every access under them are recorded in the institution’s audit log.</p>
      </Section>
      <Section title="Application safeguards">
        <Bullets items={[
          'Security headers that prevent the application being framed and limit content-type sniffing and referrer leakage; HTTPS-only transport headers in production.',
          'Request logs record paths and status codes, never request bodies, tokens or query strings.',
          'No third-party scripts, fonts, analytics or advertising trackers are loaded.',
          'An audit log of significant actions, available to each institution’s administrators.',
        ]} />
      </Section>
      <Section title="What depends on each deployment">
        <p>HTTPS certificates, encryption of the database and backups, backup frequency, hosting location and incident-notification commitments depend on how a deployment is hosted. They are not claimed here and must be confirmed in each institution’s service agreement.</p>
        <Notice tone="attention" title="To be confirmed">Hosting provider, data-centre locations, encryption at rest and backup arrangements for each deployment.</Notice>
      </Section>
      <Section title="Reporting a vulnerability">
        <p>If you believe you have found a security issue, please tell us privately and do not access data that is not yours. Security contact: {configured(SITE.securityEmail, 'security contact email')}. Until that is configured, use the <Link to="/contact" className="link">contact form</Link> with the subject “Security”, without including sensitive details; we will reply with a secure way to share them.</p>
      </Section>
    </InfoPage>
  );
}

/* ------------------------------------------------------------------ accessibility */
export function AccessibilityPage() {
  return (
    <InfoPage title="Accessibility statement" trail={[['Accessibility']]}
      lede="We want everyone who uses ACEDRA, including people who use assistive technology, to be able to do their work. This statement describes what we have done, what we have checked and what we know is not yet good enough.">
      <Section title="Our approach">
        <p>We design ACEDRA with the Web Content Accessibility Guidelines (WCAG) 2.1 at level AA as our reference. We have <strong>not</strong> completed a formal audit, and we do not claim full conformance.</p>
        <Bullets items={[
          'Semantic HTML: headings, landmarks (header, navigation, main, footer), lists, tables and form labels.',
          'Every form field has a visible label; errors are shown as text, not by colour alone.',
          'Everything can be reached with a keyboard, with a visible focus outline and a “Skip to content” link.',
          'Dialogs keep focus inside while open, close with Escape, and return you to the page.',
          'Text and interface colours are chosen for contrast in both light and dark appearance.',
          'Layouts adapt to small screens and to browser zoom.',
          'Fonts are served with the application; no content depends on third-party services.',
        ]} />
      </Section>
      <Section title="How we checked">
        <p>During development we tested the public website and sign-in pages with keyboard-only navigation, at a mobile width of 375 pixels, and with an automated checker (axe-core) in a headless browser. Automated tools find only some problems, so these checks do not replace testing with assistive-technology users.</p>
      </Section>
      <Section title="Known limitations">
        <Bullets items={[
          'Charts in dashboards present data visually. Key figures are also shown as text, but some charts do not yet have a full table alternative.',
          'Screen-reader testing with NVDA, JAWS, VoiceOver and TalkBack has not yet been carried out systematically.',
          'Some dense data tables are hard to use on very small screens; columns may be hidden on mobile.',
          'Imported documents and reports produced by institutions may not be accessible.',
        ]} />
      </Section>
      <Section title="Feedback and contact">
        <p>If you find something you cannot use, tell us what you were trying to do and on which page. Accessibility contact: {configured(SITE.accessibilityEmail, 'accessibility contact email')}. You can also use the <Link to="/contact" className="link">contact form</Link>, or ask your institution’s administrator to raise it with us.</p>
        <p className="text-[13px] text-muted">This statement was prepared in November 2026 and will be reviewed after a formal accessibility audit.</p>
      </Section>
    </InfoPage>
  );
}

/* ------------------------------------------------------------------ contact */
interface ContactForm { name: string; email: string; institution: string; subject: string; message: string; website: string }
const EMPTY: ContactForm = { name: '', email: '', institution: '', subject: '', message: '', website: '' };
const FREE_MAIL = /@(gmail|googlemail|yahoo|outlook|hotmail|live|rediffmail|icloud|aol|proton|protonmail|zoho|yandex|gmx|mail)\./i;

function validate(f: ContactForm): Partial<Record<keyof ContactForm, string>> {
  const e: Partial<Record<keyof ContactForm, string>> = {};
  if (f.name.trim().length < 2) e.name = 'Enter your name.';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email.trim())) e.email = 'Enter a valid email address.';
  else if (FREE_MAIL.test(f.email)) e.email = 'Please use your institution’s email address.';
  if (f.institution.trim().length < 2) e.institution = 'Enter your university or college.';
  if (f.subject.trim().length < 3) e.subject = 'Enter a subject.';
  if (f.message.trim().length < 20) e.message = 'Please write at least 20 characters.';
  else if ((f.message.match(/https?:\/\//gi) || []).length > 3) e.message = 'Please remove some links from your message.';
  return e;
}

export function ContactPage() {
  const [f, setF] = useState<ContactForm>(EMPTY);
  const [touched, setTouched] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState<string | null>(null);
  const errors = useMemo(() => validate(f), [f]);
  const set = (k: keyof ContactForm) => (e: { target: { value: string } }) => setF((p) => ({ ...p, [k]: e.target.value }));
  const err = (k: keyof ContactForm) => (touched ? errors[k] : undefined);

  const submit = async (e: FormEvent) => {
    e.preventDefault(); setTouched(true); setError(null);
    if (Object.keys(errors).length) return;
    setSending(true);
    try {
      await api.post('/public/contact', { ...f, website: f.website || undefined });
      setSent(f.email); setF(EMPTY); setTouched(false);
    } catch (ex) { setError(errorMessage(ex, 'Your message could not be sent. Please try again.')); } finally { setSending(false); }
  };

  return (
    <InfoPage title="Contact ACEDRA" trail={[['Contact']]}
      lede="For questions from universities and colleges. If you want to bring ACEDRA to your institution, the institutional enquiry form collects the details we need to start."
      aside={
        <div className="space-y-5 text-[13.5px]">
          <div className="rounded-lg border border-line bg-surface p-4">
            <h2 className="text-[13px] font-semibold">Starting a pilot or rollout?</h2>
            <p className="mt-1 text-muted">Use the institutional enquiry form instead.</p>
            <Link to="/enquire" className="mt-3 inline-block"><Button size="sm">Institutional enquiry</Button></Link>
          </div>
          <div className="rounded-lg border border-line p-4">
            <h2 className="text-[13px] font-semibold">Other ways to reach us</h2>
            <dl className="mt-2 space-y-2 text-muted">
              <div><dt className="text-[12px] text-faint">Email</dt><dd>{SITE.supportEmail ? <a className="link" href={`mailto:${SITE.supportEmail}`}>{SITE.supportEmail}</a> : configured(null, 'support email')}</dd></div>
              <div><dt className="text-[12px] text-faint">Phone</dt><dd>{SITE.phone ? <a className="link" href={`tel:${SITE.phone.replace(/[^\d+]/g, '')}`}>{SITE.phone}</a> : configured(null, 'phone number')}</dd></div>
              <div><dt className="text-[12px] text-faint">Address</dt><dd>{configured(SITE.address, 'office address')}</dd></div>
              <div><dt className="text-[12px] text-faint">Website</dt><dd>{SITE.website ? <a className="link" href={SITE.website} target="_blank" rel="noopener noreferrer">{SITE.website.replace(/^https?:\/\//, '')}</a> : configured(null, 'website')}</dd></div>
            </dl>
            {SITE.demoContact && <p className="mt-3 text-[12px] text-faint">Demonstration placeholders, not genuine contact details.</p>}
          </div>
          <p className="text-[12.5px] text-muted">Students and staff: for help with your account, contact your university’s administrator first.</p>
        </div>
      }>
      {sent ? (
        <Notice tone="ok" title="Thank you — your message has been received"
          action={<Button size="sm" onClick={() => setSent(null)}>Send another message</Button>}>
          We’ve sent an acknowledgement to {sent}. A member of the ACEDRA team will reply to that address.
        </Notice>
      ) : (
        <form onSubmit={submit} noValidate className="max-w-xl space-y-4" aria-describedby="contact-privacy">
          {error && <Notice tone="danger">{error}</Notice>}
          {touched && Object.keys(errors).length > 0 && <Notice tone="danger">Please correct the highlighted fields.</Notice>}
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Your name" required error={err('name')}><Input value={f.name} onChange={set('name')} autoComplete="name" maxLength={150} aria-invalid={!!err('name')} /></Field>
            <Field label="Institutional email" required error={err('email')}><Input type="email" value={f.email} onChange={set('email')} autoComplete="email" maxLength={254} aria-invalid={!!err('email')} /></Field>
          </div>
          <Field label="University or college" required error={err('institution')}><Input value={f.institution} onChange={set('institution')} autoComplete="organization" maxLength={255} aria-invalid={!!err('institution')} /></Field>
          <Field label="Subject" required error={err('subject')}><Input value={f.subject} onChange={set('subject')} maxLength={200} aria-invalid={!!err('subject')} /></Field>
          <Field label="Message" required error={err('message')} hint={`${f.message.trim().length} / 5000`}><Textarea rows={6} value={f.message} onChange={set('message')} maxLength={5000} aria-invalid={!!err('message')} /></Field>
          {/* Honeypot: hidden from people and assistive technology; automated submissions tend to fill it. */}
          <div aria-hidden="true" className="absolute left-[-10000px] top-auto h-px w-px overflow-hidden">
            <label>Website<input tabIndex={-1} autoComplete="off" value={f.website} onChange={set('website')} name="website" /></label>
          </div>
          <p id="contact-privacy" className="text-[12.5px] text-muted">We use these details only to reply to you. See the <Link to="/legal/privacy" className="link">Privacy policy</Link>.</p>
          <Button type="submit" variant="primary" loading={sending}>Send message</Button>
        </form>
      )}
    </InfoPage>
  );
}

/* ------------------------------------------------------------------ legal documents */
const LEGAL_TITLES: Record<LegalDocType, string> = { terms: 'Terms and conditions', privacy: 'Privacy policy', cookies: 'Cookie policy' };
const isLegalType = (t?: string): t is LegalDocType => t === 'terms' || t === 'privacy' || t === 'cookies';

export function LegalDocumentPage() {
  const { type } = useParams();
  const [params] = useSearchParams();
  const version = params.get('version');
  const docType = isLegalType(type) ? type : null;
  const doc = useApi<LegalDocument>(docType ? `/public/legal/${docType}` : null, version ? { version } : undefined);
  const history = useApi<LegalDocumentSummary[]>(docType ? `/public/legal/${docType}/history` : null);
  const title = docType ? LEGAL_TITLES[docType] : 'Legal document';
  useTitle(title);
  if (!docType) return <InfoPage title="Document not found" trail={[['Legal']]}><p>There is no legal document at this address. <Link to="/legal/terms" className="link">View the terms</Link>.</p></InfoPage>;

  return (
    <PublicFrame>
      <div className="mx-auto max-w-content px-5 pb-20 pt-8 sm:px-8">
        <Breadcrumbs trail={[['Legal', '/legal/terms'], [title]]} />
        <nav aria-label="Legal documents" className="mt-6 flex flex-wrap gap-2 text-[13px]">
          {(Object.keys(LEGAL_TITLES) as LegalDocType[]).map((t) => (
            <Link key={t} to={`/legal/${t}`} aria-current={t === docType ? 'page' : undefined}
              className={t === docType ? 'rounded-full bg-ink px-3 py-1 text-paper' : 'rounded-full border border-line px-3 py-1 text-muted hover:text-ink'}>{LEGAL_TITLES[t]}</Link>
          ))}
        </nav>
        <Async state={doc} rows={8}>{(d) => {
          const headings = parseHeadings(d.body);
          const today = new Date().toISOString().slice(0, 10);
          const inForce = history.data?.find((h) => !h.effective_date || h.effective_date <= today);
          const current = !version || inForce?.version === d.version;
          return (
            <div className="mt-8 grid gap-10 lg:grid-cols-[minmax(0,1fr)_16rem]">
              <article className="min-w-0 max-w-3xl" aria-labelledby="legal-title">
                <h1 id="legal-title" className="font-serif text-[36px] font-medium leading-[1.1] sm:text-[44px]">{d.title}</h1>
                <dl className="mt-4 flex flex-wrap gap-x-6 gap-y-1 text-[13px] text-muted">
                  <div><dt className="inline">Version </dt><dd className="inline font-medium text-ink">{d.version}</dd></div>
                  <div><dt className="inline">Effective </dt><dd className="inline font-medium text-ink">{fmtDate(d.effective_date)}</dd></div>
                  {d.published_at && <div><dt className="inline">Published </dt><dd className="inline">{fmtDate(d.published_at)}</dd></div>}
                </dl>
                {!current && history.data && (
                  <div className="mt-5"><Notice tone="attention" title="You are viewing an earlier version">
                    <Link to={`/legal/${docType}`} className="link">Read the current version</Link>.</Notice></div>
                )}
                {d.change_summary && <p className="mt-4 text-[13.5px] text-muted"><span className="font-medium text-ink">What changed: </span>{d.change_summary}</p>}
                <div className="mt-8"><LegalMarkdown body={d.body} /></div>
                {docType === 'cookies' && (
                  <div className="mt-8"><Button onClick={openCookiePreferences}>Change cookie preferences</Button></div>
                )}
              </article>
              <aside className="min-w-0 space-y-8 lg:sticky lg:top-6 lg:self-start">
                {headings.length > 0 && (
                  <nav aria-label="On this page">
                    <h2 className="text-[12px] font-semibold uppercase tracking-[0.06em] text-faint">On this page</h2>
                    <ul className="mt-3 space-y-1.5 text-[13px]">
                      {headings.filter((h) => h.level === 2).map((h) => <li key={h.id}><a href={`#${h.id}`} className="text-muted hover:text-ink">{h.text}</a></li>)}
                    </ul>
                  </nav>
                )}
                {history.data && history.data.length > 0 && (
                  <nav aria-label="Version history">
                    <h2 className="text-[12px] font-semibold uppercase tracking-[0.06em] text-faint">Version history</h2>
                    <ul className="mt-3 space-y-2 text-[13px]">
                      {history.data.map((h) => (
                        <li key={h.id}>
                          <Link to={h.id === inForce?.id ? `/legal/${docType}` : `/legal/${docType}?version=${encodeURIComponent(h.version)}`}
                            aria-current={h.version === d.version ? 'page' : undefined}
                            className={h.version === d.version ? 'font-medium text-ink' : 'text-muted hover:text-ink'}>
                            Version {h.version}{h.id === inForce?.id ? ' (current)' : h.effective_date && h.effective_date > today ? ' (scheduled)' : ''}
                          </Link>
                          <div className="text-[12px] text-faint">Effective {fmtDate(h.effective_date)}</div>
                        </li>
                      ))}
                    </ul>
                  </nav>
                )}
              </aside>
            </div>
          );
        }}</Async>
      </div>
    </PublicFrame>
  );
}
