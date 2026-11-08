import { User, RoleDashboardData, Department, AuditLog, SystemSetting } from '../types';

const API_BASE = '/api/v1';

class ApiClient {
  private getHeaders(): HeadersInit {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (response.status === 401) {
      if (!response.url.includes('/auth/login')) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        window.location.href = '/login';
      }
    }
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || data.detail || 'An unexpected error occurred');
    }
    return data as T;
  }

  // --- Auth ---
  async login(email: string, password: string): Promise<{ access_token: string; refresh_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return this.handleResponse(res);
  }

  async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: this.getHeaders(),
      });
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');
    }
  }

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getMyDashboard(): Promise<RoleDashboardData> {
    const res = await fetch(`${API_BASE}/dashboards/me`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  // --- Users & Departments ---
  async getUsers(role?: string): Promise<User[]> {
    const url = role ? `${API_BASE}/users/?role=${role}` : `${API_BASE}/users/`;
    const res = await fetch(url, { headers: this.getHeaders() });
    return this.handleResponse(res);
  }

  async createUser(userData: any): Promise<User> {
    const res = await fetch(`${API_BASE}/users/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(userData),
    });
    return this.handleResponse(res);
  }

  async getDepartments(): Promise<Department[]> {
    const res = await fetch(`${API_BASE}/departments/`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getAuditLogs(limit = 50): Promise<AuditLog[]> {
    const res = await fetch(`${API_BASE}/audit-logs/?limit=${limit}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getSystemSettings(): Promise<SystemSetting[]> {
    const res = await fetch(`${API_BASE}/settings/`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  // --- Password Reset ---
  async requestPasswordReset(email: string): Promise<{ message: string; reset_token?: string }> {
    const res = await fetch(`${API_BASE}/auth/password-reset-request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    return this.handleResponse(res);
  }

  async confirmPasswordReset(token: string, new_password: string): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE}/auth/password-reset-confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, new_password }),
    });
    return this.handleResponse(res);
  }

  // ==========================================
  // MODULE 1: Student Intelligence & Analytics
  // ==========================================

  async getStudents(params: {
    skip?: number;
    limit?: number;
    search?: string;
    department_id?: number;
    semester?: number;
    section?: string;
    status?: string;
  } = {}): Promise<any[]> {
    const query = new URLSearchParams();
    if (params.skip !== undefined) query.set('skip', params.skip.toString());
    if (params.limit !== undefined) query.set('limit', params.limit.toString());
    if (params.search) query.set('search', params.search);
    if (params.department_id) query.set('department_id', params.department_id.toString());
    if (params.semester) query.set('semester', params.semester.toString());
    if (params.section) query.set('section', params.section);
    if (params.status && params.status !== 'all') query.set('status', params.status);

    const res = await fetch(`${API_BASE}/students/?${query.toString()}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getStudentById(studentId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/students/${studentId}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async createStudent(studentData: any): Promise<any> {
    const res = await fetch(`${API_BASE}/students/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(studentData),
    });
    return this.handleResponse(res);
  }

  async updateStudent(studentId: number, studentData: any): Promise<any> {
    const res = await fetch(`${API_BASE}/students/${studentId}`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(studentData),
    });
    return this.handleResponse(res);
  }

  async getStudentAnalytics(studentId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/students/${studentId}/analytics`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async addStudentSkill(studentId: number, skillData: { skill_name: string; category: string; proficiency_level: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/students/${studentId}/skills`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(skillData),
    });
    return this.handleResponse(res);
  }

  async addStudentCertification(studentId: number, certData: any): Promise<any> {
    const res = await fetch(`${API_BASE}/students/${studentId}/certifications`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(certData),
    });
    return this.handleResponse(res);
  }

  async addStudentProject(studentId: number, projectData: any): Promise<any> {
    const res = await fetch(`${API_BASE}/students/${studentId}/projects`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(projectData),
    });
    return this.handleResponse(res);
  }

  async addStudentInternship(studentId: number, internData: any): Promise<any> {
    const res = await fetch(`${API_BASE}/students/${studentId}/internships`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(internData),
    });
    return this.handleResponse(res);
  }

  async getFacultyAnalytics(): Promise<any> {
    const res = await fetch(`${API_BASE}/students/analytics/faculty`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getAdminAnalytics(): Promise<any> {
    const res = await fetch(`${API_BASE}/students/analytics/admin`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  // --- Data Import Center ---
  async previewImport(file: File, importType: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('import_type', importType);

    const token = localStorage.getItem('access_token');
    const res = await fetch(`${API_BASE}/imports/preview`, {
      method: 'POST',
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: formData,
    });
    return this.handleResponse(res);
  }

  async executeImport(file: File, importType: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('import_type', importType);

    const token = localStorage.getItem('access_token');
    const res = await fetch(`${API_BASE}/imports/execute`, {
      method: 'POST',
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: formData,
    });
    return this.handleResponse(res);
  }

  async downloadTemplate(templateType: string): Promise<Blob> {
    const token = localStorage.getItem('access_token');
    const res = await fetch(`${API_BASE}/imports/template/${templateType}`, {
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    });
    if (!res.ok) throw new Error('Failed to download template');
    return res.blob();
  }

  async getImportJobs(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/imports/jobs`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  // --- MODULE 2: Risk Intelligence & Early Warning ---
  async getRiskRules(category?: string, isActive?: boolean): Promise<any[]> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (isActive !== undefined) params.append('is_active', String(isActive));
    const res = await fetch(`${API_BASE}/risk/rules?${params.toString()}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async createRiskRule(data: any): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/rules`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async updateRiskRule(id: number, data: any): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/rules/${id}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async deleteRiskRule(id: number): Promise<void> {
    const res = await fetch(`${API_BASE}/risk/rules/${id}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to delete rule');
  }

  async triggerRiskEvaluation(studentId?: number, departmentId?: number): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/evaluate`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ student_id: studentId, department_id: departmentId }),
    });
    return this.handleResponse(res);
  }

  async getRiskAlerts(params: Record<string, any> = {}): Promise<{ items: any[]; total: number; skip: number; limit: number }> {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, String(v));
    });
    const res = await fetch(`${API_BASE}/risk/alerts?${query.toString()}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getRiskAlertDetail(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/alerts/${id}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async acknowledgeAlert(id: number, notes?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/alerts/${id}/acknowledge`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ notes }),
    });
    return this.handleResponse(res);
  }

  async addAlertNote(id: number, notes: string): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/alerts/${id}/notes`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ notes }),
    });
    return this.handleResponse(res);
  }

  async assignAlertMentor(id: number, mentorId: number, notes?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/alerts/${id}/assign`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ mentor_id: mentorId, notes }),
    });
    return this.handleResponse(res);
  }

  async resolveAlert(id: number, resolutionReason: string, reviewNotes?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/alerts/${id}/resolve`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ resolution_reason: resolutionReason, review_notes: reviewNotes }),
    });
    return this.handleResponse(res);
  }

  async reopenAlert(id: number, reason: string): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/alerts/${id}/reopen`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ reason }),
    });
    return this.handleResponse(res);
  }

  async getRiskStatistics(departmentId?: number): Promise<any> {
    const params = new URLSearchParams();
    if (departmentId) params.append('department_id', String(departmentId));
    const res = await fetch(`${API_BASE}/risk/statistics?${params.toString()}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getStudentRiskProfile(studentId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/students/${studentId}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getNotifications(unreadOnly: boolean = false): Promise<any[]> {
    const res = await fetch(`${API_BASE}/risk/notifications?unread_only=${unreadOnly}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async markNotificationRead(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/notifications/${id}/read`, {
      method: 'PUT',
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  // --- MODULE 3: Personalized Recommendation Engine ---
  async getRecommendationCatalogue(params: Record<string, any> = {}): Promise<any[]> {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, String(v));
    });
    const res = await fetch(`${API_BASE}/recommendations/catalogue?${query.toString()}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async createCatalogueItem(data: any): Promise<any> {
    const res = await fetch(`${API_BASE}/recommendations/catalogue`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async updateCatalogueItem(id: number, data: any): Promise<any> {
    const res = await fetch(`${API_BASE}/recommendations/catalogue/${id}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async deleteCatalogueItem(id: number): Promise<void> {
    const res = await fetch(`${API_BASE}/recommendations/catalogue/${id}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to delete catalogue item');
  }

  async generateRecommendations(studentId: number, force: boolean = false): Promise<any[]> {
    const res = await fetch(`${API_BASE}/recommendations/generate/${studentId}?force_regenerate=${force}`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getRecommendations(params: Record<string, any> = {}): Promise<any[]> {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, String(v));
    });
    const res = await fetch(`${API_BASE}/recommendations/?${query.toString()}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getStudentLearningPath(studentId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/recommendations/students/${studentId}/learning-path`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async updateStudentCareerProfile(studentId: number, data: { career_goals: string[]; interests: string[] }): Promise<any> {
    const res = await fetch(`${API_BASE}/recommendations/students/${studentId}/career-profile`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async acceptRecommendation(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/recommendations/${id}/accept`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async rejectRecommendation(id: number, reason: string): Promise<any> {
    const res = await fetch(`${API_BASE}/recommendations/${id}/reject`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ rejection_reason: reason }),
    });
    return this.handleResponse(res);
  }

  async updateRecommendationProgress(id: number, data: { status: string; percent_complete: number; notes?: string; hours_spent?: number }): Promise<any> {
    const res = await fetch(`${API_BASE}/recommendations/${id}/progress`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async submitRecommendationFeedback(id: number, data: { rating: number; helpful: boolean; relevance_score: number; comments?: string; outcome_achieved: boolean }): Promise<any> {
    const res = await fetch(`${API_BASE}/recommendations/${id}/feedback`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async suggestMentorRecommendation(data: any): Promise<any> {
    const res = await fetch(`${API_BASE}/recommendations/suggest`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async addMentorGuidance(id: number, notes: string): Promise<any> {
    const res = await fetch(`${API_BASE}/recommendations/${id}/guidance`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ guidance_notes: notes }),
    });
    return this.handleResponse(res);
  }

  // --- MODULE 4: Skill Gap & Placement Readiness ---
  async getPlacementSkills(category?: string): Promise<any[]> {
    const query = category ? `?category=${encodeURIComponent(category)}` : '';
    const res = await fetch(`${API_BASE}/placement/skills${query}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getStudentPlacementSkills(studentId: number): Promise<any[]> {
    const res = await fetch(`${API_BASE}/placement/students/${studentId}/skills`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async addOrUpdateStudentPlacementSkill(studentId: number, data: any): Promise<any> {
    const res = await fetch(`${API_BASE}/placement/students/${studentId}/skills`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async submitSkillEvidence(studentId: number, data: any): Promise<any> {
    const res = await fetch(`${API_BASE}/placement/students/${studentId}/evidence`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async verifySkillEvidence(evidenceId: number, data: { verification_status: string; verification_feedback?: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/placement/evidence/${evidenceId}/verify`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async getCareerRoles(isActive?: boolean): Promise<any[]> {
    const query = isActive !== undefined ? `?is_active=${isActive}` : '';
    const res = await fetch(`${API_BASE}/placement/roles${query}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async createCareerRole(data: any): Promise<any> {
    const res = await fetch(`${API_BASE}/placement/roles`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async getPlacementReadiness(studentId: number, role?: string): Promise<any> {
    const query = role ? `?role=${encodeURIComponent(role)}` : '';
    const res = await fetch(`${API_BASE}/placement/readiness/${studentId}${query}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getPlacementOpportunities(params: Record<string, any> = {}): Promise<any[]> {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, String(v));
    });
    const res = await fetch(`${API_BASE}/placement/opportunities?${query.toString()}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async createPlacementOpportunity(data: any): Promise<any> {
    const res = await fetch(`${API_BASE}/placement/opportunities`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async getStudentMatchingOpportunities(studentId: number): Promise<any[]> {
    const res = await fetch(`${API_BASE}/placement/students/${studentId}/matching-opportunities`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async applyToOpportunity(data: { opportunity_id: number; resume_url?: string; cover_notes?: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/placement/applications`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async getPlacementApplications(params: Record<string, any> = {}): Promise<any[]> {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, String(v));
    });
    const res = await fetch(`${API_BASE}/placement/applications?${query.toString()}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async updatePlacementApplicationStatus(applicationId: number, data: { status: string; reviewer_notes?: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/placement/applications/${applicationId}/status`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  // =========================================================================
  // --- Module 5: Conversational AI & RAG Knowledge Base ---
  // =========================================================================

  async getSuggestedQuestions(mode: string = 'PUBLIC_MODE_A'): Promise<any[]> {
    const res = await fetch(`${API_BASE}/ai/suggested-questions?mode=${mode}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async createAIConversation(payload: { mode: string; title?: string; session_id?: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/conversations`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    return this.handleResponse(res);
  }

  async getAIConversations(sessionId?: string): Promise<any[]> {
    const query = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    const res = await fetch(`${API_BASE}/ai/conversations${query}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getAIConversation(conversationId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/conversations/${conversationId}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async deleteAIConversation(conversationId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/conversations/${conversationId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async sendAIMessage(conversationId: number, content: string, studentId?: number): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ content, student_id: studentId }),
    });
    return this.handleResponse(res);
  }

  async submitMessageFeedback(messageId: number, isHelpful: boolean, feedbackText?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/messages/${messageId}/feedback`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ is_helpful: isHelpful, feedback_text: feedbackText }),
    });
    return this.handleResponse(res);
  }

  async getRAGDocuments(category?: string, search?: string): Promise<any[]> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (search) params.append('search', search);
    const query = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/ai/documents${query}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async getDocumentDetails(documentId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/documents/${documentId}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async uploadRAGDocument(formData: FormData): Promise<any> {
    const token = localStorage.getItem('access_token');
    const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/ai/documents/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });
    return this.handleResponse(res);
  }

  async createTextDocument(data: { title: string; category: string; description?: string; access_permission: string; content_raw: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/documents/text`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse(res);
  }

  async reindexRAGDocument(documentId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/documents/${documentId}/reindex`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async deleteRAGDocument(documentId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/documents/${documentId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async searchRAG(query: string, topK: number = 4): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/rag/search?q=${encodeURIComponent(query)}&top_k=${topK}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }
}

export const api = new ApiClient();
