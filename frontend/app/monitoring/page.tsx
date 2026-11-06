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
  listReviewQueue,
  type ReviewQueueItem,
} from "@/lib/api";
import { readSession } from "@/lib/auth";

export default function MonitoringPage() {
  const session = readSession();
  const isAuthorized = Boolean(session && (session.role === "extension_worker" || session.role === "admin"));

  const [needsVisitItems, setNeedsVisitItems] = useState<ReviewQueueItem[]>([]);
  const [loading, setLoading] = useState(isAuthorized);

  useEffect(() => {
    if (!isAuthorized) {
      return;
    }
    let ignore = false;
    listReviewQueue({ status: "needs_visit" })
      .then((response) => {
        if (!ignore) {
          setNeedsVisitItems(response.items || []);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!ignore) {
          setNeedsVisitItems([]);
          setLoading(false);
        }
      });
    return () => {
      ignore = true;
    };
  }, [isAuthorized]);

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Field operations"
        title="Field Monitoring & Inspection Visits"
        lede="In v1, field visits are driven by expert review triage (`needs_visit`). Extension agents and experts perform directed field inspections on flagged observation cases."
      />

      <div className="ws-stat-grid">
        <StatCard label="Flagged for visit" value={needsVisitItems.length} detail="Review queue cases" icon="monitoring" tone="brand" />
        <StatCard label="Integration mode" value="Triage driven" detail="Spec 03 review workflow" icon="shield" tone="ok" />
        <StatCard label="Standalone scheduler" value="Pending" detail="v2 calendar feature" icon="calendar" tone="default" />
      </div>

      <div className="ws-banner ws-banner-info">
        <Icon name="monitoring" size={18} />
        <div>
          <strong>Directed Field Visits (ADR-0010)</strong>
          <p>
            Rather than maintaining unverified standalone calendars in local storage, monitoring visits are linked directly to clinical observations that an expert has triaged as requiring a physical inspection.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="ws-panel">
          <p className="ws-muted">Loading field monitoring cases...</p>
        </div>
      ) : needsVisitItems.length === 0 ? (
        <EmptyState
          title="No field visits currently pending"
          body="There are no observations currently marked as 'needs_visit' in the review queue. Cases flagged during expert review will automatically appear here."
          action={
            <Link href="/expert" className="ws-button ws-button-primary">
              Open expert desk
            </Link>
          }
        />
      ) : (
        <div className="ws-panel">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Cases requiring visit</p>
              <h2>Pending field observations</h2>
            </div>
            <Badge tone="warn">{needsVisitItems.length} pending</Badge>
          </div>

          <div className="ws-risk-list">
            {needsVisitItems.map((item) => (
              <div key={item.observation_id} className="ws-risk-row">
                <div className="ws-risk-row-main">
                  <div>
                    <strong>Report #{item.client_report_id.slice(0, 12)} · {item.crop_code.toUpperCase()}</strong>
                    <span className="ws-small ws-muted" style={{ display: "block" }}>Area: {item.area_code}</span>
                  </div>
                  <Badge tone="warn">Needs visit</Badge>
                </div>
                <div className="ws-risk-row-meta">
                  <span>Submitted {formatDateTime(item.submitted_at)}</span>
                  <Link href="/expert" className="ws-link">
                    Review case →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
