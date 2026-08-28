import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { ApiError } from "../services/api";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(username, password);
      } else {
        await register(username, email, password);
      }
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <div className="w-full max-w-sm bg-slate-900 border border-slate-800 rounded-lg p-6">
        <div className="text-accent font-mono text-xl mb-1">DNS SENTINEL</div>
        <div className="text-xs text-slate-500 mb-6">
          Public infrastructure intelligence &amp; lifecycle classification
        </div>

        <div className="flex mb-4 text-sm border border-slate-800 rounded overflow-hidden">
          <button
            className={`flex-1 py-2 ${mode === "login" ? "bg-slate-800 text-accent" : "text-slate-400"}`}
            onClick={() => setMode("login")}
            type="button"
          >
            Login
          </button>
          <button
            className={`flex-1 py-2 ${mode === "register" ? "bg-slate-800 text-accent" : "text-slate-400"}`}
            onClick={() => setMode("register")}
            type="button"
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input
            className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          {mode === "register" && (
            <input
              className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm"
              placeholder="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          )}
          <input
            className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm"
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <div className="text-rose-400 text-xs">{error}</div>}
          <button
            disabled={submitting}
            className="bg-accent text-slate-950 font-medium rounded py-2 text-sm disabled:opacity-50"
          >
            {submitting ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
          </button>
        </form>
      </div>
    </div>
  );
}
