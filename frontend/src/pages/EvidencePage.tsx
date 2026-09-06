import { useState, useEffect } from "react";
import { api, ApiError } from "../services/api";
import type { Domain, DNSObservation, IPAddressInfo, DNSRecord } from "../types";

interface EvidenceNode {
  id: string;
  type: "domain" | "subdomain" | "ip" | "certificate" | "service" | "asn" | "provider" | "observation" | "alert" | "lifecycle";
  name: string;
  data?: any;
}

interface EvidenceEdge {
  from: string;
  to: string;
  label: string;
}

export default function EvidencePage() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [dnsObservations, setDnsObservations] = useState<DNSObservation[]>([]);
  const [infrastructure, setInfrastructure] = useState<IPAddressInfo[]>([]);
  const [dnsRecords, setDnsRecords] = useState<DNSRecord[]>([]);
  const [selectedNode, setSelectedNode] = useState<EvidenceNode | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [evidenceTypeFilter, setEvidenceTypeFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [confidenceFilter, setConfidenceFilter] = useState("");

  useEffect(() => {
    loadEvidenceData();
  }, []);

  const loadEvidenceData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [domainsRes] = await Promise.all([
        api.listDomains(),
      ]);
      setDomains(domainsRes.results);
      
      if (domainsRes.results.length > 0) {
        setSelectedDomain(domainsRes.results[0].id);
        await loadDomainEvidence(domainsRes.results[0].id);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load evidence data");
    } finally {
      setLoading(false);
    }
  };

  const loadDomainEvidence = async (domainId: string) => {
    try {
      const [obsData, infraData, recordsData] = await Promise.all([
        api.dnsObservations(domainId).catch(() => []),
        api.infrastructure(domainId).catch(() => []),
        api.dnsRecords(domainId).catch(() => []),
      ]);
      setDnsObservations(obsData);
      setInfrastructure(infraData);
      setDnsRecords(recordsData);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load domain evidence");
    }
  };

  const handleDomainChange = (domainId: string) => {
    setSelectedDomain(domainId);
    loadDomainEvidence(domainId);
    setSelectedNode(null);
  };

  // Build evidence graph nodes
  const buildEvidenceNodes = (): EvidenceNode[] => {
    const nodes: EvidenceNode[] = [];
    
    const domain = domains.find(d => d.id === selectedDomain);
    if (domain) {
      nodes.push({
        id: domain.id,
        type: "domain",
        name: domain.name,
        data: domain,
      });
    }

    // Add IP addresses as nodes
    infrastructure.forEach(ip => {
      nodes.push({
        id: ip.id,
        type: "ip",
        name: ip.address,
        data: ip,
      });
    });

    // Add DNS observations as nodes
    dnsObservations.forEach(obs => {
      nodes.push({
        id: obs.id,
        type: "observation",
        name: `${obs.hostname} (${obs.record_type})`,
        data: obs,
      });
    });

    return nodes;
  };

  // Build evidence graph edges
  const buildEvidenceEdges = (): EvidenceEdge[] => {
    const edges: EvidenceEdge[] = [];
    
    const domain = domains.find(d => d.id === selectedDomain);
    if (domain) {
      // Domain to IP edges
      infrastructure.forEach(ip => {
        edges.push({
          from: domain.id,
          to: ip.id,
          label: "resolves to",
        });
      });

      // Domain to observation edges
      dnsObservations.forEach(obs => {
        edges.push({
          from: domain.id,
          to: obs.id,
          label: "observed",
        });
      });
    }

    return edges;
  };

  const nodes = buildEvidenceNodes();
  const edges = buildEvidenceEdges();

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="text-slate-500 text-sm">Loading evidence data…</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Evidence Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-100 mb-1">Evidence Explorer</h1>
            <p className="text-sm text-slate-500">
              Visualize evidence relationships and explore how infrastructure entities are connected
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={loadEvidenceData}
              className="text-xs bg-slate-800 border border-slate-700 text-slate-300 px-3 py-1.5 rounded hover:bg-slate-700"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Domain Selector */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
          <select
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm w-full md:w-64"
            value={selectedDomain || ""}
            onChange={(e) => handleDomainChange(e.target.value)}
          >
            <option value="">Select a domain...</option>
            {domains.map(domain => (
              <option key={domain.id} value={domain.id}>
                {domain.name} {domain.authorized ? "(Authorized)" : "(Unauthorized)"}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {!selectedDomain && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-8 text-center">
          <div className="text-slate-500 text-sm mb-2">Select a domain to explore evidence</div>
          <div className="text-slate-600 text-xs">Choose a domain from the dropdown above to view its evidence graph</div>
        </div>
      )}

      {selectedDomain && (
        <div className="flex gap-6">
          {/* Left: Evidence Filters */}
          <aside className="w-56 flex-shrink-0">
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-4">
              <h3 className="text-sm font-semibold text-slate-300">Filters</h3>
              
              <div>
                <label className="text-xs text-slate-500 mb-1 block">Evidence Type</label>
                <select
                  className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm w-full"
                  value={evidenceTypeFilter}
                  onChange={(e) => setEvidenceTypeFilter(e.target.value)}
                >
                  <option value="">All Types</option>
                  <option value="domain">Domain</option>
                  <option value="ip">IP Address</option>
                  <option value="observation">Observation</option>
                  <option value="certificate">Certificate</option>
                  <option value="service">Service</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-500 mb-1 block">Source</label>
                <select
                  className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm w-full"
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                >
                  <option value="">All Sources</option>
                  <option value="Public DNS">Public DNS</option>
                  <option value="RDAP">RDAP</option>
                  <option value="Certificate Transparency">Certificate Transparency</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-500 mb-1 block">Confidence</label>
                <select
                  className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm w-full"
                  value={confidenceFilter}
                  onChange={(e) => setConfidenceFilter(e.target.value)}
                >
                  <option value="">All Levels</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
              </div>

              <div className="pt-4 border-t border-slate-800">
                <div className="text-xs text-slate-500 mb-2">Evidence Summary</div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Total Nodes</span>
                    <span className="text-slate-300">{nodes.length}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Relationships</span>
                    <span className="text-slate-300">{edges.length}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Observations</span>
                    <span className="text-slate-300">{dnsObservations.length}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">IP Addresses</span>
                    <span className="text-slate-300">{infrastructure.length}</span>
                  </div>
                </div>
              </div>
            </div>
          </aside>

          {/* Center: Evidence Graph */}
          <main className="flex-1">
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Evidence Relationship Graph</h3>
              
              {nodes.length > 0 ? (
                <div className="min-h-[400px] relative">
                  {/* Simplified graph visualization */}
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {nodes.slice(0, 12).map(node => (
                      <div
                        key={node.id}
                        onClick={() => setSelectedNode(node)}
                        className={`p-3 rounded border cursor-pointer transition-colors ${
                          selectedNode?.id === node.id
                            ? "bg-accent/10 border-accent text-accent"
                            : "bg-slate-800/30 border-slate-700 text-slate-300 hover:bg-slate-800/50"
                        }`}
                      >
                        <div className="text-xs text-slate-500 mb-1">{node.type.toUpperCase()}</div>
                        <div className="text-sm truncate">{node.name}</div>
                      </div>
                    ))}
                  </div>

                  {nodes.length > 12 && (
                    <div className="text-center mt-4 text-xs text-slate-500">
                      Showing 12 of {nodes.length} nodes
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-8 text-center">
                  <div className="text-slate-500 text-sm mb-2">No evidence available</div>
                  <div className="text-slate-600 text-xs">
                    Run a domain investigation to generate evidence data
                  </div>
                </div>
              )}
            </div>

            {/* Relationship Legend */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Relationship Types</h3>
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0.5 bg-slate-600"></div>
                  <span className="text-xs text-slate-400">Domain → IP (resolves to)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0.5 bg-slate-600"></div>
                  <span className="text-xs text-slate-400">Domain → Observation (observed)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0.5 bg-slate-600"></div>
                  <span className="text-xs text-slate-400">IP → ASN (announced by)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0.5 bg-slate-600"></div>
                  <span className="text-xs text-slate-400">Domain → Certificate (secured by)</span>
                </div>
              </div>
            </div>
          </main>

          {/* Right: Evidence Detail Panel */}
          <aside className="w-80 flex-shrink-0">
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Evidence Details</h3>
              
              {selectedNode ? (
                <div className="space-y-4">
                  <div>
                    <div className="text-xs text-slate-500 mb-1">Entity Type</div>
                    <div className="text-sm text-slate-300">{selectedNode.type.toUpperCase()}</div>
                  </div>

                  <div>
                    <div className="text-xs text-slate-500 mb-1">Name</div>
                    <div className="text-sm text-slate-300">{selectedNode.name}</div>
                  </div>

                  {selectedNode.type === "ip" && selectedNode.data && (
                    <>
                      <div>
                        <div className="text-xs text-slate-500 mb-1">Association Status</div>
                        <div className={`text-sm ${
                          selectedNode.data.association_status === "CURRENT" ? "text-emerald-400" :
                          selectedNode.data.association_status === "HISTORICAL" ? "text-amber-400" :
                          "text-slate-400"
                        }`}>
                          {selectedNode.data.association_status}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-1">Organization</div>
                        <div className="text-sm text-slate-300">
                          {selectedNode.data.organization || "Unknown"}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-1">Country</div>
                        <div className="text-sm text-slate-300">
                          {selectedNode.data.country || "Unknown"}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-1">ASN</div>
                        <div className="text-sm text-slate-300">
                          {selectedNode.data.asn || "Unknown"}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-1">Likely CDN</div>
                        <div className={`text-sm ${selectedNode.data.is_likely_cdn ? "text-emerald-400" : "text-slate-400"}`}>
                          {selectedNode.data.is_likely_cdn ? "Yes" : "No"}
                        </div>
                      </div>
                    </>
                  )}

                  {selectedNode.type === "observation" && selectedNode.data && (
                    <>
                      <div>
                        <div className="text-xs text-slate-500 mb-1">Source</div>
                        <div className="text-sm text-slate-300">{selectedNode.data.source}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-1">Confidence</div>
                        <div className={`text-sm ${
                          selectedNode.data.confidence === "HIGH" ? "text-emerald-400" :
                          selectedNode.data.confidence === "MEDIUM" ? "text-amber-400" :
                          "text-slate-400"
                        }`}>
                          {selectedNode.data.confidence}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-1">Observed At</div>
                        <div className="text-sm text-slate-300">
                          {new Date(selectedNode.data.observed_at).toLocaleString()}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-1">Values</div>
                        <div className="text-sm text-slate-300">
                          {selectedNode.data.values?.length > 0 
                            ? selectedNode.data.values.join(", ") 
                            : "None"}
                        </div>
                      </div>
                    </>
                  )}

                  {selectedNode.type === "domain" && selectedNode.data && (
                    <>
                      <div>
                        <div className="text-xs text-slate-500 mb-1">Authorized</div>
                        <div className={`text-sm ${selectedNode.data.authorized ? "text-emerald-400" : "text-amber-400"}`}>
                          {selectedNode.data.authorized ? "Yes" : "No"}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-1">Created</div>
                        <div className="text-sm text-slate-300">
                          {new Date(selectedNode.data.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-1">Notes</div>
                        <div className="text-sm text-slate-300">
                          {selectedNode.data.notes || "None"}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="py-8 text-center">
                  <div className="text-slate-500 text-sm mb-2">Select an entity</div>
                  <div className="text-slate-600 text-xs">
                    Click on a node in the graph to view detailed evidence
                  </div>
                </div>
              )}
            </div>

            {/* Evidence Timeline */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mt-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Evidence Timeline</h3>
              
              {dnsObservations.length > 0 ? (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {dnsObservations.slice(0, 10).map(obs => (
                    <div key={obs.id} className="bg-slate-800/30 border border-slate-700 rounded p-2">
                      <div className="text-xs text-slate-400 mb-1">
                        {new Date(obs.observed_at).toLocaleString()}
                      </div>
                      <div className="text-xs text-slate-300">
                        {obs.hostname} ({obs.record_type})
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-slate-500">
                  No timeline data available yet
                </div>
              )}
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
