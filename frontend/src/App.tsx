import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { homeFor, Role, useAuth } from './lib/auth';
import { AppShell } from './components/shell';
import { AcedraMark } from './components/brand';
import { LoadingBlock } from './components/ui';
import { AcceptInvitationPage, EnquiryPage, ForgotPasswordPage, HomePage, LoginPage, NotFoundPage, ResetPasswordPage } from './pages/public';
import { Forbidden, ModuleGate } from './components/access';
import { CookieConsent, LegalAcceptanceGate } from './components/legal';

/**
 * Workspace pages are split into one chunk per page module and loaded on first visit, so the public
 * website and sign-in page don't download every role's workspace (or the charting library).
 */
const studentPages = () => import('./pages/student');
const staffPages = () => import('./pages/staff');
const rolePages = () => import('./pages/roles');
const adminPages = () => import('./pages/admin');
const platformPages = () => import('./pages/platform');
const commonPages = () => import('./pages/common');
const sitePages = () => import('./pages/site');
const legalAdminPages = () => import('./pages/legalAdmin');

const StudentOverview = lazy(() => studentPages().then((m) => ({ default: m.StudentOverview })));
const StudentAcademics = lazy(() => studentPages().then((m) => ({ default: m.StudentAcademics })));
const StudentSupport = lazy(() => studentPages().then((m) => ({ default: m.StudentSupport })));
const StudentPlan = lazy(() => studentPages().then((m) => ({ default: m.StudentPlan })));
const StudentCareer = lazy(() => studentPages().then((m) => ({ default: m.StudentCareer })));
const StudentsPage = lazy(() => staffPages().then((m) => ({ default: m.StudentsPage })));
const StudentDetailPage = lazy(() => staffPages().then((m) => ({ default: m.StudentDetailPage })));
const AlertsPage = lazy(() => staffPages().then((m) => ({ default: m.AlertsPage })));
const InterventionsPage = lazy(() => staffPages().then((m) => ({ default: m.InterventionsPage })));
const FacultyOverview = lazy(() => rolePages().then((m) => ({ default: m.FacultyOverview })));
const MentorOverview = lazy(() => rolePages().then((m) => ({ default: m.MentorOverview })));
const AdminOverview = lazy(() => rolePages().then((m) => ({ default: m.AdminOverview })));
const PlacementOverview = lazy(() => rolePages().then((m) => ({ default: m.PlacementOverview })));
const PlacementReadinessPage = lazy(() => rolePages().then((m) => ({ default: m.PlacementReadinessPage })));
const OpportunitiesPage = lazy(() => rolePages().then((m) => ({ default: m.OpportunitiesPage })));
const ApplicationsPage = lazy(() => rolePages().then((m) => ({ default: m.ApplicationsPage })));
const CareerRolesPage = lazy(() => rolePages().then((m) => ({ default: m.CareerRolesPage })));
const PeoplePage = lazy(() => adminPages().then((m) => ({ default: m.PeoplePage })));
const StructurePage = lazy(() => adminPages().then((m) => ({ default: m.StructurePage })));
const ImportPage = lazy(() => adminPages().then((m) => ({ default: m.ImportPage })));
const RulesPage = lazy(() => adminPages().then((m) => ({ default: m.RulesPage })));
const CataloguePage = lazy(() => adminPages().then((m) => ({ default: m.CataloguePage })));
const DocumentsPage = lazy(() => adminPages().then((m) => ({ default: m.DocumentsPage })));
const ReportsPage = lazy(() => adminPages().then((m) => ({ default: m.ReportsPage })));
const AuditPage = lazy(() => adminPages().then((m) => ({ default: m.AuditPage })));
const SettingsPage = lazy(() => adminPages().then((m) => ({ default: m.SettingsPage })));
const PlatformOverview = lazy(() => platformPages().then((m) => ({ default: m.PlatformOverview })));
const EnquiriesPage = lazy(() => platformPages().then((m) => ({ default: m.EnquiriesPage })));
const EnquiryDetailPage = lazy(() => platformPages().then((m) => ({ default: m.EnquiryDetailPage })));
const UniversitiesPage = lazy(() => platformPages().then((m) => ({ default: m.UniversitiesPage })));
const UniversityDetailPage = lazy(() => platformPages().then((m) => ({ default: m.UniversityDetailPage })));
const TeamPage = lazy(() => platformPages().then((m) => ({ default: m.TeamPage })));
const OutboxPage = lazy(() => platformPages().then((m) => ({ default: m.OutboxPage })));
const AboutPage = lazy(() => sitePages().then((m) => ({ default: m.AboutPage })));
const SolutionsPage = lazy(() => sitePages().then((m) => ({ default: m.SolutionsPage })));
const ContactPage = lazy(() => sitePages().then((m) => ({ default: m.ContactPage })));
const FaqPage = lazy(() => sitePages().then((m) => ({ default: m.FaqPage })));
const SecurityPage = lazy(() => sitePages().then((m) => ({ default: m.SecurityPage })));
const AccessibilityPage = lazy(() => sitePages().then((m) => ({ default: m.AccessibilityPage })));
const LegalDocumentPage = lazy(() => sitePages().then((m) => ({ default: m.LegalDocumentPage })));
const LegalAdminPage = lazy(() => legalAdminPages().then((m) => ({ default: m.LegalAdminPage })));
const ContactMessagesPage = lazy(() => legalAdminPages().then((m) => ({ default: m.ContactMessagesPage })));
const AccountPage = lazy(() => commonPages().then((m) => ({ default: m.AccountPage })));
const AssistantPage = lazy(() => commonPages().then((m) => ({ default: m.AssistantPage })));

const UNI: Role[] = ['student', 'faculty', 'mentor', 'admin', 'placement_officer'];
const PLATFORM: Role[] = ['platform_admin', 'platform_employee'];

function RequireAuth({ roles, children }: { roles: Role[]; children: JSX.Element }) {
  const { me, ready } = useAuth();
  const loc = useLocation();
  if (!ready) return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4" aria-busy="true" aria-label="Loading ACEDRA">
      <AcedraMark size={36} className="animate-pulse" />
      <div className="w-48"><LoadingBlock rows={2} /></div>
    </div>
  );
  if (!me) return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  if (!roles.includes(me.role)) return <Navigate to={homeFor(me.role)} replace />;
  return <LegalAcceptanceGate>{children}</LegalAcceptanceGate>;
}

/** Route-level role check. The server enforces the same rules; this only keeps navigation honest. */
function Only({ roles, children }: { roles: Role[]; children: JSX.Element }) {
  const { me } = useAuth();
  return me && roles.includes(me.role) ? children : <Forbidden />;
}

function UniversityHome() {
  const { me } = useAuth();
  switch (me?.role) {
    case 'student': return <StudentOverview />;
    case 'faculty': return <FacultyOverview />;
    case 'mentor': return <MentorOverview />;
    case 'placement_officer': return <PlacementOverview />;
    default: return <AdminOverview />;
  }
}

const STAFF: Role[] = ['faculty', 'mentor', 'admin', 'placement_officer'];

export default function App() {
  return (
    <>
    <Suspense fallback={<div className="mx-auto max-w-5xl p-6" aria-busy="true"><LoadingBlock rows={4} /></div>}>
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/enquire" element={<EnquiryPage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/solutions" element={<SolutionsPage />} />
      <Route path="/contact" element={<ContactPage />} />
      <Route path="/faq" element={<FaqPage />} />
      <Route path="/security" element={<SecurityPage />} />
      <Route path="/accessibility" element={<AccessibilityPage />} />
      <Route path="/legal" element={<Navigate to="/legal/terms" replace />} />
      <Route path="/legal/:type" element={<LegalDocumentPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/accept-invitation" element={<AcceptInvitationPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />

      <Route path="/app" element={<RequireAuth roles={UNI}><AppShell /></RequireAuth>}>
        <Route index element={<UniversityHome />} />
        <Route path="academics" element={<Only roles={['student']}><StudentAcademics /></Only>} />
        <Route path="support" element={<Only roles={['student']}><ModuleGate module="risk_identification" name="Early warning"><StudentSupport /></ModuleGate></Only>} />
        <Route path="plan" element={<Only roles={['student']}><ModuleGate module="recommendations" name="Recommendations"><StudentPlan /></ModuleGate></Only>} />
        <Route path="career" element={<Only roles={['student']}><ModuleGate module="placement_readiness" name="Placement readiness"><StudentCareer /></ModuleGate></Only>} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="account" element={<AccountPage />} />

        <Route path="students" element={<Only roles={STAFF}><StudentsPage /></Only>} />
        <Route path="students/:id" element={<Only roles={STAFF}><StudentDetailPage /></Only>} />
        <Route path="alerts" element={<Only roles={['faculty', 'mentor', 'admin']}><ModuleGate module="risk_identification" name="Early warning"><AlertsPage /></ModuleGate></Only>} />
        <Route path="interventions" element={<Only roles={['faculty', 'mentor', 'admin']}><ModuleGate module="interventions" name="Interventions"><InterventionsPage /></ModuleGate></Only>} />

        <Route path="people" element={<Only roles={['admin']}><PeoplePage /></Only>} />
        <Route path="structure" element={<Only roles={['admin']}><StructurePage /></Only>} />
        <Route path="import" element={<Only roles={['admin']}><ImportPage /></Only>} />
        <Route path="rules" element={<Only roles={['admin']}><ModuleGate module="risk_identification" name="Early warning"><RulesPage /></ModuleGate></Only>} />
        <Route path="catalogue" element={<Only roles={['admin']}><ModuleGate module="recommendations" name="Recommendations"><CataloguePage /></ModuleGate></Only>} />
        <Route path="documents" element={<Only roles={['admin']}><ModuleGate module="ai_assistant" name="The assistant"><DocumentsPage /></ModuleGate></Only>} />
        <Route path="reports" element={<Only roles={['admin']}><ReportsPage /></Only>} />
        <Route path="audit" element={<Only roles={['admin']}><AuditPage /></Only>} />
        <Route path="settings" element={<Only roles={['admin']}><SettingsPage /></Only>} />

        <Route path="readiness" element={<Only roles={['placement_officer', 'admin']}><ModuleGate module="placement_readiness" name="Placement readiness"><PlacementReadinessPage /></ModuleGate></Only>} />
        <Route path="opportunities" element={<Only roles={['placement_officer', 'admin']}><ModuleGate module="placement_readiness" name="Placement readiness"><OpportunitiesPage /></ModuleGate></Only>} />
        <Route path="applications" element={<Only roles={['placement_officer', 'admin']}><ModuleGate module="placement_readiness" name="Placement readiness"><ApplicationsPage /></ModuleGate></Only>} />
        <Route path="roles" element={<Only roles={['placement_officer', 'admin']}><ModuleGate module="placement_readiness" name="Placement readiness"><CareerRolesPage /></ModuleGate></Only>} />
        <Route path="*" element={<Forbidden />} />
      </Route>

      <Route path="/platform" element={<RequireAuth roles={PLATFORM}><AppShell /></RequireAuth>}>
        <Route index element={<PlatformOverview />} />
        <Route path="enquiries" element={<EnquiriesPage />} />
        <Route path="enquiries/:id" element={<EnquiryDetailPage />} />
        <Route path="universities" element={<UniversitiesPage />} />
        <Route path="universities/:id" element={<UniversityDetailPage />} />
        <Route path="team" element={<TeamPage />} />
        <Route path="audit" element={<AuditPage platform />} />
        <Route path="outbox" element={<Only roles={['platform_admin']}><OutboxPage /></Only>} />
        <Route path="legal" element={<LegalAdminPage />} />
        <Route path="messages" element={<ContactMessagesPage />} />
        <Route path="account" element={<AccountPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
    </Suspense>
    <CookieConsent />
    </>
  );
}
