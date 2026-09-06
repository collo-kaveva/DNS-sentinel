import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../services/api";
import type { Domain, IPAddressInfo } from "../types";
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

export default function InfrastructurePage() {
  const [domains, setDomains] = useState<Domain[] | null>(null);
  const [allIpAddresses, setAllIpAddresses] = useState<Array<IPAddressInfo & { domainName: string; domainId: string }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterVersion, setFilterVersion] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");

  const loadInfrastructureData = useCallback(async () => {
    setError(null);
    setRefreshing(true);
    try {
      const [domainsRes] = await Promise.all([
        api.listDomains(),
      ]);
      setDomains(domainsRes.results);

      // Load infrastructure data for each domain
      const ipPromises = domainsRes.results.map(async (d) => {
        try {
          const ips = await api.infrastructure(d.id);
          return ips.map(ip => ({ ...ip, domainName: d.name, domainId: d.id }));
        } catch {
          return [];
        }
      });

      const ipResults = await Promise.all(ipPromises);
      setAllIpAddresses(ipResults.flat());
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load infrastructure data");
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadInfrastructureData();
  }, [loadInfrastructureData]);

  // Filter infrastructure based on search and filters
  const filteredInfrastructure = allIpAddresses.filter(ip => {
    const matchesSearch = 
      ip.address.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (ip.reverse_dns && ip.reverse_dns.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (ip.asn && ip.asn.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (ip.organization && ip.organization.toLowerCase().includes(searchQuery.toLowerCase())) ||
      ip.domainName.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesVersion = filterVersion === "all" || ip.version === filterVersion;
    const matchesStatus = filterStatus === "all" || ip.association_status === filterStatus;
    
    return matchesSearch && matchesVersion && matchesStatus;
  });

  // Calculate overview metrics
  const totalIps = allIpAddresses.length;
  const ipv4Count = allIpAddresses.filter(ip => ip.version === "IPv4").length;
  const ipv6Count = allIpAddresses.filter(ip => ip.version === "IPv6").length;
  const uniqueAsns = new Set(allIpAddresses.filter(ip => ip.asn).map(ip => ip.asn)).size;
  const uniqueProviders = new Set(allIpAddresses.filter(ip => ip.organization).map(ip => ip.organization)).size;
  
  // Recently changed IPs (last_seen within last 7 days)
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
  const recentlyChanged = allIpAddresses.filter(ip => new Date(ip.last_seen) > sevenDaysAgo).length;
  
  // Infrastructure requiring investigation (CDN/shared hosting indicators)
  const requiringInvestigation = allIpAddresses.filter(ip => ip.is_likely_cdn || ip.is_likely_shared_hosting).length;

  // IP distribution data
  const ipDistribution = [
    { name: "IPv4", value: ipv4Count },
    { name: "IPv6", value: ipv6Count },
  ].filter(d => d.value > 0);

  // Association status distribution
  const statusDistribution = [
    { name: "Current", value: allIpAddresses.filter(ip => ip.association_status === "CURRENT").length },
    { name: "Historical", value: allIpAddresses.filter(ip => ip.association_status === "HISTORICAL").length },
    { name: "Estimated", value: allIpAddresses.filter(ip => ip.association_status === "ESTIMATED").length },
    { name: "Unknown", value: allIpAddresses.filter(ip => ip.association_status === "UNKNOWN").length },
  ].filter(d => d.value > 0);

  // Top ASNs
  const asnCounts = allIpAddresses
    .filter(ip => ip.asn)
    .reduce((acc, ip) => {
      const key = ip.asn!;
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  
  const topAsns = Object.entries(asnCounts)
    .map(([asn, count]) => ({ asn, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  // Top Providers
  const providerCounts = allIpAddresses
    .filter(ip => ip.organization)
    .reduce((acc, ip) => {
      const key = ip.organization!;
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  
  const topProviders = Object.entries(providerCounts)
    .map(([provider, count]) => ({ provider, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  // Infrastructure requiring attention
  const attentionItems = allIpAddresses.filter(ip => 
    ip.is_likely_cdn || ip.is_likely_shared_hosting || !ip.rdap_available
  ).slice(0, 5);

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100 mb-1">Infrastructure Intelligence</h1>
          <p className="text-sm text-slate-500">
            Monitor IP addresses, ASNs, providers, and infrastructure relationships across all domains
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdate && (
            <div className="text-xs text-slate-500">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
          )}
          <button
            onClick={loadInfrastructureData}
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

      {domains === null && !error && (
        <div className="text-slate-500 text-sm">Loading infrastructure data…</div>
      )}

      {domains !== null && (
        <>
          {/* Search and Filter Controls */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-6 flex flex-wrap items-center gap-4">
            <input
              className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm flex-1 min-w-[200px]"
              placeholder="Search IPs, ASNs, providers, or domains..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <select
              className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
              value={filterVersion}
              onChange={(e) => setFilterVersion(e.target.value)}
            >
              <option value="all">All IP Versions</option>
              <option value="IPv4">IPv4 Only</option>
              <option value="IPv6">IPv6 Only</option>
            </select>
            <select
              className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="CURRENT">Current</option>
              <option value="HISTORICAL">Historical</option>
              <option value="ESTIMATED">Estimated</option>
              <option value="UNKNOWN">Unknown</option>
            </select>
          </div>

          {/* Infrastructure Overview Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-8">
            <OverviewCard label="Total IPs" value={totalIps} icon="🌐" />
            <OverviewCard label="IPv4" value={ipv4Count} icon="📍" />
            <OverviewCard label="IPv6" value={ipv6Count} icon="🔗" />
            <OverviewCard label="Unique ASNs" value={uniqueAsns} icon="🏢" />
            <OverviewCard label="Providers" value={uniqueProviders} icon="🏭" />
            <OverviewCard label="Recent Changes" value={recentlyChanged} icon="📊" />
            <OverviewCard label="Needs Review" value={requiringInvestigation} icon="⚠" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* IP Distribution */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">IP Version Distribution</h3>
              {ipDistribution.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={ipDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      <Cell fill={COLORS.accent} />
                      <Cell fill={COLORS.emerald} />
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
                <EmptyState message="No IP data available" />
              )}
            </div>

            {/* Association Status Distribution */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Association Status</h3>
              {statusDistribution.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart
                    data={statusDistribution}
                    layout="vertical"
                    margin={{ left: 60, right: 20, top: 5, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis type="number" stroke="#64748b" fontSize={11} />
                    <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={55} />
                    <RechartsTooltip
                      contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px" }}
                      itemStyle={{ color: "#e2e8f0" }}
                    />
                    <Bar dataKey="value" fill={COLORS.accent} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No association status data available" />
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Top ASNs */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Top ASNs</h3>
              {topAsns.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart
                    data={topAsns}
                    layout="vertical"
                    margin={{ left: 60, right: 20, top: 5, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis type="number" stroke="#64748b" fontSize={11} />
                    <YAxis type="category" dataKey="asn" stroke="#64748b" fontSize={10} width={55} tick={{ fontSize: 10 }} />
                    <RechartsTooltip
                      contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px" }}
                      itemStyle={{ color: "#e2e8f0" }}
                    />
                    <Bar dataKey="count" fill={COLORS.amber} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No ASN data available" />
              )}
            </div>

            {/* Top Providers */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Top Providers</h3>
              {topProviders.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart
                    data={topProviders}
                    layout="vertical"
                    margin={{ left: 10, right: 20, top: 5, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis type="number" stroke="#64748b" fontSize={11} />
                    <YAxis type="category" dataKey="provider" stroke="#64748b" fontSize={10} width={120} tick={{ fontSize: 10 }} />
                    <RechartsTooltip
                      contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px" }}
                      itemStyle={{ color: "#e2e8f0" }}
                    />
                    <Bar dataKey="count" fill={COLORS.emerald} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No provider data available" />
              )}
            </div>
          </div>

          {/* Infrastructure Changes Timeline - Not Yet Available */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Infrastructure Changes Timeline</h3>
            <EmptyState 
              message="Historical infrastructure change timeline is not yet available"
              submessage="This feature requires aggregated historical infrastructure observation data."
            />
          </div>

          {/* Infrastructure Attention Section */}
          {attentionItems.length > 0 && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-5 mb-8">
              <h3 className="text-sm font-semibold text-amber-400 mb-3">Infrastructure Requiring Attention</h3>
              <div className="space-y-2">
                {attentionItems.map((ip, index) => (
                  <div key={`${ip.id}-${index}`} className="bg-amber-500/5 border border-amber-500/20 rounded p-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-xs font-semibold text-amber-400 mb-1">{ip.address}</div>
                        <div className="text-xs text-amber-300">
                          Domain: {ip.domainName}
                        </div>
                      </div>
                      <div className="text-xs text-amber-300">
                        {ip.is_likely_cdn && "CDN Indicator"}
                        {ip.is_likely_shared_hosting && "Shared Hosting"}
                        {!ip.rdap_available && "RDAP Unavailable"}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Infrastructure Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Infrastructure</h3>
            {filteredInfrastructure.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-800">
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">Domain</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">IP Address</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">Version</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">Status</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">ASN</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">Provider</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">Country</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">First Seen</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">Last Seen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredInfrastructure.slice(0, 50).map((ip) => (
                      <tr key={ip.id} className="border-b border-slate-800 hover:bg-slate-800/50">
                        <td className="py-2 px-3">
                          <Link to={`/domains/${ip.domainId}`} className="font-mono text-accent hover:underline">
                            {ip.domainName}
                          </Link>
                        </td>
                        <td className="py-2 px-3 font-mono text-slate-300">{ip.address}</td>
                        <td className="py-2 px-3">
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            ip.version === "IPv4" ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"
                          }`}>
                            {ip.version}
                          </span>
                        </td>
                        <td className="py-2 px-3">
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            ip.association_status === "CURRENT" ? "bg-emerald-500/10 text-emerald-400" :
                            ip.association_status === "HISTORICAL" ? "bg-slate-500/10 text-slate-400" :
                            ip.association_status === "ESTIMATED" ? "bg-amber-500/10 text-amber-400" :
                            "bg-rose-500/10 text-rose-400"
                          }`}>
                            {ip.association_status}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-slate-400">{ip.asn || "—"}</td>
                        <td className="py-2 px-3 text-slate-400 truncate max-w-xs">{ip.organization || "—"}</td>
                        <td className="py-2 px-3 text-slate-400">{ip.country || "—"}</td>
                        <td className="py-2 px-3 text-slate-500">{new Date(ip.first_seen).toLocaleDateString()}</td>
                        <td className="py-2 px-3 text-slate-500">{new Date(ip.last_seen).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredInfrastructure.length > 50 && (
                  <div className="text-xs text-slate-500 mt-3 text-center">
                    Showing 50 of {filteredInfrastructure.length} infrastructure entries
                  </div>
                )}
              </div>
            ) : (
              <EmptyState message="No infrastructure data available" />
            )}
          </div>

          {/* Infrastructure Relationships - Not Yet Available */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Infrastructure Relationships</h3>
            <EmptyState 
              message="Infrastructure relationship visualization is not yet available"
              submessage="This feature will show domain → subdomain → IP → ASN → provider relationships."
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
