import {
  ButtonHTMLAttributes, createContext, forwardRef, InputHTMLAttributes, type Key, ReactNode, SelectHTMLAttributes,
  TextareaHTMLAttributes, useCallback, useContext, useEffect, useId, useMemo, useRef, useState,
} from 'react';
import { createPortal } from 'react-dom';
import { AlertCircle, ArrowDown, ArrowUp, Check, ChevronLeft, ChevronRight, Info, Loader2, Search, X } from 'lucide-react';
import { clsx, ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { initials, titleCase } from '../lib/format';

export const cx = (...c: ClassValue[]) => twMerge(clsx(c));

/* ------------------------------------------------------------------ Button */
type BtnVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'quiet';
interface BtnProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: BtnVariant; size?: 'sm' | 'md'; loading?: boolean; icon?: ReactNode;
}
export const Button = forwardRef<HTMLButtonElement, BtnProps>(function Button(
  { variant = 'secondary', size = 'md', loading, icon, className, children, disabled, type = 'button', ...rest }, ref,
) {
  return (
    <button
      ref={ref} type={type} disabled={disabled || loading}
      className={cx(
        'inline-flex items-center justify-center gap-1.5 rounded font-medium whitespace-nowrap transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
        size === 'sm' ? 'h-7 px-2.5 text-[12.5px]' : 'h-9 px-3.5 text-[13.5px]',
        variant === 'primary' && 'bg-forest text-on-forest hover:bg-forest/90',
        variant === 'secondary' && 'bg-surface text-ink border border-line-strong hover:bg-sunken',
        variant === 'ghost' && 'text-ink hover:bg-sunken',
        variant === 'quiet' && 'text-muted hover:text-ink hover:bg-sunken',
        variant === 'danger' && 'bg-danger text-surface hover:bg-danger/90',
        className,
      )}
      {...rest}
    >
      {loading ? <Loader2 size={14} className="animate-spin" /> : icon}
      {children}
    </button>
  );
});

export function IconButton({ label, children, className, ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return (
    <button type="button" aria-label={label} title={label}
      className={cx('inline-flex h-8 w-8 items-center justify-center rounded text-muted hover:text-ink hover:bg-sunken', className)} {...rest}>
      {children}
    </button>
  );
}

/* ------------------------------------------------------------------ Form controls */
const control = 'w-full rounded border border-line-strong bg-surface px-3 text-[13.5px] text-ink placeholder:text-faint focus:outline-none focus:border-forest focus:ring-2 focus:ring-forest/15 disabled:bg-sunken disabled:text-muted';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input({ className, ...p }, ref) {
  return <input ref={ref} className={cx(control, 'h-9', className)} {...p} />;
});
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(function Textarea({ className, ...p }, ref) {
  return <textarea ref={ref} className={cx(control, 'py-2 min-h-[84px] leading-relaxed', className)} {...p} />;
});
export function Select({ className, children, ...p }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cx(control, 'h-9 pr-8 appearance-none cursor-pointer', className)}
    style={{ backgroundRepeat: 'no-repeat', backgroundPosition: 'right 0.6rem center', backgroundSize: '12px', backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23807d70' stroke-width='2.5'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E\")" }}
    {...p}>{children}</select>;
}

export function Field({ label, hint, error, children, required, className }: {
  label: string; hint?: ReactNode; error?: string | null; children: ReactNode; required?: boolean; className?: string;
}) {
  return (
    <label className={cx('block', className)}>
      <span className="label mb-1 block">{label}{required && <span className="text-bronze"> *</span>}</span>
      {children}
      {error ? <span className="mt-1 block text-[12px] text-danger">{error}</span>
        : hint ? <span className="mt-1 block text-[12px] text-faint">{hint}</span> : null}
    </label>
  );
}

export function Checkbox({ label, checked, onChange, description }: { label: ReactNode; checked: boolean; onChange: (v: boolean) => void; description?: ReactNode }) {
  return (
    <label className="flex items-start gap-2.5 cursor-pointer select-none">
      <input type="checkbox" className="peer sr-only" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span aria-hidden className={cx('mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-[4px] border peer-focus-visible:ring-2 peer-focus-visible:ring-forest peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-surface',
        checked ? 'bg-forest border-forest text-on-forest' : 'border-line-strong bg-surface')}>
        {checked && <Check size={12} strokeWidth={3} />}
      </span>
      <span><span className="text-[13.5px] text-ink">{label}</span>{description && <span className="block text-[12px] text-muted">{description}</span>}</span>
    </label>
  );
}

export function SearchInput({ value, onChange, placeholder = 'Search', className }: { value: string; onChange: (v: string) => void; placeholder?: string; className?: string }) {
  return (
    <div className={cx('relative', className)}>
      <Search size={14} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-faint" />
      <Input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="pl-8" aria-label={placeholder} />
    </div>
  );
}

/* ------------------------------------------------------------------ Badges */
type Tone = 'neutral' | 'forest' | 'ok' | 'caution' | 'danger' | 'bronze' | 'olive';
const toneCls: Record<Tone, string> = {
  neutral: 'bg-sunken text-muted', forest: 'bg-forest-soft text-forest', ok: 'bg-ok-soft text-ok',
  caution: 'bg-caution-soft text-caution', danger: 'bg-danger-soft text-danger', bronze: 'bg-bronze-soft text-bronze',
  olive: 'bg-sunken text-olive',
};
export function Badge({ tone = 'neutral', children, dot, className }: { tone?: Tone; children: ReactNode; dot?: boolean; className?: string }) {
  return (
    <span className={cx('inline-flex items-center gap-1.5 rounded px-1.5 py-[1px] text-[12px] font-medium whitespace-nowrap', toneCls[tone], className)}>
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}{children}
    </span>
  );
}

const STATUS_TONE: Record<string, Tone> = {
  critical: 'danger', high: 'danger', urgent: 'danger', rejected: 'danger', failed: 'danger', suspended: 'danger', inactive: 'neutral',
  moderate: 'caution', medium: 'caution', flagged: 'caution', under_review: 'caution', in_progress: 'caution', invited: 'caution',
  onboarding: 'caution', requested: 'caution', estimated: 'caution', interview_scheduled: 'caution', shortlisted: 'forest',
  meeting_scheduled: 'forest', requirements_gathering: 'forest', proposal_agreement: 'forest', contacted: 'forest',
  new: 'bronze', open: 'bronze', suggested: 'bronze', applied: 'bronze', assigned: 'forest', accepted: 'forest',
  low: 'neutral', normal: 'neutral', closed: 'neutral', expired: 'neutral', disabled: 'neutral', logged: 'neutral', withdrawn: 'neutral',
  resolved: 'ok', completed: 'ok', active: 'ok', approved: 'ok', ready: 'ok', selected: 'ok', placed: 'ok', verified: 'ok', sent: 'ok',
  pending: 'caution', early_stage: 'caution', developing: 'olive', near_ready: 'forest',
};
export function StatusBadge({ status, label }: { status?: string | null; label?: string }) {
  const k = (status || '').toLowerCase();
  return <Badge tone={STATUS_TONE[k] || 'neutral'} dot>{label || titleCase(k)}</Badge>;
}

/* ------------------------------------------------------------------ Layout primitives */
export function Panel({ title, description, actions, children, className, padded = true, id }: {
  title?: ReactNode; description?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string; padded?: boolean; id?: string;
}) {
  return (
    <section id={id} className={cx('rounded-lg border border-line bg-surface', className)}>
      {(title || actions) && (
        <header className="flex items-start justify-between gap-3 border-b border-line px-4 py-3">
          <div className="min-w-0">
            {title && <h2 className="section-title">{title}</h2>}
            {description && <p className="mt-0.5 text-[12.5px] text-muted">{description}</p>}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={padded ? 'p-4' : ''}>{children}</div>
    </section>
  );
}

/** A metric shown as a figure with context — used in rows, not as a wall of cards. */
export function Stat({ label, value, note, tone, className }: { label: string; value: ReactNode; note?: ReactNode; tone?: 'attention' | 'good'; className?: string }) {
  return (
    <div className={cx('min-w-0', className)}>
      <div className="label">{label}</div>
      <div className={cx('mt-0.5 text-[22px] font-semibold tnum leading-tight', tone === 'attention' ? 'text-bronze' : tone === 'good' ? 'text-ok' : 'text-ink')}>{value}</div>
      {note && <div className="mt-0.5 text-[12px] text-muted">{note}</div>}
    </div>
  );
}
export function StatStrip({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cx('grid grid-cols-2 gap-x-6 gap-y-4 sm:flex sm:flex-wrap sm:gap-x-10 border-y border-line py-4', className)}>{children}</div>;
}

export function Meter({ value, max = 100, threshold, tone, label, className }: { value: number; max?: number; threshold?: number; tone?: 'auto' | 'forest' | 'olive'; label?: string; className?: string }) {
  const p = Math.max(0, Math.min(100, (value / max) * 100));
  const below = threshold !== undefined && value < threshold;
  return (
    <div className={cx('relative h-1.5 w-full rounded-full bg-sunken', className)} role="meter" aria-valuenow={value} aria-valuemax={max} aria-label={label}>
      <div className={cx('h-full rounded-full', below ? 'bg-bronze' : tone === 'olive' ? 'bg-olive' : 'bg-forest')} style={{ width: `${p}%` }} />
      {threshold !== undefined && <div className="absolute -top-1 h-3.5 w-px bg-ink/50" style={{ left: `${(threshold / max) * 100}%` }} title={`Required: ${threshold}`} />}
    </div>
  );
}

export function KeyValues({ items, cols = 2 }: { items: [string, ReactNode][]; cols?: 1 | 2 | 3 }) {
  return (
    <dl className={cx('grid gap-x-6 gap-y-3', cols === 1 ? 'grid-cols-1' : cols === 2 ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 sm:grid-cols-3')}>
      {items.map(([k, v]) => (
        <div key={k} className="min-w-0"><dt className="label">{k}</dt><dd className="mt-0.5 text-[13.5px] text-ink break-words">{v ?? '—'}</dd></div>
      ))}
    </dl>
  );
}

export function Avatar({ name, size = 28 }: { name?: string; size?: number }) {
  return (
    <span className="inline-flex shrink-0 items-center justify-center rounded-full bg-forest-soft text-forest font-semibold" style={{ width: size, height: size, fontSize: size * 0.38 }} aria-hidden>
      {initials(name)}
    </span>
  );
}

export function Notice({ tone = 'info', children, title, action }: { tone?: 'info' | 'attention' | 'danger' | 'ok'; children?: ReactNode; title?: ReactNode; action?: ReactNode }) {
  const Icon = tone === 'ok' ? Check : tone === 'info' ? Info : AlertCircle;
  return (
    <div role={tone === 'danger' ? 'alert' : 'status'} className={cx('flex gap-2.5 rounded-lg border px-3.5 py-3 text-[13px]',
      tone === 'info' && 'border-line bg-sunken/60 text-ink', tone === 'attention' && 'border-bronze/25 bg-bronze-soft text-ink',
      tone === 'danger' && 'border-danger/25 bg-danger-soft text-ink', tone === 'ok' && 'border-ok/25 bg-ok-soft text-ink')}>
      <Icon size={16} className={cx('mt-0.5 shrink-0', tone === 'attention' ? 'text-bronze' : tone === 'danger' ? 'text-danger' : tone === 'ok' ? 'text-ok' : 'text-muted')} />
      <div className="min-w-0 flex-1">{title && <div className="font-medium">{title}</div>}{children && <div className={title ? 'mt-0.5 text-muted' : ''}>{children}</div>}</div>
      {action}
    </div>
  );
}

/* ------------------------------------------------------------------ States */
export function EmptyState({ title, children, action, icon }: { title: string; children?: ReactNode; action?: ReactNode; icon?: ReactNode }) {
  return (
    <div className="flex flex-col items-start gap-1.5 px-1 py-8 sm:items-center sm:text-center">
      {icon && <div className="mb-1 text-faint">{icon}</div>}
      <div className="text-[13.5px] font-medium text-ink">{title}</div>
      {children && <div className="max-w-md text-[13px] text-muted">{children}</div>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return <Notice tone="danger" title="This information could not be loaded" action={onRetry && <Button size="sm" onClick={onRetry}>Try again</Button>}>{message}</Notice>;
}
export function Skeleton({ className }: { className?: string }) { return <div className={cx('skeleton', className)} aria-hidden />; }
export function LoadingBlock({ rows = 4 }: { rows?: number }) {
  return <div className="space-y-2.5 py-2" aria-busy="true" aria-label="Loading">{Array.from({ length: rows }).map((_, i) => <Skeleton key={i} className={cx('h-4', i % 3 === 2 ? 'w-2/3' : 'w-full')} />)}</div>;
}
/** Wraps an async region: shows skeleton, error or content. */
export function Async<T>({ state, children, rows }: { state: { data: T | null; loading: boolean; error: string | null; reload: () => void }; children: (d: T) => ReactNode; rows?: number }) {
  if (state.error) return <ErrorState message={state.error} onRetry={state.reload} />;
  if (state.loading && !state.data) return <LoadingBlock rows={rows} />;
  if (!state.data) return null;
  return <>{children(state.data)}</>;
}

/* ------------------------------------------------------------------ Data table */
type SortValue = string | number | boolean | null | undefined;
export interface Column<T> {
  key: string; header: ReactNode; render?: (row: T) => ReactNode; sort?: (row: T) => SortValue; className?: string; align?: 'right';
  hideOnMobile?: boolean;
}
/** Sortable table. Columns without `render` show `row[key]`; rows are keyed by `rowKey`, else `row.id`. */
export function DataTable<T extends object>({ columns, rows, onRowClick, empty, rowKey, dense, initialSort }: {
  columns: Column<T>[]; rows: T[]; onRowClick?: (r: T) => void; empty?: ReactNode; rowKey?: (r: T) => Key; dense?: boolean;
  initialSort?: { key: string; dir: 'asc' | 'desc' };
}) {
  const [sort, setSort] = useState(initialSort || null);
  const sorted = useMemo(() => {
    if (!sort) return rows;
    const col = columns.find((c) => c.key === sort.key);
    const sortValue = col?.sort;
    if (!sortValue) return rows;
    return [...rows].sort((a, b) => {
      const x = sortValue(a), y = sortValue(b);
      const r = x === y ? 0 : x === null || x === undefined ? 1 : y === null || y === undefined ? -1 : x > y ? 1 : -1;
      return sort.dir === 'asc' ? r : -r;
    });
  }, [rows, sort, columns]);
  if (!rows.length) return <>{empty ?? <EmptyState title="Nothing to show yet" />}</>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-[13px]">
        <thead>
          <tr className="border-b border-line">
            {columns.map((c) => (
              <th key={c.key} scope="col" className={cx('px-4 py-2 text-left font-medium text-muted whitespace-nowrap', c.align === 'right' && 'text-right', c.hideOnMobile && 'hidden md:table-cell', c.className)}>
                {c.sort ? (
                  <button type="button" className="inline-flex items-center gap-1 hover:text-ink" onClick={() => setSort(sort?.key === c.key ? { key: c.key, dir: sort.dir === 'asc' ? 'desc' : 'asc' } : { key: c.key, dir: 'asc' })}>
                    {c.header}{sort?.key === c.key && (sort.dir === 'asc' ? <ArrowUp size={12} /> : <ArrowDown size={12} />)}
                  </button>
                ) : c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => (
            <tr key={rowKey ? rowKey(r) : (r as { id?: Key }).id ?? i}
              className={cx('border-b border-line last:border-0', onRowClick && 'cursor-pointer hover:bg-sunken/60 focus-within:bg-sunken/60')}
              onClick={onRowClick ? () => onRowClick(r) : undefined}
              onKeyDown={onRowClick ? (e) => { if (e.key === 'Enter') onRowClick(r); } : undefined}
              tabIndex={onRowClick ? 0 : undefined}>
              {columns.map((c) => (
                <td key={c.key} className={cx('px-4 align-middle', dense ? 'py-1.5' : 'py-2.5', c.align === 'right' && 'text-right tnum', c.hideOnMobile && 'hidden md:table-cell', c.className)}>
                  {c.render ? c.render(r) : ((r as Record<string, unknown>)[c.key] as ReactNode) ?? '—'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Pagination({ total, skip, limit, onChange }: { total: number; skip: number; limit: number; onChange: (skip: number) => void }) {
  if (total <= limit) return null;
  const from = skip + 1, to = Math.min(skip + limit, total);
  return (
    <div className="flex items-center justify-between border-t border-line px-4 py-2.5 text-[12.5px] text-muted">
      <span className="tnum">{from}–{to} of {total}</span>
      <div className="flex gap-1">
        <IconButton label="Previous page" disabled={skip === 0} onClick={() => onChange(Math.max(0, skip - limit))} className="disabled:opacity-40"><ChevronLeft size={16} /></IconButton>
        <IconButton label="Next page" disabled={to >= total} onClick={() => onChange(skip + limit)} className="disabled:opacity-40"><ChevronRight size={16} /></IconButton>
      </div>
    </div>
  );
}

export function Toolbar({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cx('flex flex-wrap items-center gap-2 border-b border-line px-4 py-3', className)}>{children}</div>;
}

/* ------------------------------------------------------------------ Tabs */
export function Tabs<T extends string>({ tabs, value, onChange, className }: { tabs: { id: T; label: ReactNode; count?: number }[]; value: T; onChange: (id: T) => void; className?: string }) {
  return (
    <div role="tablist" className={cx('flex gap-5 overflow-x-auto border-b border-line', className)}>
      {tabs.map((t) => (
        <button key={t.id} role="tab" type="button" aria-selected={value === t.id} onClick={() => onChange(t.id)}
          className={cx('-mb-px whitespace-nowrap border-b-2 pb-2 pt-1 text-[13.5px] font-medium',
            value === t.id ? 'border-forest text-ink' : 'border-transparent text-muted hover:text-ink')}>
          {t.label}{t.count !== undefined && <span className="ml-1.5 text-faint tnum">{t.count}</span>}
        </button>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ Overlays */
function useEscape(onClose: () => void, open: boolean) {
  useEffect(() => {
    if (!open) return;
    const h = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', h);
    return () => document.removeEventListener('keydown', h);
  }, [open, onClose]);
}
function useFocusTrap(open: boolean) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open || !ref.current) return;
    const prev = document.activeElement as HTMLElement | null;
    const el = ref.current.querySelector<HTMLElement>('input,select,textarea,button:not([data-close])') || ref.current;
    el.focus();
    return () => prev?.focus();
  }, [open]);
  return ref;
}

export function Dialog({ open, onClose, title, description, children, footer, wide }: {
  open: boolean; onClose: () => void; title: ReactNode; description?: ReactNode; children: ReactNode; footer?: ReactNode; wide?: boolean;
}) {
  useEscape(onClose, open);
  const ref = useFocusTrap(open);
  const id = useId();
  if (!open) return null;
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center sm:p-6">
      <div className="absolute inset-0 bg-ink/30" onClick={onClose} />
      <div ref={ref} role="dialog" aria-modal="true" aria-labelledby={id} tabIndex={-1}
        className={cx('animate-in relative flex max-h-[92vh] w-full flex-col rounded-t-lg bg-surface shadow-pop sm:rounded-lg', wide ? 'sm:max-w-3xl' : 'sm:max-w-lg')}>
        <header className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
          <div><h2 id={id} className="text-[15px] font-semibold">{title}</h2>{description && <p className="mt-0.5 text-[13px] text-muted">{description}</p>}</div>
          <IconButton label="Close" data-close onClick={onClose}><X size={16} /></IconButton>
        </header>
        <div className="overflow-y-auto px-5 py-4">{children}</div>
        {footer && <footer className="flex justify-end gap-2 border-t border-line px-5 py-3">{footer}</footer>}
      </div>
    </div>, document.body);
}

export function Drawer({ open, onClose, title, subtitle, children, footer, width = 'max-w-xl' }: {
  open: boolean; onClose: () => void; title: ReactNode; subtitle?: ReactNode; children: ReactNode; footer?: ReactNode; width?: string;
}) {
  useEscape(onClose, open);
  const ref = useFocusTrap(open);
  const id = useId();
  if (!open) return null;
  return createPortal(
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-ink/25" onClick={onClose} />
      <div ref={ref} role="dialog" aria-modal="true" aria-labelledby={id} tabIndex={-1}
        className={cx('animate-in relative flex h-full w-full flex-col border-l border-line bg-surface shadow-pop', width)}>
        <header className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
          <div className="min-w-0"><h2 id={id} className="text-[16px] font-semibold">{title}</h2>{subtitle && <div className="mt-0.5 text-[13px] text-muted">{subtitle}</div>}</div>
          <IconButton label="Close" data-close onClick={onClose}><X size={16} /></IconButton>
        </header>
        <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
        {footer && <footer className="flex justify-end gap-2 border-t border-line px-5 py-3">{footer}</footer>}
      </div>
    </div>, document.body);
}

export function ConfirmDialog({ open, onClose, onConfirm, title, children, confirmLabel, danger, loading }: {
  open: boolean; onClose: () => void; onConfirm: () => void; title: string; children?: ReactNode; confirmLabel: string; danger?: boolean; loading?: boolean;
}) {
  return (
    <Dialog open={open} onClose={onClose} title={title}
      footer={<><Button onClick={onClose}>Cancel</Button><Button variant={danger ? 'danger' : 'primary'} loading={loading} onClick={onConfirm}>{confirmLabel}</Button></>}>
      <div className="text-[13.5px] text-muted">{children}</div>
    </Dialog>
  );
}

/* ------------------------------------------------------------------ Toasts */
interface Toast { id: number; message: string; tone: 'ok' | 'error' }
const ToastCtx = createContext<(m: string, tone?: 'ok' | 'error') => void>(() => {});
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const push = useCallback((message: string, tone: 'ok' | 'error' = 'ok') => {
    const id = Date.now() + Math.random();
    setItems((t) => [...t, { id, message, tone }]);
    setTimeout(() => setItems((t) => t.filter((x) => x.id !== id)), 4200);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed bottom-4 left-1/2 z-[60] flex -translate-x-1/2 flex-col items-center gap-2">
        {items.map((t) => (
          <div key={t.id} className="animate-in pointer-events-auto flex items-center gap-2 rounded-lg bg-ink px-3.5 py-2.5 text-[13px] text-paper shadow-pop">
            {t.tone === 'ok' ? <Check size={14} /> : <AlertCircle size={14} />}{t.message}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}
export const useToast = () => useContext(ToastCtx);

/* ------------------------------------------------------------------ Dropdown menu */
export function Menu({ trigger, children, align = 'right', width = 'w-56' }: { trigger: (open: boolean, toggle: () => void) => ReactNode; children: (close: () => void) => ReactNode; align?: 'left' | 'right'; width?: string }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    const k = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', h); document.addEventListener('keydown', k);
    return () => { document.removeEventListener('mousedown', h); document.removeEventListener('keydown', k); };
  }, [open]);
  return (
    <div ref={ref} className="relative">
      {trigger(open, () => setOpen((o) => !o))}
      {open && (
        <div role="menu" className={cx('animate-in absolute z-40 mt-1.5 rounded-lg border border-line bg-surface py-1 shadow-pop', width, align === 'right' ? 'right-0' : 'left-0')}>
          {children(() => setOpen(false))}
        </div>
      )}
    </div>
  );
}
export function MenuItem({ children, onClick, icon, danger }: { children: ReactNode; onClick: () => void; icon?: ReactNode; danger?: boolean }) {
  return (
    <button role="menuitem" type="button" onClick={onClick}
      className={cx('flex w-full items-center gap-2 px-3 py-1.5 text-left text-[13px] hover:bg-sunken', danger ? 'text-danger' : 'text-ink')}>
      {icon && <span className="text-muted">{icon}</span>}{children}
    </button>
  );
}

/* ------------------------------------------------------------------ Timeline */
export function Timeline({ items }: { items: { id: Key; title: ReactNode; meta?: ReactNode; body?: ReactNode; tone?: 'forest' | 'bronze' | 'muted' }[] }) {
  if (!items.length) return <EmptyState title="No activity yet" />;
  return (
    <ol className="relative ml-1.5 border-l border-line">
      {items.map((it) => (
        <li key={it.id} className="relative pb-5 pl-5 last:pb-0">
          <span className={cx('absolute -left-[4.5px] top-1.5 h-2 w-2 rounded-full ring-4 ring-surface',
            it.tone === 'bronze' ? 'bg-bronze' : it.tone === 'muted' ? 'bg-line-strong' : 'bg-forest')} />
          <div className="text-[13.5px] text-ink">{it.title}</div>
          {it.meta && <div className="text-[12px] text-faint">{it.meta}</div>}
          {it.body && <div className="mt-1 whitespace-pre-line text-[13px] text-muted">{it.body}</div>}
        </li>
      ))}
    </ol>
  );
}

/** Lightweight markdown for assistant answers and documents (bold, lists, quotes, headings, citations). */
export function RichText({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/);
  const inline = (s: string) => s.split(/(\*\*[^*]+\*\*|\[\d+\])/g).map((p, i) =>
    p.startsWith('**') ? <strong key={i}>{p.slice(2, -2)}</strong>
      : /^\[\d+\]$/.test(p) ? <sup key={i} className="ml-0.5 text-[10px] font-semibold text-forest">{p}</sup> : p.replace(/&bull;/g, '•'));
  return (
    <div className="prose-acedra text-[13.5px] leading-relaxed">
      {blocks.map((b, i) => {
        const lines = b.split('\n');
        if (lines.every((l) => /^\s*[-*•]\s/.test(l))) return <ul key={i}>{lines.map((l, j) => <li key={j}>{inline(l.replace(/^\s*[-*•]\s/, ''))}</li>)}</ul>;
        if (lines.every((l) => /^\s*\d+\.\s/.test(l))) return <ol key={i}>{lines.map((l, j) => <li key={j}>{inline(l.replace(/^\s*\d+\.\s/, ''))}</li>)}</ol>;
        if (/^#{1,4}\s/.test(lines[0])) return <div key={i}><h4>{inline(lines[0].replace(/^#+\s/, ''))}</h4>{lines.slice(1).map((l, j) => <p key={j}>{inline(l.replace(/^\s*[-*]\s/, '• '))}</p>)}</div>;
        if (lines.every((l) => l.startsWith('>'))) return <blockquote key={i}>{inline(lines.map((l) => l.replace(/^>\s?/, '')).join(' '))}</blockquote>;
        return <p key={i}>{lines.map((l, j) => <span key={j}>{inline(l.replace(/^\s*[-*]\s/, '• '))}{j < lines.length - 1 && <br />}</span>)}</p>;
      })}
    </div>
  );
}
