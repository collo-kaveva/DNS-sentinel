import type {
  User, Domain, ScanJob, DNSRecord, DNSObservation, DNSFinding, Paginated,
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
};
