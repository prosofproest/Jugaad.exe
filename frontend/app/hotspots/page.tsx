"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  Badge,
  EmptyState,
  Icon,
  PageHeader,
  RiskPill,
  StatCard,
} from "@/components/workspace/ui";
import { formatDateTime } from "@/lib/format";
import {
  ApiError,
  listForecasts,
  type ForecastItem,
} from "@/lib/api";

export default function HotspotsPage() {
  const [forecasts, setForecasts] = useState<ForecastItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    listForecasts()
      .then((response) => {
        if (!ignore) {
          setForecasts(response.items || []);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!ignore) {
          if (err instanceof ApiError && err.status === 401) {
            setError("Sign-in required to inspect regional forecast hotspots.");
          } else {
            setError(err instanceof Error ? err.message : "Failed to load forecast data");
          }
          setLoading(false);
        }
      });
    return () => {
      ignore = true;
    };
  }, []);

  const highRisk = forecasts.filter((f) => f.risk_band === "high" || f.risk_band === "urgent");
  const insufficient = forecasts.filter((f) => f.risk_band === "insufficient_data");

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Regional pest outlook"
        title="Pest Hotspots & Area Forecasts"
        lede="Area forecasts combine weather grids, historical occurrences, and verified field cases into reproducible risk bands. A risk band is an environmental likelihood, never a confirmed diagnosis."
        actions={
          <div className="ws-chip-row">
            <Link href="/outlook" className="ws-button ws-button-secondary">
              <Icon name="map" size={16} /> Area outlook view
            </Link>
          </div>
        }
      />

      <div className="ws-stat-grid">
        <StatCard label="Forecast runs" value={forecasts.length} detail="Active area models" icon="hotspot" tone="brand" />
        <StatCard label="High / Urgent" value={highRisk.length} detail="High risk zones" icon="alert" tone="bad" />
        <StatCard label="Insufficient data" value={insufficient.length} detail="Fail-closed (R8)" icon="shield" tone="warn" />
        <StatCard label="Model calibration" value="Discrete bands" detail="No pseudo-probabilities" icon="check" tone="ok" />
      </div>

      {error ? (
        <div className="ws-banner ws-banner-warn">
          <Icon name="alert" size={18} />
          <div>
            <strong>Notice:</strong>
            <p>{error}</p>
          </div>
          <div className="ws-banner-actions">
            <Link href="/login" className="ws-button ws-button-secondary">
              Sign in
            </Link>
          </div>
        </div>
      ) : loading ? (
        <div className="ws-panel">
          <p className="ws-muted">Loading regional forecasts from backend...</p>
        </div>
      ) : forecasts.length === 0 ? (
        <EmptyState
          title="No regional forecasts found"
          body="There are currently no active forecasts generated in the database. Forecasts are generated per (crop × target × geo × horizon)."
          action={
            <Link href="/outlook" className="ws-button ws-button-primary">
              View area outlook
            </Link>
          }
        />
      ) : (
        <div className="ws-panel">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Active forecast feed</p>
              <h2>Forecasted pest risk bands</h2>
            </div>
            <Badge tone="info">Reproducible snapshots</Badge>
          </div>

          <div className="ws-risk-list">
            {forecasts.map((f) => {
              const mappedBand = f.risk_band === "insufficient_data" ? "insufficient" : f.risk_band;
              return (
                <div key={f.id} className="ws-risk-row">
                  <div className="ws-risk-row-main">
                    <div>
                      <strong>{f.geo_code} · {f.crop_code.toUpperCase()}</strong>
                      <span className="ws-small ws-muted" style={{ display: "block" }}>Target: {f.target_code}</span>
                    </div>
                    <RiskPill band={mappedBand} />
                  </div>
                  <div className="ws-risk-row-meta">
                    <span>Valid from {formatDateTime(f.valid_from)} to {formatDateTime(f.valid_until)}</span>
                    <span>Coverage: {f.coverage_status}</span>
                    {f.is_demo && <Badge tone="neutral">demo</Badge>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
