import { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { api, ApiError } from "../services/api";
import type { DNSRecord, DNSFinding, ScanJob, IPAddressInfo } from "../types";

const SEVERITY_ORDER: Record<string, number> = { HIGH: 0, MEDIUM: 1, LOW: 2, INFO: 3 };

export default function DomainDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [records, setRecords] = useState<DNSRecord[] | null>(null);
  const [findings, setFindings] = useState<DNSFinding[] | null>(null);
  const [job, setJob] = useState<ScanJob | null>(null);
  const [ipAddresses, setIpAddresses] = useState<IPAddressInfo[] | null>(null);
  const [infraJob, setInfraJob] = useState<ScanJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [startingInfra, setStartingInfra] = useState(false);

  const loadResults = useCallback(() => {
    if (!id) return;
    api.dnsRecords(id).then(setRecords).catch(() => {});
    api.dnsFindings(id).then(setFindings).catch(() => {});
  }, [id]);

  const loadInfrastructure = useCallback(() => {
    if (!id) return;
    api.infrastructure(id).then(setIpAddresses).catch(() => {});
  }, [id]);

  useEffect(() => {
    if (!id) return;
    loadResults();
    loadInfrastructure();
    api
      .jobs(id)
      .then((jobs) => {
        const dnsJob = jobs.find((j) => j.job_type === "DNS_DISCOVERY");
        const infrastructureJob = jobs.find((j) => j.job_type === "INFRASTRUCTURE_ANALYSIS");
        if (dnsJob) setJob(dnsJob);
        if (infrastructureJob) setInfraJob(infrastructureJob);
      })
      .catch(() => {});
  }, [id, loadResults, loadInfrastructure]);

  // Poll active DNS job until completion
  useEffect(() => {
    if (!job || !id) return;
    if (job.status === "COMPLETED" || job.status === "FAILED") return;
    const interval = setInterval(async () => {
      const jobs = await api.jobs(id);
      const latest = jobs.find((j) => j.job_type === "DNS_DISCOVERY");
      if (latest) {
        setJob(latest);
        if (latest.status === "COMPLETED") {
          loadResults();
          clearInterval(interval);
        } else if (latest.status === "FAILED") {
          clearInterval(interval);
        }
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [job, id, loadResults]);

  // Poll active infrastructure job until completion
  useEffect(() => {
    if (!infraJob || !id) return;
    if (infraJob.status === "COMPLETED" || infraJob.status === "FAILED") return;
    const interval = setInterval(async () => {
      const jobs = await api.jobs(id);
      const latest = jobs.find((j) => j.job_type === "INFRASTRUCTURE_ANALYSIS");
      if (latest) {
        setInfraJob(latest);
        if (latest.status === "COMPLETED") {
          loadInfrastructure();
          clearInterval(interval);
        } else if (latest.status === "FAILED") {
          clearInterval(interval);
        }
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [infraJob, id, loadInfrastructure]);

  async function handleInvestigate() {
    if (!id) return;
    setError(null);
    setStarting(true);
    try {
      const newJob = await api.investigate(id);
      setJob(newJob);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start investigation.");
    } finally {
      setStarting(false);
    }
  }

  async function handleInvestigateInfrastructure() {
    if (!id) return;
    setError(null);
    setStartingInfra(true);
    try {
      const newJob = await api.investigateInfrastructure(id);
      setInfraJob(newJob);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start infrastructure analysis.");
    } finally {
      setStartingInfra(false);
    }
  }

  const sortedFindings = findings
    ? [...findings].sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity])
    : [];

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold">Domain Investigation</h1>
        <button
          onClick={handleInvestigate}
          disabled={starting || job?.status === "RUNNING" || job?.status === "QUEUED"}
          className="bg-accent text-slate-950 text-sm font-medium rounded px-4 py-2 disabled:opacity-50"
        >
          {starting ? "Starting…" : "Run DNS investigation"}
        </button>
      </div>

      {error && <div className="text-rose-400 text-sm mb-4">{error}</div>}

      {job && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-6">
          <div className="text-xs text-slate-500 mb-2">
            Job status: <span className="text-slate-300">{job.status}</span>
          </div>
          <div className="flex flex-col gap-1">
            {job.progress_steps.map((step) => (
              <div key={step.label} className="flex items-center gap-2 text-sm">
                <span>
                  {step.status === "COMPLETED" ? "✓" : step.status === "RUNNING" ? "●" : "○"}
                </span>
                <span className={step.status === "COMPLETED" ? "text-slate-300" : "text-slate-500"}>
                  {step.label}
                </span>
              </div>
            ))}
          </div>
          {job.status === "FAILED" && (
            <div className="text-rose-400 text-xs mt-2">{job.error_message}</div>
          )}
        </div>
      )}

      <section className="mb-8">
        <h2 className="text-sm font-semibold text-slate-300 mb-2">Current DNS Records</h2>
        {records === null && <div className="text-slate-500 text-sm">Loading…</div>}
        {records !== null && records.length === 0 && (
          <div className="text-slate-500 text-sm">
            No records yet. Run a DNS investigation to populate this section.
          </div>
        )}
        <div className="flex flex-col gap-1">
          {records?.map((r) => (
            <div
              key={r.id}
              className="bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm font-mono flex justify-between"
            >
              <span className="text-accent">{r.record_type}</span>
              <span className="truncate max-w-md text-slate-300">{r.value}</span>
              <span className="text-slate-500 text-xs">TTL {r.ttl ?? "—"}</span>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-300 mb-2">DNS Analysis Findings</h2>
        {sortedFindings.length === 0 && findings !== null && (
          <div className="text-slate-500 text-sm">No findings.</div>
        )}
        <div className="flex flex-col gap-2">
          {sortedFindings.map((f) => (
            <div key={f.id} className="bg-slate-900 border border-slate-800 rounded-lg p-3">
              <div className={`text-xs font-semibold sev-${f.severity} mb-1`}>{f.severity}</div>
              <div className="text-sm font-medium">{f.title}</div>
              <div className="text-xs text-slate-500 mt-1">{f.description}</div>
            </div>
          ))}
        </div>
      </section>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold text-slate-300">Infrastructure (IP / ASN / Reverse DNS)</h2>
          <button
            onClick={handleInvestigateInfrastructure}
            disabled={
              startingInfra || infraJob?.status === "RUNNING" || infraJob?.status === "QUEUED" ||
              !records || records.filter((r) => r.record_type === "A" || r.record_type === "AAAA").length === 0
            }
            className="bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium rounded px-3 py-1.5 disabled:opacity-40"
          >
            {startingInfra ? "Starting…" : "Run infrastructure analysis"}
          </button>
        </div>

        {infraJob && (
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 mb-3 text-xs">
            <div className="text-slate-500 mb-1">
              Job status: <span className="text-slate-300">{infraJob.status}</span>
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1">
              {infraJob.progress_steps.map((step) => (
                <span key={step.label} className={step.status === "COMPLETED" ? "text-slate-300" : "text-slate-500"}>
                  {step.status === "COMPLETED" ? "✓" : step.status === "RUNNING" ? "●" : "○"} {step.label}
                </span>
              ))}
            </div>
            {infraJob.status === "FAILED" && (
              <div className="text-rose-400 mt-2">{infraJob.error_message}</div>
            )}
          </div>
        )}

        {ipAddresses !== null && ipAddresses.length === 0 && (
          <div className="text-slate-500 text-sm">
            No infrastructure data yet. Run DNS investigation first, then run infrastructure analysis.
          </div>
        )}

        <div className="flex flex-col gap-2">
          {ipAddresses?.map((ip) => (
            <div key={ip.id} className="bg-slate-900 border border-slate-800 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-sm text-accent">{ip.address}</span>
                <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                  {ip.association_status}
                </span>
              </div>
              <div className="text-xs text-slate-500 flex flex-wrap gap-x-4 gap-y-1">
                <span>Reverse DNS: {ip.reverse_dns || "—"}</span>
                {ip.rdap_available ? (
                  <>
                    <span>ASN: {ip.asn || "—"}</span>
                    <span>Org: {ip.organization || "—"}</span>
                    <span>Country: {ip.country || "—"}</span>
                  </>
                ) : (
                  <span className="text-amber-400">
                    Ownership data unavailable (RDAP lookup did not succeed) — do not infer ownership.
                  </span>
                )}
              </div>
              {(ip.is_likely_cdn || ip.is_likely_shared_hosting) && (
                <div className="text-xs text-orange-400 mt-1">
                  {ip.is_likely_cdn ? "Indicators of CDN/proxy infrastructure" : "Indicators of shared hosting"}
                  {ip.cdn_indicator_source && ` (${ip.cdn_indicator_source})`} — reduces confidence of any
                  ownership or lifecycle inference for this address.
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
