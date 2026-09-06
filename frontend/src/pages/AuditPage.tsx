import { useState, useEffect } from "react";
import { api, ApiError } from "../services/api";
import type { AuditEvent as AuditEventType } from "../types";

export default function AuditPage() {
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<AuditEventType | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [eventFilter, setEventFilter] = useState("");
  const [resourceFilter, setResourceFilter] = useState("");
  const [resultFilter, setResultFilter] = useState("");
  const [auditEvents, setAuditEvents] = useState<AuditEventType[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const loadAuditEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.listAuditEvents({
        event_type: eventFilter || undefined,
        resource_type: resourceFilter || undefined,
        result: resultFilter || undefined,
        date_from: dateRange.start || undefined,
        date_to: dateRange.end || undefined,
        page,
      });
      setAuditEvents(response.results);
      setTotalCount(response.count);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load audit events");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadAuditEvents();
  }, [page, eventFilter, resourceFilter, resultFilter, dateRange]);

  const handleRefresh = () => {
    setError(null);
    setRefreshing(true);
    loadAuditEvents();
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
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex flex-wrap items-center gap-3">
          <input
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm flex-1 min-w-[200px]"
            placeholder="Search audit events..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <input
            type="date"
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            value={dateRange.start}
            onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
          />
          <input
            type="date"
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            value={dateRange.end}
            onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
          />
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            value={eventFilter}
            onChange={(e) => setEventFilter(e.target.value)}
          >
            <option value="">All Event Types</option>
            <option value="LOGIN">Login</option>
            <option value="LOGOUT">Logout</option>
            <option value="REGISTRATION">Registration</option>
            <option value="DOMAIN_CREATED">Domain Created</option>
            <option value="DOMAIN_DELETED">Domain Deleted</option>
            <option value="INVESTIGATION_STARTED">Investigation Started</option>
            <option value="INVESTIGATION_COMPLETED">Investigation Completed</option>
            <option value="SETTINGS_UPDATED">Settings Updated</option>
          </select>
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            value={resourceFilter}
            onChange={(e) => setResourceFilter(e.target.value)}
          >
            <option value="">All Resources</option>
            <option value="Domain">Domain</option>
            <option value="Investigation">Investigation</option>
            <option value="UserSettings">User Settings</option>
            <option value="AnalystNote">Analyst Note</option>
          </select>
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
            value={resultFilter}
            onChange={(e) => setResultFilter(e.target.value)}
          >
            <option value="">All Results</option>
            <option value="SUCCESS">Success</option>
            <option value="FAILURE">Failure</option>
            <option value="PARTIAL">Partial</option>
          </select>
          <div className="text-xs text-slate-500 ml-auto">
            {totalCount} events
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
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Activity Over Time</h3>
          <div className="h-32 flex items-center justify-center text-slate-600 text-sm">
            Timeline visualization coming soon
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Actions by Category</h3>
          <div className="h-32 flex items-center justify-center text-slate-600 text-sm">
            Category breakdown coming soon
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Success vs Failed</h3>
          <div className="h-32 flex items-center justify-center text-slate-600 text-sm">
            Outcome distribution coming soon
          </div>
        </div>
      </div>

      {/* Split Layout: Event Stream + Detail Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Audit Event Stream */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Event Stream</h3>
          {loading ? (
            <div className="text-slate-500 text-sm">Loading audit events…</div>
          ) : auditEvents.length === 0 ? (
            <EmptyState 
              message="No audit events available"
              submessage="Audit events will appear here as you perform actions in the system."
            />
          ) : (
            <div className="space-y-2">
              {auditEvents.map((event) => (
                <div 
                  key={event.id} 
                  className={`bg-slate-800/30 border rounded p-3 cursor-pointer transition-colors ${
                    selectedEvent?.id === event.id 
                      ? "border-accent bg-accent/5" 
                      : "border-slate-700 hover:bg-slate-800/50"
                  }`}
                  onClick={() => setSelectedEvent(event)}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs text-slate-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded ml-auto ${
                      event.result === "SUCCESS" ? "bg-emerald-500/15 text-emerald-400" :
                      event.result === "FAILURE" ? "bg-rose-500/15 text-rose-400" :
                      "bg-amber-500/15 text-amber-400"
                    }`}>
                      {event.result}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mb-1">
                    {event.action} by {event.actor_username}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {event.resource_type}: {event.resource_name || "N/A"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Event Detail Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Event Details</h3>
          {selectedEvent ? (
            <div className="space-y-4">
              <div>
                <div className="text-xs text-slate-500 mb-1">Timestamp</div>
                <div className="text-sm text-slate-300">{new Date(selectedEvent.timestamp).toLocaleString()}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Actor</div>
                <div className="text-sm text-slate-300">{selectedEvent.actor_username}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Event Type</div>
                <div className="text-sm text-slate-300">{selectedEvent.event_type}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Action</div>
                <div className="text-sm text-slate-300">{selectedEvent.action}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Resource Type</div>
                <div className="text-sm text-slate-300">{selectedEvent.resource_type || "N/A"}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Resource Name</div>
                <div className="text-sm text-slate-300">{selectedEvent.resource_name || "N/A"}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Result</div>
                <div className={`text-sm ${selectedEvent.result === "SUCCESS" ? "text-emerald-400" : "text-rose-400"}`}>
                  {selectedEvent.result}
                </div>
              </div>
              {selectedEvent.ip_address && (
                <div>
                  <div className="text-xs text-slate-500 mb-1">IP Address</div>
                  <div className="text-sm text-slate-300">{selectedEvent.ip_address}</div>
                </div>
              )}
              {selectedEvent.user_agent && (
                <div>
                  <div className="text-xs text-slate-500 mb-1">User Agent</div>
                  <div className="text-sm text-slate-300 truncate">{selectedEvent.user_agent}</div>
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
