import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const NAV = [
  { to: "/", label: "Dashboard" },
  { to: "/domains", label: "Domains" },
];

export default function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      <aside className="w-56 border-r border-slate-800 p-4 flex flex-col">
        <div className="mb-8">
          <div className="text-accent font-mono text-lg tracking-wide">DNS SENTINEL</div>
          <div className="text-xs text-slate-500">Infrastructure Intelligence</div>
        </div>
        <nav className="flex flex-col gap-1 flex-1">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === "/"}
              className={({ isActive }) =>
                `px-3 py-2 rounded text-sm ${
                  isActive ? "bg-slate-800 text-accent" : "text-slate-400 hover:bg-slate-900"
                }`
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-800 pt-3 text-xs text-slate-500">
          <div className="mb-2 truncate">{user?.username}</div>
          <button onClick={logout} className="text-rose-400 hover:underline">
            Log out
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
