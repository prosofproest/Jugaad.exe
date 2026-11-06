"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  Badge,
  EmptyState,
  Icon,
  PageHeader,
  StatCard,
} from "@/components/workspace/ui";
import { formatDateTime } from "@/lib/format";
import {
  ApiError,
  listAlerts,
  type AlertItem,
} from "@/lib/api";
import { readSession } from "@/lib/auth";

export default function NotificationsPage() {
  const isAuth = !!readSession();

  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(isAuth);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuth) {
      return;
    }
    let ignore = false;
    listAlerts("in_app")
      .then((response) => {
        if (!ignore) {
          setAlerts(response.items || []);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!ignore) {
          if (err instanceof ApiError && err.status === 401) {
            setError("Sign-in required to view notifications");
          } else {
            setError(err instanceof Error ? err.message : "Failed to load alerts");
          }
          setLoading(false);
        }
      });
    return () => {
      ignore = true;
    };
  }, [isAuth]);

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Notifications & in-app alerts"
        title="Alerts & Regional Advisories"
        lede="Alerts delivered per user-configured notification preferences (in_app, SMS, WhatsApp) based on high-risk forecast thresholds in assigned blocks."
        actions={
          <Link href="/settings" className="ws-button ws-button-secondary">
            <Icon name="settings" size={16} /> Alert settings
          </Link>
        }
      />

      <div className="ws-stat-grid">
        <StatCard label="Delivered alerts" value={alerts.length} detail="In-app notification feed" icon="bell" tone="brand" />
        <StatCard label="Channel" value="in_app" detail="Active feed channel" icon="check" tone="ok" />
        <StatCard label="Cooldown policy" value="24 hours" detail="Alert throttle window" icon="shield" tone="default" />
      </div>

      {!isAuth ? (
        <div className="ws-panel">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Authentication</p>
              <h2>Sign in to view your alert feed</h2>
            </div>
            <Badge tone="warn">Protected</Badge>
          </div>
          <p className="ws-muted">
            In-app alerts are delivered to registered farmer and staff accounts based on assigned administrative areas.
          </p>
          <div className="ws-banner-actions" style={{ marginTop: "1rem" }}>
            <Link href="/login" className="ws-button ws-button-primary">
              Sign in
            </Link>
          </div>
        </div>
      ) : error ? (
        <div className="ws-notice ws-notice-bad">
          <strong>Error:</strong> {error}
        </div>
      ) : loading ? (
        <div className="ws-panel">
          <p className="ws-muted">Loading alerts from backend...</p>
        </div>
      ) : alerts.length === 0 ? (
        <EmptyState
          title="No alerts delivered"
          body="There are currently no active high-risk alerts delivered to your feed. When regional pest conditions trigger policy thresholds in your area, alerts will appear here."
          action={
            <Link href="/outlook" className="ws-button ws-button-primary">
              Check area outlook
            </Link>
          }
        />
      ) : (
        <div className="ws-panel">
          <div className="ws-risk-list">
            {alerts.map((alert) => (
              <div key={alert.id || alert.delivery_id} className="ws-risk-row">
                <div className="ws-risk-row-main">
                  <div>
                    <strong>{alert.headline}</strong>
                    <p style={{ margin: "0.25rem 0", fontSize: "0.95rem" }}>{alert.body}</p>
                    <span className="ws-small ws-muted">Area: {alert.geo_code} · Target: {alert.target_code}</span>
                  </div>
                  <Badge tone={alert.risk_band === "urgent" ? "bad" : "warn"}>{alert.risk_band}</Badge>
                </div>
                <div className="ws-risk-row-meta">
                  <span>Delivered {formatDateTime(alert.sent_at)}</span>
                  <span>Channel: {alert.channel}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
