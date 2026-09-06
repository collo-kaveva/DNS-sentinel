import { useState } from "react";
import { api, ApiError } from "../services/api";

const INTELLIGENCE_LABELS = {
  OBSERVED: { label: "OBSERVED", color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" },
  HISTORICAL: { label: "HISTORICAL", color: "bg-amber-500/10 text-amber-400 border-amber-500/30" },
  INFERRED: { label: "INFERRED", color: "bg-orange-500/10 text-orange-400 border-orange-500/30" },
  ANALYST: { label: "ANALYST", color: "bg-blue-500/10 text-blue-400 border-blue-500/30" },
  UNKNOWN: { label: "UNKNOWN", color: "bg-slate-500/10 text-slate-400 border-slate-500/30" },
};

const REPORT_SECTIONS = [
  "Executive Summary",
  "Scope",
  "Key Observations",
  "Infrastructure Findings",
  "DNS Findings",
  "Certificate Findings",
  "Service Findings",
  "Lifecycle Assessment",
  "Historical Changes",
  "Evidence",
  "Security Findings",
  "Recommendations",
  "Limitations",
];

export default function ReportsPage() {
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [view, setView] = useState<"library" | "create" | "preview">("library");
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [creationStep, setCreationStep] = useState<1 | 2 | 3 | 4>(1);

  const handleRefresh = () => {
    setError(null);
    setRefreshing(true);
    // Report data is not yet available from the backend
    setTimeout(() => setRefreshing(false), 500);
  };

  const handleCreateReport = () => {
    setView("create");
    setCreationStep(1);
  };

  const handleOpenReport = (reportId: string) => {
    setSelectedReport(reportId);
    setView("preview");
  };

  const handleBackToLibrary = () => {
    setView("library");
    setSelectedReport(null);
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Report Workspace Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-100 mb-1">Security Intelligence Reports</h1>
            <p className="text-sm text-slate-500">
              Generate, review, and manage security intelligence reports with structured findings and evidence
            </p>
          </div>
          <div className="flex items-center gap-3">
            {view === "library" && (
              <button
                onClick={handleCreateReport}
                className="text-xs bg-accent/10 text-accent border border-accent/30 px-3 py-1.5 rounded hover:bg-accent/20"
              >
                + Create Report
              </button>
            )}
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
            placeholder="Search reports..."
            disabled
          />
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            disabled
          >
            <option value="">All Status</option>
            <option value="draft">Draft</option>
            <option value="generated">Generated</option>
            <option value="archived">Archived</option>
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

      {/* Report Library View */}
      {view === "library" && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-300">Report Library</h3>
            <div className="flex items-center gap-2 opacity-50">
              <button disabled className="text-xs text-slate-400">Grid</button>
              <button disabled className="text-xs text-slate-400">List</button>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 opacity-50">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
                <div className="text-sm font-medium text-slate-400 mb-2">Security Intelligence Report {i}</div>
                <div className="text-[10px] text-slate-500 mb-1">Created: —</div>
                <div className="text-[10px] text-slate-500 mb-1">Assets: —</div>
                <div className="text-[10px] text-slate-500 mb-3">Status: —</div>
                <div className="flex gap-2">
                  <button disabled className="text-xs bg-slate-700 text-slate-400 px-2 py-1 rounded">Open</button>
                  <button disabled className="text-xs bg-slate-700 text-slate-400 px-2 py-1 rounded">Delete</button>
                </div>
              </div>
            ))}
          </div>
          <EmptyState 
            message="No reports have been generated yet"
            submessage="Create your first report to begin documenting security intelligence findings."
          />
        </div>
      )}

      {/* Report Creation Workspace */}
      {view === "create" && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={handleBackToLibrary}
              className="text-xs text-slate-400 hover:text-slate-300"
            >
              ← Back to Library
            </button>
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4].map((step) => (
                <div
                  key={step}
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs ${
                    step === creationStep
                      ? "bg-accent text-slate-950"
                      : step < creationStep
                      ? "bg-emerald-500 text-slate-950"
                      : "bg-slate-800 text-slate-500"
                  }`}
                >
                  {step}
                </div>
              ))}
            </div>
          </div>

          {/* Step 1: Scope */}
          {creationStep === 1 && (
            <div className="opacity-50">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Step 1: Scope</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-xs text-slate-500 mb-1 block">Assets/Domains</label>
                  <select disabled className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm">
                    <option>Select assets...</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500 mb-1 block">Lifecycle Classifications</label>
                  <select disabled className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm">
                    <option>All classifications</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500 mb-1 block">Date Range</label>
                  <input disabled type="date" className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                </div>
              </div>
              <EmptyState 
                message="Report scope selection is not yet available"
                submessage="This feature requires report generation backend support."
                compact
              />
            </div>
          )}

          {/* Step 2: Sections */}
          {creationStep === 2 && (
            <div className="opacity-50">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Step 2: Sections</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {REPORT_SECTIONS.map((section) => (
                  <label key={section} className="flex items-center gap-2 text-xs text-slate-400">
                    <input type="checkbox" disabled className="rounded" />
                    {section}
                  </label>
                ))}
              </div>
              <EmptyState 
                message="Report section selection is not yet available"
                submessage="This feature requires report generation backend support."
                compact
              />
            </div>
          )}

          {/* Step 3: Review */}
          {creationStep === 3 && (
            <div className="opacity-50">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Step 3: Review</h3>
              <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
                <div className="text-xs text-slate-500">Report preview will appear here</div>
              </div>
              <EmptyState 
                message="Report preview is not yet available"
                submessage="This feature requires report generation backend support."
                compact
              />
            </div>
          )}

          {/* Step 4: Generate */}
          {creationStep === 4 && (
            <div className="opacity-50">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Step 4: Generate</h3>
              <button disabled className="text-xs bg-slate-800 text-slate-400 px-4 py-2 rounded">
                Generate Report
              </button>
              <EmptyState 
                message="Report generation is not yet available"
                submessage="This feature requires report generation backend support."
                compact
              />
            </div>
          )}

          <div className="flex justify-between mt-6">
            <button
              disabled={creationStep === 1}
              onClick={() => setCreationStep((creationStep - 1) as 1 | 2 | 3 | 4)}
              className="text-xs bg-slate-800 text-slate-300 px-3 py-1.5 rounded disabled:opacity-50"
            >
              Previous
            </button>
            <button
              disabled={creationStep === 4}
              onClick={() => setCreationStep((creationStep + 1) as 1 | 2 | 3 | 4)}
              className="text-xs bg-accent/10 text-accent border border-accent/30 px-3 py-1.5 rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Report Preview View */}
      {view === "preview" && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={handleBackToLibrary}
              className="text-xs text-slate-400 hover:text-slate-300"
            >
              ← Back to Library
            </button>
            <div className="flex items-center gap-2 opacity-50">
              <button disabled className="text-xs bg-slate-800 text-slate-400 px-3 py-1.5 rounded">
                Export PDF
              </button>
              <button disabled className="text-xs bg-slate-800 text-slate-400 px-3 py-1.5 rounded">
                Export CSV
              </button>
              <button disabled className="text-xs bg-slate-800 text-slate-400 px-3 py-1.5 rounded">
                Print
              </button>
            </div>
          </div>

          {/* Document-style Report Preview */}
          <div className="bg-slate-950 border border-slate-800 rounded-lg p-6 opacity-50">
            <h2 className="text-lg font-semibold text-slate-100 mb-2">Security Intelligence Report</h2>
            <div className="text-xs text-slate-500 mb-6">Generated: — | Scope: —</div>

            {/* Executive Summary */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Executive Summary</h3>
              <div className="text-xs text-slate-500">—</div>
            </div>

            {/* Scope */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Scope</h3>
              <div className="text-xs text-slate-500">—</div>
            </div>

            {/* Key Observations */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Key Observations</h3>
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div key={i} className="bg-slate-800/30 border border-slate-700 rounded p-2">
                    <IntelligenceLabel type="OBSERVED" />
                    <div className="text-xs text-slate-400 mt-1">Observation {i}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Infrastructure Findings */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Infrastructure Findings</h3>
              <div className="text-xs text-slate-500">—</div>
            </div>

            {/* DNS Findings */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">DNS Findings</h3>
              <div className="text-xs text-slate-500">—</div>
            </div>

            {/* Certificate Findings */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Certificate Findings</h3>
              <div className="text-xs text-slate-500">—</div>
            </div>

            {/* Service Findings */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Service Findings</h3>
              <div className="text-xs text-slate-500">—</div>
            </div>

            {/* Lifecycle Assessment */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Lifecycle Assessment</h3>
              <div className="flex items-center gap-2 mb-2">
                {["Active", "Legacy", "Potentially Abandoned", "Likely Abandoned", "Unknown"].map((cat) => (
                  <span key={cat} className="text-[10px] bg-slate-800 text-slate-400 px-2 py-1 rounded">
                    {cat}: —
                  </span>
                ))}
              </div>
            </div>

            {/* Historical Changes */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Historical Changes</h3>
              <div className="text-xs text-slate-500">—</div>
            </div>

            {/* Evidence */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Evidence</h3>
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div key={i} className="bg-slate-800/30 border border-slate-700 rounded p-2">
                    <div className="flex items-center gap-2 mb-1">
                      <IntelligenceLabel type="OBSERVED" />
                      <span className="text-[10px] text-slate-500">Asset: —</span>
                    </div>
                    <div className="text-xs text-slate-400">Evidence {i}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Security Findings */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Security Findings</h3>
              <div className="text-xs text-slate-500">—</div>
            </div>

            {/* Recommendations */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Recommendations</h3>
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div key={i} className="bg-slate-800/30 border border-slate-700 rounded p-2">
                    <IntelligenceLabel type="INFERRED" />
                    <div className="text-xs text-slate-400 mt-1">Recommendation {i}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Limitations */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Limitations</h3>
              <div className="text-xs text-slate-500">—</div>
            </div>
          </div>

          <EmptyState 
            message="Report preview is not yet available"
            submessage="This feature requires report generation and data aggregation backend support."
          />
        </div>
      )}

      {/* Report Comparison */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Report Comparison</h3>
        <div className="flex items-center justify-center py-8 opacity-50">
          <div className="flex items-center gap-4 text-slate-600 text-sm">
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <div className="text-xs">Report A</div>
            </div>
            <span className="text-2xl">vs</span>
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <div className="text-xs">Report B</div>
            </div>
          </div>
        </div>
        <EmptyState 
          message="Report comparison is not yet available"
          submessage="This feature requires historical report data for comparison analysis."
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
