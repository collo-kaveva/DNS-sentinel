import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../services/api";
import type { Domain } from "../types";

export default function DomainsPage() {
  const [domains, setDomains] = useState<Domain[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [authorized, setAuthorized] = useState(false);
  const [creating, setCreating] = useState(false);

  function load() {
    setError(null);
    api
      .listDomains()
      .then((res) => setDomains(res.results))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load domains."));
  }

  useEffect(load, []);

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await api.createDomain({ name: name.trim(), authorized });
      setName("");
      setAuthorized(false);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add domain.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-lg font-semibold mb-1">Authorized Domains</h1>
      <p className="text-sm text-slate-500 mb-6">
        Only add domains you are authorized to investigate. DNS Sentinel uses public,
        passive data sources exclusively.
      </p>

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

      {error && <div className="text-rose-400 text-sm mb-4">{error}</div>}

      {domains === null && !error && <div className="text-slate-500 text-sm">Loading domains…</div>}

      {domains !== null && domains.length === 0 && (
        <div className="text-slate-500 text-sm">No domains yet. Add one above to get started.</div>
      )}

      <div className="flex flex-col gap-2">
        {domains?.map((d) => (
          <Link
            key={d.id}
            to={`/domains/${d.id}`}
            className="bg-slate-900 border border-slate-800 rounded-lg px-4 py-3 flex items-center justify-between hover:border-slate-700"
          >
            <div>
              <div className="font-mono text-sm">{d.name}</div>
              <div className="text-xs text-slate-500">
                Added {new Date(d.created_at).toLocaleDateString()}
              </div>
            </div>
            <span className={`text-xs px-2 py-1 rounded ${d.authorized ? "text-emerald-400" : "text-slate-500"}`}>
              {d.authorized ? "Authorized" : "Not authorized"}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
