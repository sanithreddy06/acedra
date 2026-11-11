import { ReactNode, useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Bell, BookOpen, Briefcase, Building2, ClipboardList, FileText, FlagTriangleRight, GraduationCap, HeartHandshake,
  Inbox, KeyRound, LayoutGrid, LifeBuoy, ListChecks, LogOut, Mail, Menu as MenuIcon, MessageSquareText, Moon, ScrollText,
  Scale, Settings, ShieldCheck, Sparkles, Sun, Target, Upload, Users, X, Network, Compass, type LucideIcon,
} from 'lucide-react';
import { useAuth, Role } from '../lib/auth';
import { api } from '../lib/api';
import type { NotificationInbox } from '../types/api';
import { getTheme, setTheme } from '../lib/theme';
import { relTime, ROLE_LABEL } from '../lib/format';
import { Avatar, cx, IconButton, Menu, MenuItem } from './ui';
import { AcedraMark, AcedraWordmark, BRAND } from './brand';
import { LegalLinks } from './legal';

export { AcedraMark };


interface NavItem { to: string; label: string; icon: ReactNode; module?: string; end?: boolean; adminOnly?: boolean }
const I = (Icon: LucideIcon) => <Icon size={16} strokeWidth={1.75} />;

export function navFor(role: Role): { section?: string; items: NavItem[] }[] {
  switch (role) {
    case 'student':
      return [{ items: [
        { to: '/app', label: 'Overview', icon: I(LayoutGrid), end: true },
        { to: '/app/academics', label: 'Academics', icon: I(GraduationCap) },
        { to: '/app/support', label: 'Support & alerts', icon: I(LifeBuoy), module: 'risk_identification' },
        { to: '/app/plan', label: 'My plan', icon: I(ListChecks), module: 'recommendations' },
        { to: '/app/career', label: 'Career readiness', icon: I(Compass), module: 'placement_readiness' },
        { to: '/app/assistant', label: 'Assistant', icon: I(MessageSquareText), module: 'ai_assistant' },
      ] }];
    case 'faculty':
      return [{ items: [
        { to: '/app', label: 'Overview', icon: I(LayoutGrid), end: true },
        { to: '/app/students', label: 'My students', icon: I(Users) },
        { to: '/app/alerts', label: 'Early alerts', icon: I(FlagTriangleRight), module: 'risk_identification' },
        { to: '/app/interventions', label: 'Interventions', icon: I(HeartHandshake), module: 'interventions' },
        { to: '/app/assistant', label: 'Assistant', icon: I(MessageSquareText), module: 'ai_assistant' },
      ] }];
    case 'mentor':
      return [{ items: [
        { to: '/app', label: 'Caseload', icon: I(LayoutGrid), end: true },
        { to: '/app/students', label: 'Mentees', icon: I(Users) },
        { to: '/app/interventions', label: 'Interventions', icon: I(HeartHandshake), module: 'interventions' },
        { to: '/app/alerts', label: 'Early alerts', icon: I(FlagTriangleRight), module: 'risk_identification' },
        { to: '/app/assistant', label: 'Assistant', icon: I(MessageSquareText), module: 'ai_assistant' },
      ] }];
    case 'placement_officer':
      return [{ items: [
        { to: '/app', label: 'Overview', icon: I(LayoutGrid), end: true },
        { to: '/app/readiness', label: 'Student readiness', icon: I(Target), module: 'placement_readiness' },
        { to: '/app/opportunities', label: 'Opportunities', icon: I(Briefcase), module: 'placement_readiness' },
        { to: '/app/applications', label: 'Applications', icon: I(ClipboardList), module: 'placement_readiness' },
        { to: '/app/roles', label: 'Career roles', icon: I(Network), module: 'placement_readiness' },
        { to: '/app/assistant', label: 'Assistant', icon: I(MessageSquareText), module: 'ai_assistant' },
      ] }];
    case 'admin':
      return [
        { items: [
          { to: '/app', label: 'Overview', icon: I(LayoutGrid), end: true },
          { to: '/app/students', label: 'Students', icon: I(GraduationCap) },
          { to: '/app/alerts', label: 'Early alerts', icon: I(FlagTriangleRight), module: 'risk_identification' },
          { to: '/app/interventions', label: 'Interventions', icon: I(HeartHandshake), module: 'interventions' },
          { to: '/app/reports', label: 'Reports', icon: I(FileText) },
        ] },
        { section: 'Manage', items: [
          { to: '/app/people', label: 'People & access', icon: I(Users) },
          { to: '/app/structure', label: 'Academic structure', icon: I(Building2) },
          { to: '/app/import', label: 'Data import', icon: I(Upload) },
          { to: '/app/rules', label: 'Early-warning rules', icon: I(ShieldCheck), module: 'risk_identification' },
          { to: '/app/catalogue', label: 'Recommendation catalogue', icon: I(BookOpen), module: 'recommendations' },
          { to: '/app/documents', label: 'Knowledge base', icon: I(ScrollText), module: 'ai_assistant' },
        ] },
        { section: 'University', items: [
          { to: '/app/assistant', label: 'Assistant', icon: I(MessageSquareText), module: 'ai_assistant' },
          { to: '/app/audit', label: 'Audit log', icon: I(KeyRound) },
          { to: '/app/settings', label: 'Settings', icon: I(Settings) },
        ] },
      ];
    default:
      return [
        { items: [
          { to: '/platform', label: 'Overview', icon: I(LayoutGrid), end: true },
          { to: '/platform/enquiries', label: 'Enquiries', icon: I(Inbox) },
          { to: '/platform/universities', label: 'Universities', icon: I(Building2) },
          { to: '/platform/messages', label: 'Contact messages', icon: I(MessageSquareText) },
        ] },
        { section: 'Operations', items: [
          { to: '/platform/team', label: 'ACEDRA team', icon: I(Users) },
          { to: '/platform/audit', label: 'Audit log', icon: I(KeyRound) },
          { to: '/platform/outbox', label: 'Email outbox', icon: I(Mail), adminOnly: true },
          { to: '/platform/legal', label: 'Legal documents', icon: I(Scale) },
        ] },
      ];
  }
}

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { me, hasModule } = useAuth();
  if (!me) return null;
  const groups = navFor(me.role);
  const uni = me.university;
  return (
    <nav aria-label="Main" className="flex h-full flex-col">
      <div className="px-4 pb-4 pt-4">
        {uni ? (
          <div className="flex items-center gap-2.5">
            <AcedraMark />
            <div className="min-w-0 leading-tight">
              <div className="truncate text-[13.5px] font-semibold">{uni.short_name}</div>
              <div className="truncate text-[11.5px] text-muted">on {BRAND.name}</div>
            </div>
          </div>
        ) : (
          <div><AcedraWordmark size={22} /><div className="mt-1.5 pl-[32px] text-[11.5px] text-muted">Platform operations</div></div>
        )}
      </div>
      <div className="flex-1 space-y-5 overflow-y-auto px-2 pb-4">
        {groups.map((g, gi) => {
          const items = g.items.filter((i) => (!i.module || hasModule(i.module)) && (!i.adminOnly || me.role === 'platform_admin'));
          if (!items.length) return null;
          return (
            <div key={gi}>
              {g.section && <div className="px-2.5 pb-1 text-[11.5px] font-medium text-faint">{g.section}</div>}
              <ul className="space-y-px">
                {items.map((i) => (
                  <li key={i.to}>
                    <NavLink to={i.to} end={i.end} onClick={onNavigate}
                      className={({ isActive }) => cx('flex items-center gap-2.5 rounded px-2.5 py-[7px] text-[13.5px]',
                        isActive ? 'bg-surface text-ink font-medium shadow-hair ring-1 ring-line' : 'text-muted hover:bg-sunken hover:text-ink')}>
                      {i.icon}{i.label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
      {uni?.is_synthetic && (
        <div className="mx-3 mb-3 rounded border border-line px-3 py-2 text-[11.5px] leading-snug text-muted">
          Demonstration workspace. All records are synthetic.
        </div>
      )}
    </nav>
  );
}

function NotificationMenu() {
  const { me } = useAuth();
  const [data, setData] = useState<NotificationInbox | null>(null);
  const load = () => { if (!me?.is_platform) api.get<NotificationInbox>('/notifications', { limit: 12 }).then(setData).catch(() => {}); };
  useEffect(load, [me]);
  if (me?.is_platform) return null;
  const unread = data?.unread_count || 0;
  return (
    <Menu width="w-80" trigger={(open, toggle) => (
      <button type="button" onClick={() => { toggle(); if (!open) load(); }} aria-label={`Notifications${unread ? `, ${unread} unread` : ''}`}
        className="relative inline-flex h-8 w-8 items-center justify-center rounded text-muted hover:bg-sunken hover:text-ink">
        <Bell size={16} strokeWidth={1.75} />
        {unread > 0 && <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-bronze ring-2 ring-paper" />}
      </button>
    )}>
      {(close) => (
        <div>
          <div className="flex items-center justify-between px-3 pb-2 pt-1.5">
            <span className="text-[13px] font-semibold">Notifications</span>
            {unread > 0 && <button className="text-[12px] text-forest hover:underline" onClick={async () => { await api.put('/notifications/read-all'); load(); }}>Mark all read</button>}
          </div>
          <div className="max-h-96 overflow-y-auto border-t border-line">
            {!data?.notifications?.length && <div className="px-3 py-6 text-center text-[13px] text-muted">You're all caught up.</div>}
            {data?.notifications?.map((n) => (
              <button key={n.id} type="button" className="block w-full border-b border-line px-3 py-2.5 text-left last:border-0 hover:bg-sunken"
                onClick={async () => { if (!n.is_read) await api.put(`/notifications/${n.id}/read`).catch(() => {}); load(); close(); }}>
                <div className="flex items-start gap-2">
                  {!n.is_read && <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-bronze" />}
                  <div className="min-w-0"><div className="text-[13px] font-medium text-ink">{n.title}</div>
                    <div className="line-clamp-2 text-[12.5px] text-muted">{n.message}</div>
                    <div className="mt-0.5 text-[11.5px] text-faint">{relTime(n.created_at)}</div></div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </Menu>
  );
}

function UserMenu() {
  const { me, signOut } = useAuth();
  const nav = useNavigate();
  const [theme, setT] = useState(getTheme());
  if (!me) return null;
  return (
    <Menu width="w-64" trigger={(_, toggle) => (
      <button type="button" onClick={toggle} className="flex items-center gap-2 rounded py-1 pl-1 pr-2 hover:bg-sunken" aria-label="Account menu">
        <Avatar name={me.full_name} size={26} />
        <span className="hidden text-[13px] font-medium sm:inline">{me.full_name.replace(/\s*\[.*\]/, '')}</span>
      </button>
    )}>
      {(close) => (
        <>
          <div className="border-b border-line px-3 pb-2.5 pt-1.5">
            <div className="truncate text-[13px] font-medium">{me.full_name.replace(/\s*\[.*\]/, '')}</div>
            <div className="truncate text-[12px] text-muted">{me.email}</div>
            <div className="mt-1 text-[12px] text-faint">{ROLE_LABEL[me.role]}{me.university ? ` · ${me.university.short_name}` : ''}</div>
          </div>
          <div className="py-1">
            <MenuItem icon={theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />} onClick={() => { const t = theme === 'dark' ? 'light' : 'dark'; setTheme(t); setT(t); }}>
              {theme === 'dark' ? 'Light appearance' : 'Dark appearance'}
            </MenuItem>
            <MenuItem icon={<KeyRound size={14} />} onClick={() => { close(); nav(me.is_platform ? '/platform/account' : '/app/account'); }}>Account & password</MenuItem>
            <MenuItem icon={<LogOut size={14} />} onClick={async () => { close(); await signOut(); nav('/login'); }}>Sign out</MenuItem>
          </div>
        </>
      )}
    </Menu>
  );
}

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const loc = useLocation();
  useEffect(() => setMobileOpen(false), [loc.pathname]);
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[232px_1fr]">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-2">Skip to content</a>
      <aside className="sticky top-0 hidden h-screen border-r border-line bg-paper lg:block"><Sidebar /></aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-ink/30" onClick={() => setMobileOpen(false)} />
          <aside className="animate-in absolute inset-y-0 left-0 w-72 border-r border-line bg-paper">
            <IconButton label="Close menu" className="absolute right-2 top-3" onClick={() => setMobileOpen(false)}><X size={16} /></IconButton>
            <Sidebar onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}
      <div className="min-w-0">
        <header className="sticky top-0 z-30 flex h-12 items-center gap-2 border-b border-line bg-paper/90 px-3 backdrop-blur sm:px-5">
          <IconButton label="Open menu" className="lg:hidden" onClick={() => setMobileOpen(true)}><MenuIcon size={18} /></IconButton>
          <Breadcrumbs />
          <div className="ml-auto flex items-center gap-1"><NotificationMenu /><UserMenu /></div>
        </header>
        <main id="main" className="mx-auto w-full max-w-content px-4 pb-10 pt-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
        <footer className="mx-auto w-full max-w-content border-t border-line px-4 py-5 sm:px-6 lg:px-8"><LegalLinks /></footer>
      </div>
    </div>
  );
}

const CRUMB: Record<string, string> = {
  app: 'Home', platform: 'Platform', academics: 'Academics', support: 'Support & alerts', plan: 'My plan', career: 'Career readiness',
  assistant: 'Assistant', students: 'Students', alerts: 'Early alerts', interventions: 'Interventions', people: 'People & access',
  structure: 'Academic structure', import: 'Data import', rules: 'Early-warning rules', catalogue: 'Recommendation catalogue',
  documents: 'Knowledge base', reports: 'Reports', audit: 'Audit log', settings: 'Settings', readiness: 'Student readiness',
  opportunities: 'Opportunities', applications: 'Applications', roles: 'Career roles', enquiries: 'Enquiries',
  universities: 'Universities', team: 'ACEDRA team', outbox: 'Email outbox', account: 'Account',
  legal: 'Legal documents', messages: 'Contact messages',
};
function Breadcrumbs() {
  const parts = useLocation().pathname.split('/').filter(Boolean);
  if (parts.length <= 1) return null;
  return (
    <nav aria-label="Breadcrumb" className="min-w-0 truncate text-[13px] text-muted">
      {parts.map((p, i) => {
        const to = '/' + parts.slice(0, i + 1).join('/');
        const label = CRUMB[p] || (/^\d+$/.test(p) ? 'Detail' : p);
        const last = i === parts.length - 1;
        return (
          <span key={to}>
            {i > 0 && <span className="mx-1.5 text-faint">/</span>}
            {last ? <span className="text-ink">{label}</span> : <Link to={to} className="hover:text-ink">{label}</Link>}
          </span>
        );
      })}
    </nav>
  );
}

export function PageHeader({ title, lede, actions, meta }: { title: ReactNode; lede?: ReactNode; actions?: ReactNode; meta?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0 max-w-prose">
        {meta && <div className="mb-1.5 text-[12.5px] text-muted">{meta}</div>}
        <h1 className="page-title">{title}</h1>
        {lede && <p className="mt-1.5 text-[14px] text-muted">{lede}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export { Sparkles };
