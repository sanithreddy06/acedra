import { ReactNode, useEffect, useState } from 'react';
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis, Bar, BarChart } from 'recharts';

function readTokens() {
  const s = getComputedStyle(document.documentElement);
  const c = (n: string) => `rgb(${s.getPropertyValue(`--${n}`).trim().split(' ').join(',')})`;
  return { forest: c('forest'), olive: c('olive'), bronze: c('bronze'), line: c('line'), muted: c('muted'), ink: c('ink'), surface: c('surface') };
}
export function useChartTokens() {
  const [t, setT] = useState(readTokens);
  useEffect(() => {
    const o = new MutationObserver(() => setT(readTokens()));
    o.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => o.disconnect();
  }, []);
  return t;
}

export function ChartContainer({ title, caption, children, height = 200 }: { title?: string; caption?: ReactNode; children: ReactNode; height?: number }) {
  return (
    <figure className="min-w-0">
      {title && <figcaption className="mb-2 flex items-baseline justify-between gap-2"><span className="section-title">{title}</span>{caption && <span className="text-[12px] text-muted">{caption}</span>}</figcaption>}
      <div style={{ height }}>{children}</div>
    </figure>
  );
}

const tooltipStyle = (t: ReturnType<typeof readTokens>) => ({
  contentStyle: { background: t.surface, border: `1px solid ${t.line}`, borderRadius: 6, fontSize: 12, color: t.ink, boxShadow: 'none' },
  labelStyle: { color: t.muted, marginBottom: 2 }, cursor: { stroke: t.line },
});

export function TrendLine({ data, x, y, y2, domain, reference, referenceLabel, names }: {
  data: object[]; x: string; y: string; y2?: string; domain?: [number, number]; reference?: number; referenceLabel?: string; names?: [string, string?];
}) {
  const t = useChartTokens();
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -18 }}>
        <CartesianGrid stroke={t.line} vertical={false} />
        <XAxis dataKey={x} tick={{ fontSize: 11.5, fill: t.muted }} tickLine={false} axisLine={{ stroke: t.line }} />
        <YAxis domain={domain || ['auto', 'auto']} tick={{ fontSize: 11.5, fill: t.muted }} tickLine={false} axisLine={false} />
        <Tooltip {...tooltipStyle(t)} />
        {reference !== undefined && <ReferenceLine y={reference} stroke={t.bronze} strokeDasharray="3 3" label={{ value: referenceLabel, position: 'insideTopRight', fill: t.bronze, fontSize: 11 }} />}
        <Line type="monotone" dataKey={y} name={names?.[0] || y} stroke={t.forest} strokeWidth={2} dot={{ r: 3, fill: t.forest, strokeWidth: 0 }} activeDot={{ r: 4 }} />
        {y2 && <Line type="monotone" dataKey={y2} name={names?.[1] || y2} stroke={t.olive} strokeWidth={1.5} strokeDasharray="4 3" dot={false} />}
      </LineChart>
    </ResponsiveContainer>
  );
}

export function ColumnChart({ data, x, y, name }: { data: object[]; x: string; y: string; name?: string }) {
  const t = useChartTokens();
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
        <CartesianGrid stroke={t.line} vertical={false} />
        <XAxis dataKey={x} tick={{ fontSize: 11.5, fill: t.muted }} tickLine={false} axisLine={{ stroke: t.line }} />
        <YAxis tick={{ fontSize: 11.5, fill: t.muted }} tickLine={false} axisLine={false} allowDecimals={false} />
        <Tooltip {...tooltipStyle(t)} cursor={{ fill: t.line, opacity: 0.4 }} />
        <Bar dataKey={y} name={name || y} fill={t.forest} radius={[3, 3, 0, 0]} maxBarSize={36} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Horizontal distribution rows — clearer than a pie for a handful of buckets. */
export function Distribution({ rows, total }: { rows: { label: string; value: number; attention?: boolean }[]; total?: number }) {
  const sum = total ?? rows.reduce((a, r) => a + r.value, 0);
  return (
    <div className="space-y-2.5">
      {rows.map((r) => (
        <div key={r.label} className="grid grid-cols-[minmax(0,9rem)_1fr_2.5rem] items-center gap-3 text-[13px]">
          <span className="truncate text-muted">{r.label}</span>
          <div className="h-2 rounded-full bg-sunken"><div className={r.attention ? 'h-full rounded-full bg-bronze' : 'h-full rounded-full bg-forest'} style={{ width: `${sum ? (r.value / sum) * 100 : 0}%` }} /></div>
          <span className="text-right tnum text-ink">{r.value}</span>
        </div>
      ))}
    </div>
  );
}
