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

export default function ServicesPage() {
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = () => {
    setError(null);
    setRefreshing(true);
    // Service data is not yet available from the backend
    setTimeout(() => setRefreshing(false), 500);
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100 mb-1">Services Intelligence</h1>
          <p className="text-sm text-slate-500">
            Monitor services, protocols, ports, availability, and HTTP behavior across all infrastructure
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
          placeholder="Search services, domains, or IPs..."
          disabled
        />
        <select
          className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
          disabled
        >
          <option value="">All Protocols</option>
          <option value="http">HTTP</option>
          <option value="https">HTTPS</option>
          <option value="ssh">SSH</option>
          <option value="smtp">SMTP</option>
        </select>
        <select
          className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
          disabled
        >
          <option value="">All Statuses</option>
          <option value="available">Available</option>
          <option value="unavailable">Unavailable</option>
          <option value="unknown">Unknown</option>
        </select>
      </div>

      {/* Service Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-8">
        <OverviewCard label="Total Services" value="—" icon="🔧" />
        <OverviewCard label="Active" value="—" icon="✓" />
        <OverviewCard label="Unavailable" value="—" icon="✗" />
        <OverviewCard label="HTTP" value="—" icon="🌐" />
        <OverviewCard label="HTTPS" value="—" icon="🔒" />
        <OverviewCard label="Recently Discovered" value="—" icon="🔍" />
        <OverviewCard label="Recently Disappeared" value="—" icon="📉" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Service Distribution */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Service Distribution</h3>
          <EmptyState 
            message="Service intelligence is not yet available"
            submessage="This feature requires service discovery and protocol analysis."
          />
        </div>

        {/* Service Availability Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Service Availability</h3>
          <EmptyState 
            message="Service availability data is not yet available"
            submessage="This feature requires historical service availability monitoring."
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* HTTP Status Distribution */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">HTTP Status Distribution</h3>
          <EmptyState 
            message="HTTP status data is not yet available"
            submessage="This feature requires HTTP response code tracking."
          />
        </div>

        {/* Response-Time Analytics */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Response-Time Analytics</h3>
          <EmptyState 
            message="Response-time data is not yet available"
            submessage="This feature requires service response time measurement."
          />
        </div>
      </div>

      {/* Service Changes Timeline */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Service Changes Timeline</h3>
        <EmptyState 
          message="Service change history is not yet available"
          submessage="This feature requires historical service observation data."
        />
      </div>

      {/* Services Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Services</h3>
        <EmptyState 
          message="Service data is not yet available"
          submessage="Service discovery and monitoring is planned for a future release. See ROADMAP.md for details."
        />
      </div>

      {/* Service Relationships */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Service Relationships</h3>
        <EmptyState 
          message="Service relationship visualization is not yet available"
          submessage="This feature will show domain → IP → service → certificate relationships."
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
