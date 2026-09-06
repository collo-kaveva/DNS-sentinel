import { useState } from "react";
import { api, ApiError } from "../services/api";

const STATUS_INDICATORS = {
  operational: { label: "Operational", color: "bg-emerald-500", text: "text-emerald-400" },
  degraded: { label: "Degraded", color: "bg-amber-500", text: "text-amber-400" },
  failed: { label: "Failed", color: "bg-rose-500", text: "text-rose-400" },
  unknown: { label: "Unknown", color: "bg-slate-500", text: "text-slate-400" },
};

const HEALTH_STATUS = {
  healthy: { label: "Healthy", color: "bg-emerald-500" },
  changed: { label: "Changed", color: "bg-amber-500" },
  warning: { label: "Warning", color: "bg-orange-500" },
  failed: { label: "Failed", color: "bg-rose-500" },
  unknown: { label: "Unknown", color: "bg-slate-500" },
};

export default function MonitoringPage() {
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [paused, setPaused] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<string | null>(null);

  const handleRefresh = () => {
    setError(null);
    setRefreshing(true);
    // Monitoring data is not yet available from the backend
    setTimeout(() => setRefreshing(false), 500);
  };

  const togglePause = () => {
    setPaused(!paused);
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Monitoring Control Bar */}
      <div className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-100 mb-1">Security Monitoring Control Center</h1>
            <p className="text-sm text-slate-500">
              Real-time monitoring of DNS, TLS, infrastructure, and service changes across all assets
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={togglePause}
              disabled={refreshing}
              className={`text-xs px-3 py-1.5 rounded font-medium ${
                paused 
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/30" 
                  : "bg-slate-800 text-slate-300 border border-slate-700"
              }`}
            >
              {paused ? "▶ Resume" : "⏸ Pause"}
            </button>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="text-xs bg-slate-800 border border-slate-700 text-slate-300 px-3 py-1.5 rounded hover:bg-slate-700 disabled:opacity-50"
            >
              {refreshing ? "Refreshing…" : "Refresh"}
            </button>
          </div>
        </div>

        {/* Compact Filter Bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex flex-wrap items-center gap-3 opacity-50">
          <input
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm flex-1 min-w-[200px]"
            placeholder="Search assets..."
            disabled
          />
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          >
            <option value="">All Assets</option>
          </select>
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          >
            <option value="">All Check Types</option>
          </select>
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          >
            <option value="">All Statuses</option>
            <option value="operational">Operational</option>
            <option value="degraded">Degraded</option>
            <option value="failed">Failed</option>
            <option value="unknown">Unknown</option>
          </select>
          <input
            type="date"
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          />
        </div>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Live Monitoring Status */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-slate-300">Monitoring Status</h3>
          <div className="flex items-center gap-2">
            <span className={`text-xs px-2 py-1 rounded ${STATUS_INDICATORS.unknown.text} bg-slate-800`}>
              ● Unknown
            </span>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 opacity-50">
          <StatusMetric label="Monitored Assets" value="—" />
          <StatusMetric label="Checks Running" value="—" />
          <StatusMetric label="Failed Checks" value="—" />
          <StatusMetric label="Last Scan" value="—" />
          <StatusMetric label="Next Check" value="—" />
          <StatusMetric label="Recently Changed" value="—" />
        </div>
        <EmptyState 
          message="Monitoring service status is not yet available"
          submessage="This feature requires the monitoring engine to be implemented."
          compact
        />
      </div>

      {/* Split Layout: Asset Monitoring Grid + Change Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Asset Monitoring Grid */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Asset Monitoring Grid</h3>
          <div className="grid grid-cols-2 gap-3 opacity-50">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-slate-800/50 border border-slate-700 rounded-lg p-3">
                <div className="text-xs font-mono text-slate-400 mb-2">example{i}.com</div>
                <div className="flex items-center gap-1 mb-1">
                  <span className="w-2 h-2 rounded-full bg-slate-600"></span>
                  <span className="text-[10px] text-slate-500">DNS</span>
                </div>
                <div className="flex items-center gap-1 mb-1">
                  <span className="w-2 h-2 rounded-full bg-slate-600"></span>
                  <span className="text-[10px] text-slate-500">TLS</span>
                </div>
                <div className="flex items-center gap-1 mb-1">
                  <span className="w-2 h-2 rounded-full bg-slate-600"></span>
                  <span className="text-[10px] text-slate-500">Infra</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-slate-600"></span>
                  <span className="text-[10px] text-slate-500">Services</span>
                </div>
              </div>
            ))}
          </div>
          <EmptyState 
            message="No assets currently monitored"
            submessage="Monitoring data is required to populate the asset grid."
            compact
          />
        </div>

        {/* Change Stream */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Change Stream</h3>
          <div className="space-y-2 opacity-50">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-slate-800/30 border border-slate-700 rounded p-2">
                <div className="text-[10px] text-slate-500">—</div>
                <div className="text-xs text-slate-400">Event type</div>
              </div>
            ))}
          </div>
          <EmptyState 
            message="No recent changes detected"
            submessage="Change stream requires monitoring event data."
            compact
          />
        </div>
      </div>

      {/* Monitoring Activity Visualization */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Monitoring Activity</h3>
        <div className="h-40 flex items-center justify-center opacity-50">
          <div className="text-slate-600 text-3xl">—</div>
        </div>
        <EmptyState 
          message="Monitoring activity data is not yet available"
          submessage="This feature requires historical monitoring activity tracking."
          compact
        />
      </div>

      {/* Asset Health Matrix */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Asset Health Matrix</h3>
        <div className="overflow-x-auto opacity-50">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="text-left py-2 px-3 text-slate-500 font-medium">Asset</th>
                <th className="text-center py-2 px-3 text-slate-500 font-medium">DNS</th>
                <th className="text-center py-2 px-3 text-slate-500 font-medium">TLS</th>
                <th className="text-center py-2 px-3 text-slate-500 font-medium">Infra</th>
                <th className="text-center py-2 px-3 text-slate-500 font-medium">Services</th>
                <th className="text-center py-2 px-3 text-slate-500 font-medium">Lifecycle</th>
              </tr>
            </thead>
            <tbody>
              {[1, 2, 3].map((i) => (
                <tr key={i} className="border-b border-slate-800">
                  <td className="py-2 px-3 text-slate-400">example{i}.com</td>
                  <td className="py-2 px-3 text-center">
                    <span className="inline-block w-3 h-3 rounded-full bg-slate-600"></span>
                  </td>
                  <td className="py-2 px-3 text-center">
                    <span className="inline-block w-3 h-3 rounded-full bg-slate-600"></span>
                  </td>
                  <td className="py-2 px-3 text-center">
                    <span className="inline-block w-3 h-3 rounded-full bg-slate-600"></span>
                  </td>
                  <td className="py-2 px-3 text-center">
                    <span className="inline-block w-3 h-3 rounded-full bg-slate-600"></span>
                  </td>
                  <td className="py-2 px-3 text-center">
                    <span className="inline-block w-3 h-3 rounded-full bg-slate-600"></span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <EmptyState 
          message="Asset health matrix is not yet available"
          submessage="This feature requires comprehensive monitoring data across all categories."
          compact
        />
      </div>

      {/* Monitoring Detail Drawer */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Monitoring Details</h3>
        <EmptyState 
          message="Select an asset to view monitoring details"
          submessage="Monitoring detail drawer requires asset selection and monitoring data."
        />
      </div>

      {/* Monitoring History */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Monitoring History</h3>
        <div className="space-y-2 opacity-50">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-3 text-xs text-slate-500">
              <span className="text-slate-600">—</span>
              <span>Event description</span>
            </div>
          ))}
        </div>
        <EmptyState 
          message="Monitoring history is not yet available"
          submessage="This feature requires chronological monitoring event tracking."
          compact
        />
      </div>
    </div>
  );
}

function StatusMetric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-lg font-semibold text-slate-100">{value}</div>
      <div className="text-[10px] text-slate-500">{label}</div>
    </div>
  );
}

function EmptyState({ message, submessage, compact = false }: { message: string; submessage?: string; compact?: boolean }) {
  if (compact) {
    return (
      <div className="text-center mt-4">
        <div className="text-xs text-slate-500">{message}</div>
        {submessage && <div className="text-[10px] text-slate-600 mt-1">{submessage}</div>}
      </div>
    );
  }
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <div className="text-slate-600 text-3xl mb-2">—</div>
      <div className="text-sm text-slate-500">{message}</div>
      {submessage && <div className="text-xs text-slate-600 mt-1">{submessage}</div>}
    </div>
  );
}
