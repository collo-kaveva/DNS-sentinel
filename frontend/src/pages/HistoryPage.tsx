import { useState } from "react";
import { api, ApiError } from "../services/api";

const INTELLIGENCE_LABELS = {
  OBSERVED: { label: "OBSERVED", color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" },
  HISTORICAL: { label: "HISTORICAL", color: "bg-amber-500/10 text-amber-400 border-amber-500/30" },
  INFERRED: { label: "INFERRED", color: "bg-orange-500/10 text-orange-400 border-orange-500/30" },
  UNKNOWN: { label: "UNKNOWN", color: "bg-slate-500/10 text-slate-400 border-slate-500/30" },
};

const EVENT_TYPES = [
  "DNS record added",
  "DNS record removed",
  "DNS record changed",
  "IP changed",
  "Certificate appeared",
  "Certificate changed",
  "Certificate expired",
  "Service appeared",
  "Service disappeared",
  "ASN changed",
  "Provider changed",
  "Lifecycle classification changed",
];

export default function HistoryPage() {
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<string | null>(null);
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<"day" | "week" | "month" | "custom">("week");
  const [selectedAsset, setSelectedAsset] = useState<string | null>(null);

  const handleRefresh = () => {
    setError(null);
    setRefreshing(true);
    // Historical data is not yet available from the backend
    setTimeout(() => setRefreshing(false), 500);
  };

  const toggleExpand = (eventId: string) => {
    setExpandedEvent(expandedEvent === eventId ? null : eventId);
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Historical Explorer Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-100 mb-1">Historical Intelligence Explorer</h1>
            <p className="text-sm text-slate-500">
              Reconstruct how infrastructure changed over time with before/after comparisons and historical evidence
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
            placeholder="Search assets..."
            disabled
          />
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          >
            <option value="">All Event Types</option>
            {EVENT_TYPES.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          >
            <option value="">All Lifecycle</option>
          </select>
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          >
            <option value="">All Sources</option>
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

      {/* Time Navigation */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-2 opacity-50">
          <button disabled className="text-xs bg-slate-800 text-slate-400 px-3 py-1.5 rounded">
            ← Previous
          </button>
          <div className="flex-1 flex items-center justify-center gap-2">
            {["day", "week", "month", "custom"].map((range) => (
              <button
                key={range}
                disabled
                className={`text-xs px-3 py-1.5 rounded ${
                  timeRange === range
                    ? "bg-accent/10 text-accent border border-accent/30"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                {range.charAt(0).toUpperCase() + range.slice(1)}
              </button>
            ))}
          </div>
          <button disabled className="text-xs bg-slate-800 text-slate-400 px-3 py-1.5 rounded">
            Next →
          </button>
        </div>
        <EmptyState 
          message="Time navigation is not yet available"
          submessage="This feature requires historical observation data with timestamp support."
          compact
        />
      </div>

      {/* Split Layout: Timeline + Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Main Timeline (Primary Component) */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Historical Timeline</h3>
          <div className="relative">
            <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-slate-700"></div>
            <div className="space-y-4 opacity-50">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="relative pl-8">
                  <div className="absolute left-2 w-2.5 h-2.5 rounded-full bg-slate-600 border-2 border-slate-900"></div>
                  <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] text-slate-500">—</span>
                      <span className="text-[10px] text-slate-500">example{i}.com</span>
                    </div>
                    <div className="text-xs text-slate-400 mb-1">Event type</div>
                    <div className="flex items-center gap-2">
                      <IntelligenceLabel type="OBSERVED" />
                      <button disabled className="text-[10px] text-slate-500">
                        View details
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <EmptyState 
            message="No historical events recorded"
            submessage="Historical observation data is required to populate the timeline."
            compact
          />
        </div>

        {/* Before/After Comparison Workspace */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Before / After Comparison</h3>
          <div className="space-y-3 opacity-50">
            <div className="bg-slate-800/30 border border-slate-700 rounded p-3">
              <div className="text-[10px] text-slate-500 mb-1">BEFORE</div>
              <div className="text-xs text-slate-400">Previous state</div>
            </div>
            <div className="flex items-center justify-center">
              <span className="text-slate-600 text-xl">↓</span>
            </div>
            <div className="bg-slate-800/30 border border-slate-700 rounded p-3">
              <div className="text-[10px] text-slate-500 mb-1">CHANGE</div>
              <div className="text-xs text-slate-400">What changed</div>
            </div>
            <div className="flex items-center justify-center">
              <span className="text-slate-600 text-xl">↓</span>
            </div>
            <div className="bg-slate-800/30 border border-slate-700 rounded p-3">
              <div className="text-[10px] text-slate-500 mb-1">AFTER</div>
              <div className="text-xs text-slate-400">Current state</div>
            </div>
          </div>
          <EmptyState 
            message="Select an event to view before/after comparison"
            submessage="Comparison requires event selection and historical state data."
            compact
          />
        </div>
      </div>

      {/* Asset History View */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Asset History View</h3>
        <div className="flex items-center justify-center py-8 opacity-50">
          <div className="flex items-center gap-2 text-slate-600 text-sm">
            <span>Domain</span>
            <span className="text-xl">↓</span>
            <span>DNS</span>
            <span className="text-xl">↓</span>
            <span>IP</span>
            <span className="text-xl">↓</span>
            <span>Certificate</span>
            <span className="text-xl">↓</span>
            <span>Services</span>
            <span className="text-xl">↓</span>
            <span>ASN/Provider</span>
            <span className="text-xl">↓</span>
            <span>Lifecycle</span>
          </div>
        </div>
        <EmptyState 
          message="Asset history reconstruction is not yet available"
          submessage="This feature requires historical observation data for asset reconstruction."
          compact
        />
      </div>

      {/* Historical State Snapshot */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Historical State Snapshot</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 opacity-50">
          <div className="bg-slate-800/30 border border-slate-700 rounded p-3">
            <div className="text-[10px] text-slate-500 mb-1">DNS Records</div>
            <div className="text-xs text-slate-400">—</div>
          </div>
          <div className="bg-slate-800/30 border border-slate-700 rounded p-3">
            <div className="text-[10px] text-slate-500 mb-1">IP Addresses</div>
            <div className="text-xs text-slate-400">—</div>
          </div>
          <div className="bg-slate-800/30 border border-slate-700 rounded p-3">
            <div className="text-[10px] text-slate-500 mb-1">Certificates</div>
            <div className="text-xs text-slate-400">—</div>
          </div>
          <div className="bg-slate-800/30 border border-slate-700 rounded p-3">
            <div className="text-[10px] text-slate-500 mb-1">Services</div>
            <div className="text-xs text-slate-400">—</div>
          </div>
          <div className="bg-slate-800/30 border border-slate-700 rounded p-3">
            <div className="text-[10px] text-slate-500 mb-1">ASN</div>
            <div className="text-xs text-slate-400">—</div>
          </div>
          <div className="bg-slate-800/30 border border-slate-700 rounded p-3">
            <div className="text-[10px] text-slate-500 mb-1">Provider</div>
            <div className="text-xs text-slate-400">—</div>
          </div>
          <div className="bg-slate-800/30 border border-slate-700 rounded p-3">
            <div className="text-[10px] text-slate-500 mb-1">Lifecycle</div>
            <div className="text-xs text-slate-400">—</div>
          </div>
          <div className="bg-slate-800/30 border border-slate-700 rounded p-3">
            <div className="text-[10px] text-slate-500 mb-1">Confidence</div>
            <div className="text-xs text-slate-400">—</div>
          </div>
        </div>
        <EmptyState 
          message="Historical state snapshot is not yet available"
          submessage="This feature requires point-in-time historical observation data."
          compact
        />
      </div>

      {/* Change Density Visualization */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Change Density Visualization</h3>
        <div className="h-40 flex items-center justify-center opacity-50">
          <div className="text-slate-600 text-3xl">—</div>
        </div>
        <EmptyState 
          message="Change density visualization is not yet available"
          submessage="This feature requires sufficient historical data for calendar/heatmap visualization."
          compact
        />
      </div>

      {/* Lifecycle History */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Lifecycle History</h3>
        <div className="flex items-center justify-center py-8 opacity-50">
          <div className="flex items-center gap-2 text-slate-600 text-sm">
            <span>ACTIVE</span>
            <span className="text-xl">↓</span>
            <span>LEGACY</span>
            <span className="text-xl">↓</span>
            <span>POTENTIALLY_ABANDONED</span>
          </div>
        </div>
        <EmptyState 
          message="Lifecycle history is not yet available"
          submessage="This feature requires historical lifecycle classification tracking."
          compact
        />
      </div>

      {/* Historical Evidence */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Historical Evidence</h3>
        <div className="space-y-2 opacity-50">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-slate-800/30 border border-slate-700 rounded p-3">
              <div className="flex items-center gap-2 mb-1">
                <IntelligenceLabel type="OBSERVED" />
                <span className="text-[10px] text-slate-500">—</span>
              </div>
              <div className="text-xs text-slate-400">Observation {i}</div>
            </div>
          ))}
        </div>
        <EmptyState 
          message="Historical evidence is not yet available"
          submessage="This feature requires detailed historical observation data with provenance."
          compact
        />
      </div>
    </div>
  );
}

function IntelligenceLabel({ type }: { type: keyof typeof INTELLIGENCE_LABELS }) {
  const label = INTELLIGENCE_LABELS[type];
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded border ${label.color}`}>
      {label.label}
    </span>
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
