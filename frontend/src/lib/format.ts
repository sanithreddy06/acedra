export const fmtDate = (v?: string | null, withTime = false) => {
  if (!v) return '—';
  const d = new Date(v.endsWith('Z') || v.includes('+') ? v : v + (v.length > 10 ? 'Z' : ''));
  if (isNaN(d.getTime())) return v;
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', ...(withTime ? { hour: '2-digit', minute: '2-digit' } : {}) });
};
export const relTime = (v?: string | null) => {
  if (!v) return '';
  const d = new Date(v.endsWith('Z') || v.includes('+') ? v : v + 'Z');
  const s = (Date.now() - d.getTime()) / 1000;
  if (s < 60) return 'just now';
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  if (s < 86400 * 7) return `${Math.floor(s / 86400)} d ago`;
  return fmtDate(v);
};
type Numeric = number | string | null | undefined;
export const num = (v: Numeric, digits = 1) => (v === null || v === undefined || v === '' || isNaN(Number(v)) ? '—' : Number(v).toFixed(digits));
/** True only for a recorded value below the limit (missing values are never flagged). */
export const isBelow = (v: number | null | undefined, limit: number) => v !== null && v !== undefined && v < limit;
export const pct = (v: Numeric, digits = 0) => (v === null || v === undefined || isNaN(Number(v)) ? '—' : `${Number(v).toFixed(digits)}%`);
export const titleCase = (s?: string | null) => (s || '').toLowerCase().replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase());
export const initials = (name?: string) => (name || '?').replace(/\[.*?\]/g, '').trim().split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]).join('').toUpperCase();
export const cleanName = (name?: string | null) => (name || '').replace(/\s*\[Synthetic Demo\]\s*/g, '').trim();

export const MODULES: Record<string, { name: string; short: string; summary: string }> = {
  student_intelligence: { name: 'Student intelligence & analytics', short: 'Student intelligence', summary: 'Academic records, attendance, assessments and trends in one place.' },
  risk_identification: { name: 'Early-warning risk identification', short: 'Early warning', summary: 'Configurable, explainable rules that flag students who may need support.' },
  recommendations: { name: 'Personalised recommendations', short: 'Recommendations', summary: 'Improvement plans grounded in each student’s record and your catalogue.' },
  placement_readiness: { name: 'Skill gap & placement readiness', short: 'Placement readiness', summary: 'Explainable readiness against career roles, opportunities and applications.' },
  ai_assistant: { name: 'University AI assistant', short: 'AI assistant', summary: 'Answers grounded in your approved documents, with citations.' },
  interventions: { name: 'Dashboards & intervention tracking', short: 'Interventions', summary: 'Mentor follow-ups, outcomes and reports connected to every alert.' },
};

export const ROLE_LABEL: Record<string, string> = {
  student: 'Student', faculty: 'Faculty', mentor: 'Mentor', admin: 'University administrator',
  placement_officer: 'Placement officer', platform_admin: 'ACEDRA super administrator', platform_employee: 'ACEDRA employee',
};
