"use client";

/** Client-side area-outlook layers for the authenticated web surface. */

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiError, getMapLayer, type MapLayer, type MapLayerName } from "@/lib/api";

interface LayerDefinition {
  name: MapLayerName;
  label: string;
  description: string;
}

const LAYERS: LayerDefinition[] = [
  {
    name: "verified_reports",
    label: "Verified reports",
    description:
      "Human-verified cases only. Unverified photo assessments never appear here.",
  },
  {
    name: "unverified_reports",
    label: "Unverified reports",
    description:
      "Submitted but not yet verified. A report is not a confirmed case.",
  },
  {
    name: "modelled_risk",
    label: "Modelled risk",
    description:
      "Bounded forecast areas with issue time, horizon, model version and coverage.",
  },
  {
    name: "coverage",
    label: "Coverage",
    description:
      "Completeness and freshness of inputs. Low coverage is not low risk.",
  },
  {
    name: "boundaries",
    label: "Boundaries",
    description:
      "Versioned administrative boundaries used for aggregation; never farm-level.",
  },
];

type LayerState = "available" | "empty" | "unavailable" | "error";

interface LayerResult {
  definition: LayerDefinition;
  state: LayerState;
  detail: string;
  layer: MapLayer | null;
}

function describeFailure(caught: unknown): { state: LayerState; detail: string } {
  if (caught instanceof ApiError) {
    if (caught.problem?.code === "map_not_configured") {
      return {
        state: "unavailable",
        detail:
          "Not configured in this deployment. No geometry is invented to fill the gap.",
      };
    }
    if (caught.status === 503) {
      return {
        state: "unavailable",
        detail: caught.problem?.detail ?? "This layer is temporarily unavailable.",
      };
    }
    if (caught.status === 401) {
      return {
        state: "error",
        detail: "Sign-in required.",
      };
    }
    return {
      state: "error",
      detail: `${caught.status} ${caught.problem?.code ?? "request_failed"}`,
    };
  }
  return {
    state: "error",
    detail: "The API is unreachable, so no layer state can be confirmed.",
  };
}

async function loadLayer(definition: LayerDefinition): Promise<LayerResult> {
  try {
    const layer = await getMapLayer(definition.name);
    if (layer.empty) {
      return {
        definition,
        state: "empty",
        detail:
          layer.empty_message ??
          "No features in this layer. An empty layer is not evidence of absence.",
        layer,
      };
    }
    const count = layer.features.length;
    return {
      definition,
      state: "available",
      detail: `${count} ${count === 1 ? "feature" : "features"} · boundary ${layer.boundary_version}`,
      layer,
    };
  } catch (caught) {
    return { definition, ...describeFailure(caught), layer: null };
  }
}

const STATE_LABEL: Record<LayerState, string> = {
  available: "Available",
  empty: "Empty",
  unavailable: "Not configured",
  error: "Unavailable",
};

export function OutlookClient() {
  const [results, setResults] = useState<LayerResult[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const fetched = await Promise.all(LAYERS.map(loadLayer));
      if (!cancelled) setResults(fetched);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (results === null) {
    return (
      <div className="page">
        <header className="page-header">
          <p className="eyebrow">Area outlook</p>
          <h1>Area outlook</h1>
        </header>
        <p className="small muted">Loading independent map layers…</p>
      </div>
    );
  }

  const configured = results.filter((result) => result.state === "available").length;

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Area outlook</p>
        <h1>Area outlook</h1>
        <p className="page-lede">
          How likely a threat is in an area over a window — crop × target ×
          geography × horizon.
        </p>
      </header>

      <p className="notice notice-warning">
        <span className="badge badge-muted">not computed</span> No forecast is
        generated in this build. This page reports each map layer&apos;s own state;
        it never merges them into one risk number.
      </p>

      <section aria-labelledby="layers-heading">
        <div className="section-heading">
          <h2 id="layers-heading">Independent map layers</h2>
          <p className="small muted">
            {configured} of {results.length} layers serving data
          </p>
        </div>

        <ul className="layer-grid">
          {results.map((result) => (
            <li key={result.definition.name} className="layer-card">
              <div className="panel-header">
                <h3>{result.definition.label}</h3>
                <span
                  className={
                    result.state === "error"
                      ? "badge badge-warning"
                      : "badge badge-muted"
                  }
                >
                  {STATE_LABEL[result.state]}
                </span>
              </div>
              <p className="small muted">{result.definition.description}</p>
              <p className="small">{result.detail}</p>
              {result.layer ? (
                <dl className="layer-meta small muted">
                  <div>
                    <dt>Aggregation</dt>
                    <dd>{result.layer.aggregation_level}</dd>
                  </div>
                  <div>
                    <dt>Generated</dt>
                    <dd>
                      <time dateTime={result.layer.generated_at}>
                        {new Date(result.layer.generated_at).toLocaleString()}
                      </time>
                    </dd>
                  </div>
                  <div>
                    <dt>Small counts</dt>
                    <dd>
                      {result.layer.small_count_suppression_applied
                        ? "suppressed"
                        : "no suppression applied"}
                    </dd>
                  </div>
                </dl>
              ) : null}
            </li>
          ))}
        </ul>
      </section>

      <section className="card" aria-labelledby="separation-heading">
        <h2 id="separation-heading">A separate output, on purpose</h2>
        <p className="small">
          An area outlook has its own model version, issue and expiry times, and
          coverage. It is never merged with a photo assessment, and a photo
          assessment never becomes an outlook input until a human has verified it.
        </p>
        <p className="small muted">
          <Link href="/chat">Photo assessment</Link> answers a different question
          about one plant in one photo.
        </p>
      </section>

      <section className="card" aria-labelledby="coverage-heading">
        <h2 id="coverage-heading">Coverage is not risk</h2>
        <p className="small">
          When forecasts arrive, low reporting coverage will be shown as low
          coverage — never as low risk. No reports in an area is not evidence that
          the area is disease-free.
        </p>
        <div className="locked-state">
          <p>
            <strong>No outlook values are shown.</strong>
          </p>
          <p className="small muted">
            The map, forecast detail and coverage panel arrive with the forecasting
            phase. Nothing on this page is a forecast.
          </p>
          <Link href="/" className="button button-secondary">
            Back to overview
          </Link>
        </div>
      </section>
    </div>
  );
}
