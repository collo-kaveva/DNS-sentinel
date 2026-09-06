import { useEffect, useState, useCallback, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../services/api";
import type { Domain, DNSRecord, DNSFinding, DNSObservation } from "../types";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip
} from "recharts";

const COLORS = {
  emerald: "#10b981",
  amber: "#f59e0b",
  orange: "#f97316",
  rose: "#f43f5e",
  slate: "#64748b",
  accent: "#22d3ee",
};

export default function DomainsPage() {
  const [domains, setDomains] = useState<Domain[] | null>(null);
  const [allDnsRecords, setAllDnsRecords] = useState<DNSRecord[]>([]);
  const [allFindings, setAllFindings] = useState<DNSFinding[]>([]);
  const [allObservations, setAllObservations] = useState<DNSObservation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterAuthorized, setFilterAuthorized] = useState<boolean | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [name, setName] = useState("");
  const [authorized, setAuthorized] = useState(false);
  const [creating, setCreating] = useState(false);

  const loadDnsData = useCallback(async () => {
    setError(null);
    setRefreshing(true);
    try {
      const [domainsRes] = await Promise.all([
        api.listDomains(),
      ]);
      setDomains(domainsRes.results);

      // Load DNS records, findings, and observations for each domain
      const recordsPromises = domainsRes.results.map(d => 
        api.dnsRecords(d.id).catch(() => [])
      );
      const findingsPromises = domainsRes.results.map(d => 
        api.dnsFindings(d.id).catch(() => [])
      );
      const observationsPromises = domainsRes.results.map(d => 
        api.dnsObservations(d.id).catch(() => [])
      );

      const [recordsResults, findingsResults, observationsResults] = await Promise.all([
        Promise.all(recordsPromises),
        Promise.all(findingsPromises),
        Promise.all(observationsPromises),
      ]);

      setAllDnsRecords(recordsResults.flat());
      setAllFindings(findingsResults.flat());
      setAllObservations(observationsResults.flat());
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load DNS data");
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadDnsData();
  }, [loadDnsData]);

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await api.createDomain({ name: name.trim(), authorized });
      setName("");
      setAuthorized(false);
      setShowAddForm(false);
      loadDnsData();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add domain.");
    } finally {
      setCreating(false);
    }
  }

  // Filter domains based on search and authorization
  const filteredDomains = domains?.filter(d => {
    const matchesSearch = d.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesAuth = filterAuthorized === null || d.authorized === filterAuthorized;
    return matchesSearch && matchesAuth;
  }) ?? [];

  // Calculate overview metrics
  const totalDomains = domains?.length ?? 0;
  const totalRecords = allDnsRecords.length;
  const aRecords = allDnsRecords.filter(r => r.record_type === "A").length;
  const aaaaRecords = allDnsRecords.filter(r => r.record_type === "AAAA").length;
  const cnameRecords = allDnsRecords.filter(r => r.record_type === "CNAME").length;
  const mxRecords = allDnsRecords.filter(r => r.record_type === "MX").length;
  const nsRecords = allDnsRecords.filter(r => r.record_type === "NS").length;
  const txtRecords = allDnsRecords.filter(r => r.record_type === "TXT").length;
  
  // Recently changed records (last_seen within last 7 days)
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
  const recentlyChanged = allDnsRecords.filter(r => new Date(r.last_seen) > sevenDaysAgo).length;

  // DNS record distribution data
  const recordTypeDistribution = [
    { name: "A", value: aRecords },
    { name: "AAAA", value: aaaaRecords },
    { name: "CNAME", value: cnameRecords },
    { name: "MX", value: mxRecords },
    { name: "NS", value: nsRecords },
    { name: "TXT", value: txtRecords },
  ].filter(d => d.value > 0);

  // Filter DNS records for table
  const filteredRecords = allDnsRecords.filter(r => {
    if (searchQuery) {
      return r.hostname.toLowerCase().includes(searchQuery.toLowerCase()) ||
             r.value.toLowerCase().includes(searchQuery.toLowerCase());
    }
    return true;
  });

  // High severity findings for attention section
  const highSeverityFindings = allFindings.filter(f => f.severity === "HIGH");

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100 mb-1">DNS Intelligence</h1>
          <p className="text-sm text-slate-500">
            Monitor DNS records, observations, and security findings across all domains
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdate && (
            <div className="text-xs text-slate-500">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
          )}
          <button
            onClick={loadDnsData}
            disabled={refreshing}
            className="text-xs bg-slate-800 border border-slate-700 text-slate-300 px-3 py-1.5 rounded hover:bg-slate-700 disabled:opacity-50"
          >
            {refreshing ? "Refreshing…" : "Refresh"}
          </button>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="text-xs bg-accent text-slate-950 px-3 py-1.5 rounded font-medium hover:bg-cyan-400"
          >
            {showAddForm ? "Cancel" : "Add Domain"}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {showAddForm && (
        <form
          onSubmit={handleAdd}
          className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-6 flex flex-col gap-3"
        >
          <input
            className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm"
            placeholder="example.com"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <label className="flex items-center gap-2 text-xs text-slate-400">
            <input
              type="checkbox"
              checked={authorized}
              onChange={(e) => setAuthorized(e.target.checked)}
            />
            I am authorized to investigate this domain's public infrastructure.
          </label>
          <button
            disabled={creating}
            className="self-start bg-accent text-slate-950 text-sm font-medium rounded px-4 py-2 disabled:opacity-50"
          >
            {creating ? "Adding…" : "Add domain"}
          </button>
        </form>
      )}

      {domains === null && !error && (
        <div className="text-slate-500 text-sm">Loading DNS data…</div>
      )}

      {domains !== null && (
        <>
          {/* Search and Filter Controls */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-6 flex flex-wrap items-center gap-4">
            <input
              className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm flex-1 min-w-[200px]"
              placeholder="Search domains or records..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <select
              className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
              value={filterAuthorized === null ? "" : filterAuthorized.toString()}
              onChange={(e) => setFilterAuthorized(e.target.value === "" ? null : e.target.value === "true")}
            >
              <option value="">All Domains</option>
              <option value="true">Authorized Only</option>
              <option value="false">Unauthorized Only</option>
            </select>
          </div>

          {/* DNS Overview Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4 mb-8">
            <OverviewCard label="Domains" value={totalDomains} icon="🌐" />
            <OverviewCard label="Records" value={totalRecords} icon="📋" />
            <OverviewCard label="A" value={aRecords} icon="📍" />
            <OverviewCard label="AAAA" value={aaaaRecords} icon="🔗" />
            <OverviewCard label="CNAME" value={cnameRecords} icon="🔄" />
            <OverviewCard label="MX" value={mxRecords} icon="📧" />
            <OverviewCard label="NS" value={nsRecords} icon="🌍" />
            <OverviewCard label="TXT" value={txtRecords} icon="📝" />
          </div>

          {/* Recently Changed Indicator */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Records changed in last 7 days</span>
              <span className="text-lg font-semibold text-accent">{recentlyChanged}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* DNS Record Distribution */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">DNS Record Distribution</h3>
              {recordTypeDistribution.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={recordTypeDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {recordTypeDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={[COLORS.accent, COLORS.emerald, COLORS.amber, COLORS.rose, COLORS.slate, COLORS.orange][index % 6]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px" }}
                      itemStyle={{ color: "#e2e8f0" }}
                    />
                    <Legend
                      wrapperStyle={{ fontSize: "12px", color: "#94a3b8" }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No DNS records data available" />
              )}
            </div>

            {/* DNS Activity Timeline - Not Yet Available */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">DNS Activity Timeline</h3>
              <EmptyState 
                message="Historical DNS activity timeline is not yet available"
                submessage="This feature requires aggregated historical data analysis."
              />
            </div>
          </div>

          {/* Attention Required Section */}
          {highSeverityFindings.length > 0 && (
            <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-5 mb-8">
              <h3 className="text-sm font-semibold text-rose-400 mb-3">Attention Required</h3>
              <div className="space-y-2">
                {highSeverityFindings.slice(0, 5).map((finding) => (
                  <div key={finding.id} className="bg-rose-500/5 border border-rose-500/20 rounded p-3">
                    <div className="text-xs font-semibold text-rose-400 mb-1">{finding.title}</div>
                    <div className="text-xs text-rose-300">{finding.description}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* DNS Records Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">DNS Records</h3>
            {filteredRecords.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-800">
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">Hostname</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">Type</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">Value</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">TTL</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">First Seen</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">Last Seen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRecords.slice(0, 50).map((record) => (
                      <tr key={record.id} className="border-b border-slate-800 hover:bg-slate-800/50">
                        <td className="py-2 px-3 font-mono text-slate-300">{record.hostname}</td>
                        <td className="py-2 px-3">
                          <span className="bg-accent/10 text-accent px-2 py-0.5 rounded text-xs">
                            {record.record_type}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-slate-400 truncate max-w-xs">{record.value}</td>
                        <td className="py-2 px-3 text-slate-500">{record.ttl ?? "—"}</td>
                        <td className="py-2 px-3 text-slate-500">{new Date(record.first_seen).toLocaleDateString()}</td>
                        <td className="py-2 px-3 text-slate-500">{new Date(record.last_seen).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredRecords.length > 50 && (
                  <div className="text-xs text-slate-500 mt-3 text-center">
                    Showing 50 of {filteredRecords.length} records
                  </div>
                )}
              </div>
            ) : (
              <EmptyState message="No DNS records available" />
            )}
          </div>

          {/* Domains List */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Domains</h3>
            {filteredDomains.length > 0 ? (
              <div className="flex flex-col gap-2">
                {filteredDomains.map((d) => (
                  <Link
                    key={d.id}
                    to={`/domains/${d.id}`}
                    className="bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-3 flex items-center justify-between hover:border-slate-600 transition-colors"
                  >
                    <div>
                      <div className="font-mono text-sm text-slate-200">{d.name}</div>
                      <div className="text-xs text-slate-500">
                        Added {new Date(d.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${
                      d.authorized 
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" 
                        : "bg-slate-500/10 text-slate-400 border border-slate-500/30"
                    }`}>
                      {d.authorized ? "Authorized" : "Not authorized"}
                    </span>
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState message="No domains match your filters" />
            )}
          </div>

          {/* DNS Relationship Visualization - Not Yet Available */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">DNS Relationship Visualization</h3>
            <EmptyState 
              message="DNS relationship visualization is not yet available"
              submessage="This feature will show domain → subdomain → record → IP relationships."
            />
          </div>
        </>
      )}
    </div>
  );
}

function OverviewCard({ label, value, icon }: { label: string; value: number; icon: string }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
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
