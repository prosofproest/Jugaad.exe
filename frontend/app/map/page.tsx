"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  Badge,
  EmptyState,
  Icon,
  PageHeader,
  StatCard,
  Tabs,
} from "@/components/workspace/ui";
import {
  ApiError,
  getMapLayer,
  listAreas,
  type MapLayerName,
} from "@/lib/api";

type LayerOption = MapLayerName;

export default function FarmHealthMapPage() {
  const [layer, setLayer] = useState<LayerOption>("modelled_risk");
  const [areas, setAreas] = useState<{ code: string; level: string; name: string }[]>([]);
  const [layerData, setLayerData] = useState<Record<string, unknown> | null>(null);
  const [layerError, setLayerError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    listAreas()
      .then((areaData) => {
        if (!ignore) {
          setAreas(areaData.geographies || []);
        }
      })
      .catch(() => {
        // Areas list unauthenticated or offline
      });

    getMapLayer(layer)
      .then((result) => {
        if (!ignore) {
          setLayerData(result as unknown as Record<string, unknown>);
          setLayerError(null);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!ignore) {
          if (err instanceof ApiError && err.problem?.code === "map_not_configured") {
            setLayerError("The GIS spatial engine has no boundary geometries loaded in this deployment.");
          } else if (err instanceof ApiError && err.status === 401) {
            setLayerError("Sign-in required to inspect private GIS map layers.");
          } else {
            setLayerError(err instanceof Error ? err.message : "Map layer unavailable");
          }
          setLayerData(null);
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [layer]);

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Spatial intelligence"
        title="Administrative & Risk Map"
        lede="Spatial views display administrative boundaries, observation densities, and regional risk bands. Individual farm plots are aggregated to protect producer privacy."
        actions={
          <Link href="/outlook" className="ws-button ws-button-primary">
            <Icon name="map" size={17} /> Area outlook
          </Link>
        }
      />

      <div className="ws-stat-grid">
        <StatCard label="Administrative units" value={areas.length} detail="Configured geographies" icon="map" tone="brand" />
        <StatCard label="Spatial resolution" value="Block / Mandal" detail="Aggregated GIS boundaries" icon="shield" tone="default" />
        <StatCard label="Active layer" value={layer.toUpperCase()} detail="Current GIS feed" icon="location" tone="ok" />
      </div>

      <Tabs
        label="Map layer selector"
        value={layer}
        onChange={(val) => setLayer(val as MapLayerName)}
        tabs={[
          { value: "modelled_risk", label: "Modelled risk" },
          { value: "verified_reports", label: "Verified reports" },
          { value: "unverified_reports", label: "Unverified reports" },
          { value: "boundaries", label: "Boundaries" },
        ]}
      />

      {layerError ? (
        <div className="ws-panel">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Layer status</p>
              <h2>{layer.toUpperCase()} layer</h2>
            </div>
            <Badge tone="warn">Unavailable</Badge>
          </div>
          <p className="ws-muted">{layerError}</p>
          <p className="ws-small ws-muted" style={{ marginTop: "1rem" }}>
            Per spec 06, when GIS tiles or boundary shapefiles are not mounted, the system refuses silent interpolation and returns an explicit status.
          </p>
          <div className="ws-banner-actions" style={{ marginTop: "1rem" }}>
            <Link href="/outlook" className="ws-button ws-button-secondary">
              Explore tabular area outlook
            </Link>
          </div>
        </div>
      ) : loading ? (
        <div className="ws-panel">
          <p className="ws-muted">Loading map layers...</p>
        </div>
      ) : (
        <div className="ws-panel">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Spatial features</p>
              <h2>Active layer features</h2>
            </div>
            <Badge tone="ok">Connected</Badge>
          </div>
          {layerData ? (
            <pre className="ws-code-block" style={{ padding: "1rem", background: "var(--ws-bg)", borderRadius: "0.5rem", overflowX: "auto" }}>
              {JSON.stringify(layerData, null, 2)}
            </pre>
          ) : (
            <EmptyState
              title="No spatial geometry"
              body="No features are present for this layer in the current spatial bounding box."
            />
          )}
        </div>
      )}

      <section className="ws-panel">
        <div className="ws-panel-head">
          <div>
            <p className="ws-eyebrow">Configured geographies</p>
            <h3>Administrative Areas</h3>
          </div>
          <Badge tone="neutral">{areas.length} areas</Badge>
        </div>
        {areas.length > 0 ? (
          <div className="ws-area-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "0.75rem", marginTop: "1rem" }}>
            {areas.map((a) => (
              <div key={a.code} style={{ padding: "0.75rem", background: "var(--ws-bg)", borderRadius: "0.5rem" }}>
                <strong>{a.name}</strong>
                <p className="ws-small ws-muted" style={{ margin: 0 }}>Code: {a.code} · Level: {a.level}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="ws-muted ws-small">Sign in to view user-assigned administrative boundaries.</p>
        )}
      </section>
    </div>
  );
}
