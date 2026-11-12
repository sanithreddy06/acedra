/**
 * Domain types for the ACEDRA API.
 *
 * Where the backend declares a response schema, the type is an alias of the generated OpenAPI type
 * (`src/types/openapi.ts`, regenerate with `npm run gen:api` after changing backend schemas), so the
 * frontend cannot drift from the server. A few endpoints still return plain dictionaries; their shapes
 * are written out below and mirror the builder named in each comment.
 */
import type { components } from './openapi';

type Schemas = components['schemas'];

/* ---------------------------------------------------------------- identity and tenancy */
export type UniversityRole = 'student' | 'faculty' | 'mentor' | 'admin' | 'placement_officer';
export type PlatformRole = 'platform_admin' | 'platform_employee';
export type Role = UniversityRole | PlatformRole;

export type ModuleKey =
  | 'student_intelligence' | 'risk_identification' | 'recommendations' | 'placement_readiness' | 'ai_assistant'
  | 'interventions';

/** University-configurable academic rules (`DEFAULT_ACADEMIC_STRUCTURE` in models/platform.py). */
export interface AcademicStructure {
  term_label?: string;
  terms_per_year?: number;
  programme_duration_years?: number;
  grading_scale?: string;
  cgpa_max?: number;
  pass_grade_point?: number;
  minimum_attendance_percent?: number;
  internal_assessment_max?: number;
  [key: string]: unknown;
}

/** The caller's university as embedded in `/auth/me` (AuthService.build_user_info). */
export interface University {
  id: number; name: string; short_name: string; slug: string; logo_url?: string | null; brand_color: string;
  status: string; is_synthetic: boolean; enabled_modules: string[]; academic_structure: AcademicStructure;
}

/** `/auth/me` and the `user` returned at sign-in (AuthService.build_user_info). */
export interface Me {
  id: number; email: string; full_name: string; role: Role; title?: string | null; department_id?: number | null;
  department_name?: string | null; avatar_url?: string | null; is_platform: boolean; university: University | null;
  student_id?: number; roll_number?: string; usn?: string; cgpa?: number; current_semester?: number;
  faculty_id?: number; mentor_id?: number; employee_id?: string; designation?: string | null;
}

export interface TokenResponse { access_token: string; refresh_token: string; user: Me }

/** `/auth/invitations/{token}` (AuthService.describe_invitation). */
export interface InvitationInfo { email: string; full_name?: string | null; role: Role; university_name: string; expires_at: string }

/* ---------------------------------------------------------------- public website (api/v1/public.py) */
export interface EnquiryOptions {
  institution_types: string[]; population_bands: string[]; modules: string[]; email_service_unit_cost_inr: number;
}
/** Indicative estimate for the optional assisted email service (`estimate_email_service`). */
export interface EmailServiceEstimate {
  accounts: number; unit_cost_inr_per_year: number; estimated_total_inr_per_year: number; note: string;
}
export interface EnquiryReceipt { reference: string; message: string; email_service_estimate?: EmailServiceEstimate | null }

/** Brief person reference used across platform responses (`_user_brief` in api/v1/platform.py). */
export interface UserBrief {
  id: number; full_name: string; email: string; phone?: string | null; title?: string | null; role: string;
}

/** University member as listed by `/users/` (`_user_out` in api/v1/users.py). */
export interface UniversityUser {
  id: number; email: string; full_name: string; role: UniversityRole; title?: string | null; phone?: string | null;
  department_id?: number | null; department_name?: string | null; is_active: boolean; is_verified: boolean;
  status: 'active' | 'invited' | 'disabled'; invited_at?: string | null; last_login_at?: string | null;
  is_synthetic: boolean; created_at?: string | null;
}
export interface UserList { items: UniversityUser[]; total: number; role_counts: Record<string, number> }

/* ---------------------------------------------------------------- university workspace (api/v1/tenant.py) */
export interface Domain { id?: number; domain: string; purpose: string; is_primary: boolean }

export interface TenantProfile {
  id: number; name: string; short_name: string; logo_url?: string | null; tagline?: string | null; brand_color: string;
  status: string; is_synthetic: boolean; enabled_modules: string[]; academic_structure: AcademicStructure;
  document_categories: string[];
  // Administrator-only fields:
  official_website?: string | null; location?: string | null; institution_type?: string | null;
  student_email_mode?: string | null; enforce_email_domains?: boolean; notification_settings?: Record<string, unknown>;
  domains?: Domain[]; agreement_reference?: string | null;
  acedra_contact?: { full_name: string; email: string; phone?: string | null; title?: string | null } | null;
}

export interface DepartmentSummary {
  id: number; code: string; name: string; hod_name?: string | null; description?: string | null;
  student_count?: number | null; faculty_count: number;
}

export interface MentorSummary {
  id: number; user_id: number; full_name: string; email: string; department?: string | null;
  designation?: string | null; mentee_count: number; max_mentees: number;
}

export interface StaffAccess {
  id: number; staff?: string | null; student?: string | null; student_id: number; user_id: number; reason: string;
  created_at: string;
}

export interface ProvisioningRequest {
  id: number; university_id?: number; method: string; accounts_requested: number; accounts_completed: number;
  is_chargeable: boolean; estimated_cost?: number | null; currency?: string | null; status: string;
  notes?: string | null; created_at: string;
}

/* ---------------------------------------------------------------- modules (generated) */
export type StudentProfile = Schemas['StudentProfileOut'];
export type StudentAnalytics = Schemas['StudentAnalyticsOut'];
export type FacultyAnalytics = Schemas['FacultyAnalyticsOut'];
export type AdminAnalytics = Schemas['AdminAnalyticsOut'];
export type Semester = Schemas['SemesterOut'];
export type Subject = Schemas['SubjectOut'];
export type TeachingAssignment = Schemas['FacultyCourseAssignmentOut'];
export type ImportJob = Schemas['ImportJobOut'];
export type ImportPreview = Schemas['ImportPreviewResult'];
export type AuditLogEntry = Schemas['AuditLogOut'];
export interface MessageResult { message: string }
/**
 * `/dashboards/me` (services/dashboard_service.py). The envelope is shared; `quick_stats` and `details`
 * differ by role, so pages pick the matching shape below.
 */
export type RoleDashboard<Q = Record<string, unknown>, D = Record<string, unknown>> =
  Omit<Schemas['RoleDashboardResponse'], 'quick_stats' | 'details'> & { quick_stats: Q; details: D };

export interface MentorDashboard {
  quick_stats: {
    total_mentees: number; at_risk_count: number; open_interventions: number; resolved_interventions: number;
    pending_followups_count: number; cohort_avg_cgpa: number;
  };
  details: {
    mentor_id: number | null;
    mentee_roster: { id: number; name: string; roll_number: string; usn: string; department: string; semester: number;
      cgpa: number; attendance: number; status: 'At Risk' | 'On Track' }[];
    active_interventions: { id: number; student_name: string; title: string; type: string; priority: string;
      status: string; updated_at: string }[];
    pending_followups: { id: number; intervention_id: number; intervention_title?: string | null; student_name: string; scheduled_date: string;
      status: string }[];
    mentee_risk_alerts: { id: number; student_name: string; severity: string; rule: string }[];
  };
}

export interface AdminDashboard {
  quick_stats: {
    total_users: number; total_students: number; total_departments: number;
    intervention_stats: { total: number; open: number; assigned: number; in_progress: number; resolved: number };
    recommendation_stats: { total: number; accepted: number; completed: number };
    [key: string]: unknown;
  };
  details: Record<string, unknown>;
}

export interface PlacementDashboard {
  quick_stats: {
    total_students: number; eligible_count: number; placed_count: number; conversion_rate: number;
    career_roles_count: number; opportunities_count: number; pipeline: { stage: string; count: number }[];
  };
  details: {
    roles: { id: number; title: string; category: string; min_experience_level?: string | null;
      required_skills_count: number }[];
    opportunities: { id: number; title: string; company: string; location?: string | null;
      salary_package?: string | null; application_deadline: string }[];
    eligible_roster: { id: number; name: string; usn: string; department: string; cgpa: number; status: string }[];
  };
}

export type RiskRule = Schemas['RiskRuleResponse'];
export type RiskRuleInput = Schemas['RiskRuleCreate'];
export type RiskAlert = Schemas['RiskAlertResponse'];
export type RiskAlertList = Schemas['RiskAlertListResponse'];
export type RiskStatistics = Schemas['RiskStatisticsResponse'];
export type RiskEvaluation = Schemas['RiskEvaluationResponse'];
export type StudentRiskProfile = Schemas['StudentRiskProfileResponse'];
export type RiskAlertDetail = Schemas['RiskAlertDetailResponse'];

export type Recommendation = Schemas['RecommendationOut'];
export type CatalogueItem = Schemas['CatalogueItemOut'];
export type CatalogueItemInput = Schemas['CatalogueItemCreate'];

export type CareerRole = Schemas['CareerRoleResponse'];
export type PlacementReadiness = Schemas['PlacementReadinessResponse'];
export type SkillGap = Schemas['SkillGapItem'];
export type Opportunity = Schemas['PlacementOpportunityResponse'];
export type OpportunityMatch = Schemas['OpportunityMatchForStudent'];
export type Application = Schemas['StudentApplicationResponse'];

export type Conversation = Schemas['ConversationResponse'];
export type ConversationDetail = Schemas['ConversationDetailResponse'];
export type ChatMessage = Schemas['MessageResponse'];
export type SourceCitation = Schemas['SourceCitation'];
export type SuggestedQuestion = Schemas['SuggestedQuestion'];
export type AssistantDocument = Schemas['DocumentResponse'];
/** `/ai/rag/search` (retrieval check for administrators). */
export interface RetrievalResult {
  query: string; role_evaluated: string; results_count: number;
  results: { score: number; document_title: string; category?: string | null;
    chunk: { id: number; document_id: number; content: string; section_heading?: string | null; page_number?: number | null } }[];
}
/** `/ai/status`. */
export interface AssistantStatus {
  llm_provider: string; llm_model?: string | null; llm_configured: boolean; retrieval: string;
  semantic_retrieval: boolean; personal_mode_available: boolean;
}

/** `/notifications` (api/v1/interventions.py). */
export interface AppNotification {
  id: number; user_id: number; title: string; message: string; notification_type: string; severity?: string | null;
  reference_id?: number | null; reference_type?: string | null; action_url?: string | null; is_read: boolean;
  read_at?: string | null; created_at: string;
}
export interface NotificationInbox { notifications: AppNotification[]; unread_count: number }

export type Intervention = Schemas['InterventionResponse'];
export type InterventionDetail = Schemas['InterventionDetailResponse'];
export type ReportExport = Schemas['ReportExportResponse'];

/* ---------------------------------------------------------------- platform workspace (api/v1/platform.py) */
export interface EnquiryActivity {
  id: number; kind: string; from_status?: string | null; to_status?: string | null; body: string;
  meeting_at?: string | null; author?: UserBrief | null; created_at: string;
}

/** `_enquiry_out` (list rows). */
export interface Enquiry {
  id: number; reference: string; status: string; status_label?: string | null; university_name: string;
  institution_type?: string | null; location?: string | null; student_population?: string | null;
  contact_name: string; contact_designation?: string | null; contact_email: string; requested_modules: string[];
  email_provisioning?: string | null; owner?: UserBrief | null; university_id?: number | null;
  created_at: string; updated_at?: string | null;
}

/** `_enquiry_out(full=True)` (detail view). */
export interface EnquiryDetail extends Enquiry {
  official_website?: string | null; department_count?: number | null; campus_count?: number | null;
  contact_phone?: string | null; preferred_contact_method?: string | null; existing_sis?: string | null;
  existing_academic_systems?: string | null; has_student_emails?: boolean | null; accounts_required?: number | null;
  institutional_requirements?: string | null; expected_outcomes?: string | null; additional_information?: string | null;
  finalized_requirements?: string | null; agreement_reference?: string | null; agreement_recorded_at?: string | null;
  agreed_modules: string[]; email_service_estimate?: EmailServiceEstimate | null; activities: EnquiryActivity[];
}
export interface EnquiryList { items: Enquiry[]; total: number; statuses: Record<string, string> }

export interface EmployeeAssignment {
  id: number; employee?: UserBrief | null; assignment_role: string; is_active: boolean; started_at?: string | null;
  ended_at?: string | null; notes?: string | null;
}

/** Onboarding checklist (`PlatformService.readiness`); activation requires every check done. */
export interface OnboardingReadiness { checks: { key: string; label: string; done: boolean }[]; ready: boolean }

/** `_university_out` (list rows and overview cards). */
export interface UniversitySummary {
  id: number; name: string; short_name: string; slug: string; status: string; location?: string | null;
  institution_type?: string | null; is_synthetic: boolean; brand_color: string; logo_url?: string | null;
  enabled_modules: string[]; primary_employee?: UserBrief | null; activated_at?: string | null; created_at: string;
  domains: Domain[];
}

/** `_university_out(full=True)` (detail view). */
export interface UniversityDetail extends UniversitySummary {
  official_website?: string | null; tagline?: string | null; academic_structure: AcademicStructure;
  document_categories: string[]; notification_settings: Record<string, unknown>; enforce_email_domains: boolean;
  student_email_mode?: string | null; agreement_reference?: string | null; enquiry_id?: number | null;
  user_counts: Record<string, number>; readiness: OnboardingReadiness; assignments: EmployeeAssignment[];
  admins: (UserBrief & { is_verified: boolean; is_active: boolean })[];
}

/** `_employee_out`. */
export interface PlatformEmployee extends UserBrief {
  is_active: boolean; is_verified: boolean; employee_code?: string | null; permissions: string[];
  assignments: { university_id: number; university: string; assignment_role: string }[];
}

export interface DataAccessGrant {
  id: number; employee?: UserBrief | null; scope: string; reason: string; university_authorised_by: string;
  starts_at: string; expires_at: string; revoked_at?: string | null; is_active: boolean;
}

/** Grant-checked, audited minimal directory (`granted_student_directory`). */
export interface StudentDirectory {
  grant_expires_at: string;
  students: { id: number; full_name: string; usn: string; department: string; semester: number; status: string }[];
}

export interface PlatformOverview {
  enquiries_by_status: Record<string, number>; open_enquiries: number; tenants_by_status: Record<string, number>;
  my_universities: UniversitySummary[]; recent_enquiries: Enquiry[]; pending_provisioning: number;
  email_provider: string;
}

export interface OutboxMessage {
  id: number; to_email: string; subject: string; template: string; status: string; provider: string;
  body_text?: string | null; created_at: string;
}
export interface Outbox { provider: string; bodies_visible: boolean; items: OutboxMessage[] }

export interface PlatformAuditEntry {
  id: number; action: string; resource_type?: string | null; resource_id?: string | null; university?: string | null;
  actor?: string | null; ip_address?: string | null; details?: Record<string, unknown> | null; created_at: string;
}
export interface PlatformAuditList { total: number; items: PlatformAuditEntry[] }

/* ---------------------------------------------------------------- legal documents and contact */
export type LegalDocType = 'terms' | 'privacy' | 'cookies';
export type LegalDocumentSummary = Schemas['LegalDocumentSummary'];
export type LegalDocument = Schemas['LegalDocumentOut'];
export type LegalDocumentAdmin = Schemas['LegalDocumentAdminOut'];
export type LegalStatus = Schemas['LegalStatusOut'];
export type ContactMessage = Schemas['ContactMessageOut'];
