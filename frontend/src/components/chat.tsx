import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from 'react';
import { BookMarked, Plus, SendHorizontal, ThumbsDown, ThumbsUp, Trash2 } from 'lucide-react';
import { api, errorMessage } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useApi } from '../lib/useApi';
import { cleanName, relTime } from '../lib/format';
import type {
  AssistantStatus, ChatMessage as ApiMessage, Conversation, ConversationDetail, SourceCitation, StudentProfile,
  SuggestedQuestion,
} from '../types/api';
import { Badge, Button, cx, IconButton, LoadingBlock, RichText, Select, Tabs, useToast } from './ui';

type Mode = 'PUBLIC_MODE_A' | 'PERSONAL_MODE_B';
/** A stored message, or a local placeholder while a reply is being generated. */
type Msg = Pick<ApiMessage, 'id' | 'role' | 'content' | 'created_at'> & {
  generation_mode?: string;
  sources_json?: SourceCitation[];
  pending?: boolean;
};

const MODE_COPY: Record<Mode, { label: string; help: string }> = {
  PUBLIC_MODE_A: { label: 'University information', help: 'Policies, regulations, examinations and placement rules from your university’s approved documents.' },
  PERSONAL_MODE_B: { label: 'Academic records', help: 'Questions about authorised academic records: attendance, marks, alerts, plan and readiness.' },
};

export function AssistantWorkspace() {
  const { me } = useAuth();
  const toast = useToast();
  const isStudent = me?.role === 'student';
  const [mode, setMode] = useState<Mode>('PUBLIC_MODE_A');
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [studentId, setStudentId] = useState<string>('');
  const convs = useApi<Conversation[]>('/ai/conversations');
  const status = useApi<AssistantStatus>('/ai/status');
  const suggestions = useApi<SuggestedQuestion[]>('/ai/suggested-questions', { mode });
  const students = useApi<StudentProfile[]>(!isStudent && mode === 'PERSONAL_MODE_B' ? '/students/' : null, { limit: 100 });
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [messages]);

  const open = async (id: number) => {
    const c = await api.get<ConversationDetail>(`/ai/conversations/${id}`);
    setActiveId(id); setMode(c.mode === 'PERSONAL_MODE_B' ? 'PERSONAL_MODE_B' : 'PUBLIC_MODE_A'); setMessages(c.messages || []);
  };
  const startNew = () => { setActiveId(null); setMessages([]); };

  const send = async (text?: string) => {
    const content = (text ?? draft).trim();
    if (!content || sending) return;
    if (mode === 'PERSONAL_MODE_B' && !isStudent && !studentId) { toast('Choose a student you support first.', 'error'); return; }
    setSending(true); setDraft('');
    const temp: Msg = { id: -Date.now(), role: 'user', content, created_at: new Date().toISOString() };
    setMessages((m) => [...m, temp, { id: -1, role: 'assistant', content: '', created_at: '', pending: true }]);
    try {
      let id = activeId;
      if (!id) {
        const c = await api.post<Conversation>('/ai/conversations', { mode, title: content.slice(0, 60) });
        id = c.id; setActiveId(c.id);
      }
      const reply = await api.post<Msg>(`/ai/conversations/${id}/messages`, { content, student_id: studentId ? Number(studentId) : undefined });
      setMessages((m) => [...m.filter((x) => !x.pending), reply]);
      convs.reload();
    } catch (e) {
      setMessages((m) => m.filter((x) => !x.pending));
      toast(errorMessage(e), 'error');
    } finally { setSending(false); }
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } };

  return (
    <div className="grid min-h-[calc(100vh-10rem)] gap-0 overflow-hidden rounded-lg border border-line bg-surface lg:grid-cols-[240px_1fr]">
      <aside className="hidden flex-col border-r border-line lg:flex">
        <div className="p-3"><Button className="w-full" icon={<Plus size={14} />} onClick={startNew}>New conversation</Button></div>
        <div className="flex-1 overflow-y-auto px-2 pb-3">
          <div className="px-2 pb-1 text-[11.5px] font-medium text-faint">History</div>
          {convs.loading && !convs.data ? <div className="px-2"><LoadingBlock rows={3} /></div> : null}
          {convs.data?.length === 0 && <p className="px-2 text-[12.5px] text-muted">Your conversations appear here. Only you can see them.</p>}
          {convs.data?.map((c) => (
            <div key={c.id} className={cx('group flex items-center rounded', activeId === c.id ? 'bg-sunken' : 'hover:bg-sunken/60')}>
              <button type="button" onClick={() => open(c.id)} className="min-w-0 flex-1 px-2 py-1.5 text-left">
                <div className="truncate text-[13px] text-ink">{c.title}</div>
                <div className="text-[11.5px] text-faint">{c.mode === 'PERSONAL_MODE_B' ? 'Records' : 'University'} · {relTime(c.updated_at)}</div>
              </button>
              <IconButton label="Delete conversation" className="invisible h-7 w-7 group-hover:visible" onClick={async () => { await api.del(`/ai/conversations/${c.id}`); if (activeId === c.id) startNew(); convs.reload(); }}>
                <Trash2 size={13} />
              </IconButton>
            </div>
          ))}
        </div>
      </aside>

      <section className="flex min-w-0 flex-col">
        <div className="border-b border-line px-4 pt-3">
          <Tabs value={mode} onChange={(m) => { if (m !== mode) { setMode(m); startNew(); } }}
            tabs={[{ id: 'PUBLIC_MODE_A' as Mode, label: MODE_COPY.PUBLIC_MODE_A.label }, { id: 'PERSONAL_MODE_B', label: isStudent ? 'My records' : MODE_COPY.PERSONAL_MODE_B.label }]} className="border-0" />
        </div>
        <div className="flex flex-wrap items-center gap-2 border-b border-line bg-sunken/40 px-4 py-2 text-[12.5px] text-muted">
          <span className="min-w-0 flex-1">{MODE_COPY[mode].help}</span>
          {status.data && (status.data.llm_configured
            ? <Badge tone="forest">Model: {status.data.llm_model || status.data.llm_provider}</Badge>
            : <Badge tone="neutral" className="whitespace-normal">No language model connected — answers come straight from documents and records</Badge>)}
        </div>
        {mode === 'PERSONAL_MODE_B' && !isStudent && (
          <div className="flex items-center gap-2 border-b border-line px-4 py-2">
            <span className="label">Student</span>
            <Select value={studentId} onChange={(e) => { setStudentId(e.target.value); startNew(); }} className="h-8 max-w-xs">
              <option value="">Choose a student you support…</option>
              {students.data?.map((s) => <option key={s.id} value={s.id}>{cleanName(s.full_name)} · {s.usn}</option>)}
            </Select>
          </div>
        )}

        <div className="flex-1 overflow-y-auto px-4 py-5 sm:px-8">
          {!messages.length ? (
            <div className="mx-auto max-w-xl">
              <h2 className="font-serif text-[22px] font-medium">{mode === 'PERSONAL_MODE_B' ? (isStudent ? 'Ask about your own records' : 'Ask about a student you support') : `Ask about ${me?.university?.short_name || 'your university'}`}</h2>
              <p className="mt-1 text-[13.5px] text-muted">{mode === 'PERSONAL_MODE_B'
                ? 'Answers use only records you are authorised to see. Nothing about other students is ever included.'
                : 'Answers cite the approved documents they come from, so you can check the source.'}</p>
              <div className="mt-5 space-y-1.5">
                {suggestions.data?.slice(0, 5).map((q, i) => (
                  <button key={i} type="button" onClick={() => send(q.prompt)}
                    className="block w-full rounded border border-line px-3 py-2 text-left text-[13px] text-ink hover:border-line-strong hover:bg-sunken/60">{q.prompt}</button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-2xl space-y-5">
              {messages.map((m) => <ChatMessage key={m.id} m={m} />)}
              <div ref={endRef} />
            </div>
          )}
        </div>

        <form onSubmit={(e: FormEvent) => { e.preventDefault(); send(); }} className="border-t border-line p-3 sm:px-8">
          <div className="mx-auto flex max-w-2xl items-end gap-2 rounded-lg border border-line-strong bg-surface p-1.5 focus-within:border-forest focus-within:ring-2 focus-within:ring-forest/15">
            <textarea value={draft} onChange={(e) => setDraft(e.target.value)} onKeyDown={onKey} rows={1} maxLength={4000}
              placeholder={mode === 'PERSONAL_MODE_B' ? 'Ask about attendance, marks, alerts or your plan…' : 'Ask about a policy or regulation…'}
              aria-label="Message" className="max-h-40 min-h-[36px] flex-1 resize-none bg-transparent px-2 py-1.5 text-[13.5px] focus:outline-none" />
            <Button type="submit" variant="primary" loading={sending} icon={!sending ? <SendHorizontal size={14} /> : undefined} aria-label="Send">Send</Button>
          </div>
          <p className="mx-auto mt-1.5 max-w-2xl text-[11.5px] text-faint">The assistant supports, and does not replace, guidance from your faculty and offices. It never makes disciplinary decisions.</p>
        </form>
      </section>
    </div>
  );
}

function ChatMessage({ m }: { m: Msg }) {
  const toast = useToast();
  const [voted, setVoted] = useState<boolean | null>(null);
  if (m.role === 'user') return <div className="ml-auto max-w-[85%] rounded-lg bg-sunken px-3.5 py-2.5 text-[13.5px] text-ink whitespace-pre-wrap">{m.content}</div>;
  if (m.pending) return <div className="flex items-center gap-2 text-[13px] text-muted"><span className="h-2 w-2 animate-pulse rounded-full bg-forest" />Looking through your university’s sources…</div>;
  const fallback = m.generation_mode !== 'llm';
  const vote = async (v: boolean) => {
    try { await api.post(`/ai/messages/${m.id}/feedback`, { is_helpful: v }); setVoted(v); toast('Thanks — feedback recorded'); } catch (e) { toast(errorMessage(e), 'error'); }
  };
  return (
    <div>
      <RichText text={m.content} />
      {!!m.sources_json?.length && (
        <div className="mt-3 space-y-1.5">
          <div className="flex items-center gap-1.5 text-[12px] font-medium text-muted"><BookMarked size={13} />Sources</div>
          {m.sources_json.map((c, i) => (
            <details key={i} className="rounded border border-line px-3 py-1.5 text-[12.5px]">
              <summary className="cursor-pointer text-ink"><span className="mr-1.5 font-semibold text-forest">[{i + 1}]</span>{c.document_title}{c.section ? ` — ${c.section}` : ''}</summary>
              <p className="mt-1.5 text-muted">{c.snippet}</p>
            </details>
          ))}
        </div>
      )}
      <div className="mt-2 flex items-center gap-2 text-[11.5px] text-faint">
        {fallback ? <span>Offline answer · no language model used</span> : <span>Generated by the configured model from cited sources</span>}
        <span className="ml-auto flex gap-0.5">
          <IconButton label="Helpful" className={cx('h-7 w-7', voted === true && 'text-forest')} onClick={() => vote(true)}><ThumbsUp size={13} /></IconButton>
          <IconButton label="Not helpful" className={cx('h-7 w-7', voted === false && 'text-bronze')} onClick={() => vote(false)}><ThumbsDown size={13} /></IconButton>
        </span>
      </div>
    </div>
  );
}

