import { useState } from "react";
import { api, ApiError } from "../services/api";

const LIFECYCLE_CATEGORIES = [
  { id: "ACTIVE", label: "Active", color: "bg-emerald-500" },
  { id: "LEGACY", label: "Legacy", color: "bg-amber-500" },
  { id: "POTENTIALLY_ABANDONED", label: "Potentially Abandoned", color: "bg-orange-500" },
  { id: "LIKELY_ABANDONED", label: "Likely Abandoned", color: "bg-rose-500" },
  { id: "UNKNOWN", label: "Unknown", color: "bg-slate-500" },
];

const CONFIDENCE_LEVELS = ["HIGH", "MEDIUM", "LOW", "UNKNOWN"];

export default function LifecyclePage() {
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedLifecycle, setSelectedLifecycle] = useState<string | null>(null);
  const [selectedConfidence, setSelectedConfidence] = useState<string | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<string | null>(null);

  const handleRefresh = () => {
    setError(null);
    setRefreshing(true);
    // Lifecycle data is not yet available from the backend
    setTimeout(() => setRefreshing(false), 500);
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Lifecycle Command Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-100 mb-1">Lifecycle Intelligence</h1>
            <p className="text-sm text-slate-500">
              Asset lifecycle classification based on observed DNS, certificate, service, and infrastructure evidence
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
            placeholder="Search assets or domains..."
            disabled
          />
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          >
            <option value="">All Lifecycle</option>
            {LIFECYCLE_CATEGORIES.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.label}</option>
            ))}
          </select>
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          >
            <option value="">All Confidence</option>
            {CONFIDENCE_LEVELS.map(level => (
              <option key={level} value={level}>{level}</option>
            ))}
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

      {/* Lifecycle Distribution - Primary Visual */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Lifecycle Distribution</h3>
        <div className="flex items-center gap-2 opacity-50">
          {LIFECYCLE_CATEGORIES.map(cat => (
            <button
              key={cat.id}
              disabled
              className={`flex-1 py-3 px-4 rounded-lg text-xs font-medium text-slate-950 ${cat.color} opacity-30`}
            >
              <div className="text-lg font-bold">—</div>
              <div className="text-[10px]">{cat.label}</div>
            </button>
          ))}
        </div>
        <EmptyState 
          message="Lifecycle classification is not yet available"
          submessage="This feature requires the lifecycle classification engine to be implemented."
          compact
        />
      </div>

      {/* Split Layout: Investigation Queue + Analysis Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Investigation Queue */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Investigation Queue</h3>
          <EmptyState 
            message="No assets requiring investigation"
            submessage="Lifecycle classification data is required to populate the investigation queue."
          />
        </div>

        {/* Lifecycle Decision Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Lifecycle Analysis</h3>
          <EmptyState 
            message="Select an asset to view lifecycle analysis"
            submessage="Lifecycle classification and evidence data are required for detailed analysis."
          />
        </div>
      </div>

      {/* Evidence Balance Visualization */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Evidence Balance</h3>
        <div className="grid grid-cols-2 gap-4 opacity-50">
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
            <div className="text-xs text-emerald-400 font-medium mb-2">Supporting Evidence</div>
            <div className="text-2xl font-bold text-emerald-400">—</div>
          </div>
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4">
            <div className="text-xs text-rose-400 font-medium mb-2">Contradicting Evidence</div>
            <div className="text-2xl font-bold text-rose-400">—</div>
          </div>
        </div>
        <EmptyState 
          message="Evidence balance data is not yet available"
          submessage="This feature requires lifecycle evidence analysis."
          compact
        />
      </div>

      {/* Confidence Analysis */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Classification Confidence</h3>
        <div className="flex items-center gap-2 opacity-50">
          {CONFIDENCE_LEVELS.map(level => (
            <button
              key={level}
              disabled
              className="flex-1 py-2 px-3 rounded bg-slate-800 border border-slate-700 text-xs text-slate-400"
            >
              {level}: —
            </button>
          ))}
        </div>
        <EmptyState 
          message="Confidence analysis is not yet available"
          submessage="This feature requires lifecycle confidence scoring."
          compact
        />
      </div>

      {/* Lifecycle Transition Timeline */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Lifecycle Transition Timeline</h3>
        <div className="flex items-center justify-center py-8 opacity-50">
          <div className="flex items-center gap-2 text-slate-600">
            <span className="text-lg">ACTIVE</span>
            <span className="text-2xl">→</span>
            <span className="text-lg">LEGACY</span>
            <span className="text-2xl">→</span>
            <span className="text-lg">POTENTIALLY_ABANDONED</span>
            <span className="text-2xl">→</span>
            <span className="text-lg">LIKELY_ABANDONED</span>
          </div>
        </div>
        <EmptyState 
          message="Historical lifecycle transition data is not yet available"
          submessage="This feature requires historical lifecycle classification tracking."
          compact
        />
      </div>

      {/* Evidence Breakdown */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Evidence Breakdown</h3>
        <EmptyState 
          message="Evidence breakdown is not yet available"
          submessage="This feature requires detailed lifecycle evidence collection and analysis."
        />
      </div>

      {/* Analyst Feedback */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Analyst Feedback</h3>
        <EmptyState 
          message="Analyst feedback functionality is not yet available"
          submessage="This feature will allow analysts to confirm, disagree, or add notes to lifecycle classifications."
        />
      </div>

      {/* Recommendations */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Investigation Recommendations</h3>
        <EmptyState 
          message="Recommendations are not yet available"
          submessage="This feature requires lifecycle analysis to generate context-aware investigation recommendations."
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
