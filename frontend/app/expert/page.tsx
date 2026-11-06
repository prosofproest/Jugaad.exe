"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  Badge,
  EmptyState,
  Field,
  Icon,
  Modal,
  PageHeader,
  StatCard,
} from "@/components/workspace/ui";
import { formatDateTime } from "@/lib/format";
import {
  ApiError,
  listReviewQueue,
  submitReviewDecision,
  type ReviewQueueItem,
} from "@/lib/api";
import { readSession } from "@/lib/auth";

export default function ExpertPage() {
  const session = readSession();
  const isAuthorized = Boolean(session && (session.role === "extension_worker" || session.role === "admin"));

  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [loading, setLoading] = useState(isAuthorized);
  const [error, setError] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<ReviewQueueItem | null>(null);
  const [decision, setDecision] = useState<"confirmed" | "probable" | "rejected" | "needs_visit">("confirmed");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    if (!isAuthorized) {
      return;
    }
    let ignore = false;
    listReviewQueue()
      .then((response) => {
        if (!ignore) {
          setQueue(response.items || []);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!ignore) {
          if (err instanceof ApiError) {
            setError(`${err.status} ${err.problem?.code ?? "error"}: ${err.problem?.detail ?? err.message}`);
          } else {
            setError(err instanceof Error ? err.message : "Failed to load review queue");
          }
          setLoading(false);
        }
      });
    return () => {
      ignore = true;
    };
  }, [isAuthorized]);

  const reloadQueue = () => {
    setLoading(true);
    listReviewQueue()
      .then((res) => {
        setQueue(res.items || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  async function handleDecisionSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedItem) return;

    setSubmitting(true);
    try {
      await submitReviewDecision(selectedItem.observation_id, {
        decision,
        note: note || undefined,
      });
      setModalOpen(false);
      setNote("");
      reloadQueue();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit review decision");
    } finally {
      setSubmitting(false);
    }
  }

  if (!isAuthorized) {
    return (
      <div className="ws-page">
        <PageHeader
          eyebrow="Expert desk"
          title="Restricted Verification Surface"
          lede="Per Safety Rule R4, AI outputs are never auto-promoted to verified cases. Expert verification is restricted to extension workers and pathologists."
        />
        <div className="ws-panel">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Access control</p>
              <h2>Staff authentication required</h2>
            </div>
            <Badge tone="warn">Protected</Badge>
          </div>
          <p className="ws-muted">
            You must be signed in with an <strong>extension_worker</strong> or <strong>admin</strong> role to inspect the case review queue and record verification decisions.
          </p>
          <div className="ws-banner-actions" style={{ marginTop: "1rem" }}>
            <Link href="/login" className="ws-button ws-button-primary">
              Staff sign-in
            </Link>
            <Link href="/review" className="ws-button ws-button-secondary">
              View review portal info
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Human verification desk"
        title="Expert Review Queue"
        lede="Inspect unverified observations, corroborate field symptoms against reference literature, and record immutable verification events."
        actions={
          <button type="button" className="ws-button ws-button-secondary" onClick={reloadQueue}>
            <Icon name="sync" size={16} /> Refresh queue
          </button>
        }
      />

      <div className="ws-stat-grid">
        <StatCard label="Awaiting review" value={queue.length} detail="Active queue items" icon="expert" tone="warn" />
        <StatCard label="Reviewer role" value={session?.role ?? "expert"} detail="Authorized evaluator" icon="shield" tone="brand" />
        <StatCard label="Safety rule" value="R4 active" detail="Never auto-promoted" icon="check" tone="ok" />
      </div>

      {error && (
        <div className="ws-notice ws-notice-bad" style={{ marginBottom: "1rem" }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading ? (
        <div className="ws-panel">
          <p className="ws-muted">Loading queue from backend...</p>
        </div>
      ) : queue.length === 0 ? (
        <EmptyState
          title="Review queue is clear"
          body="There are currently no observations awaiting human triage in your assigned administrative area."
          action={
            <Link href="/analysis" className="ws-button ws-button-primary">
              Browse observations
            </Link>
          }
        />
      ) : (
        <div className="ws-panel">
          <table className="ws-table" style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <th style={{ textAlign: "left", padding: "0.75rem" }}>Report ID</th>
                <th style={{ textAlign: "left", padding: "0.75rem" }}>Crop</th>
                <th style={{ textAlign: "left", padding: "0.75rem" }}>Area</th>
                <th style={{ textAlign: "left", padding: "0.75rem" }}>Submitted</th>
                <th style={{ textAlign: "left", padding: "0.75rem" }}>Status</th>
                <th style={{ textAlign: "right", padding: "0.75rem" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((item) => (
                <tr key={item.observation_id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "0.75rem" }} className="ws-mono">{item.client_report_id.slice(0, 14)}</td>
                  <td style={{ padding: "0.75rem" }}><span className="ws-crop-pill">{item.crop_code}</span></td>
                  <td style={{ padding: "0.75rem" }}>{item.area_code}</td>
                  <td style={{ padding: "0.75rem" }}>{formatDateTime(item.submitted_at)}</td>
                  <td style={{ padding: "0.75rem" }}><Badge tone="warn">{item.verification_status}</Badge></td>
                  <td style={{ padding: "0.75rem", textAlign: "right" }}>
                    <button
                      type="button"
                      className="ws-button ws-button-primary"
                      onClick={() => {
                        setSelectedItem(item);
                        setModalOpen(true);
                      }}
                    >
                      Review
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={`Review observation ${selectedItem?.client_report_id || ""}`}>
        {selectedItem && (
          <form className="ws-modal-form" onSubmit={(e) => void handleDecisionSubmit(e)}>
            <Field label="Verification decision" hint="Select the human clinical outcome">
              <select
                className="ws-input"
                value={decision}
                onChange={(e) => setDecision(e.target.value as typeof decision)}
                disabled={submitting}
              >
                <option value="confirmed">Confirmed (Verified positive diagnosis)</option>
                <option value="probable">Probable (High visual likelihood)</option>
                <option value="needs_visit">Needs physical field inspection</option>
                <option value="rejected">Rejected (Not consistent with symptoms)</option>
              </select>
            </Field>

            <Field label="Clinical evaluation note" hint="Recorded into append-only audit trail">
              <textarea
                className="ws-textarea"
                rows={3}
                placeholder="Detail visible symptoms, pathogen characteristics or justification..."
                value={note}
                onChange={(e) => setNote(e.target.value)}
                disabled={submitting}
                required
              />
            </Field>

            <div className="ws-modal-actions">
              <button
                type="button"
                className="ws-button ws-button-secondary"
                onClick={() => setModalOpen(false)}
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="ws-button ws-button-primary"
                disabled={submitting || !note.trim()}
              >
                {submitting ? "Recording decision..." : "Commit Decision"}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
