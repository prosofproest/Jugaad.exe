"use client";

import Link from "next/link";
import { useState } from "react";

import {
  Badge,
  EmptyState,
  Field,
  Icon,
  Modal,
  PageHeader,
  StatCard,
} from "@/components/workspace/ui";
import { useWorkspace } from "@/lib/workspace/store";

export default function FarmsPage() {
  const { state } = useWorkspace();
  const [open, setOpen] = useState(false);
  const query = "";

  const farms = state.farms.filter((farm) =>
    `${farm.name} ${farm.village} ${farm.district}`.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Farms & plots"
        title="Farm & Boundary Management"
        lede="In v1, field scouting, weather ingestion, and photo assessment operate against administrative area boundaries (blocks/mandals) rather than cadastral farm boundary polygons."
        actions={
          <button
            type="button"
            className="ws-button ws-button-primary"
            onClick={() => setOpen(true)}
          >
            <Icon name="plus" size={17} /> Add farm
          </button>
        }
      />

      <div className="ws-banner ws-banner-warn">
        <Icon name="alert" size={18} />
        <div>
          <strong>Backend capability pending (`/v1/farms`)</strong>
          <p>
            The backend does not yet expose a standalone <code>/v1/farms</code> CRUD router.
            Per ADR-0010 and Feature Spec 05, v1 focuses on area-level surveillance and photo triage. No mock farm records are fabricated.
          </p>
        </div>
      </div>

      <div className="ws-stat-grid">
        <StatCard label="Configured farms" value={farms.length} detail="Active farms" icon="farm" tone="default" />
        <StatCard label="Administrative scope" value="Block-level" detail="Spatial matching level" icon="map" tone="brand" />
        <StatCard label="Backend status" value="Not configured" detail="Endpoints pending" icon="settings" tone="warn" />
      </div>

      {farms.length > 0 ? (
        <div className="ws-farm-grid">
          {farms.map((farm) => (
            <Link key={farm.id} href={`/farms/${farm.id}`} className="ws-farm-card">
              <div className="ws-farm-card-head">
                <div>
                  <h3>{farm.name}</h3>
                  <p className="ws-muted ws-small">{farm.village}, {farm.district}</p>
                </div>
                <Badge tone="neutral">{farm.areaAcres} acres</Badge>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No farm records found"
          body="The standalone farm registration service is awaiting backend deployment. You can continue using Photo Assessment and Area Outlook using administrative area codes."
          action={
            <Link href="/chat" className="ws-button ws-button-primary">
              Open photo assessment
            </Link>
          }
        />
      )}

      <Modal open={open} onClose={() => setOpen(false)} title="Add farm (Feature pending)">
        <div className="ws-modal-form">
          <p className="ws-notice ws-notice-warning">
            The farm registry API is currently unavailable. Farm creation is disabled to prevent storing unpersisted records in browser storage.
          </p>
          <Field label="Farm name" hint="Awaiting backend endpoint">
            <input type="text" disabled placeholder="e.g. Green Valley Farm" />
          </Field>
          <Field label="District" hint="Administrative unit">
            <input type="text" disabled placeholder="e.g. Krishnagiri" />
          </Field>
          <div className="ws-modal-actions">
            <button
              type="button"
              className="ws-button ws-button-secondary"
              onClick={() => setOpen(false)}
            >
              Close
            </button>
            <button
              type="button"
              className="ws-button ws-button-primary"
              disabled
            >
              Endpoint not available
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
