import { useState } from "react";

interface AuditEvent {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  resource: string;
  result: "SUCCESS" | "FAILURE";
  source?: string;
  category: string;
  status: string;
}

export default function AuditPage() {
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [userFilter, setUserFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [resourceFilter, setResourceFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  const handleRefresh = () => {
    setError(null);
    setRefreshing(true);
    // Audit log API is not yet available from the backend
    setTimeout(() => setRefreshing(false), 500);
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Audit Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-100 mb-1">Audit Logs</h1>
            <p className="text-sm text-slate-500">
              Security audit log viewer for tracking user actions, system events, and configuration changes
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

        {/* Audit Filter Bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex flex-wrap items-center gap-3 opacity-50">
          <input
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm flex-1 min-w-[200px]"
            placeholder="Search audit events..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            disabled
          />
          <input
            type="date"
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            value={dateRange.start}
            onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
            disabled
          />
          <input
            type="date"
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            value={dateRange.end}
            onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
            disabled
          />
          <input
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm w-32"
            placeholder="User"
            value={userFilter}
            onChange={(e) => setUserFilter(e.target.value)}
            disabled
          />
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            disabled
          >
            <option value="">All Actions</option>
          </select>
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            value={resourceFilter}
            onChange={(e) => setResourceFilter(e.target.value)}
            disabled
          >
            <option value="">All Resources</option>
          </select>
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            disabled
          >
            <option value="">All Categories</option>
          </select>
          <div className="text-xs text-slate-500 ml-auto">
            0 events
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Audit Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 opacity-50">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Activity Over Time</h3>
          <div className="h-32 flex items-center justify-center text-slate-600 text-sm">
            Audit timeline not available
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 opacity-50">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Actions by Category</h3>
          <div className="h-32 flex items-center justify-center text-slate-600 text-sm">
            Category breakdown not available
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 opacity-50">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Success vs Failed</h3>
          <div className="h-32 flex items-center justify-center text-slate-600 text-sm">
            Outcome distribution not available
          </div>
        </div>
      </div>

      {/* Split Layout: Event Stream + Detail Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Audit Event Stream */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Event Stream</h3>
          <div className="space-y-2 opacity-50">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-slate-800/30 border border-slate-700 rounded p-3">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs text-slate-500">Timestamp</span>
                  <span className="text-xs text-slate-400 ml-auto">Category</span>
                </div>
                <div className="text-xs text-slate-400 mb-1">Action by user</div>
                <div className="text-[10px] text-slate-500">Resource affected</div>
              </div>
            ))}
          </div>
          <EmptyState 
            message="No audit events available"
            submessage="Audit log tracking is not yet implemented in the backend."
          />
        </div>

        {/* Event Detail Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Event Details</h3>
          {selectedEvent ? (
            <div className="space-y-4">
              <div>
                <div className="text-xs text-slate-500 mb-1">Timestamp</div>
                <div className="text-sm text-slate-300">{selectedEvent.timestamp}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">User</div>
                <div className="text-sm text-slate-300">{selectedEvent.user}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Action</div>
                <div className="text-sm text-slate-300">{selectedEvent.action}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Resource</div>
                <div className="text-sm text-slate-300">{selectedEvent.resource}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Result</div>
                <div className={`text-sm ${selectedEvent.result === "SUCCESS" ? "text-emerald-400" : "text-rose-400"}`}>
                  {selectedEvent.result}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Category</div>
                <div className="text-sm text-slate-300">{selectedEvent.category}</div>
              </div>
              {selectedEvent.source && (
                <div>
                  <div className="text-xs text-slate-500 mb-1">Source</div>
                  <div className="text-sm text-slate-300">{selectedEvent.source}</div>
                </div>
              )}
            </div>
          ) : (
            <EmptyState 
              message="Select an event to view details"
              submessage="Event details will appear here when an audit event is selected."
            />
          )}
        </div>
      </div>
    </div>
  );
}

function EmptyState({ message, submessage, compact = false }: { message: string; submessage: string; compact?: boolean }) {
  return (
    <div className={compact ? "py-4" : "py-8"}>
      <div className="text-slate-500 text-sm mb-2">{message}</div>
      <div className="text-slate-600 text-xs">{submessage}</div>
    </div>
  );
}
