import { ReactNode, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, ApiError, errorMessage } from '../lib/api';
import { useAuth } from '../lib/auth';
import { fmtDate } from '../lib/format';
import { getConsent, onOpenCookiePreferences, openCookiePreferences, saveConsent } from '../lib/consent';
import type { LegalDocumentSummary, LegalStatus } from '../types/api';
import { AcedraWordmark } from './brand';
import { Button, Checkbox, cx, Dialog, LoadingBlock, Notice } from './ui';

/* ------------------------------------------------------------------ legal links */
export const LEGAL_LINKS: [string, string][] = [
  ['/legal/terms', 'Terms'],
  ['/legal/privacy', 'Privacy'],
  ['/legal/cookies', 'Cookie policy'],
  ['/accessibility', 'Accessibility'],
  ['/security', 'Security'],
];

/** The compact row of legal links used on sign-in pages and inside every workspace. */
export function LegalLinks({ className }: { className?: string }) {
  return (
    <nav aria-label="Legal" className={cx('flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-muted', className)}>
      {LEGAL_LINKS.map(([to, label]) => <Link key={to} to={to} className="hover:text-ink hover:underline">{label}</Link>)}
      <button type="button" onClick={openCookiePreferences} className="hover:text-ink hover:underline">Cookie preferences</button>
    </nav>
  );
}

/* ------------------------------------------------------------------ cookie consent */
/**
 * First-visit banner and the preferences dialog. Only one optional item exists (the saved appearance), so the
 * choice is "essential only" or "allow preferences". Nothing optional is stored until the person chooses.
 */
export function CookieConsent() {
  const [decided, setDecided] = useState(() => getConsent() !== null);
  const [open, setOpen] = useState(false);
  const [prefs, setPrefs] = useState(() => getConsent()?.preferences ?? false);

  const banner = useRef<HTMLElement>(null);
  const showBanner = !decided && !open;

  useEffect(() => onOpenCookiePreferences(() => { setPrefs(getConsent()?.preferences ?? false); setOpen(true); }), []);
  // Reserve space under the page while the banner is shown, so it never covers footer or legal links.
  useLayoutEffect(() => {
    const el = banner.current;
    if (!showBanner || !el) return;
    const apply = () => { document.body.style.paddingBottom = `${el.offsetHeight + 24}px`; };
    apply();
    const ro = new ResizeObserver(apply);
    ro.observe(el);
    return () => { ro.disconnect(); document.body.style.paddingBottom = ''; };
  }, [showBanner]);

  const choose = (preferences: boolean) => { saveConsent(preferences); setPrefs(preferences); setDecided(true); setOpen(false); };

  return (
    <>
      {showBanner && (
        <section ref={banner} aria-label="Cookie and storage choices" role="region"
          className="fixed inset-x-3 bottom-3 z-40 mx-auto max-w-2xl rounded-lg border border-line bg-surface p-4 shadow-pop sm:inset-x-6">
          <p className="text-[13px] leading-relaxed text-ink">
            ACEDRA uses no advertising or analytics cookies. We use essential browser storage to keep you signed in, and — only
            if you allow it — to remember your light or dark appearance. <Link to="/legal/cookies" className="link">Cookie policy</Link>
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button size="sm" onClick={() => choose(false)}>Essential only</Button>
            <Button size="sm" variant="primary" onClick={() => choose(true)}>Allow preferences</Button>
            <Button size="sm" variant="ghost" onClick={() => setOpen(true)}>Choose…</Button>
          </div>
        </section>
      )}
      <Dialog open={open} onClose={() => setOpen(false)} title="Cookie preferences"
        description="ACEDRA sets no cookies and uses no trackers. These settings cover browser storage."
        footer={<><Button onClick={() => setOpen(false)}>Cancel</Button><Button variant="primary" onClick={() => choose(prefs)}>Save choices</Button></>}>
        <div className="space-y-4 text-[13px]">
          <div className="rounded border border-line p-3">
            <div className="flex items-center justify-between gap-3"><span className="font-semibold">Strictly necessary</span><span className="text-[12px] text-muted">Always on</span></div>
            <p className="mt-1 text-muted">Your sign-in session (cleared when you sign out or close the tab) and this choice.</p>
          </div>
          <div className="rounded border border-line p-3">
            <Checkbox checked={prefs} onChange={setPrefs} label={<span className="font-semibold">Preferences</span>}
              description="Remember whether you chose the light or dark appearance. Turning this off removes the saved setting." />
          </div>
          <p className="text-[12px] text-muted">See the <Link to="/legal/cookies" className="link" onClick={() => setOpen(false)}>Cookie policy</Link> for the exact items stored.</p>
        </div>
      </Dialog>
    </>
  );
}

/* ------------------------------------------------------------------ markdown */
export interface Heading { id: string; text: string; level: 2 | 3 }
const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

function inline(text: string): ReactNode[] {
  // **bold**, *italic*, [label](href) — rendered as React elements, never as HTML.
  return text.split(/(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|\[[^\]]+\]\([^)\s]+\))/g).filter(Boolean).map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (/^\*[^*].*\*$/.test(part)) return <em key={i}>{part.slice(1, -1)}</em>;
    const link = /^\[([^\]]+)\]\(([^)\s]+)\)$/.exec(part);
    if (link) {
      const [, label, href] = link;
      if (href.startsWith('/')) return <Link key={i} to={href} className="link">{label}</Link>;
      if (/^https?:\/\//.test(href) || href.startsWith('mailto:')) return <a key={i} href={href} className="link" rel="noopener noreferrer" target="_blank">{label}</a>;
      return label;
    }
    return part;
  });
}

export function parseHeadings(body: string): Heading[] {
  return body.split('\n').flatMap((l) => {
    const m = /^(#{2,3})\s+(.+)$/.exec(l.trim());
    return m ? [{ id: slug(m[2]), text: m[2], level: m[1].length as 2 | 3 }] : [];
  });
}

/** Renders the limited Markdown used by legal documents. Blockquotes are shown as "needs confirmation" callouts. */
export function LegalMarkdown({ body }: { body: string }) {
  const blocks = body.replace(/\r\n/g, '\n').split(/\n{2,}/).map((b) => b.trim()).filter(Boolean);
  return (
    <div className="legal-body space-y-4 text-[14.5px] leading-[1.7] text-ink">
      {blocks.map((b, i) => {
        const lines = b.split('\n');
        const h = /^(#{1,3})\s+(.+)$/.exec(lines[0]);
        if (h && lines.length === 1) {
          const text = h[2];
          return h[1].length <= 2
            ? <h2 key={i} id={slug(text)} className="scroll-mt-20 pt-4 font-serif text-[22px] font-medium leading-snug">{text}</h2>
            : <h3 key={i} id={slug(text)} className="scroll-mt-20 pt-2 text-[15.5px] font-semibold">{text}</h3>;
        }
        if (lines.every((l) => l.startsWith('>'))) {
          return (
            <aside key={i} className="rounded border-l-[3px] border-bronze bg-bronze-soft/60 px-4 py-3 text-[13.5px] leading-relaxed">
              {inline(lines.map((l) => l.replace(/^>\s?/, '')).join(' '))}
            </aside>
          );
        }
        if (lines.every((l) => /^\s*[-*]\s/.test(l))) return <ul key={i} className="list-disc space-y-1.5 pl-5">{lines.map((l, j) => <li key={j}>{inline(l.replace(/^\s*[-*]\s/, ''))}</li>)}</ul>;
        if (lines.every((l) => /^\s*\d+\.\s/.test(l))) return <ol key={i} className="list-decimal space-y-1.5 pl-5">{lines.map((l, j) => <li key={j}>{inline(l.replace(/^\s*\d+\.\s/, ''))}</li>)}</ol>;
        return <p key={i}>{inline(lines.join(' '))}</p>;
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ acceptance after sign-in */
/**
 * Shown after sign-in when a required document (terms, privacy) has a version this person has not accepted.
 * Signing in is never treated as acceptance: the person must tick the box, and the server records the exact
 * versions shown. The server can also enforce this (LEGAL_ACCEPTANCE_ENFORCED) by refusing other requests.
 */
export function LegalAcceptanceGate({ children }: { children: ReactNode }) {
  const { me, signOut } = useAuth();
  const [pending, setPending] = useState<LegalDocumentSummary[] | null>(null);
  const [previously, setPreviously] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [agreed, setAgreed] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setError(null);
    api.get<LegalStatus>('/auth/legal-status').then((s) => { setPending(s.pending); setPreviously(new Set(s.accepted.map((a) => a.doc_type))); })
      .catch((e) => setError(errorMessage(e, 'We could not check whether you have accepted the current terms.')));
  };
  useEffect(load, [me?.id]);

  if (error) return (
    <GateFrame title="Something went wrong">
      <Notice tone="danger" action={<Button size="sm" onClick={load}>Try again</Button>}>{error}</Notice>
      <button type="button" className="mt-4 text-[13px] text-muted hover:text-ink" onClick={() => signOut()}>Sign out</button>
    </GateFrame>
  );
  if (pending === null) return <div className="mx-auto max-w-xl p-8" aria-busy="true"><LoadingBlock rows={3} /></div>;
  if (pending.length === 0) return <>{children}</>;

  const accept = async () => {
    setSaving(true); setError(null);
    try {
      const s = await api.post<LegalStatus>('/auth/legal-acceptances', {
        accepted_versions: Object.fromEntries(pending.map((d) => [d.doc_type, d.version])),
      });
      setAgreed(false); setPending(s.pending);
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) { setAgreed(false); load(); }
      setError(errorMessage(e));
    } finally { setSaving(false); }
  };
  const updated = pending.some((d) => previously.has(d.doc_type));
  return (
    <GateFrame title={updated ? 'Please review the updated terms' : 'Before you continue'}>
      <p className="text-[14px] leading-relaxed text-muted">
        To use ACEDRA you need to accept the current version of the following {pending.length === 1 ? 'document' : 'documents'}.
        Open each one to read it; it opens in a new tab.
      </p>
      <ul className="mt-5 divide-y divide-line rounded-lg border border-line bg-surface">
        {pending.map((d) => (
          <li key={d.id} className="flex items-start justify-between gap-4 px-4 py-3">
            <div className="min-w-0">
              <Link to={`/legal/${d.doc_type}`} target="_blank" className="link text-[14px] font-medium">{d.title}</Link>
              <div className="text-[12.5px] text-muted">Version {d.version} · effective {fmtDate(d.effective_date)}</div>
              {d.change_summary && <div className="mt-1 text-[12.5px] text-muted">What changed: {d.change_summary}</div>}
            </div>
          </li>
        ))}
      </ul>
      <div className="mt-5">
        <Checkbox checked={agreed} onChange={setAgreed} label="I have read and accept these documents."
          description="Your acceptance is recorded with the version numbers and the time." />
      </div>
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <Button variant="primary" onClick={accept} disabled={!agreed} loading={saving}>Accept and continue</Button>
        <button type="button" className="text-[13px] text-muted hover:text-ink" onClick={() => signOut()}>Sign out instead</button>
      </div>
    </GateFrame>
  );
}

function GateFrame({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-paper">
      <header className="mx-auto flex h-16 w-full max-w-content items-center px-5 sm:px-8"><AcedraWordmark size={24} /></header>
      <main id="main" className="flex flex-1 justify-center px-5 pt-8 sm:pt-16">
        <div className="w-full max-w-lg">
          <h1 className="font-serif text-[30px] font-medium leading-tight">{title}</h1>
          <div className="mt-4">{children}</div>
        </div>
      </main>
      <footer className="mx-auto w-full max-w-content px-5 py-6 sm:px-8"><LegalLinks className="justify-center" /></footer>
    </div>
  );
}
