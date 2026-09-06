import { useState } from "react";
import { api, ApiError } from "../services/api";

const COLORS = {
  emerald: "#10b981",
  amber: "#f59e0b",
  orange: "#f97316",
  rose: "#f43f5e",
  slate: "#64748b",
  accent: "#22d3ee",
};

export default function CertificatesPage() {
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = () => {
    setError(null);
    setRefreshing(true);
    // Certificate data is not yet available from the backend
    setTimeout(() => setRefreshing(false), 500);
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100 mb-1">Certificates Intelligence</h1>
          <p className="text-sm text-slate-500">
            Monitor TLS/SSL certificates, expiration dates, issuers, and certificate health across all domains
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="text-xs bg-slate-800 border border-slate-700 text-slate-300 px-3 py-1.5 rounded hover:bg-slate-700 disabled:opacity-50"
          >
            {refreshing ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Search and Filter Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-6 flex flex-wrap items-center gap-4 opacity-50">
        <input
          className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm flex-1 min-w-[200px]"
          placeholder="Search certificates or domains..."
          disabled
        />
        <select
          className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
          disabled
        >
          <option value="">All Statuses</option>
          <option value="valid">Valid</option>
          <option value="expiring">Expiring Soon</option>
          <option value="expired">Expired</option>
        </select>
      </div>

      {/* Certificate Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
        <OverviewCard label="Total Certificates" value="—" icon="🔐" />
        <OverviewCard label="Valid" value="—" icon="✓" />
        <OverviewCard label="Expiring Soon" value="—" icon="⏰" />
        <OverviewCard label="Expired" value="—" icon="✗" />
        <OverviewCard label="Self-Signed" value="—" icon="🔒" />
        <OverviewCard label="Recently Changed" value="—" icon="📊" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Certificate Health Visualization */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Certificate Health</h3>
          <EmptyState 
            message="Certificate intelligence is not yet available"
            submessage="This feature requires TLS/SSL certificate data collection and analysis."
          />
        </div>

        {/* Certificate Expiration Timeline */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Certificate Expiration Timeline</h3>
          <EmptyState 
            message="Certificate expiration timeline is not yet available"
            submessage="This feature requires certificate validity period tracking."
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Certificate Issuer Distribution */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Certificate Issuer Distribution</h3>
          <EmptyState 
            message="Certificate issuer data is not yet available"
            submessage="This feature requires certificate authority (CA) information."
          />
        </div>

        {/* Certificate Changes Timeline */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Certificate Changes</h3>
          <EmptyState 
            message="Certificate change history is not yet available"
            submessage="This feature requires historical certificate observation data."
          />
        </div>
      </div>

      {/* Certificate Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Certificates</h3>
        <EmptyState 
          message="Certificate data is not yet available"
          submessage="TLS/SSL certificate collection and analysis is planned for a future release. See ROADMAP.md for details."
        />
      </div>

      {/* Certificate Relationships */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Certificate Relationships</h3>
        <EmptyState 
          message="Certificate relationship visualization is not yet available"
          submessage="This feature will show certificate → domain → IP → ASN → provider relationships."
        />
      </div>
    </div>
  );
}

function OverviewCard({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 opacity-50">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm">{icon}</span>
        <span className="text-xl font-semibold text-slate-100">{value}</span>
      </div>
      <div className="text-[10px] text-slate-500">{label}</div>
    </div>
  );
}

function EmptyState({ message, submessage }: { message: string; submessage?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <div className="text-slate-600 text-3xl mb-2">—</div>
      <div className="text-sm text-slate-500">{message}</div>
      {submessage && <div className="text-xs text-slate-600 mt-1">{submessage}</div>}
    </div>
  );
}
