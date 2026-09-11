export interface User {
  id: number;
  username: string;
  email: string;
  date_joined: string;
}

export interface Domain {
  id: string;
  name: string;
  notes: string;
  authorized: boolean;
  created_at: string;
  updated_at: string;
}

export type JobStatus = "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED";

export interface ProgressStep {
  label: string;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
}

export interface ScanJob {
  id: string;
  domain: string;
  job_type: string;
  status: JobStatus;
  progress_steps: ProgressStep[];
  error_message: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface DNSRecord {
  id: string;
  hostname: string;
  record_type: string;
  value: string;
  ttl: number | null;
  is_current: boolean;
  first_seen: string;
  last_seen: string;
}

export interface DNSObservation {
  id: string;
  hostname: string;
  record_type: string;
  values: string[];
  response_code: string;
  ttl: number | null;
  resolver_used: string;
  query_time_ms: number | null;
  dnssec_signed: boolean | null;
  source: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  observed_at: string;
}

export type Severity = "INFO" | "LOW" | "MEDIUM" | "HIGH";

export interface DNSFinding {
  id: string;
  severity: Severity;
  title: string;
  description: string;
  evidence: Record<string, unknown>;
  created_at: string;
}

export interface IPAddressInfo {
  id: string;
  address: string;
  version: "IPv4" | "IPv6";
  association_status: "CURRENT" | "HISTORICAL" | "ESTIMATED" | "UNKNOWN";
  reverse_dns: string | null;
  asn: string | null;
  network: string | null;
  organization: string | null;
  country: string | null;
  is_likely_cdn: boolean;
  is_likely_shared_hosting: boolean;
  cdn_indicator_source: string;
  rdap_available: boolean;
  first_seen: string;
  last_seen: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Certificate types
export interface Certificate {
  id: string;
  domain: string;
  domain_name: string;
  subject: string;
  issuer: string;
  serial_number: string;
  fingerprint: string;
  fingerprint_sha256: string;
  valid_from: string;
  valid_until: string;
  sans: string[];
  public_key_algorithm: string;
  public_key_size: number | null;
  tls_version: string;
  cipher_suite: string;
  is_valid: boolean;
  is_expired: boolean;
  is_self_signed: boolean;
  source: string;
  collection_timestamp: string;
  first_seen: string;
  last_seen: string;
  days_until_expiry: number | null;
}

export interface CertificateObservation {
  id: string;
  domain: string;
  domain_name: string;
  subject: string;
  issuer: string;
  serial_number: string;
  fingerprint: string;
  fingerprint_sha256: string;
  valid_from: string;
  valid_until: string;
  sans: string[];
  public_key_algorithm: string;
  public_key_size: number | null;
  tls_version: string;
  cipher_suite: string;
  is_valid: boolean;
  is_expired: boolean;
  is_self_signed: boolean;
  source: string;
  collection_method: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  observed_at: string;
}

// Service types
export interface Service {
  id: string;
  domain: string;
  domain_name: string;
  ip_address: string;
  port: number;
  protocol: string;
  service_type: string;
  is_available: boolean;
  http_status: number | null;
  response_time_ms: number | null;
  service_banner: string;
  ssl_tls_enabled: boolean;
  source: string;
  collection_timestamp: string;
  first_observed: string;
  last_observed: string;
}

export interface ServiceObservation {
  id: string;
  domain: string;
  domain_name: string;
  ip_address: string;
  port: number;
  protocol: string;
  service_type: string;
  is_available: boolean;
  http_status: number | null;
  response_time_ms: number | null;
  service_banner: string;
  ssl_tls_enabled: boolean;
  source: string;
  collection_method: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  observed_at: string;
}

// Lifecycle types
export type LifecycleClassification = 
  | "ACTIVE" 
  | "LEGACY" 
  | "POTENTIALLY_ABANDONED" 
  | "LIKELY_ABANDONED" 
  | "UNKNOWN";

export interface LifecycleAssessment {
  id: string;
  domain: string;
  domain_name: string;
  classification: LifecycleClassification;
  confidence: number;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  model_version: string;
  limitations: string;
  explanation: string;
  generated_at: string;
}

// History API types
export interface TimelineEvent {
  event_id: string;
  event_type: string;
  timestamp: string;
  asset: string;
  description: string;
  source: string;
  previous_state: string | null;
  new_state: string | null;
  evidence_id: string | null;
  metadata: Record<string, unknown>;
}

export interface TimelineResponse {
  domain_id: string;
  domain_name: string;
  total_events: number;
  events: TimelineEvent[];
}

// Audit types
export type AuditEventType = 
  | "LOGIN" 
  | "LOGOUT" 
  | "REGISTRATION" 
  | "PASSWORD_CHANGE"
  | "DOMAIN_CREATED" 
  | "DOMAIN_DELETED" 
  | "DOMAIN_UPDATED"
  | "INVESTIGATION_STARTED" 
  | "INVESTIGATION_COMPLETED" 
  | "INVESTIGATION_FAILED"
  | "ALERT_ACKNOWLEDGED" 
  | "ALERT_RESOLVED" 
  | "ALERT_REOPENED"
  | "ANALYST_NOTE_CREATED" 
  | "ANALYST_NOTE_UPDATED" 
  | "ANALYST_NOTE_DELETED"
  | "SETTINGS_UPDATED"
  | "REPORT_GENERATED" 
  | "REPORT_EXPORTED"
  | "OTHER";

export type AuditResult = "SUCCESS" | "FAILURE" | "PARTIAL";

export interface AuditEvent {
  id: string;
  actor: number;
  actor_username: string;
  event_type: AuditEventType;
  action: string;
  resource_type: string;
  resource_id: string;
  resource_name: string;
  result: AuditResult;
  status_code: number | null;
  ip_address: string | null;
  user_agent: string;
  metadata: Record<string, unknown>;
  timestamp: string;
}

// Settings types
export type DateFormat = "ISO_8601" | "US" | "EUROPEAN";
export type TimeFormat = "24_HOUR" | "12_HOUR";
export type MonitoringBehavior = "PASSIVE" | "ACTIVE";
export type AlertSeverityThreshold = "INFO" | "LOW" | "MEDIUM" | "HIGH";

export interface UserSettings {
  date_format: DateFormat;
  time_format: TimeFormat;
  timezone: string;
  auto_refresh: boolean;
  refresh_interval_minutes: number;
  default_monitoring_behavior: MonitoringBehavior;
  email_alerts: boolean;
  alert_severity_threshold: AlertSeverityThreshold;
  session_timeout_minutes: number;
  default_dashboard_view: string;
  updated_at: string;
}

// Investigation types
export type InvestigationStatus = "OPEN" | "IN_PROGRESS" | "RESOLVED" | "CLOSED" | "REOPENED";
export type InvestigationPriority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface Investigation {
  id: string;
  domain: string;
  domain_name: string;
  owner: number;
  title: string;
  description: string;
  status: InvestigationStatus;
  priority: InvestigationPriority;
  assigned_analyst: number | null;
  assigned_analyst_username: string | null;
  related_evidence: string[];
  related_alerts: string[];
  important_observations: string;
  limitations: string;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
}

export interface AnalystNote {
  id: string;
  investigation: string;
  author: number;
  author_username: string;
  content: string;
  created_at: string;
  updated_at: string;
}

// Evidence types
export type EvidenceType = 
  | "DNS_OBSERVATION" 
  | "DNS_RECORD" 
  | "IP_ADDRESS" 
  | "CERTIFICATE" 
  | "SERVICE" 
  | "ASN" 
  | "PROVIDER" 
  | "ALERT" 
  | "LIFECYCLE_ASSESSMENT" 
  | "ANALYST_NOTE";

export type EvidenceStatus = "OBSERVED" | "HISTORICAL" | "INFERRED" | "ANALYST" | "UNKNOWN";
export type EvidenceConfidence = "HIGH" | "MEDIUM" | "LOW";

export interface Evidence {
  id: string;
  domain: string;
  evidence_type: EvidenceType;
  status: EvidenceStatus;
  confidence: EvidenceConfidence;
  source: string;
  collection_method: string;
  observation: string;
  entity_name: string;
  entity_type: string;
  related_object_id: string | null;
  related_object_type: string;
  metadata: Record<string, unknown>;
  observed_at: string;
  first_observed: string;
  last_observed: string;
}

export interface EvidenceRelationship {
  id: string;
  from_evidence: string;
  to_evidence: string;
  from_evidence_details: Evidence;
  to_evidence_details: Evidence;
  relationship_type: string;
  confidence: EvidenceConfidence;
  observed_at: string;
}

// Lifecycle types
export type LifecycleStatus = "ACTIVE" | "LEGACY" | "POTENTIALLY_ABANDONED" | "LIKELY_ABANDONED" | "UNKNOWN";

export interface LifecycleAssessment {
  id: string;
  domain: string;
  classification: LifecycleStatus;
  confidence: number;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  model_version: string;
  limitations: string;
  explanation: string;
  generated_at: string;
}

// Timeline types
export type TimelineEventType = 
  | "DNS_OBSERVATION" 
  | "DNS_RECORD" 
  | "IP_ADDRESS" 
  | "DNS_FINDING" 
  | "AUDIT_EVENT" 
  | "INVESTIGATION" 
  | "INVESTIGATION_STATUS_CHANGE" 
  | "ANALYST_NOTE" 
  | "LIFECYCLE_ASSESSMENT" 
  | "INVESTIGATION_CREATED";

export interface TimelineEvent {
  event_id: string;
  event_type: string;
  timestamp: string;
  asset: string;
  description: string;
  source: string;
  previous_state: string | null;
  new_state: string | null;
  evidence_id: string | null;
  metadata: Record<string, unknown>;
}

// Monitoring types
export type MonitorType = "DNS" | "IP" | "CERTIFICATE" | "SERVICE" | "ASN" | "LIFECYCLE";
export type MonitorFrequency = "HOURLY" | "DAILY" | "WEEKLY" | "MONTHLY";
export type MonitorCheckStatus = "SUCCESS" | "FAILURE" | "PARTIAL";

export interface MonitoringConfig {
  id: string;
  domain: string;
  domain_name: string;
  monitor_type: MonitorType;
  is_enabled: boolean;
  frequency: MonitorFrequency;
  alert_on_change: boolean;
  alert_on_failure: boolean;
  next_check_scheduled: string | null;
  last_check_completed: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface MonitoringResult {
  id: string;
  domain: string;
  domain_name: string;
  monitoring_config: string;
  monitor_type: MonitorType;
  status: MonitorCheckStatus;
  observation_id: string | null;
  observation_type: string;
  previous_state: Record<string, unknown>;
  new_state: Record<string, unknown>;
  has_changes: boolean;
  evidence_id: string | null;
  scan_job_id: string | null;
  error_message: string;
  check_started_at: string;
  check_completed_at: string;
  duration_seconds: number | null;
  created_at: string;
}

export type ChangeEventType = 
  | "DNS_RECORD_ADDED" 
  | "DNS_RECORD_REMOVED" 
  | "DNS_RECORD_CHANGED"
  | "IP_CHANGED" 
  | "CERTIFICATE_CHANGED" 
  | "CERTIFICATE_EXPIRED"
  | "SERVICE_APPEARED" 
  | "SERVICE_DISAPPEARED"
  | "ASN_CHANGED" 
  | "PROVIDER_CHANGED" 
  | "LIFECYCLE_CHANGED";

export interface ChangeEvent {
  id: string;
  domain: string;
  domain_name: string;
  monitoring_result: string;
  event_type: ChangeEventType;
  description: string;
  previous_value: string;
  new_value: string;
  entity_name: string;
  entity_type: string;
  evidence_id: string | null;
  alert_generated: boolean;
  alert_id: string | null;
  metadata: Record<string, unknown>;
  detected_at: string;
}

// Alert types
export type AlertStatus = "NEW" | "OPEN" | "ACKNOWLEDGED" | "RESOLVED" | "DISMISSED";
export type AlertSeverityLevel = "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type AlertType = 
  | "DNS_RECORD_ADDED" 
  | "DNS_RECORD_REMOVED" 
  | "DNS_RECORD_CHANGED"
  | "IP_CHANGED" 
  | "CERTIFICATE_CHANGED" 
  | "CERTIFICATE_EXPIRED"
  | "CERTIFICATE_EXPIRING_SOON"
  | "SERVICE_APPEARED" 
  | "SERVICE_DISAPPEARED"
  | "ASN_CHANGED" 
  | "PROVIDER_CHANGED" 
  | "LIFECYCLE_CHANGED";

export interface Alert {
  id: string;
  domain: string;
  domain_name: string;
  owner: number;
  owner_username: string;
  alert_type: AlertType;
  severity: AlertSeverityLevel;
  status: AlertStatus;
  title: string;
  description: string;
  trigger_event_id: string | null;
  trigger_event_type: string;
  evidence_id: string | null;
  investigation: string | null;
  assigned_analyst: number | null;
  assigned_analyst_username: string | null;
  resolution_notes: string;
  created_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  dismissed_at: string | null;
}

export interface AlertRule {
  id: string;
  owner: number;
  owner_username: string;
  name: string;
  description: string;
  alert_type: AlertType;
  severity: AlertSeverityLevel;
  apply_to_all_domains: boolean;
  specific_domains: string[];
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

// Report types
export type ReportStatus = "QUEUED" | "GENERATING" | "COMPLETED" | "FAILED";
export type ReportFormat = "JSON" | "HTML" | "PDF";
export type ReportSectionType = 
  | "EXECUTIVE_SUMMARY" 
  | "SCOPE" 
  | "ASSETS" 
  | "DNS"
  | "CERTIFICATES" 
  | "INFRASTRUCTURE" 
  | "SERVICES" 
  | "LIFECYCLE"
  | "MONITORING" 
  | "ALERTS" 
  | "HISTORY" 
  | "EVIDENCE"
  | "FINDINGS" 
  | "RECOMMENDATIONS" 
  | "LIMITATIONS";

export interface Report {
  id: string;
  owner: number;
  owner_username: string;
  title: string;
  domains: string[];
  scope_description: string;
  format: ReportFormat;
  requested_sections: string[];
  status: ReportStatus;
  error_message: string;
  celery_task_id: string;
  content: Record<string, unknown>;
  content_html: string;
  generated_at: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ReportSection {
  id: string;
  report: string;
  section_type: ReportSectionType;
  title: string;
  content: string;
  evidence_ids: string[];
  observation_ids: string[];
  findings: Record<string, unknown>[];
  status: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  order: number;
  created_at: string;
}

export interface ReportFinding {
  id: string;
  report_section: string;
  title: string;
  description: string;
  severity: "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  source_observation_id: string | null;
  source_observation_type: string;
  evidence_id: string | null;
  asset_id: string | null;
  asset_name: string;
  asset_type: string;
  finding_status: string;
  observed_at: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}
