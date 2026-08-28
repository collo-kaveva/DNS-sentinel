import { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { api, ApiError } from "../services/api";
import type { DNSRecord, DNSFinding, ScanJob } from "../types";

const SEVERITY_ORDER: Record<string, number> = { HIGH: 0, MEDIUM: 1, LOW: 2, INFO: 3 };

export default function DomainDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [records, setRecords] = useState<DNSRecord[] | null>(null);
  const [findings, setFindings] = useState<DNSFinding[] | null>(null);
  const [job, setJob] = useState<ScanJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const loadResults = useCallback(() => {
    if (!id) return;
    api.dnsRecords(id).then(setRecords).catch(() => {});
    api.dnsFindings(id).then(setFindings).catch(() => {});
  }, [id]);

  useEffect(() => {
    if (!id) return;
    loadResults();
    api
      .jobs(id)
      .then((jobs) => {
        if (jobs.length > 0) setJob(jobs[0]);
      })
      .catch(() => {});
  }, [id, loadResults]);

  // Poll active job until completion
  useEffect(() => {
    if (!job || !id) return;
    if (job.status === "COMPLETED" || job.status === "FAILED") return;
    const interval = setInterval(async () => {
      const jobs = await api.jobs(id);
      if (jobs.length > 0) {
        setJob(jobs[0]);
        if (jobs[0].status === "COMPLETED") {
          loadResults();
          clearInterval(interval);
        } else if (jobs[0].status === "FAILED") {
          clearInterval(interval);
        }
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [job, id, loadResults]);

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
    </div>
  );
}
