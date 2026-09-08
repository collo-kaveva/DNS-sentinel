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
export type AlertSeverity = "INFO" | "LOW" | "MEDIUM" | "HIGH";

export interface UserSettings {
  date_format: DateFormat;
  time_format: TimeFormat;
  timezone: string;
  auto_refresh: boolean;
  refresh_interval_minutes: number;
  default_monitoring_behavior: MonitoringBehavior;
  email_alerts: boolean;
  alert_severity_threshold: AlertSeverity;
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
  event_type: TimelineEventType;
  timestamp: string;
  asset: string;
  description: string;
  source: string;
  previous_state: string | null;
  new_state: string | null;
  evidence_id: string | null;
  metadata: Record<string, unknown>;
}
