import { useState } from "react";
import { api, ApiError } from "../services/api";

const SEVERITY_LEVELS = [
  { id: "CRITICAL", label: "Critical", color: "bg-rose-500", text: "text-rose-400" },
  { id: "HIGH", label: "High", color: "bg-orange-500", text: "text-orange-400" },
  { id: "MEDIUM", label: "Medium", color: "bg-amber-500", text: "text-amber-400" },
  { id: "LOW", label: "Low", color: "bg-emerald-500", text: "text-emerald-400" },
  { id: "INFORMATIONAL", label: "Informational", color: "bg-slate-500", text: "text-slate-400" },
];

const ALERT_STATES = ["NEW", "OPEN", "ACKNOWLEDGED", "RESOLVED", "DISMISSED", "UNKNOWN"];

export default function AlertsPage() {
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<string | null>(null);
  const [expandedAlert, setExpandedAlert] = useState<string | null>(null);

  const handleRefresh = () => {
    setError(null);
    setRefreshing(true);
    // Alert data is not yet available from the backend
    setTimeout(() => setRefreshing(false), 500);
  };

  const toggleExpand = (alertId: string) => {
    setExpandedAlert(expandedAlert === alertId ? null : alertId);
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Alert Command Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-100 mb-1">Security Alert Triage Center</h1>
            <p className="text-sm text-slate-500">
              Investigate and triage security alerts based on DNS, certificate, infrastructure, and service changes
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

        {/* Compact Filter Bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex flex-wrap items-center gap-3 opacity-50">
          <input
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm flex-1 min-w-[200px]"
            placeholder="Search alerts..."
            disabled
          />
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          >
            <option value="">All Severity</option>
            {SEVERITY_LEVELS.map(level => (
              <option key={level.id} value={level.id}>{level.label}</option>
            ))}
          </select>
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          >
            <option value="">All Status</option>
            {ALERT_STATES.map(state => (
              <option key={state} value={state}>{state}</option>
            ))}
          </select>
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          >
            <option value="">All Types</option>
          </select>
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          >
            <option value="">All Lifecycle</option>
          </select>
          <input
            type="date"
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          />
          <div className="text-xs text-slate-500 ml-auto">
            0 alerts
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Alert Priority Overview Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-2 opacity-50">
          {SEVERITY_LEVELS.map(level => (
            <button
              key={level.id}
              disabled
              className={`flex-1 py-2 px-3 rounded text-xs font-medium text-slate-950 ${level.color} opacity-30`}
            >
              {level.label}: 0
            </button>
          ))}
          <button
            disabled
            className="flex-1 py-2 px-3 rounded text-xs font-medium text-slate-300 bg-slate-800 opacity-30"
          >
            Unresolved: 0
          </button>
        </div>
        <EmptyState 
          message="Alert priority overview is not yet available"
          submessage="This feature requires alert generation and severity classification."
          compact
        />
      </div>

      {/* Split Layout: Alert Triage Queue + Investigation Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Alert Triage Queue */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Alert Triage Queue</h3>
          <div className="space-y-2 opacity-50">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-slate-800/30 border border-slate-700 rounded p-3">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2 h-2 rounded-full bg-slate-600"></span>
                  <span className="text-xs text-slate-400">Severity</span>
                  <span className="text-[10px] text-slate-500 ml-auto">—</span>
                </div>
                <div className="text-xs text-slate-400 mb-1">Alert type</div>
                <div className="text-[10px] text-slate-500">example{i}.com</div>
              </div>
            ))}
          </div>
          <EmptyState 
            message="No alerts require attention"
            submessage="Alert generation and triage data are required to populate the queue."
            compact
          />
        </div>

        {/* Alert Investigation Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Alert Investigation</h3>
          <EmptyState 
            message="Select an alert to view investigation details"
            submessage="Alert investigation requires alert selection and detailed alert data."
          />
        </div>
      </div>

      {/* Alert Timeline */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Alert Timeline</h3>
        <div className="flex items-center justify-center py-8 opacity-50">
          <div className="flex items-center gap-2 text-slate-600 text-sm">
            <span>Detection</span>
            <span className="text-xl">→</span>
            <span>Observation</span>
            <span className="text-xl">→</span>
            <span>Change</span>
            <span className="text-xl">→</span>
            <span>Alert Generated</span>
            <span className="text-xl">→</span>
            <span>Analyst Action</span>
          </div>
        </div>
        <EmptyState 
          message="Alert timeline data is not yet available"
          submessage="This feature requires chronological alert event tracking."
          compact
        />
      </div>

      {/* Alert Correlation */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Alert Correlation</h3>
        <div className="flex items-center justify-center py-8 opacity-50">
          <div className="flex items-center gap-2 text-slate-600 text-sm">
            <span>Domain</span>
            <span className="text-xl">→</span>
            <span>IP Changed</span>
            <span className="text-xl">→</span>
            <span>ASN Changed</span>
            <span className="text-xl">→</span>
            <span>Service Disappeared</span>
            <span className="text-xl">→</span>
            <span>Lifecycle Changed</span>
          </div>
        </div>
        <EmptyState 
          message="Alert correlation data is not yet available"
          submessage="This feature requires alert relationship analysis."
          compact
        />
      </div>

      {/* Triage Actions */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Triage Actions</h3>
        <div className="flex flex-wrap gap-2 opacity-50">
          <button disabled className="text-xs bg-slate-800 border border-slate-700 text-slate-400 px-3 py-1.5 rounded">
            Acknowledge
          </button>
          <button disabled className="text-xs bg-slate-800 border border-slate-700 text-slate-400 px-3 py-1.5 rounded">
            Resolve
          </button>
          <button disabled className="text-xs bg-slate-800 border border-slate-700 text-slate-400 px-3 py-1.5 rounded">
            Reopen
          </button>
          <button disabled className="text-xs bg-slate-800 border border-slate-700 text-slate-400 px-3 py-1.5 rounded">
            Mark for Investigation
          </button>
          <button disabled className="text-xs bg-slate-800 border border-slate-700 text-slate-400 px-3 py-1.5 rounded">
            Add Analyst Note
          </button>
        </div>
        <EmptyState 
          message="Triage actions are not yet available"
          submessage="This feature requires alert state management and analyst action support."
          compact
        />
      </div>

      {/* Analyst Notes */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Analyst Notes</h3>
        <EmptyState 
          message="Analyst notes functionality is not yet available"
          submessage="This feature will allow analysts to add notes and view previous notes with attribution."
        />
      </div>

      {/* Alert Analytics */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Alert Analytics</h3>
        <div className="h-40 flex items-center justify-center opacity-50">
          <div className="text-slate-600 text-3xl">—</div>
        </div>
        <EmptyState 
          message="Alert analytics are not yet available"
          submessage="This feature requires historical alert data for meaningful visualizations."
          compact
        />
      </div>
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
