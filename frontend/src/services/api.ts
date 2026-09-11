import type {
  User, Domain, ScanJob, DNSRecord, DNSObservation, DNSFinding, Paginated, IPAddressInfo,
  AuditEvent, UserSettings, Investigation, AnalystNote, Evidence, EvidenceRelationship,
  LifecycleAssessment, TimelineEvent, Certificate, CertificateObservation, Service, ServiceObservation, TimelineResponse,
  MonitoringConfig, MonitoringResult, ChangeEvent, Alert, AlertRule, Report, ReportSection, ReportFinding,
} from "../types";

const BASE = "/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  return localStorage.getItem("dns_sentinel_token");
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem("dns_sentinel_token", token);
  else localStorage.removeItem("dns_sentinel_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Token ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 204) return undefined as T;

  let body: any = null;
  try {
    body = await res.json();
  } catch {
    // no body
  }

  if (!res.ok) {
    const message =
      (body && (body.detail || JSON.stringify(body))) || `Request failed (${res.status})`;
    throw new ApiError(res.status, message);
  }

  return body as T;
}

export const api = {
  register: (data: { username: string; email: string; password: string }) =>
    request<{ user: User; token: string }>("/auth/register/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: { username: string; password: string }) =>
    request<{ user: User; token: string }>("/auth/login/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  logout: () => request<void>("/auth/logout/", { method: "POST" }),

  me: () => request<User>("/auth/me/"),

  getDashboard: () =>
    request<{
      domains: { total: number; authorized: number; unauthorized: number };
      findings: { high: number; medium: number; low: number; info: number; total: number };
      infrastructure: { total_ips: number; current_ips: number; cdn_detected: number };
      lifecycle: {
        ACTIVE: number;
        LEGACY: number;
        POTENTIALLY_ABANDONED: number;
        LIKELY_ABANDONED: number;
        UNKNOWN: number;
      };
      monitoring: { recent_changes: number; total_alerts: number; open_alerts: number };
      attention_required: boolean;
    }>("/auth/dashboard/"),

  listDomains: () => request<Paginated<Domain>>("/domains/"),

  createDomain: (data: { name: string; notes?: string; authorized: boolean }) =>
    request<Domain>("/domains/", { method: "POST", body: JSON.stringify(data) }),

  deleteDomain: (id: string) => request<void>(`/domains/${id}/`, { method: "DELETE" }),

  investigate: (id: string) =>
    request<ScanJob>(`/domains/${id}/investigate/`, { method: "POST" }),

  jobs: (id: string) => request<ScanJob[]>(`/domains/${id}/jobs/`),

  dnsRecords: (id: string) => request<DNSRecord[]>(`/domains/${id}/dns/`),

  dnsObservations: (id: string) => request<DNSObservation[]>(`/domains/${id}/observations/`),

  dnsFindings: (id: string) => request<DNSFinding[]>(`/domains/${id}/findings/`),

  investigateInfrastructure: (id: string) =>
    request<ScanJob>(`/domains/${id}/investigate-infrastructure/`, { method: "POST" }),

  infrastructure: (id: string) => request<IPAddressInfo[]>(`/domains/${id}/infrastructure/`),

  // Audit API
  listAuditEvents: (params?: {
    event_type?: string;
    resource_type?: string;
    result?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.event_type) queryParams.set("event_type", params.event_type);
    if (params?.resource_type) queryParams.set("resource_type", params.resource_type);
    if (params?.result) queryParams.set("result", params.result);
    if (params?.date_from) queryParams.set("date_from", params.date_from);
    if (params?.date_to) queryParams.set("date_to", params.date_to);
    if (params?.page) queryParams.set("page", params.page.toString());
    const queryString = queryParams.toString();
    return request<Paginated<AuditEvent>>(`/auth/audit/${queryString ? `?${queryString}` : ""}`);
  },

  getAuditEvent: (id: string) => request<AuditEvent>(`/auth/audit/${id}/`),

  // Settings API
  getSettings: () => request<UserSettings>("/auth/settings/"),

  updateSettings: (data: Partial<UserSettings>) =>
    request<UserSettings>("/auth/settings/", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  // Investigation API
  listInvestigations: (params?: {
    domain?: string;
    status?: string;
    priority?: string;
    assigned_analyst?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.domain) queryParams.set("domain", params.domain);
    if (params?.status) queryParams.set("status", params.status);
    if (params?.priority) queryParams.set("priority", params.priority);
    if (params?.assigned_analyst) queryParams.set("assigned_analyst", params.assigned_analyst);
    const queryString = queryParams.toString();
    return request<Paginated<Investigation>>(`/investigation/investigations/${queryString ? `?${queryString}` : ""}`);
  },

  getInvestigation: (id: string) => request<Investigation>(`/investigation/investigations/${id}/`),

  createInvestigation: (data: {
    domain: string;
    title: string;
    description?: string;
    priority?: string;
  }) =>
    request<Investigation>("/investigation/investigations/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateInvestigation: (id: string, data: Partial<Investigation>) =>
    request<Investigation>(`/investigation/investigations/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  changeInvestigationStatus: (id: string, status: string) =>
    request<Investigation>(`/investigation/investigations/${id}/change_status/`, {
      method: "POST",
      body: JSON.stringify({ status }),
    }),

  assignInvestigation: (id: string, analyst_id: string) =>
    request<Investigation>(`/investigation/investigations/${id}/assign/`, {
      method: "POST",
      body: JSON.stringify({ analyst_id }),
    }),

  getInvestigationTimeline: (id: string, limit?: number) => {
    const queryParams = new URLSearchParams();
    if (limit) queryParams.set("limit", limit.toString());
    const queryString = queryParams.toString();
    return request<{ investigation_id: string; timeline: TimelineEvent[] }>(
      `/investigation/investigations/${id}/timeline/${queryString ? `?${queryString}` : ""}`
    );
  },

  getInvestigationRelatedEvidence: (id: string) =>
    request<{ investigation_id: string; related_evidence: string[] }>(
      `/investigation/investigations/${id}/related_evidence/`
    ),

  addEvidenceToInvestigation: (id: string, evidence_id: string) =>
    request<{ related_evidence: string[] }>(`/investigation/investigations/${id}/add_evidence/`, {
      method: "POST",
      body: JSON.stringify({ evidence_id }),
    }),

  // Analyst Notes API
  listAnalystNotes: (params?: { investigation?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.investigation) queryParams.set("investigation", params.investigation);
    const queryString = queryParams.toString();
    return request<Paginated<AnalystNote>>(`/investigation/analyst-notes/${queryString ? `?${queryString}` : ""}`);
  },

  getAnalystNote: (id: string) => request<AnalystNote>(`/investigation/analyst-notes/${id}/`),

  createAnalystNote: (data: {
    investigation: string;
    content: string;
  }) =>
    request<AnalystNote>("/investigation/analyst-notes/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateAnalystNote: (id: string, data: Partial<AnalystNote>) =>
    request<AnalystNote>(`/investigation/analyst-notes/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteAnalystNote: (id: string) =>
    request<void>(`/investigation/analyst-notes/${id}/`, { method: "DELETE" }),

  // Evidence API
  listEvidence: (params?: {
    domain?: string;
    evidence_type?: string;
    status?: string;
    source?: string;
    confidence?: string;
    date_from?: string;
    date_to?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.domain) queryParams.set("domain", params.domain);
    if (params?.evidence_type) queryParams.set("evidence_type", params.evidence_type);
    if (params?.status) queryParams.set("status", params.status);
    if (params?.source) queryParams.set("source", params.source);
    if (params?.confidence) queryParams.set("confidence", params.confidence);
    if (params?.date_from) queryParams.set("date_from", params.date_from);
    if (params?.date_to) queryParams.set("date_to", params.date_to);
    const queryString = queryParams.toString();
    return request<Paginated<Evidence>>(`/lifecycle/evidence/${queryString ? `?${queryString}` : ""}`);
  },

  getEvidence: (id: string) => request<Evidence>(`/lifecycle/evidence/${id}/`),

  getEvidenceForAsset: (domain_id: string) => {
    const queryParams = new URLSearchParams();
    queryParams.set("domain_id", domain_id);
    return request<Paginated<Evidence>>(`/lifecycle/evidence/for_asset/?${queryParams.toString()}`);
  },

  getRelatedEvidence: (evidence_id: string) => {
    const queryParams = new URLSearchParams();
    queryParams.set("evidence_id", evidence_id);
    return request<Evidence[]>(`/lifecycle/evidence/related/?${queryParams.toString()}`);
  },

  // Evidence Relationships API
  listEvidenceRelationships: (params?: { evidence_id?: string; relationship_type?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.evidence_id) queryParams.set("evidence_id", params.evidence_id);
    if (params?.relationship_type) queryParams.set("relationship_type", params.relationship_type);
    const queryString = queryParams.toString();
    return request<Paginated<EvidenceRelationship>>(
      `/lifecycle/evidence-relationships/${queryString ? `?${queryString}` : ""}`
    );
  },

  getEvidenceRelationship: (id: string) =>
    request<EvidenceRelationship>(`/lifecycle/evidence-relationships/${id}/`),

  createEvidenceRelationship: (data: {
    from_evidence: string;
    to_evidence: string;
    relationship_type: string;
    confidence?: string;
  }) =>
    request<EvidenceRelationship>("/lifecycle/evidence-relationships/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Lifecycle Assessment API
  listLifecycleAssessments: (params?: { domain?: string; classification?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.domain) queryParams.set("domain", params.domain);
    if (params?.classification) queryParams.set("classification", params.classification);
    const queryString = queryParams.toString();
    return request<Paginated<LifecycleAssessment>>(
      `/lifecycle/lifecycle-assessments/${queryString ? `?${queryString}` : ""}`
    );
  },

  getLifecycleAssessment: (id: string) =>
    request<LifecycleAssessment>(`/lifecycle/lifecycle-assessments/${id}/`),

  getLatestLifecycleAssessment: (domain_id: string) => {
    const queryParams = new URLSearchParams();
    queryParams.set("domain_id", domain_id);
    return request<LifecycleAssessment>(`/lifecycle/lifecycle-assessments/latest/?${queryParams.toString()}`);
  },

  // Monitoring API
  listMonitoringConfigs: (params?: {
    monitor_type?: string;
    is_enabled?: boolean;
    frequency?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.monitor_type) queryParams.set("monitor_type", params.monitor_type);
    if (params?.is_enabled !== undefined) queryParams.set("is_enabled", params.is_enabled.toString());
    if (params?.frequency) queryParams.set("frequency", params.frequency);
    const queryString = queryParams.toString();
    return request<Paginated<MonitoringConfig>>(`/monitoring/configs/${queryString ? `?${queryString}` : ""}`);
  },

  getMonitoringConfig: (id: string) =>
    request<MonitoringConfig>(`/monitoring/configs/${id}/`),

  createMonitoringConfig: (data: {
    domain: string;
    monitor_type: string;
    is_enabled?: boolean;
    frequency?: string;
    alert_on_change?: boolean;
    alert_on_failure?: boolean;
    notes?: string;
  }) =>
    request<MonitoringConfig>("/monitoring/configs/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateMonitoringConfig: (id: string, data: Partial<MonitoringConfig>) =>
    request<MonitoringConfig>(`/monitoring/configs/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteMonitoringConfig: (id: string) =>
    request<void>(`/monitoring/configs/${id}/`, { method: "DELETE" }),

  getMonitoringConfigResults: (id: string) =>
    request<MonitoringResult[]>(`/monitoring/configs/${id}/results/`),

  listMonitoringResults: (params?: {
    monitor_type?: string;
    status?: string;
    has_changes?: boolean;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.monitor_type) queryParams.set("monitor_type", params.monitor_type);
    if (params?.status) queryParams.set("status", params.status);
    if (params?.has_changes !== undefined) queryParams.set("has_changes", params.has_changes.toString());
    const queryString = queryParams.toString();
    return request<Paginated<MonitoringResult>>(`/monitoring/results/${queryString ? `?${queryString}` : ""}`);
  },

  getMonitoringResult: (id: string) =>
    request<MonitoringResult>(`/monitoring/results/${id}/`),

  getMonitoringResultChanges: (id: string) =>
    request<ChangeEvent[]>(`/monitoring/results/${id}/changes/`),

  listChangeEvents: (params?: {
    event_type?: string;
    alert_generated?: boolean;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.event_type) queryParams.set("event_type", params.event_type);
    if (params?.alert_generated !== undefined) queryParams.set("alert_generated", params.alert_generated.toString());
    const queryString = queryParams.toString();
    return request<Paginated<ChangeEvent>>(`/monitoring/changes/${queryString ? `?${queryString}` : ""}`);
  },

  getChangeEvent: (id: string) =>
    request<ChangeEvent>(`/monitoring/changes/${id}/`),

  // Alerts API
  listAlerts: (params?: {
    alert_type?: string;
    severity?: string;
    status?: string;
    domain?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.alert_type) queryParams.set("alert_type", params.alert_type);
    if (params?.severity) queryParams.set("severity", params.severity);
    if (params?.status) queryParams.set("status", params.status);
    if (params?.domain) queryParams.set("domain", params.domain);
    const queryString = queryParams.toString();
    return request<Paginated<Alert>>(`/alerts/${queryString ? `?${queryString}` : ""}`);
  },

  getAlert: (id: string) =>
    request<Alert>(`/alerts/${id}/`),

  createAlert: (data: {
    domain: string;
    alert_type: string;
    severity: string;
    title: string;
    description: string;
    trigger_event_id?: string;
    trigger_event_type?: string;
    evidence_id?: string;
  }) =>
    request<Alert>("/alerts/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateAlert: (id: string, data: Partial<Alert>) =>
    request<Alert>(`/alerts/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteAlert: (id: string) =>
    request<void>(`/alerts/${id}/`, { method: "DELETE" }),

  acknowledgeAlert: (id: string, data: { status: string; notes?: string }) =>
    request<Alert>(`/alerts/${id}/acknowledge/`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  resolveAlert: (id: string, data: { status: string; notes?: string }) =>
    request<Alert>(`/alerts/${id}/resolve/`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  reopenAlert: (id: string) =>
    request<Alert>(`/alerts/${id}/reopen/`, { method: "POST" }),

  dismissAlert: (id: string, data: { status: string; notes?: string }) =>
    request<Alert>(`/alerts/${id}/dismiss/`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  assignAlert: (id: string, data: { assigned_analyst_id?: number }) =>
    request<Alert>(`/alerts/${id}/assign/`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  linkAlertToInvestigation: (id: string, data: { investigation_id?: string }) =>
    request<Alert>(`/alerts/${id}/investigation/`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getAlertEvidence: (id: string) =>
    request<{ evidence: any }>(`/alerts/${id}/evidence/`),

  // Alert Rules API
  listAlertRules: (params?: {
    alert_type?: string;
    severity?: string;
    enabled?: boolean;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.alert_type) queryParams.set("alert_type", params.alert_type);
    if (params?.severity) queryParams.set("severity", params.severity);
    if (params?.enabled !== undefined) queryParams.set("enabled", params.enabled.toString());
    const queryString = queryParams.toString();
    return request<Paginated<AlertRule>>(`/alerts/rules/${queryString ? `?${queryString}` : ""}`);
  },

  getAlertRule: (id: string) =>
    request<AlertRule>(`/alerts/rules/${id}/`),

  createAlertRule: (data: {
    name: string;
    description?: string;
    alert_type: string;
    severity: string;
    apply_to_all_domains?: boolean;
    specific_domains?: string[];
    enabled?: boolean;
  }) =>
    request<AlertRule>("/alerts/rules/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateAlertRule: (id: string, data: Partial<AlertRule>) =>
    request<AlertRule>(`/alerts/rules/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteAlertRule: (id: string) =>
    request<void>(`/alerts/rules/${id}/`, { method: "DELETE" }),

  // Reports API
  listReports: (params?: {
    status?: string;
    format?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.set("status", params.status);
    if (params?.format) queryParams.set("format", params.format);
    const queryString = queryParams.toString();
    return request<Paginated<Report>>(`/reports/${queryString ? `?${queryString}` : ""}`);
  },

  getReport: (id: string) =>
    request<Report>(`/reports/${id}/`),

  createReport: (data: {
    title: string;
    domains: string[];
    scope_description?: string;
    format?: string;
    requested_sections?: string[];
  }) =>
    request<Report>("/reports/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateReport: (id: string, data: Partial<Report>) =>
    request<Report>(`/reports/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteReport: (id: string) =>
    request<void>(`/reports/${id}/`, { method: "DELETE" }),

  getReportSections: (id: string) =>
    request<ReportSection[]>(`/reports/${id}/sections/`),

  downloadReport: (id: string) =>
    request<any>(`/reports/${id}/download/`),

  regenerateReport: (id: string) =>
    request<Report>(`/reports/${id}/regenerate/`, { method: "POST" }),

  listReportSections: (params?: {
    section_type?: string;
    status?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.section_type) queryParams.set("section_type", params.section_type);
    if (params?.status) queryParams.set("status", params.status);
    const queryString = queryParams.toString();
    return request<Paginated<ReportSection>>(`/reports/sections/${queryString ? `?${queryString}` : ""}`);
  },

  getReportSection: (id: string) =>
    request<ReportSection>(`/reports/sections/${id}/`),

  getReportSectionFindings: (id: string) =>
    request<ReportFinding[]>(`/reports/sections/${id}/findings/`),

  classifyDomain: (data: { domain_id: string }) =>
    request<LifecycleAssessment>("/lifecycle/lifecycle-assessments/classify/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Certificate API
  listCertificates: (params?: {
    domain?: string;
    issuer?: string;
    is_valid?: string;
    is_expired?: string;
    expiring_before?: string;
    expiring_after?: string;
    date_from?: string;
    date_to?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.domain) queryParams.set("domain", params.domain);
    if (params?.issuer) queryParams.set("issuer", params.issuer);
    if (params?.is_valid) queryParams.set("is_valid", params.is_valid);
    if (params?.is_expired) queryParams.set("is_expired", params.is_expired);
    if (params?.expiring_before) queryParams.set("expiring_before", params.expiring_before);
    if (params?.expiring_after) queryParams.set("expiring_after", params.expiring_after);
    if (params?.date_from) queryParams.set("date_from", params.date_from);
    if (params?.date_to) queryParams.set("date_to", params.date_to);
    const queryString = queryParams.toString();
    return request<Paginated<Certificate>>(`/certificates/certificates/${queryString ? `?${queryString}` : ""}`);
  },

  getCertificate: (id: string) => request<Certificate>(`/certificates/certificates/${id}/`),

  getCertificateHistory: (domain_id: string) => {
    const queryParams = new URLSearchParams();
    queryParams.set("domain_id", domain_id);
    return request<Paginated<CertificateObservation>>(`/certificates/certificates/history/?${queryParams.toString()}`);
  },

  getCertificateStatus: (domain_id: string) => {
    const queryParams = new URLSearchParams();
    queryParams.set("domain_id", domain_id);
    return request<{
      domain_id: string;
      domain_name: string;
      has_certificate: boolean;
      is_valid: boolean;
      is_expired: boolean;
      days_until_expiry: number | null;
      issuer: string | null;
      subject: string | null;
      last_observed: string | null;
    }>(`/certificates/certificates/status/?${queryParams.toString()}`);
  },

  getCertificateIssuerDistribution: () =>
    request<{ issuer: string; count: number; percentage: number }[]>(
      "/certificates/certificates/issuer_distribution/"
    ),

  getCertificateChanges: (domain_id: string) => {
    const queryParams = new URLSearchParams();
    queryParams.set("domain_id", domain_id);
    return request<{
      domain_id: string;
      domain_name: string;
      old_fingerprint: string;
      new_fingerprint: string;
      old_issuer: string;
      new_issuer: string;
      changed_at: string;
    }[]>(`/certificates/certificates/changes/?${queryParams.toString()}`);
  },

  // Service API
  listServices: (params?: {
    domain?: string;
    ip_address?: string;
    port?: string;
    protocol?: string;
    service_type?: string;
    is_available?: string;
    date_from?: string;
    date_to?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.domain) queryParams.set("domain", params.domain);
    if (params?.ip_address) queryParams.set("ip_address", params.ip_address);
    if (params?.port) queryParams.set("port", params.port);
    if (params?.protocol) queryParams.set("protocol", params.protocol);
    if (params?.service_type) queryParams.set("service_type", params.service_type);
    if (params?.is_available) queryParams.set("is_available", params.is_available);
    if (params?.date_from) queryParams.set("date_from", params.date_from);
    if (params?.date_to) queryParams.set("date_to", params.date_to);
    const queryString = queryParams.toString();
    return request<Paginated<Service>>(`/services/services/${queryString ? `?${queryString}` : ""}`);
  },

  getService: (id: string) => request<Service>(`/services/services/${id}/`),

  getServiceHistory: (domain_id: string) => {
    const queryParams = new URLSearchParams();
    queryParams.set("domain_id", domain_id);
    return request<Paginated<ServiceObservation>>(`/services/services/history/?${queryParams.toString()}`);
  },

  getServiceAvailability: (domain_id: string) => {
    const queryParams = new URLSearchParams();
    queryParams.set("domain_id", domain_id);
    return request<{
      domain_id: string;
      domain_name: string;
      total_services: number;
      available_services: number;
      unavailable_services: number;
      availability_percentage: number;
    }>(`/services/services/availability/?${queryParams.toString()}`);
  },

  getServiceHTTPStatusDistribution: () =>
    request<{ http_status: number; count: number; percentage: number }[]>(
      "/services/services/http_status_distribution/"
    ),

  getServiceChanges: (domain_id: string) => {
    const queryParams = new URLSearchParams();
    queryParams.set("domain_id", domain_id);
    return request<{
      domain_id: string;
      domain_name: string;
      ip_address: string;
      port: number;
      service_type: string;
      old_status: boolean;
      new_status: boolean;
      changed_at: string;
    }[]>(`/services/services/changes/?${queryParams.toString()}`);
  },

  // History API
  getTimeline: (params: {
    domain_id: string;
    event_type?: string;
    date_from?: string;
    date_to?: string;
    limit?: number;
  }) => {
    const queryParams = new URLSearchParams();
    queryParams.set("domain_id", params.domain_id);
    if (params.event_type) queryParams.set("event_type", params.event_type);
    if (params.date_from) queryParams.set("date_from", params.date_from);
    if (params.date_to) queryParams.set("date_to", params.date_to);
    if (params.limit) queryParams.set("limit", params.limit.toString());
    return request<TimelineResponse>(`/lifecycle/history/timeline/?${queryParams.toString()}`);
  },

  getAssetHistory: (params: {
    domain_id: string;
    asset_type: string;
    asset_identifier: string;
    date_from?: string;
    date_to?: string;
  }) => {
    const queryParams = new URLSearchParams();
    queryParams.set("domain_id", params.domain_id);
    queryParams.set("asset_type", params.asset_type);
    queryParams.set("asset_identifier", params.asset_identifier);
    if (params.date_from) queryParams.set("date_from", params.date_from);
    if (params.date_to) queryParams.set("date_to", params.date_to);
    return request<{
      domain_id: string;
      domain_name: string;
      asset_type: string;
      asset_identifier: string;
      history: Record<string, unknown>[];
    }>(`/lifecycle/history/asset/?${queryParams.toString()}`);
  },
};
