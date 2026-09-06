import { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import { api, ApiError } from "../services/api";
import type { UserSettings } from "../types";

type SettingsSection = "general" | "monitoring" | "notifications" | "security" | "account";

export default function SettingsPage() {
  const { user } = useAuth();
  const [activeSection, setActiveSection] = useState<SettingsSection>("general");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState<UserSettings | null>(null);

  // General settings
  const [dateFormat, setDateFormat] = useState("ISO_8601");
  const [timeFormat, setTimeFormat] = useState("24_HOUR");
  const [timezone, setTimezone] = useState("UTC");

  // Monitoring settings
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [defaultMonitoringBehavior, setDefaultMonitoringBehavior] = useState("PASSIVE");

  // Notification settings
  const [emailAlerts, setEmailAlerts] = useState(false);
  const [alertSeverity, setAlertSeverity] = useState("HIGH");

  // Security settings
  const [sessionTimeout, setSessionTimeout] = useState(60);

  // Account settings
  const [username, setUsername] = useState(user?.username || "");
  const [email, setEmail] = useState(user?.email || "");

  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSettings();
      setSettings(data);
      
      // Update local state with loaded settings
      setDateFormat(data.date_format);
      setTimeFormat(data.time_format);
      setTimezone(data.timezone);
      setAutoRefresh(data.auto_refresh);
      setRefreshInterval(data.refresh_interval_minutes);
      setDefaultMonitoringBehavior(data.default_monitoring_behavior);
      setEmailAlerts(data.email_alerts);
      setAlertSeverity(data.alert_severity_threshold);
      setSessionTimeout(data.session_timeout_minutes);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleSave = async () => {
    setError(null);
    setSuccess(null);
    setSaving(true);
    try {
      const updateData: Partial<UserSettings> = {
        date_format: dateFormat as any,
        time_format: timeFormat as any,
        timezone,
        auto_refresh: autoRefresh,
        refresh_interval_minutes: refreshInterval,
        default_monitoring_behavior: defaultMonitoringBehavior as any,
        email_alerts: emailAlerts,
        alert_severity_threshold: alertSeverity as any,
        session_timeout_minutes: sessionTimeout,
      };
      
      await api.updateSettings(updateData);
      setSuccess("Settings saved successfully");
      setHasChanges(false);
      
      // Reload settings to confirm
      await loadSettings();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (settings) {
      setDateFormat(settings.date_format);
      setTimeFormat(settings.time_format);
      setTimezone(settings.timezone);
      setAutoRefresh(settings.auto_refresh);
      setRefreshInterval(settings.refresh_interval_minutes);
      setDefaultMonitoringBehavior(settings.default_monitoring_behavior);
      setEmailAlerts(settings.email_alerts);
      setAlertSeverity(settings.alert_severity_threshold);
      setSessionTimeout(settings.session_timeout_minutes);
    }
    setHasChanges(false);
  };

  const renderSection = () => {
    switch (activeSection) {
      case "general":
        return (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-100">General Settings</h2>
            
            <SettingGroup title="Date & Time Preferences">
              <SettingRow
                label="Date Format"
                description="Preferred format for displaying dates"
              >
                <select
                  className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
                  value={dateFormat}
                  onChange={(e) => { setDateFormat(e.target.value); setHasChanges(true); }}
                >
                  <option value="ISO 8601">ISO 8601 (YYYY-MM-DD)</option>
                  <option value="US">US (MM/DD/YYYY)</option>
                  <option value="European">European (DD/MM/YYYY)</option>
                </select>
              </SettingRow>
              
              <SettingRow
                label="Time Format"
                description="Preferred format for displaying times"
              >
                <select
                  className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
                  value={timeFormat}
                  onChange={(e) => { setTimeFormat(e.target.value); setHasChanges(true); }}
                >
                  <option value="24-hour">24-hour (14:30)</option>
                  <option value="12-hour">12-hour (2:30 PM)</option>
                </select>
              </SettingRow>
              
              <SettingRow
                label="Timezone"
                description="Default timezone for timestamps"
              >
                <select
                  className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
                  value={timezone}
                  onChange={(e) => { setTimezone(e.target.value); setHasChanges(true); }}
                >
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">America/New_York</option>
                  <option value="America/Los_Angeles">America/Los_Angeles</option>
                  <option value="Europe/London">Europe/London</option>
                  <option value="Europe/Berlin">Europe/Berlin</option>
                  <option value="Asia/Tokyo">Asia/Tokyo</option>
                </select>
              </SettingRow>
            </SettingGroup>

            <SettingGroup title="Display Preferences">
              <SettingRow
                label="Theme"
                description="Application color theme"
              >
                <select
                  className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm opacity-50"
                  disabled
                >
                  <option>Dark (default)</option>
                </select>
              </SettingRow>
            </SettingGroup>
          </div>
        );

      case "monitoring":
        return (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-100">Monitoring Configuration</h2>
            
            <SettingGroup title="Auto-Refresh Settings">
              <SettingRow
                label="Auto-Refresh"
                description="Automatically refresh monitoring data"
              >
                <Toggle
                  enabled={autoRefresh}
                  onChange={(e) => { setAutoRefresh(e); setHasChanges(true); }}
                />
              </SettingRow>
              
              <SettingRow
                label="Refresh Interval"
                description="Minutes between automatic refreshes"
              >
                <select
                  className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
                  value={refreshInterval}
                  onChange={(e) => { setRefreshInterval(parseInt(e.target.value)); setHasChanges(true); }}
                  disabled={!autoRefresh}
                >
                  <option value="1">1 minute</option>
                  <option value="5">5 minutes</option>
                  <option value="10">10 minutes</option>
                  <option value="15">15 minutes</option>
                  <option value="30">30 minutes</option>
                </select>
              </SettingRow>
            </SettingGroup>

            <SettingGroup title="Default Monitoring Behavior">
              <SettingRow
                label="Default Mode"
                description="Default monitoring behavior for new investigations"
              >
                <select
                  className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
                  value={defaultMonitoringBehavior}
                  onChange={(e) => { setDefaultMonitoringBehavior(e.target.value); setHasChanges(true); }}
                >
                  <option value="passive">Passive (observation only)</option>
                  <option value="active">Active (periodic scanning)</option>
                </select>
              </SettingRow>
            </SettingGroup>
          </div>
        );

      case "notifications":
        return (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-100">Notification Preferences</h2>
            
            <SettingGroup title="Alert Notifications">
              <SettingRow
                label="Email Alerts"
                description="Receive security alerts via email"
              >
                <Toggle
                  enabled={emailAlerts}
                  onChange={(e) => { setEmailAlerts(e); setHasChanges(true); }}
                />
              </SettingRow>
              
              <SettingRow
                label="Minimum Severity"
                description="Only send alerts at or above this severity"
              >
                <select
                  className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
                  value={alertSeverity}
                  onChange={(e) => { setAlertSeverity(e.target.value); setHasChanges(true); }}
                >
                  <option value="INFO">Informational</option>
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                </select>
              </SettingRow>
            </SettingGroup>

            <div className="bg-slate-800/30 border border-slate-700 rounded p-4">
              <div className="text-sm text-slate-400 mb-2">Additional notification channels</div>
              <div className="text-xs text-slate-500">
                Webhook, Slack, and other integrations are not yet available.
              </div>
            </div>
          </div>
        );

      case "security":
        return (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-100">Security Settings</h2>
            
            <SettingGroup title="Session Management">
              <SettingRow
                label="Session Timeout"
                description="Minutes of inactivity before session expires"
              >
                <select
                  className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm"
                  value={sessionTimeout}
                  onChange={(e) => { setSessionTimeout(parseInt(e.target.value)); setHasChanges(true); }}
                >
                  <option value="30">30 minutes</option>
                  <option value="60">1 hour</option>
                  <option value="120">2 hours</option>
                  <option value="480">8 hours</option>
                </select>
              </SettingRow>
            </SettingGroup>

            <div className="bg-slate-800/30 border border-slate-700 rounded p-4">
              <div className="text-sm text-slate-400 mb-2">Two-Factor Authentication</div>
              <div className="text-xs text-slate-500">
                2FA is not yet implemented in the backend.
              </div>
            </div>
          </div>
        );

      case "account":
        return (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-100">Account Settings</h2>
            
            <SettingGroup title="Profile Information">
              <SettingRow
                label="Username"
                description="Your account username"
              >
                <input
                  type="text"
                  className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm w-64"
                  value={username}
                  onChange={(e) => { setUsername(e.target.value); setHasChanges(true); }}
                />
              </SettingRow>
              
              <SettingRow
                label="Email"
                description="Your account email address"
              >
                <input
                  type="email"
                  className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm w-64"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setHasChanges(true); }}
                />
              </SettingRow>
              
              <SettingRow
                label="Member Since"
                description="Account creation date"
              >
                <div className="text-sm text-slate-400">
                  {user?.date_joined ? new Date(user.date_joined).toLocaleDateString() : "Unknown"}
                </div>
              </SettingRow>
            </SettingGroup>

            <SettingGroup title="Security Actions">
              <SettingRow
                label="Change Password"
                description="Update your account password"
              >
                <button
                  className="text-xs bg-slate-800 border border-slate-700 text-slate-300 px-3 py-1.5 rounded hover:bg-slate-700 opacity-50"
                  disabled
                >
                  Change Password
                </button>
              </SettingRow>
            </SettingGroup>
          </div>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="text-slate-500 text-sm">Loading settings…</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-slate-100 mb-1">Settings</h1>
        <p className="text-sm text-slate-500">
          Configure application preferences, monitoring behavior, notifications, and account settings
        </p>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm px-4 py-3 rounded-lg mb-6">
          {success}
        </div>
      )}

      <div className="flex gap-6">
        {/* Settings Navigation */}
        <aside className="w-56 flex-shrink-0">
          <nav className="bg-slate-900 border border-slate-800 rounded-lg p-2 space-y-1">
            <SettingsNavItem
              section="general"
              label="General"
              active={activeSection === "general"}
              onClick={() => setActiveSection("general")}
            />
            <SettingsNavItem
              section="monitoring"
              label="Monitoring"
              active={activeSection === "monitoring"}
              onClick={() => setActiveSection("monitoring")}
            />
            <SettingsNavItem
              section="notifications"
              label="Notifications"
              active={activeSection === "notifications"}
              onClick={() => setActiveSection("notifications")}
            />
            <SettingsNavItem
              section="security"
              label="Security"
              active={activeSection === "security"}
              onClick={() => setActiveSection("security")}
            />
            <SettingsNavItem
              section="account"
              label="Account"
              active={activeSection === "account"}
              onClick={() => setActiveSection("account")}
            />
          </nav>
        </aside>

        {/* Settings Content */}
        <main className="flex-1">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 mb-4">
            {renderSection()}
          </div>

          {/* Action Bar */}
          <div className="flex items-center justify-between bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="text-xs text-slate-500">
              {hasChanges ? "You have unsaved changes" : "All changes saved"}
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleReset}
                disabled={!hasChanges}
                className="text-xs bg-slate-800 border border-slate-700 text-slate-300 px-4 py-1.5 rounded hover:bg-slate-700 disabled:opacity-50"
              >
                Reset
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges || saving}
                className="text-xs bg-accent text-slate-950 px-4 py-1.5 rounded font-medium hover:bg-cyan-400 disabled:opacity-50"
              >
                {saving ? "Saving…" : "Save Changes"}
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

function SettingsNavItem({ 
  section, 
  label, 
  active, 
  onClick 
}: { 
  section: SettingsSection; 
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

function SettingGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-b border-slate-800 pb-6 last:border-0">
      <h3 className="text-sm font-medium text-slate-300 mb-4">{title}</h3>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

function SettingRow({ 
  label, 
  description, 
  children 
}: { 
  label: string; 
  description: string; 
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <div className="text-sm text-slate-300 mb-1">{label}</div>
        <div className="text-xs text-slate-500">{description}</div>
      </div>
      <div className="ml-6">{children}</div>
    </div>
  );
}

function Toggle({ enabled, onChange }: { enabled: boolean; onChange: (enabled: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`relative w-12 h-6 rounded-full transition-colors ${
        enabled ? "bg-accent" : "bg-slate-700"
      }`}
    >
      <span
        className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
          enabled ? "left-7" : "left-1"
        }`}
      />
    </button>
  );
}
