/**
 * ACEDRA platform: legal document versions (super administrators edit, approve and publish; employees read)
 * and the inbox for the public contact form. University accounts never reach these pages; the API returns
 * 404 for them.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { api, errorMessage } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useApi } from '../lib/useApi';
import { fmtDate, relTime, titleCase } from '../lib/format';
import { PageHeader } from '../components/shell';
import { LegalMarkdown } from '../components/legal';
import {
  Async, Badge, Button, DataTable, Dialog, Drawer, EmptyState, Field, Input, KeyValues, Notice, Panel, Select, Tabs, Textarea, useToast,
} from '../components/ui';
import type { ContactMessage, LegalDocType, LegalDocumentAdmin } from '../types/api';

const TYPES: [LegalDocType, string][] = [['terms', 'Terms and conditions'], ['privacy', 'Privacy policy'], ['cookies', 'Cookie policy']];
const STATUS_TONE: Record<string, 'neutral' | 'bronze' | 'forest'> = { draft: 'neutral', approved: 'bronze', published: 'forest' };

function statusBadge(d: LegalDocumentAdmin) {
  if (d.is_current) return <Badge tone="ok" dot>In force</Badge>;
  const today = new Date().toISOString().slice(0, 10);
  if (d.status === 'published' && d.effective_date && d.effective_date > today) return <Badge tone="bronze">Scheduled</Badge>;
  if (d.status === 'published') return <Badge>Superseded</Badge>;
  return <Badge tone={STATUS_TONE[d.status]}>{titleCase(d.status)}</Badge>;
}

export function LegalAdminPage() {
  const { me } = useAuth();
  const canEdit = me?.role === 'platform_admin';
  const docs = useApi<LegalDocumentAdmin[]>('/platform/legal-documents');
  const [type, setType] = useState<LegalDocType>('terms');
  const [openId, setOpenId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const open = docs.data?.find((d) => d.id === openId) || null;

  const replace = (d: LegalDocumentAdmin) => { docs.reload(); setOpenId(d.id); };

  return (
    <div>
      <PageHeader title="Legal documents"
        lede="Versions of the terms, privacy policy and cookie policy shown on the website and accepted by users. A version can be published only after a super administrator records its approval."
        actions={canEdit && <Button variant="primary" icon={<Plus size={14} />} onClick={() => setCreating(true)}>New draft version</Button>} />
      {!canEdit && <div className="mb-5"><Notice>You can read every version. Only ACEDRA super administrators can edit, approve or publish legal documents.</Notice></div>}
      <Tabs className="mb-4" value={type} onChange={setType}
        tabs={TYPES.map(([id, label]) => ({ id, label, count: docs.data?.filter((d) => d.doc_type === id).length }))} />
      <Async state={docs}>{(all) => {
        const rows = all.filter((d) => d.doc_type === type);
        return rows.length === 0 ? <EmptyState title="No versions yet" /> : (
          <Panel padded={false}>
            <DataTable rows={rows} rowKey={(d) => d.id} onRowClick={(d) => setOpenId(d.id)} columns={[
              { key: 'v', header: 'Version', render: (d) => <span className="font-medium">{d.version}</span> },
              { key: 's', header: 'Status', render: statusBadge },
              { key: 'e', header: 'Effective', render: (d) => fmtDate(d.effective_date) },
              { key: 'a', header: 'Approved by', hideOnMobile: true, render: (d) => d.approved_by_name || '—' },
              { key: 'u', header: 'Last change', hideOnMobile: true, render: (d) => relTime(d.updated_at) },
            ]} />
          </Panel>
        );
      }}</Async>
      <p className="mt-4 text-[12.5px] text-muted">University administrators cannot change these documents. Published versions are permanent and remain available in the public version history.</p>
      {creating && <CreateDraftDialog defaultType={type} onClose={() => setCreating(false)} onCreated={(d) => { setCreating(false); setType(d.doc_type as LegalDocType); replace(d); }} />}
      {open && <VersionDrawer doc={open} canEdit={canEdit} onClose={() => setOpenId(null)} onChanged={replace} />}
    </div>
  );
}

function CreateDraftDialog({ defaultType, onClose, onCreated }: { defaultType: LegalDocType; onClose: () => void; onCreated: (d: LegalDocumentAdmin) => void }) {
  const [docType, setDocType] = useState<LegalDocType>(defaultType);
  const [version, setVersion] = useState('');
  const [summary, setSummary] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const valid = /^[A-Za-z0-9.-]+$/.test(version);
  const submit = async () => {
    setSaving(true); setError(null);
    try { onCreated(await api.post<LegalDocumentAdmin>('/platform/legal-documents', { doc_type: docType, version, change_summary: summary || undefined })); }
    catch (e) { setError(errorMessage(e)); } finally { setSaving(false); }
  };
  return (
    <Dialog open onClose={onClose} title="New draft version" description="The draft starts as a copy of the version currently in force."
      footer={<><Button onClick={onClose}>Cancel</Button><Button variant="primary" onClick={submit} loading={saving} disabled={!valid}>Create draft</Button></>}>
      <div className="space-y-4">
        {error && <Notice tone="danger">{error}</Notice>}
        <Field label="Document"><Select value={docType} onChange={(e) => setDocType(e.target.value as LegalDocType)}>{TYPES.map(([id, l]) => <option key={id} value={id}>{l}</option>)}</Select></Field>
        <Field label="Version number" required hint="Letters, numbers, dots and hyphens, e.g. 1.0" error={version && !valid ? 'Use only letters, numbers, dots and hyphens.' : undefined}>
          <Input value={version} onChange={(e) => setVersion(e.target.value)} maxLength={40} /></Field>
        <Field label="What changes in this version" hint="Shown to users when they are asked to accept it."><Textarea rows={2} value={summary} onChange={(e) => setSummary(e.target.value)} maxLength={500} /></Field>
      </div>
    </Dialog>
  );
}

function VersionDrawer({ doc, canEdit, onClose, onChanged }: { doc: LegalDocumentAdmin; canEdit: boolean; onClose: () => void; onChanged: (d: LegalDocumentAdmin) => void }) {
  const toast = useToast();
  const [mode, setMode] = useState<'view' | 'edit' | 'approve' | 'publish'>('view');
  const [title, setTitle] = useState(doc.title);
  const [body, setBody] = useState(doc.body);
  const [summary, setSummary] = useState(doc.change_summary || '');
  const [note, setNote] = useState('');
  const [effective, setEffective] = useState(doc.effective_date || new Date().toISOString().slice(0, 10));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (fn: () => Promise<LegalDocumentAdmin>, done: string) => {
    setBusy(true); setError(null);
    try { const d = await fn(); toast(done); setMode('view'); onChanged(d); }
    catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  };
  const base = `/platform/legal-documents/${doc.id}`;

  const footer = !canEdit ? undefined : mode === 'edit' ? (
    <><Button onClick={() => setMode('view')}>Cancel</Button>
      <Button variant="primary" loading={busy} onClick={() => run(() => api.patch(base, { title, body, change_summary: summary }), 'Draft saved')}>Save draft</Button></>
  ) : mode === 'approve' ? (
    <><Button onClick={() => setMode('view')}>Cancel</Button>
      <Button variant="primary" loading={busy} disabled={note.trim().length < 10} onClick={() => run(() => api.post(`${base}/approve`, { approval_note: note }), 'Version approved')}>Record approval</Button></>
  ) : mode === 'publish' ? (
    <><Button onClick={() => setMode('view')}>Cancel</Button>
      <Button variant="primary" loading={busy} disabled={!effective} onClick={() => run(() => api.post(`${base}/publish`, { effective_date: effective }), 'Version published')}>Publish</Button></>
  ) : doc.status === 'draft' ? (
    <><Button onClick={() => setMode('edit')}>Edit draft</Button><Button variant="primary" onClick={() => setMode('approve')}>Approve…</Button></>
  ) : doc.status === 'approved' ? (
    <><Button loading={busy} onClick={() => run(() => api.post(`${base}/reopen`), 'Returned to draft')}>Return to draft</Button><Button variant="primary" onClick={() => setMode('publish')}>Publish…</Button></>
  ) : undefined;

  return (
    <Drawer open onClose={onClose} width="max-w-3xl" title={`${TYPES.find(([t]) => t === doc.doc_type)?.[1]} · version ${doc.version}`}
      subtitle={<span className="inline-flex items-center gap-2">{statusBadge(doc)}</span>} footer={footer}>
      <div className="space-y-5">
        {error && <Notice tone="danger">{error}</Notice>}
        <KeyValues items={[
          ['Effective date', fmtDate(doc.effective_date)],
          ['Published', doc.published_at ? `${fmtDate(doc.published_at)}${doc.published_by_name ? ` by ${doc.published_by_name}` : ''}` : '—'],
          ['Approved', doc.approved_at ? `${fmtDate(doc.approved_at)}${doc.approved_by_name ? ` by ${doc.approved_by_name}` : ''}` : '—'],
          ['Approval record', doc.approval_note || '—'],
        ]} />
        {doc.status === 'published' && <Link to={`/legal/${doc.doc_type}?version=${encodeURIComponent(doc.version)}`} target="_blank" className="link text-[13px]">Open the public page</Link>}

        {mode === 'edit' ? (
          <div className="space-y-4">
            <Field label="Title"><Input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} /></Field>
            <Field label="What changes in this version"><Textarea rows={2} value={summary} onChange={(e) => setSummary(e.target.value)} maxLength={500} /></Field>
            <Field label="Text" hint="Markdown: ## headings, - lists, **bold**, and lines starting with > for notes that need confirmation.">
              <Textarea rows={22} value={body} onChange={(e) => setBody(e.target.value)} className="font-mono text-[12.5px]" /></Field>
          </div>
        ) : mode === 'approve' ? (
          <div className="space-y-3">
            <Notice tone="attention" title="Approval is a formal step">Approve only text that has been reviewed by legal counsel or another authorised reviewer. After approval the text cannot be edited unless it is returned to draft.</Notice>
            <Field label="Approval record" required hint="Who reviewed the text and on what basis (at least 10 characters).">
              <Textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} maxLength={500} /></Field>
          </div>
        ) : mode === 'publish' ? (
          <div className="space-y-3">
            <Notice tone="attention" title="Publishing is permanent">The version becomes public on its effective date. For terms and privacy, every user will be asked to accept it the next time they use ACEDRA.</Notice>
            <Field label="Effective date" required><Input type="date" value={effective} onChange={(e) => setEffective(e.target.value)} /></Field>
          </div>
        ) : null}

        {mode !== 'edit' && (
          <div className="rounded-lg border border-line p-5">
            <h3 className="mb-3 font-serif text-[22px] font-medium">{doc.title}</h3>
            {doc.change_summary && <p className="mb-4 text-[13px] text-muted">What changed: {doc.change_summary}</p>}
            <LegalMarkdown body={doc.body} />
          </div>
        )}
      </div>
    </Drawer>
  );
}

/* ------------------------------------------------------------------ contact inbox */
const MSG_STATUSES: [string, string][] = [['new', 'New'], ['in_progress', 'In progress'], ['closed', 'Closed']];

export function ContactMessagesPage() {
  const [status, setStatus] = useState('');
  const msgs = useApi<ContactMessage[]>('/platform/contact-messages', { status });
  const [open, setOpen] = useState<ContactMessage | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const setMsgStatus = async (m: ContactMessage, s: string) => {
    setSaving(true); setError(null);
    try { const d = await api.patch<ContactMessage>(`/platform/contact-messages/${m.id}`, { status: s }); setOpen(d); msgs.reload(); }
    catch (e) { setError(errorMessage(e)); } finally { setSaving(false); }
  };
  return (
    <div>
      <PageHeader title="Contact messages" lede="Messages sent through the contact form on the ACEDRA website. Reply from your own mailbox; this inbox only tracks status." />
      <Tabs className="mb-4" value={status} onChange={setStatus} tabs={[{ id: '', label: 'All' }, ...MSG_STATUSES.map(([id, label]) => ({ id, label }))]} />
      <Async state={msgs}>{(rows) => rows.length === 0 ? <EmptyState title="No messages">New messages from the contact form appear here.</EmptyState> : (
        <Panel padded={false}>
          <DataTable rows={rows} rowKey={(m) => m.id} onRowClick={(m) => { setError(null); setOpen(m); }} columns={[
            { key: 'f', header: 'From', render: (m) => <div><div className="font-medium">{m.name}</div><div className="text-[12px] text-muted">{m.institution}</div></div> },
            { key: 's', header: 'Subject', render: (m) => m.subject },
            { key: 'st', header: 'Status', render: (m) => <Badge tone={m.status === 'new' ? 'bronze' : m.status === 'closed' ? 'neutral' : 'forest'}>{titleCase(m.status)}</Badge> },
            { key: 'd', header: 'Received', hideOnMobile: true, render: (m) => relTime(m.created_at) },
          ]} />
        </Panel>
      )}</Async>
      <Drawer open={!!open} onClose={() => setOpen(null)} title={open?.subject || ''} subtitle={open ? `${open.name} · ${open.email}` : ''}
        footer={open && <div className="flex flex-wrap gap-2">{MSG_STATUSES.filter(([s]) => s !== open.status).map(([s, l]) => (
          <Button key={s} loading={saving} onClick={() => setMsgStatus(open, s)}>Mark {l.toLowerCase()}</Button>))}</div>}>
        {open && (
          <div className="space-y-4">
            {error && <Notice tone="danger">{error}</Notice>}
            <KeyValues items={[['Institution', open.institution], ['Email', open.email], ['Received', fmtDate(open.created_at, true)], ['Status', titleCase(open.status)]]} />
            <p className="whitespace-pre-wrap break-words text-[14px] leading-relaxed">{open.message}</p>
          </div>
        )}
      </Drawer>
    </div>
  );
}
