"use client";

import Link from "next/link";
import { useState } from "react";

import { Badge, Icon, Modal, PageHeader } from "@/components/workspace/ui";
import { useWorkspace } from "@/lib/workspace/store";
import type { Language, Role } from "@/lib/workspace/types";

const ROLE_LABEL: Record<Role, string> = {
  farmer: "Farmer",
  expert: "Agricultural expert",
  agent: "Field agent",
  admin: "Administrator",
};

export default function SettingsPage() {
  const { state, role, setRole, setLanguage, resetDemo } = useWorkspace();
  const [prefs, setPrefs] = useState({
    inApp: true,
    reviewUpdates: true,
    reminders: true,
    digest: false,
    sms: false,
    shareLocation: true,
    analytics: false,
  });
  const [resetOpen, setResetOpen] = useState(false);
  const [exported, setExported] = useState(false);

  function toggle(key: keyof typeof prefs) {
    setPrefs((current) => ({ ...current, [key]: !current[key] }));
  }

  function exportData() {
    const payload = {
      exported_at: new Date().toISOString(),
      user: state.currentUser,
      farms: state.farms,
      observations: state.analyses,
      captures: state.captures,
      inspections: state.inspections,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "cropsentinel-demo-export.json";
    anchor.click();
    URL.revokeObjectURL(url);
    setExported(true);
    window.setTimeout(() => setExported(false), 2500);
  }

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Settings"
        title="Workspace preferences"
        lede="Language, notification channels, location permission, privacy and demo data controls. Sensible defaults are designed for low-bandwidth field use."
        actions={<Link href="/help" className="ws-button ws-button-secondary"><Icon name="help" size={16} /> Help & support</Link>}
      />

      <div className="ws-settings-grid">
        <section className="ws-panel">
          <div className="ws-panel-head"><div><p className="ws-eyebrow">Account</p><h2>Profile & role</h2></div><Badge tone="brand">{ROLE_LABEL[role]}</Badge></div>
          <div className="ws-settings-row">
            <div><strong>Signed-in account</strong><span className="ws-small ws-muted">{state.currentUser.name} · {state.currentUser.phone}</span></div>
            <Link href="/profile" className="ws-button ws-button-secondary">Edit profile</Link>
          </div>
          <div className="ws-settings-row">
            <div><strong>Demo role</strong><span className="ws-small ws-muted">Preview permissions for each role</span></div>
            <select value={role} onChange={(event) => setRole(event.target.value as Role)}>
              {(Object.keys(ROLE_LABEL) as Role[]).map((option) => <option key={option} value={option}>{ROLE_LABEL[option]}</option>)}
            </select>
          </div>
          <div className="ws-settings-row">
            <div><strong>Language</strong><span className="ws-small ws-muted">Navigation and key interface labels</span></div>
            <select value={state.currentUser.language} onChange={(event) => setLanguage(event.target.value as Language)}>
              <option value="en">English</option>
              <option value="hi">हिन्दी (Hindi)</option>
              <option value="kn">ಕನ್ನಡ (Kannada)</option>
            </select>
          </div>
          <Link href="/login" className="ws-button ws-button-secondary ws-button-block ws-mt"><Icon name="logout" size={16} /> Switch account</Link>
        </section>

        <section className="ws-panel">
          <div className="ws-panel-head"><div><p className="ws-eyebrow">Notifications</p><h2>Channels & reminders</h2></div></div>
          {[
            { key: "inApp" as const, label: "In-app notifications", detail: "Alerts, reviews and system messages" },
            { key: "reviewUpdates" as const, label: "Expert review updates", detail: "When a diagnosis is verified or corrected" },
            { key: "reminders" as const, label: "Inspection reminders", detail: "24 hours before a scheduled visit" },
            { key: "digest" as const, label: "Daily hotspot digest", detail: "One regional summary at 07:00" },
            { key: "sms" as const, label: "SMS alerts (optional)", detail: "Low-bandwidth fallback for urgent alerts" },
          ].map((item) => (
            <div key={item.key} className="ws-settings-row">
              <div><strong>{item.label}</strong><span className="ws-small ws-muted">{item.detail}</span></div>
              <button type="button" role="switch" aria-checked={prefs[item.key]} className={prefs[item.key] ? "ws-switch ws-switch-on" : "ws-switch"} onClick={() => toggle(item.key)}>
                <span />
              </button>
            </div>
          ))}
        </section>

        <section className="ws-panel">
          <div className="ws-panel-head"><div><p className="ws-eyebrow">Privacy</p><h2>Location & data</h2></div><Badge tone="neutral">Consent-based</Badge></div>
          <div className="ws-settings-row">
            <div><strong>Attach GPS to observations</strong><span className="ws-small ws-muted">Requested per capture; permission is never assumed</span></div>
            <button type="button" role="switch" aria-checked={prefs.shareLocation} className={prefs.shareLocation ? "ws-switch ws-switch-on" : "ws-switch"} onClick={() => toggle("shareLocation")}>
              <span />
            </button>
          </div>
          <div className="ws-settings-row">
            <div><strong>Anonymous usage analytics</strong><span className="ws-small ws-muted">No photos, names or coordinates in analytics</span></div>
            <button type="button" role="switch" aria-checked={prefs.analytics} className={prefs.analytics ? "ws-switch ws-switch-on" : "ws-switch"} onClick={() => toggle("analytics")}>
              <span />
            </button>
          </div>
          <div className="ws-settings-row">
            <div><strong>Retention</strong><span className="ws-small ws-muted">Demo records stay on this device until reset</span></div>
            <Badge tone="info">Local only</Badge>
          </div>
          <div className="ws-settings-row">
            <div><strong>Export my data</strong><span className="ws-small ws-muted">Download a JSON copy of the demo workspace</span></div>
            <button type="button" className="ws-button ws-button-secondary" onClick={exportData}>
              <Icon name="upload" size={15} /> {exported ? "Exported" : "Export"}
            </button>
          </div>
          <div className="ws-settings-row">
            <div><strong>Reset demo data</strong><span className="ws-small ws-muted">Restore the original farms, observations and queue</span></div>
            <button type="button" className="ws-button ws-button-danger" onClick={() => setResetOpen(true)}>Reset</button>
          </div>
        </section>

        <section className="ws-panel">
          <div className="ws-panel-head"><div><p className="ws-eyebrow">Integration</p><h2>Data source</h2></div><Badge tone="warn">Demo adapter</Badge></div>
          <p className="ws-small ws-muted">
            The web interface reads from a typed local workspace so every screen works offline.
            The existing FastAPI client in <span className="ws-mono">lib/api.ts</span> is untouched and
            can power live photo assessment, upload and review once the corresponding endpoints are
            enabled.
          </p>
          <dl className="ws-detail-list">
            <div><dt>Health, conversations, uploads</dt><dd><Badge tone="ok">Connected client retained</Badge></dd></div>
            <div><dt>Farms, plots, plants</dt><dd><Badge tone="warn">Demo workspace</Badge></dd></div>
            <div><dt>Hotspots & forecasts</dt><dd><Badge tone="neutral">Separate layers</Badge></dd></div>
            <div><dt>Storage</dt><dd>Browser localStorage</dd></div>
          </dl>
          <Link href="/help" className="ws-link">Read the data & safety notes <Icon name="arrow" size={13} /></Link>
        </section>
      </div>

      <Modal
        open={resetOpen}
        onClose={() => setResetOpen(false)}
        title="Reset demo data?"
        footer={
          <>
            <button type="button" className="ws-button ws-button-ghost" onClick={() => setResetOpen(false)}>Cancel</button>
            <button
              type="button"
              className="ws-button ws-button-danger"
              onClick={() => {
                resetDemo();
                setResetOpen(false);
              }}
            >
              Reset workspace
            </button>
          </>
        }
      >
        <p>This restores the original demo farms, observations, inspections and notifications. Any farms or captures you added on this device will be removed.</p>
        <p className="ws-small ws-muted">The reset cannot be undone.</p>
      </Modal>
    </div>
  );
}
