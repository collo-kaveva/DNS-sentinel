import { useState, useEffect } from "react";
import { api, ApiError } from "../services/api";
import type { Domain, Evidence, EvidenceRelationship } from "../types";

export default function EvidencePage() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<Domain | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [relationships, setRelationships] = useState<EvidenceRelationship[]>([]);
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Filter states
  const [evidenceTypeFilter, setEvidenceTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [confidenceFilter, setConfidenceFilter] = useState("");

  useEffect(() => {
    loadDomains();
  }, []);

  useEffect(() => {
    if (selectedDomain) {
      loadEvidence();
    }
  }, [selectedDomain, evidenceTypeFilter, statusFilter, sourceFilter, confidenceFilter]);

  const loadDomains = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.listDomains();
      setDomains(response.results);
      if (response.results.length > 0) {
        setSelectedDomain(response.results[0]);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load domains");
    } finally {
      setLoading(false);
    }
  };

  const loadEvidence = async () => {
    if (!selectedDomain) return;
    
    setLoading(true);
    setError(null);
    try {
      const [evidenceData, relationshipsData] = await Promise.all([
        api.listEvidence({
          domain: selectedDomain.id,
          evidence_type: evidenceTypeFilter || undefined,
          status: statusFilter || undefined,
          source: sourceFilter || undefined,
          confidence: confidenceFilter || undefined,
        }),
        api.listEvidenceRelationships().catch(() => ({ results: [] })),
      ]);
      
      setEvidence(evidenceData.results);
      setRelationships(relationshipsData.results);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load evidence");
    } finally {
      setLoading(false);
    }
  };

  const handleDomainChange = (domainId: string) => {
    const domain = domains.find(d => d.id === domainId);
    setSelectedDomain(domain || null);
    setSelectedEvidence(null);
  };

  // Build evidence graph nodes from evidence data
  const buildEvidenceNodes = () => {
    return evidence.map(ev => ({
      id: ev.id,
      type: ev.evidence_type.toLowerCase(),
      name: ev.entity_name || ev.observation,
      data: ev,
    }));
  };

  const nodes = buildEvidenceNodes();

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
              onClick={loadEvidence}
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
            value={selectedDomain?.id || ""}
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
                    <span className="text-slate-400">Total Evidence</span>
                    <span className="text-slate-300">{evidence.length}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Relationships</span>
                    <span className="text-slate-300">{relationships.length}</span>
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
                        onClick={() => setSelectedEvidence(node.data)}
                        className={`p-3 rounded border cursor-pointer transition-colors ${
                          selectedEvidence?.id === node.id
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
              
              {selectedEvidence ? (
                <div className="space-y-4">
                  <div>
                    <div className="text-xs text-slate-500 mb-1">Evidence Type</div>
                    <div className="text-sm text-slate-300">{selectedEvidence.evidence_type.replace(/_/g, " ")}</div>
                  </div>

                  <div>
                    <div className="text-xs text-slate-500 mb-1">Status</div>
                    <div className={`text-sm ${
                      selectedEvidence.status === "OBSERVED" ? "text-emerald-400" :
                      selectedEvidence.status === "HISTORICAL" ? "text-amber-400" :
                      "text-slate-400"
                    }`}>
                      {selectedEvidence.status}
                    </div>
                  </div>

                  <div>
                    <div className="text-xs text-slate-500 mb-1">Confidence</div>
                    <div className={`text-sm ${
                      selectedEvidence.confidence === "HIGH" ? "text-emerald-400" :
                      selectedEvidence.confidence === "MEDIUM" ? "text-amber-400" :
                      "text-slate-400"
                    }`}>
                      {selectedEvidence.confidence}
                    </div>
                  </div>

                  <div>
                    <div className="text-xs text-slate-500 mb-1">Source</div>
                    <div className="text-sm text-slate-300">{selectedEvidence.source}</div>
                  </div>

                  <div>
                    <div className="text-xs text-slate-500 mb-1">Entity Name</div>
                    <div className="text-sm text-slate-300">{selectedEvidence.entity_name || "N/A"}</div>
                  </div>

                  <div>
                    <div className="text-xs text-slate-500 mb-1">Observation</div>
                    <div className="text-sm text-slate-300 truncate">{selectedEvidence.observation}</div>
                  </div>

                  <div>
                    <div className="text-xs text-slate-500 mb-1">Observed At</div>
                    <div className="text-sm text-slate-300">
                      {new Date(selectedEvidence.observed_at).toLocaleString()}
                    </div>
                  </div>

                  <div>
                    <div className="text-xs text-slate-500 mb-1">First Observed</div>
                    <div className="text-sm text-slate-300">
                      {new Date(selectedEvidence.first_observed).toLocaleString()}
                    </div>
                  </div>

                  <div>
                    <div className="text-xs text-slate-500 mb-1">Last Observed</div>
                    <div className="text-sm text-slate-300">
                      {new Date(selectedEvidence.last_observed).toLocaleString()}
                    </div>
                  </div>
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
              
              {evidence.length > 0 ? (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {evidence.slice(0, 10).map(ev => (
                    <div key={ev.id} className="bg-slate-800/30 border border-slate-700 rounded p-2">
                      <div className="text-xs text-slate-400 mb-1">
                        {new Date(ev.observed_at).toLocaleString()}
                      </div>
                      <div className="text-xs text-slate-300">
                        {ev.evidence_type}: {ev.entity_name || ev.observation}
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
