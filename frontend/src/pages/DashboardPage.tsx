import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import type { Domain } from "../types";

export default function DashboardPage() {
  const [domains, setDomains] = useState<Domain[] | null>(null);

  useEffect(() => {
    api.listDomains().then((res) => setDomains(res.results)).catch(() => setDomains([]));
  }, []);

  const total = domains?.length ?? 0;
  const authorized = domains?.filter((d) => d.authorized).length ?? 0;

  return (
    <div>
      <h1 className="text-lg font-semibold mb-1">Dashboard</h1>
      <p className="text-sm text-slate-500 mb-6">
        Phase 1–2 build: authentication, domain management, and the real DNS
        resolution &amp; analysis engine are live. Certificates, infrastructure,
        service observation, and the lifecycle classification engine ship in
        later phases — see docs/ROADMAP.md.
      </p>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard label="Total Domains" value={total} />
        <StatCard label="Authorized" value={authorized} />
        <StatCard label="Investigations Run" value={"—"} hint="Available once job history endpoint is aggregated" />
      </div>

      <Link to="/domains" className="text-accent text-sm hover:underline">
        Go to Domains →
      </Link>
    </div>
  );
}

function StatCard({ label, value, hint }: { label: string; value: number | string; hint?: string }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
      <div className="text-2xl font-semibold">{value}</div>
      <div className="text-xs text-slate-500 mt-1">{label}</div>
      {hint && <div className="text-[10px] text-slate-600 mt-1">{hint}</div>}
    </div>
  );
}
