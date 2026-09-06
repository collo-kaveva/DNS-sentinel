import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../services/api";
import type { Domain, DNSFinding, IPAddressInfo, ScanJob } from "../types";
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

export default function DashboardPage() {
  const [domains, setDomains] = useState<Domain[] | null>(null);
  const [allFindings, setAllFindings] = useState<DNSFinding[]>([]);
  const [allIpAddresses, setAllIpAddresses] = useState<IPAddressInfo[]>([]);
  const [recentJobs, setRecentJobs] = useState<ScanJob[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadDashboardData = useCallback(async () => {
    setError(null);
    setRefreshing(true);
    try {
      const [domainsRes] = await Promise.all([
        api.listDomains(),
      ]);
      setDomains(domainsRes.results);

      // Load findings, IPs, and jobs for each domain
      const findingsPromises = domainsRes.results.map(d => 
        api.dnsFindings(d.id).catch(() => [])
      );
      const ipPromises = domainsRes.results.map(d => 
        api.infrastructure(d.id).catch(() => [])
      );
      const jobsPromises = domainsRes.results.map(d => 
        api.jobs(d.id).catch(() => [])
      );

      const [findingsResults, ipResults, jobsResults] = await Promise.all([
        Promise.all(findingsPromises),
        Promise.all(ipPromises),
        Promise.all(jobsPromises),
      ]);

      setAllFindings(findingsResults.flat());
      setAllIpAddresses(ipResults.flat());
      setRecentJobs(jobsResults.flat().slice(0, 10));
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load dashboard data");
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const totalAssets = domains?.length ?? 0;
  const authorizedAssets = domains?.filter((d) => d.authorized).length ?? 0;
  const unauthorizedAssets = totalAssets - authorizedAssets;
  const highSeverityFindings = allFindings.filter(f => f.severity === "HIGH").length;
  const assetsRequiringInvestigation = highSeverityFindings > 0 ? domains?.filter(d => 
    allFindings.some(f => f.severity === "HIGH" && d.id === f.id.substring(0, 36))
  ).length ?? 0 : 0;

  // Infrastructure activity counts
  const ipCount = allIpAddresses.length;
  const currentIpCount = allIpAddresses.filter(ip => ip.association_status === "CURRENT").length;
  const cdnCount = allIpAddresses.filter(ip => ip.is_likely_cdn).length;

  // Recent activity from jobs
  const recentActivity = recentJobs.slice(0, 5);

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100 mb-1">Security Dashboard</h1>
          <p className="text-sm text-slate-500">
            Monitor domain infrastructure, DNS security, and asset lifecycle
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdate && (
            <div className="text-xs text-slate-500">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
          )}
          <button
            onClick={loadDashboardData}
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
        <div className="text-slate-500 text-sm">Loading dashboard data…</div>
      )}

      {domains !== null && (
        <>
          {/* Security Metrics Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4 mb-8">
            <MetricCard
              label="Total Assets"
              value={totalAssets}
              icon="📊"
              to="/domains"
            />
            <MetricCard
              label="Authorized"
              value={authorizedAssets}
              icon="✓"
              to="/domains"
              subtitle="For investigation"
            />
            <MetricCard
              label="Unauthorized"
              value={unauthorizedAssets}
              icon="⚠"
              to="/domains"
              subtitle="Requires authorization"
            />
            <MetricCard
              label="IP Addresses"
              value={ipCount}
              icon="🌐"
              to="/domains"
            />
            <MetricCard
              label="Current IPs"
              value={currentIpCount}
              icon="📍"
              to="/domains"
              subtitle="Active associations"
            />
            <MetricCard
              label="CDN Detected"
              value={cdnCount}
              icon="☁"
              to="/domains"
              subtitle="Proxy infrastructure"
            />
          </div>

          {/* Assets Requiring Investigation */}
          {highSeverityFindings > 0 && (
            <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 mb-8">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-rose-400">Attention Required</h3>
                <Link to="/domains" className="text-xs text-rose-400 hover:underline">
                  View all →
                </Link>
              </div>
              <div className="text-xs text-rose-300">
                {highSeverityFindings} high-severity finding(s) across {assetsRequiringInvestigation} asset(s) require investigation.
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Findings by Severity */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">DNS Findings by Severity</h3>
              {allFindings.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: "HIGH", value: allFindings.filter(f => f.severity === "HIGH").length },
                        { name: "MEDIUM", value: allFindings.filter(f => f.severity === "MEDIUM").length },
                        { name: "LOW", value: allFindings.filter(f => f.severity === "LOW").length },
                        { name: "INFO", value: allFindings.filter(f => f.severity === "INFO").length },
                      ].filter(d => d.value > 0)}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      <Cell fill={COLORS.rose} />
                      <Cell fill={COLORS.amber} />
                      <Cell fill={COLORS.slate} />
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
                <EmptyState message="No DNS findings data available" />
              )}
            </div>

            {/* IP Association Status */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">IP Association Status</h3>
              {allIpAddresses.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart
                    data={[
                      { name: "Current", value: allIpAddresses.filter(ip => ip.association_status === "CURRENT").length },
                      { name: "Historical", value: allIpAddresses.filter(ip => ip.association_status === "HISTORICAL").length },
                      { name: "Estimated", value: allIpAddresses.filter(ip => ip.association_status === "ESTIMATED").length },
                      { name: "Unknown", value: allIpAddresses.filter(ip => ip.association_status === "UNKNOWN").length },
                    ].filter(d => d.value > 0)}
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
                <EmptyState message="No infrastructure data available" />
              )}
            </div>
          </div>

          {/* Lifecycle Distribution - Not Yet Available */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Lifecycle Distribution</h3>
            <EmptyState 
              message="Lifecycle classification is not yet implemented"
              submessage="This feature will be available in a future phase. See docs/ROADMAP.md for details."
            />
          </div>

          {/* Lifecycle Trend - Not Yet Available */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Lifecycle Trend Over Time</h3>
            <EmptyState 
              message="Lifecycle trend data is not yet available"
              submessage="This feature will be available in a future phase. See docs/ROADMAP.md for details."
            />
          </div>

          {/* Infrastructure Activity */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Infrastructure Activity</h3>
            {allIpAddresses.length > 0 ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400 py-2 border-b border-slate-800">
                  <span>Total IP addresses observed</span>
                  <span className="text-slate-200">{ipCount}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 py-2 border-b border-slate-800">
                  <span>Current associations</span>
                  <span className="text-emerald-400">{currentIpCount}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 py-2 border-b border-slate-800">
                  <span>CDN/Proxy indicators detected</span>
                  <span className="text-amber-400">{cdnCount}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 py-2">
                  <span>Shared hosting indicators</span>
                  <span className="text-slate-200">{allIpAddresses.filter(ip => ip.is_likely_shared_hosting).length}</span>
                </div>
              </div>
            ) : (
              <EmptyState message="No infrastructure activity data available" />
            )}
          </div>

          {/* Recent Activity */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Recent Activity</h3>
            {recentActivity.length > 0 ? (
              <div className="space-y-3">
                {recentActivity.map((job) => (
                  <div key={job.id} className="flex items-start gap-3 text-xs py-2 border-b border-slate-800 last:border-0">
                    <div className={`w-2 h-2 rounded-full mt-1.5 ${
                      job.status === "COMPLETED" ? "bg-emerald-500" :
                      job.status === "FAILED" ? "bg-rose-500" :
                      job.status === "RUNNING" ? "bg-amber-500" :
                      "bg-slate-500"
                    }`} />
                    <div className="flex-1">
                      <div className="text-slate-300">{job.job_type.replace(/_/g, " ")}</div>
                      <div className="text-slate-500 mt-0.5">
                        {new Date(job.created_at).toLocaleString()} · {job.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState message="No recent activity" />
            )}
          </div>

          {/* Quick Actions */}
          <div className="flex items-center gap-4">
            <Link 
              to="/domains"
              className="text-sm bg-slate-800 border border-slate-700 text-slate-300 px-4 py-2 rounded-lg hover:bg-slate-700"
            >
              Manage Domains
            </Link>
          </div>
        </>
      )}
    </div>
  );
}

function MetricCard({ 
  label, 
  value, 
  icon, 
  to, 
  subtitle 
}: { 
  label: string; 
  value: number; 
  icon: string; 
  to: string;
  subtitle?: string;
}) {
  return (
    <Link to={to} className="block">
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition-colors">
        <div className="flex items-start justify-between mb-2">
          <span className="text-lg">{icon}</span>
          <span className="text-2xl font-semibold text-slate-100">{value}</span>
        </div>
        <div className="text-xs text-slate-500">{label}</div>
        {subtitle && <div className="text-[10px] text-slate-600 mt-0.5">{subtitle}</div>}
      </div>
    </Link>
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
