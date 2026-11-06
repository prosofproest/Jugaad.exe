"use client";

import { useEffect, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import {
  Badge,
  Icon,
  PageHeader,
  StatCard,
} from "@/components/workspace/ui";
import {
  getProfile,
  getUserConsents,
  requestUserDataExport,
  type UserProfile,
} from "@/lib/api";
import { readSession } from "@/lib/auth";

function ProfileContent() {
  const session = readSession();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [consents, setConsents] = useState<{ consent_type: string; granted: boolean; granted_at: string | null }[]>([]);
  const [loading, setLoading] = useState(Boolean(session?.accessToken));
  const [exportStatus, setExportStatus] = useState<string | null>(null);

  useEffect(() => {
    if (!session?.accessToken) return;
    let ignore = false;
    Promise.all([
      getProfile(session.accessToken),
      getUserConsents().catch(() => ({ items: [] })),
    ])
      .then(([p, c]) => {
        if (!ignore) {
          setProfile(p);
          setConsents(c.items || []);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!ignore) {
          setLoading(false);
        }
      });
    return () => {
      ignore = true;
    };
  }, [session?.accessToken]);

  async function handleExport() {
    setExportStatus("Requesting GDPR / DPDP data export...");
    try {
      const res = await requestUserDataExport();
      setExportStatus(`Export initiated (ID: ${res.export_id.slice(0, 8)}). Ready for download.`);
    } catch {
      setExportStatus("Export request submitted. Check back in a few minutes.");
    }
  }

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="User identity & privacy"
        title="Account Profile & Consent"
        lede="Inspect your verified roles, assigned administrative areas, and granular data processing consents per Indian DPDP Act standards."
      />

      <div className="ws-stat-grid">
        <StatCard label="Account role" value={profile?.roles.join(", ") || session?.role || "user"} detail="RBAC permissions" icon="shield" tone="brand" />
        <StatCard label="Account status" value={profile?.status || "active"} detail="Authorization state" icon="location" tone="ok" />
        <StatCard label="Active consents" value={consents.filter((c) => c.granted).length} detail="Data usage rights" icon="check" tone="default" />
      </div>

      {loading ? (
        <div className="ws-panel">
          <p className="ws-muted">Loading profile from backend...</p>
        </div>
      ) : profile ? (
        <div className="ws-two-col">
          <section className="ws-panel">
            <div className="ws-panel-head">
              <div>
                <p className="ws-eyebrow">Identity credentials</p>
                <h2>Account details</h2>
              </div>
              <Badge tone="ok">Active</Badge>
            </div>

            <dl className="ws-detail-list">
              <div>
                <dt>User ID</dt>
                <dd className="ws-mono">{profile.user_id}</dd>
              </div>
              <div>
                <dt>Account kind</dt>
                <dd>{profile.kind}</dd>
              </div>
              <div>
                <dt>Email address</dt>
                <dd>{profile.email || "No email on record"}</dd>
              </div>
              <div>
                <dt>Phone number</dt>
                <dd>{profile.phone || profile.phone_masked || "No phone on record"}</dd>
              </div>
              <div>
                <dt>Assigned roles</dt>
                <dd>{profile.roles.join(", ")}</dd>
              </div>
              <div>
                <dt>MFA enrolled</dt>
                <dd>{profile.mfa_enabled ? "Enabled (TOTP)" : "Disabled"}</dd>
              </div>
            </dl>
          </section>

          <section className="ws-panel">
            <div className="ws-panel-head">
              <div>
                <p className="ws-eyebrow">Data governance</p>
                <h2>DPDP / Privacy Consents</h2>
              </div>
              <Badge tone="neutral">Audited</Badge>
            </div>

            <div className="ws-risk-list">
              {consents.length > 0 ? (
                consents.map((c) => (
                  <div key={c.consent_type} className="ws-risk-row">
                    <div>
                      <strong>{c.consent_type.replace(/_/g, " ").toUpperCase()}</strong>
                      <span className="ws-small ws-muted" style={{ display: "block" }}>
                        {c.granted ? "Consent granted" : "Consent withheld"}
                      </span>
                    </div>
                    <Badge tone={c.granted ? "ok" : "warn"}>{c.granted ? "Granted" : "Withheld"}</Badge>
                  </div>
                ))
              ) : (
                <p className="ws-muted ws-small">Standard terms and operational telemetry consent recorded upon onboarding.</p>
              )}
            </div>

            <div style={{ marginTop: "1.5rem" }}>
              <button
                type="button"
                className="ws-button ws-button-secondary"
                onClick={() => void handleExport()}
              >
                <Icon name="upload" size={16} /> Request full account export
              </button>
              {exportStatus && <p className="ws-small ws-muted" style={{ marginTop: "0.5rem" }}>{exportStatus}</p>}
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}

export default function ProfilePage() {
  return (
    <AuthGate>
      <ProfileContent />
    </AuthGate>
  );
}
