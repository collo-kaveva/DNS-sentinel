import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api, ApiError } from "../services/api";
import type { Domain, ScanJob, DNSRecord, DNSObservation, DNSFinding, IPAddressInfo, Investigation, TimelineEvent, AnalystNote } from "../types";

type InvestigationSection = "overview" | "timeline" | "evidence" | "dns" | "infrastructure" | "certificates" | "services" | "lifecycle" | "alerts" | "notes";

export default function InvestigationPage() {
  const { id } = useParams<{ id: string }>();
  const [activeSection, setActiveSection] = useState<InvestigationSection>("overview");
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [domain, setDomain] = useState<Domain | null>(null);
  const [jobs, setJobs] = useState<ScanJob[]>([]);
  const [dnsRecords, setDnsRecords] = useState<DNSRecord[]>([]);
  const [dnsObservations, setDnsObservations] = useState<DNSObservation[]>([]);
  const [dnsFindings, setDnsFindings] = useState<DNSFinding[]>([]);
  const [infrastructure, setInfrastructure] = useState<IPAddressInfo[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [analystNotes, setAnalystNotes] = useState<AnalystNote[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    
    const loadInvestigationData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Load investigation
        const invData = await api.getInvestigation(id);
        setInvestigation(invData);
        
        // Load domain data
        const [domainsRes] = await Promise.all([
          api.listDomains(),
        ]);
        
        const foundDomain = domainsRes.results.find(d => d.id === invData.domain);
        if (!foundDomain) {
          setError("Domain not found");
          setLoading(false);
          return;
        }
        
        setDomain(foundDomain);

        // Load related data in parallel
        const [jobsData, dnsRecordsData, dnsObservationsData, dnsFindingsData, infrastructureData, timelineData, notesData] = await Promise.all([
          api.jobs(invData.domain).catch(() => []),
          api.dnsRecords(invData.domain).catch(() => []),
          api.dnsObservations(invData.domain).catch(() => []),
          api.dnsFindings(invData.domain).catch(() => []),
          api.infrastructure(invData.domain).catch(() => []),
          api.getInvestigationTimeline(id, 100).catch(() => ({ timeline: [] })),
          api.listAnalystNotes({ investigation: id }).catch(() => ({ results: [] })),
        ]);

        setJobs(jobsData);
        setDnsRecords(dnsRecordsData);
        setDnsObservations(dnsObservationsData);
        setDnsFindings(dnsFindingsData);
        setInfrastructure(infrastructureData);
        setTimeline(timelineData.timeline);
        setAnalystNotes(notesData.results);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load investigation data");
      } finally {
        setLoading(false);
      }
    };

    loadInvestigationData();
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="text-slate-500 text-sm">Loading investigation data…</div>
      </div>
    );
  }

  if (error || !domain) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm px-4 py-3 rounded-lg">
          {error || "Domain not found"}
        </div>
      </div>
    );
  }

  const latestJob = jobs[0];
  const investigationStatus = investigation?.status || "UNKNOWN";
  const jobType = latestJob?.job_type || "UNKNOWN";

  return (
    <div className="max-w-7xl mx-auto">
      {/* Investigation Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-xl font-semibold text-slate-100">{domain.name}</h1>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                investigationStatus === "RESOLVED" || investigationStatus === "CLOSED" ? "bg-emerald-500/15 text-emerald-400" :
                investigationStatus === "IN_PROGRESS" ? "bg-amber-500/15 text-amber-400" :
                investigationStatus === "OPEN" || investigationStatus === "REOPENED" ? "bg-blue-500/15 text-blue-400" :
                "bg-slate-500/15 text-slate-400"
              }`}>
                {investigationStatus}
              </span>
            </div>
            <div className="text-sm text-slate-500">
              {investigation ? `Investigation: ${investigation.title}` : `Investigation ID: ${id}`} • Latest Job: {jobType}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/domains"
              className="text-xs bg-slate-800 border border-slate-700 text-slate-300 px-3 py-1.5 rounded hover:bg-slate-700"
            >
              Back to Domains
            </Link>
            {domain.authorized && id && (
              <button
                onClick={() => api.investigate(id).catch(() => {})}
                className="text-xs bg-accent text-slate-950 px-3 py-1.5 rounded font-medium hover:bg-cyan-400"
              >
                Reinvestigate
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-xs text-slate-500 mb-1">Created</div>
            <div className="text-slate-300">{new Date(domain.created_at).toLocaleDateString()}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">Last Updated</div>
            <div className="text-slate-300">{new Date(domain.updated_at).toLocaleDateString()}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">Authorized</div>
            <div className={domain.authorized ? "text-emerald-400" : "text-amber-400"}>
              {domain.authorized ? "Yes" : "No"}
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">Notes</div>
            <div className="text-slate-300 truncate">{domain.notes || "None"}</div>
          </div>
        </div>
      </div>

      {/* Investigation Workspace */}
      <div className="flex gap-6">
        {/* Left Navigation */}
        <aside className="w-56 flex-shrink-0">
          <nav className="bg-slate-900 border border-slate-800 rounded-lg p-2 space-y-1">
            <InvestigationNavItem
              section="overview"
              label="Overview"
              active={activeSection === "overview"}
              onClick={() => setActiveSection("overview")}
            />
            <InvestigationNavItem
              section="timeline"
              label="Timeline"
              active={activeSection === "timeline"}
              onClick={() => setActiveSection("timeline")}
            />
            <InvestigationNavItem
              section="evidence"
              label="Evidence"
              active={activeSection === "evidence"}
              onClick={() => setActiveSection("evidence")}
            />
            <InvestigationNavItem
              section="dns"
              label="DNS"
              active={activeSection === "dns"}
              onClick={() => setActiveSection("dns")}
            />
            <InvestigationNavItem
              section="infrastructure"
              label="Infrastructure"
              active={activeSection === "infrastructure"}
              onClick={() => setActiveSection("infrastructure")}
            />
            <InvestigationNavItem
              section="certificates"
              label="Certificates"
              active={activeSection === "certificates"}
              onClick={() => setActiveSection("certificates")}
            />
            <InvestigationNavItem
              section="services"
              label="Services"
              active={activeSection === "services"}
              onClick={() => setActiveSection("services")}
            />
            <InvestigationNavItem
              section="lifecycle"
              label="Lifecycle"
              active={activeSection === "lifecycle"}
              onClick={() => setActiveSection("lifecycle")}
            />
            <InvestigationNavItem
              section="alerts"
              label="Alerts"
              active={activeSection === "alerts"}
              onClick={() => setActiveSection("alerts")}
            />
            <InvestigationNavItem
              section="notes"
              label="Analyst Notes"
              active={activeSection === "notes"}
              onClick={() => setActiveSection("notes")}
            />
          </nav>
        </aside>

        {/* Center Content */}
        <main className="flex-1">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
            {renderSection(activeSection, domain, jobs, dnsRecords, dnsObservations, dnsFindings, infrastructure, timeline, analystNotes)}
          </div>
        </main>

        {/* Right Context Panel */}
        <aside className="w-72 flex-shrink-0">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Investigation Context</h3>
            
            <div className="space-y-4">
              <div>
                <div className="text-xs text-slate-500 mb-1">Asset</div>
                <div className="text-sm text-slate-300">{domain.name}</div>
              </div>
              
              <div>
                <div className="text-xs text-slate-500 mb-1">Current Status</div>
                <div className={`text-sm ${
                  investigationStatus === "RESOLVED" || investigationStatus === "CLOSED" ? "text-emerald-400" :
                  investigationStatus === "IN_PROGRESS" ? "text-amber-400" :
                  investigationStatus === "OPEN" || investigationStatus === "REOPENED" ? "text-blue-400" :
                  "text-slate-400"
                }`}>
                  {investigationStatus}
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-500 mb-1">DNS Records</div>
                <div className="text-sm text-slate-300">{dnsRecords.length}</div>
              </div>

              <div>
                <div className="text-xs text-slate-500 mb-1">IP Addresses</div>
                <div className="text-sm text-slate-300">{infrastructure.length}</div>
              </div>

              <div>
                <div className="text-xs text-slate-500 mb-1">Findings</div>
                <div className="text-sm text-slate-300">{dnsFindings.length}</div>
              </div>

              {dnsFindings.filter(f => f.severity === "HIGH").length > 0 && (
                <div className="bg-rose-500/10 border border-rose-500/30 rounded p-3">
                  <div className="text-xs text-rose-400 mb-1">High Severity Findings</div>
                  <div className="text-sm text-rose-300">
                    {dnsFindings.filter(f => f.severity === "HIGH").length}
                  </div>
                </div>
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

function InvestigationNavItem({ 
  section, 
  label, 
  active, 
  onClick 
}: { 
  section: InvestigationSection; 
  label: string; 
  active: boolean; 
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-3 py-2 rounded text-sm ${
        active 
          ? "bg-slate-800 text-accent" 
          : "text-slate-400 hover:bg-slate-800/50"
      }`}
    >
      {label}
    </button>
  );
}

function renderSection(
  section: InvestigationSection,
  domain: Domain,
  jobs: ScanJob[],
  dnsRecords: DNSRecord[],
  dnsObservations: DNSObservation[],
  dnsFindings: DNSFinding[],
  infrastructure: IPAddressInfo[],
  timeline: TimelineEvent[],
  analystNotes: AnalystNote[]
) {
  switch (section) {
    case "overview":
      return (
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-slate-100">Investigation Overview</h2>
          
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-slate-300 mb-2">What is being investigated?</h3>
              <div className="text-sm text-slate-400">{domain.name}</div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-slate-300 mb-2">Why?</h3>
              <div className="text-sm text-slate-400">
                {domain.authorized 
                  ? "This domain is authorized for investigation to monitor its public infrastructure, DNS configuration, and security posture."
                  : "This domain is not authorized for investigation. Mark it as authorized to enable full investigation capabilities."}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-slate-300 mb-2">Current Assessment</h3>
              <div className="text-sm text-slate-400">
                {jobs.length > 0 
                  ? `${jobs.length} scan job(s) completed. Latest status: ${jobs[0].status}`
                  : "No scan jobs have been run yet."}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-slate-300 mb-2">Important Observations</h3>
              <div className="space-y-2">
                {dnsFindings.length > 0 ? (
                  dnsFindings.slice(0, 5).map(finding => (
                    <div key={finding.id} className="bg-slate-800/30 border border-slate-700 rounded p-3">
                      <div className={`text-xs font-medium mb-1 ${
                        finding.severity === "HIGH" ? "text-rose-400" :
                        finding.severity === "MEDIUM" ? "text-amber-400" :
                        "text-slate-400"
                      }`}>
                        {finding.severity}: {finding.title}
                      </div>
                      <div className="text-xs text-slate-500">{finding.description}</div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-slate-500">No findings available yet.</div>
                )}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-slate-300 mb-2">Limitations</h3>
              <div className="text-sm text-slate-500">
                Certificate analysis, service observation, and lifecycle classification are not yet implemented in the backend.
              </div>
            </div>
          </div>
        </div>
      );

    case "timeline":
      return (
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-slate-100">Investigation Timeline</h2>
          
          <div className="space-y-4">
            {timeline.length > 0 ? (
              timeline.map((event, idx) => (
                <div key={event.event_id} className="relative pl-6 pb-4 border-l-2 border-slate-700">
                  <div className={`absolute left-0 top-0 w-3 h-3 rounded-full ${
                    event.event_type === "DNS_OBSERVATION" ? "bg-blue-500" :
                    event.event_type === "DNS_RECORD" ? "bg-cyan-500" :
                    event.event_type === "IP_ADDRESS" ? "bg-purple-500" :
                    event.event_type === "AUDIT_EVENT" ? "bg-amber-500" :
                    event.event_type === "INVESTIGATION" || event.event_type === "INVESTIGATION_CREATED" ? "bg-emerald-500" :
                    event.event_type === "ANALYST_NOTE" ? "bg-rose-500" :
                    "bg-slate-500"
                  }`} style={{ transform: "translateX(-5px)" }} />
                  
                  <div className="text-sm text-slate-300 mb-1">{event.event_type.replace(/_/g, " ")}</div>
                  <div className="text-xs text-slate-500 mb-2">
                    {new Date(event.timestamp).toLocaleString()}
                  </div>
                  
                  <div className="text-xs text-slate-400 mb-1">{event.description}</div>
                  
                  <div className="text-[10px] text-slate-500">
                    Asset: {event.asset} • Source: {event.source}
                  </div>
                  
                  {event.new_state && (
                    <div className="text-[10px] text-slate-400 mt-1">
                      State: {event.new_state}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-sm text-slate-500">No timeline events available yet.</div>
            )}
          </div>
        </div>
      );

    case "evidence":
      return (
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-slate-100">Evidence</h2>
          
          <div className="space-y-4">
            {dnsObservations.length > 0 ? (
              dnsObservations.slice(0, 10).map(obs => (
                <div key={obs.id} className="bg-slate-800/30 border border-slate-700 rounded p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/15 text-emerald-400">OBSERVED</span>
                    <span className="text-xs text-slate-500 ml-auto">
                      {new Date(obs.observed_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="text-sm text-slate-300 mb-1">
                    {obs.hostname} ({obs.record_type})
                  </div>
                  <div className="text-xs text-slate-500 mb-1">
                    Source: {obs.source} • Confidence: {obs.confidence}
                  </div>
                  <div className="text-xs text-slate-400">
                    Values: {obs.values.length > 0 ? obs.values.join(", ") : "None"}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm text-slate-500">No evidence available yet.</div>
            )}
          </div>
        </div>
      );

    case "dns":
      return (
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-slate-100">DNS Records</h2>
          
          <div className="space-y-2">
            {dnsRecords.length > 0 ? (
              dnsRecords.map(record => (
                <div key={record.id} className="bg-slate-800/30 border border-slate-700 rounded p-3">
                  <div className="flex items-center justify-between mb-1">
                    <div className="text-sm text-slate-300">
                      {record.hostname} ({record.record_type})
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      record.is_current ? "bg-emerald-500/15 text-emerald-400" : "bg-slate-500/15 text-slate-400"
                    }`}>
                      {record.is_current ? "CURRENT" : "HISTORICAL"}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mb-1">{record.value}</div>
                  <div className="text-xs text-slate-600">
                    First seen: {new Date(record.first_seen).toLocaleDateString()} • 
                    Last seen: {new Date(record.last_seen).toLocaleDateString()}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm text-slate-500">No DNS records available yet.</div>
            )}
          </div>
        </div>
      );

    case "infrastructure":
      return (
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-slate-100">Infrastructure</h2>
          
          <div className="space-y-2">
            {infrastructure.length > 0 ? (
              infrastructure.map(ip => (
                <div key={ip.id} className="bg-slate-800/30 border border-slate-700 rounded p-3">
                  <div className="flex items-center justify-between mb-1">
                    <div className="text-sm text-slate-300">{ip.address}</div>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      ip.association_status === "CURRENT" ? "bg-emerald-500/15 text-emerald-400" :
                      ip.association_status === "HISTORICAL" ? "bg-amber-500/15 text-amber-400" :
                      "bg-slate-500/15 text-slate-400"
                    }`}>
                      {ip.association_status}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mb-1">
                    {ip.organization || "Unknown organization"} • {ip.country || "Unknown country"}
                  </div>
                  <div className="text-xs text-slate-600">
                    ASN: {ip.asn || "Unknown"} • CDN: {ip.is_likely_cdn ? "Yes" : "No"}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm text-slate-500">No infrastructure data available yet.</div>
            )}
          </div>
        </div>
      );

    case "certificates":
      return (
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-slate-100">Certificates</h2>
          <div className="text-sm text-slate-500">
            Certificate analysis is not yet implemented in the backend.
          </div>
        </div>
      );

    case "services":
      return (
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-slate-100">Services</h2>
          <div className="text-sm text-slate-500">
            Service observation is not yet implemented in the backend.
          </div>
        </div>
      );

    case "lifecycle":
      return (
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-slate-100">Lifecycle Classification</h2>
          <div className="text-sm text-slate-500">
            Lifecycle classification is not yet implemented in the backend.
          </div>
        </div>
      );

    case "alerts":
      return (
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-slate-100">Alerts</h2>
          <div className="text-sm text-slate-500">
            Alert generation is not yet implemented in the backend.
          </div>
        </div>
      );

    case "notes":
      return (
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-slate-100">Analyst Notes</h2>
          
          <div className="space-y-4">
            {analystNotes.length > 0 ? (
              analystNotes.map(note => (
                <div key={note.id} className="bg-slate-800/30 border border-slate-700 rounded p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm text-slate-300">{note.author_username}</div>
                    <div className="text-xs text-slate-500">
                      {new Date(note.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div className="text-sm text-slate-400 whitespace-pre-wrap">{note.content}</div>
                  {note.updated_at !== note.created_at && (
                    <div className="text-[10px] text-slate-500 mt-2">
                      Updated: {new Date(note.updated_at).toLocaleString()}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-sm text-slate-500">No analyst notes yet.</div>
            )}
          </div>
        </div>
      );

    default:
      return null;
  }
}
