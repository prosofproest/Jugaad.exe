"use client";

import { useMemo, useState } from "react";

import { healthLabel } from "@/lib/workspace/store";
import type { Analysis, Farm, Health, Plot } from "@/lib/workspace/types";
import { useWorkspace } from "@/lib/workspace/store";

export type FarmLayer = "health" | "pest" | "disease" | "severity" | "recovery" | "history";

const LAYERS: { value: FarmLayer; label: string; hint: string }[] = [
  { value: "health", label: "Plant health", hint: "Healthy, watch, pest and disease signs" },
  { value: "pest", label: "Pest affected", hint: "Blocks with a pest observation" },
  { value: "disease", label: "Disease affected", hint: "Blocks with a disease observation" },
  { value: "severity", label: "Severity", hint: "Highest recorded severity per block" },
  { value: "recovery", label: "Recovery", hint: "Recovery progress after treatment" },
  { value: "history", label: "History", hint: "Observations from the last 30 days" },
];

function healthClass(health: Health): string {
  return `ws-health-${health}`;
}

function plotAnalysis(analyses: Analysis[], plot: Plot, groups: string[]): Analysis[] {
  return analyses.filter(
    (analysis) =>
      (analysis.subjectType === "crop_group" && groups.includes(analysis.subjectId)) ||
      (analysis.subjectType === "plant" && groups.length > 0 && plot.farmId === analysis.farmId),
  );
}

function severityRank(severity: Analysis["severity"]): number {
  switch (severity) {
    case "critical":
      return 5;
    case "high":
      return 4;
    case "moderate":
      return 3;
    case "low":
      return 2;
    default:
      return 1;
  }
}

export function FarmMap({
  farm,
  layer = "health",
  showPlants = true,
  onLayerChange,
  compact = false,
}: {
  farm: Farm;
  layer?: FarmLayer;
  showPlants?: boolean;
  onLayerChange?: (layer: FarmLayer) => void;
  compact?: boolean;
}) {
  const { state } = useWorkspace();
  const [selectedPlot, setSelectedPlot] = useState<string | null>(null);
  const [hoveredPlant, setHoveredPlant] = useState<string | null>(null);

  const plots = state.plots.filter((plot) => plot.farmId === farm.id);
  const plotsWithGroups = useMemo(
    () =>
      plots.map((plot) => {
        const groups = state.cropGroups.filter((group) => group.plotId === plot.id);
        const groupIds = groups.map((group) => group.id);
        const analyses = plotAnalysis(state.analyses, plot, groupIds);
        const plants = state.plants.filter((plant) => plant.plotId === plot.id);
        const highest = analyses.reduce(
          (current, analysis) =>
            severityRank(analysis.severity) > severityRank(current) ? analysis.severity : current,
          "none" as Analysis["severity"],
        );
        const hasPest = analyses.some((analysis) => analysis.category === "pest");
        const hasDisease = analyses.some((analysis) => analysis.category === "disease" || analysis.category === "nutrient");
        const recovering = plants.filter((plant) => plant.health === "recovering").length;
        const health: Health =
          plants.some((plant) => plant.health === "pest")
            ? "pest"
            : plants.some((plant) => plant.health === "diseased")
              ? "diseased"
              : plants.some((plant) => plant.health === "recovering") || recovering > 0
                ? "recovering"
                : plants.some((plant) => plant.health === "watch")
                  ? "watch"
                  : plot.health;
        return { plot, groups, analyses, plants, highest, hasPest, hasDisease, health };
      }),
    [plots, state.analyses, state.cropGroups, state.plants],
  );

  const focus = plotsWithGroups.find((item) => item.plot.id === selectedPlot) ?? null;

  function fillClass(item: (typeof plotsWithGroups)[number]): string {
    if (layer === "health" || layer === "history") return healthClass(item.health);
    if (layer === "pest") return item.hasPest ? "ws-health-pest" : "ws-health-healthy";
    if (layer === "disease") return item.hasDisease ? "ws-health-diseased" : "ws-health-healthy";
    if (layer === "recovery") {
      return item.health === "recovering" ? "ws-health-recovering" : "ws-health-neutral";
    }
    switch (item.highest) {
      case "critical":
      case "high":
        return "ws-health-diseased";
      case "moderate":
        return "ws-health-watch";
      case "low":
        return "ws-health-recovering";
      default:
        return "ws-health-healthy";
    }
  }

  return (
    <div className={compact ? "ws-farm-map ws-farm-map-compact" : "ws-farm-map"}>
      {onLayerChange ? (
        <div className="ws-map-layers">
          {LAYERS.map((option) => (
            <button
              key={option.value}
              type="button"
              title={option.hint}
              className={layer === option.value ? "ws-map-layer ws-map-layer-active" : "ws-map-layer"}
              onClick={() => onLayerChange(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>
      ) : null}

      <div className="ws-map-canvas">
        <svg viewBox="0 0 100 100" role="img" aria-label={`${farm.name} farm map, ${layer} layer`}>
          <defs>
            <pattern id="diseaseHatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <line x1="0" y1="0" x2="0" y2="4" className="ws-hatch-line" />
            </pattern>
            <pattern id="recoveryHatch" width="5" height="5" patternUnits="userSpaceOnUse">
              <circle cx="1" cy="1" r="0.7" className="ws-hatch-dot" />
            </pattern>
            <linearGradient id="farmWater" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#dbeafe" />
              <stop offset="1" stopColor="#bfdbfe" />
            </linearGradient>
          </defs>

          <polygon
            points={farm.boundary.map((point) => `${point.x},${point.y}`).join(" ")}
            className="ws-map-boundary"
          />

          <path d="M6 76 C 24 70, 30 84, 44 82 S 68 72, 92 78" className="ws-map-road" fill="none" />
          <path d="M64 6 C 66 26, 58 42, 62 62 S 70 84, 68 94" className="ws-map-water" fill="none" />

          {plotsWithGroups.map((item) => {
            const { plot } = item;
            const sections = plot.sections.length || 1;
            return (
              <g
                key={plot.id}
                className="ws-map-plot"
                tabIndex={0}
                role="button"
                aria-label={`${plot.name}, ${healthLabel(item.health)}`}
                onClick={() => setSelectedPlot(plot.id === selectedPlot ? null : plot.id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    setSelectedPlot(plot.id === selectedPlot ? null : plot.id);
                  }
                }}
              >
                <rect
                  x={plot.box.x}
                  y={plot.box.y}
                  width={plot.box.w}
                  height={plot.box.h}
                  rx="2"
                  className={`ws-map-plot-base ${fillClass(item)}`}
                />
                <rect
                  x={plot.box.x}
                  y={plot.box.y}
                  width={plot.box.w}
                  height={plot.box.h}
                  rx="2"
                  className="ws-map-plot-outline"
                />
                {layer === "disease" && item.hasDisease ? (
                  <rect
                    x={plot.box.x}
                    y={plot.box.y}
                    width={plot.box.w}
                    height={plot.box.h}
                    rx="2"
                    fill="url(#diseaseHatch)"
                  />
                ) : null}
                {layer === "recovery" && item.health === "recovering" ? (
                  <rect
                    x={plot.box.x}
                    y={plot.box.y}
                    width={plot.box.w}
                    height={plot.box.h}
                    rx="2"
                    fill="url(#recoveryHatch)"
                  />
                ) : null}

                {Array.from({ length: sections }).map((_, index) => {
                  const sectionWidth = plot.box.w / sections;
                  return (
                    <line
                      key={`${plot.id}-section-${index}`}
                      x1={plot.box.x + sectionWidth * index}
                      y1={plot.box.y}
                      x2={plot.box.x + sectionWidth * index}
                      y2={plot.box.y + plot.box.h}
                      className="ws-map-section-line"
                    />
                  );
                })}

                <text
                  x={plot.box.x + plot.box.w / 2}
                  y={plot.box.y + 6}
                  textAnchor="middle"
                  className="ws-map-plot-label"
                >
                  {plot.name}
                </text>
                <text
                  x={plot.box.x + plot.box.w / 2}
                  y={plot.box.y + 10}
                  textAnchor="middle"
                  className="ws-map-plot-area"
                >
                  {plot.areaAcres} ac
                </text>

                {showPlants
                  ? item.plants.map((plant) => (
                      <circle
                        key={plant.id}
                        cx={plot.box.x + (plant.mapPosition.x / 100) * plot.box.w}
                        cy={plot.box.y + (plant.mapPosition.y / 100) * plot.box.h}
                        r={hoveredPlant === plant.id ? 1.8 : 1.2}
                        className={`ws-map-plant ${healthClass(plant.health)}`}
                        onMouseEnter={() => setHoveredPlant(plant.id)}
                        onMouseLeave={() => setHoveredPlant(null)}
                        onClick={(event) => {
                          event.stopPropagation();
                          setSelectedPlot(plot.id);
                        }}
                      >
                        <title>{`${plant.code} · ${healthLabel(plant.health)}`}</title>
                      </circle>
                    ))
                  : null}
              </g>
            );
          })}

          <circle cx="94" cy="8" r="2.2" className="ws-map-north" />
          <text x="94" y="6" textAnchor="middle" className="ws-map-compass">
            N
          </text>
        </svg>

        <div className="ws-map-legend" aria-label="Map legend">
          <span><i className="ws-legend-swatch ws-health-healthy" /> Healthy</span>
          <span><i className="ws-legend-swatch ws-health-watch" /> Watch</span>
          <span><i className="ws-legend-swatch ws-health-pest" /> Pest</span>
          <span><i className="ws-legend-swatch ws-health-diseased" /> Disease</span>
          <span><i className="ws-legend-swatch ws-health-recovering" /> Recovering</span>
        </div>
      </div>

      {focus ? (
        <div className="ws-map-detail">
          <div className="ws-map-detail-head">
            <div>
              <p className="ws-eyebrow">Selected plot</p>
              <h3>{focus.plot.name}</h3>
            </div>
            <span className={`ws-health-chip ${healthClass(focus.health)}`}>{healthLabel(focus.health)}</span>
          </div>
          <div className="ws-map-detail-grid">
            <div>
              <span>Area</span>
              <strong>{focus.plot.areaAcres} acres</strong>
            </div>
            <div>
              <span>Plants tracked</span>
              <strong>{focus.plants.length}</strong>
            </div>
            <div>
              <span>Observations</span>
              <strong>{focus.analyses.length}</strong>
            </div>
            <div>
              <span>Highest severity</span>
              <strong>{focus.highest}</strong>
            </div>
          </div>
          <div className="ws-map-groups">
            {focus.groups.map((group) => (
              <span key={group.id} className="ws-chip">
                {group.crop} · {group.variety}
              </span>
            ))}
          </div>
          <p className="ws-small ws-muted">
            Plant dots show the latest scouting status. Select a plot to inspect crop groups and plants.
          </p>
        </div>
      ) : (
        <p className="ws-map-hint">
          Tap a plot to see its crop groups, plants and observations. Colour is always paired with a label.
        </p>
      )}
    </div>
  );
}

export { LAYERS };
