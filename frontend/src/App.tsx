import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import AppLayout from "./layouts/AppLayout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import DomainsPage from "./pages/DomainsPage";
import DomainDetailPage from "./pages/DomainDetailPage";
import InfrastructurePage from "./pages/InfrastructurePage";
import CertificatesPage from "./pages/CertificatesPage";
import ServicesPage from "./pages/ServicesPage";
import LifecyclePage from "./pages/LifecyclePage";
import MonitoringPage from "./pages/MonitoringPage";

function ProtectedRoutes() {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-slate-500">Loading…</div>;
  }
  if (!user) return <Navigate to="/login" replace />;
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/domains" element={<DomainsPage />} />
        <Route path="/domains/:id" element={<DomainDetailPage />} />
        <Route path="/infrastructure" element={<InfrastructurePage />} />
        <Route path="/certificates" element={<CertificatesPage />} />
        <Route path="/services" element={<ServicesPage />} />
        <Route path="/lifecycle" element={<LifecyclePage />} />
        <Route path="/monitoring" element={<MonitoringPage />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={<ProtectedRoutes />} />
      </Routes>
    </AuthProvider>
  );
}
