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

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
