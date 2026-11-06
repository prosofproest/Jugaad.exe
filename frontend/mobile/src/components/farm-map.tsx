import { useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { Badge, HealthDot, HealthPill, Icon, styles as uiStyles } from "@/components/ui";
import { healthLabel, useWorkspace } from "@/lib/workspace/store";
import type { Analysis, Farm, Health, Plot } from "@/lib/workspace/types";
import { colors, healthColor, radius, spacing } from "@/theme";

export type FarmLayer = "health" | "pest" | "disease" | "severity" | "recovery" | "history";

export const LAYERS: { value: FarmLayer; label: string; hint: string }[] = [
  { value: "health", label: "Plant health", hint: "Healthy, watch, pest and disease signs" },
  { value: "pest", label: "Pest affected", hint: "Blocks with a pest observation" },
  { value: "disease", label: "Disease affected", hint: "Blocks with a disease observation" },
  { value: "severity", label: "Severity", hint: "Highest recorded severity per block" },
  { value: "recovery", label: "Recovery", hint: "Recovery progress after treatment" },
  { value: "history", label: "History", hint: "Observations from the last 30 days" },
];

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

function plotAnalysis(analyses: Analysis[], plot: Plot, groups: string[]): Analysis[] {
  return analyses.filter(
    (analysis) =>
      (analysis.subjectType === "crop_group" && groups.includes(analysis.subjectId)) ||
      (analysis.subjectType === "plant" && groups.length > 0 && plot.farmId === analysis.farmId),
  );
}

export function FarmMap({
  farm,
  layer = "health",
  showPlants = true,
  onLayerChange,
}: {
  farm: Farm;
  layer?: FarmLayer;
  showPlants?: boolean;
  onLayerChange?: (layer: FarmLayer) => void;
}) {
  const { state } = useWorkspace();
  const [selectedPlot, setSelectedPlot] = useState<string | null>(null);

  const plotsWithGroups = useMemo(() => {
    const plots = state.plots.filter((plot) => plot.farmId === farm.id);
    return plots.map((plot) => {
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
      const hasDisease = analyses.some(
        (analysis) => analysis.category === "disease" || analysis.category === "nutrient",
      );
      const health: Health = plants.some((plant) => plant.health === "pest")
        ? "pest"
        : plants.some((plant) => plant.health === "diseased")
          ? "diseased"
          : plants.some((plant) => plant.health === "recovering")
            ? "recovering"
            : plants.some((plant) => plant.health === "watch")
              ? "watch"
              : plot.health;
      return { plot, groups, analyses, plants, highest, hasPest, hasDisease, health };
    });
  }, [farm.id, state.analyses, state.cropGroups, state.plants, state.plots]);

  const focus = plotsWithGroups.find((item) => item.plot.id === selectedPlot) ?? null;

  function fill(item: (typeof plotsWithGroups)[number]): string {
    if (layer === "health" || layer === "history") return healthColor(item.health);
    if (layer === "pest") return item.hasPest ? colors.pest : colors.healthy;
    if (layer === "disease") return item.hasDisease ? colors.diseased : colors.healthy;
    if (layer === "recovery") return item.health === "recovering" ? colors.recovering : colors.idle;
    switch (item.highest) {
      case "critical":
      case "high":
        return colors.diseased;
      case "moderate":
        return colors.watch;
      case "low":
        return colors.recovering;
      default:
        return colors.healthy;
    }
  }

  return (
    <View style={styles.wrap}>
      {onLayerChange ? (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.layers}>
          {LAYERS.map((option) => {
            const active = option.value === layer;
            return (
              <Pressable
                key={option.value}
                onPress={() => onLayerChange(option.value)}
                accessibilityRole="button"
                accessibilityState={{ selected: active }}
                style={[styles.layer, active && styles.layerActive]}
              >
                <Text style={[styles.layerText, active && styles.layerTextActive]}>{option.label}</Text>
              </Pressable>
            );
          })}
        </ScrollView>
      ) : null}

      <View style={styles.canvas} accessibilityLabel={`${farm.name} farm map, ${layer} layer`}>
        <View style={styles.boundary} />
        <View style={styles.road} />
        <View style={styles.water} />
        {plotsWithGroups.map((item) => {
          const { plot } = item;
          const sections = Math.max(plot.sections.length, 1);
          return (
            <Pressable
              key={plot.id}
              onPress={() => setSelectedPlot(plot.id === selectedPlot ? null : plot.id)}
              accessibilityRole="button"
              accessibilityLabel={`${plot.name}, ${healthLabel(item.health)}`}
              style={{
                position: "absolute",
                left: `${plot.box.x}%`,
                top: `${plot.box.y}%`,
                width: `${plot.box.w}%`,
                height: `${plot.box.h}%`,
                backgroundColor: fill(item),
                borderRadius: 4,
                borderWidth: selectedPlot === plot.id ? 2 : 1,
                borderColor: selectedPlot === plot.id ? colors.text : "rgba(14,15,12,0.28)",
                overflow: "hidden",
              }}
            >
              {Array.from({ length: sections - 1 }).map((_, index) => (
                <View
                  key={`${plot.id}-section-${index}`}
                  style={{
                    position: "absolute",
                    left: `${((index + 1) / sections) * 100}%`,
                    top: 0,
                    bottom: 0,
                    width: 1,
                    backgroundColor: "rgba(14,15,12,0.22)",
                  }}
                />
              ))}
              <Text numberOfLines={1} style={styles.plotName}>
                {plot.name}
              </Text>
              <Text style={styles.plotArea}>{plot.areaAcres} ac</Text>
              {showPlants
                ? item.plants.map((plant) => (
                    <View
                      key={plant.id}
                      style={{
                        position: "absolute",
                        left: `${Math.min(94, Math.max(2, plant.mapPosition.x))}%`,
                        top: `${Math.min(92, Math.max(18, plant.mapPosition.y))}%`,
                        width: 6,
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: healthColor(plant.health),
                        borderWidth: 1,
                        borderColor: "rgba(14,15,12,0.45)",
                      }}
                    />
                  ))
                : null}
            </Pressable>
          );
        })}
        <Text style={styles.compass}>N</Text>
      </View>

      <View style={styles.legend}>
        {(["healthy", "watch", "pest", "diseased", "recovering"] as Health[]).map((health) => (
          <View key={health} style={styles.legendItem}>
            <HealthDot health={health} size={9} />
            <Text style={styles.legendText}>
              {health === "diseased" ? "Disease" : health === "pest" ? "Pest" : healthLabel(health)}
            </Text>
          </View>
        ))}
      </View>

      {focus ? (
        <View style={styles.detail}>
          <View style={styles.detailHead}>
            <View style={uiStyles.flex}>
              <Text style={styles.detailEyebrow}>Selected plot</Text>
              <Text style={styles.detailTitle}>{focus.plot.name}</Text>
            </View>
            <HealthPill health={focus.health} />
          </View>
          <View style={styles.detailGrid}>
            <View style={styles.detailCell}>
              <Text style={styles.detailLabel}>Area</Text>
              <Text style={styles.detailValue}>{focus.plot.areaAcres} acres</Text>
            </View>
            <View style={styles.detailCell}>
              <Text style={styles.detailLabel}>Plants tracked</Text>
              <Text style={styles.detailValue}>{focus.plants.length}</Text>
            </View>
            <View style={styles.detailCell}>
              <Text style={styles.detailLabel}>Observations</Text>
              <Text style={styles.detailValue}>{focus.analyses.length}</Text>
            </View>
            <View style={styles.detailCell}>
              <Text style={styles.detailLabel}>Highest severity</Text>
              <Text style={styles.detailValue}>{focus.highest}</Text>
            </View>
          </View>
          <View style={styles.groupRow}>
            {focus.groups.map((group) => (
              <Badge key={group.id} tone="neutral">
                {group.crop} · {group.variety}
              </Badge>
            ))}
          </View>
          <Text style={styles.hint}>
            Plant dots show the latest scouting status. Tap a plot to inspect crop groups and plants.
          </Text>
        </View>
      ) : (
        <Text style={styles.hint}>
          Tap a plot to see its crop groups, plants and observations. Colour is always paired with a
          label.
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.sm },
  layers: { flexDirection: "row", gap: spacing.xs, paddingVertical: 2 },
  layer: {
    borderWidth: 1,
    borderColor: colors.borderStrong,
    borderRadius: radius.chip,
    paddingHorizontal: 10,
    paddingVertical: 5,
    backgroundColor: colors.surface,
  },
  layerActive: { backgroundColor: colors.text, borderColor: colors.text },
  layerText: { fontSize: 11, fontWeight: "600", color: colors.textSecondary },
  layerTextActive: { color: colors.textInverse },
  canvas: {
    width: "100%",
    aspectRatio: 1,
    backgroundColor: "#eef1e8",
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: "hidden",
  },
  boundary: {
    position: "absolute",
    left: "4%",
    top: "4%",
    right: "4%",
    bottom: "4%",
    borderWidth: 2,
    borderStyle: "dashed",
    borderColor: "#9aa78f",
    borderRadius: 6,
  },
  road: {
    position: "absolute",
    left: "4%",
    right: "4%",
    top: "78%",
    height: 8,
    backgroundColor: "#e6dcc8",
    borderRadius: 4,
  },
  water: {
    position: "absolute",
    left: "62%",
    top: "4%",
    bottom: "4%",
    width: 6,
    backgroundColor: "#bfdbfe",
    borderRadius: 3,
  },
  plotName: {
    position: "absolute",
    top: 4,
    left: 4,
    right: 4,
    fontSize: 10,
    fontWeight: "800",
    color: colors.text,
  },
  plotArea: {
    position: "absolute",
    top: 17,
    left: 4,
    fontSize: 8,
    fontWeight: "600",
    color: "rgba(14,15,12,0.65)",
  },
  compass: {
    position: "absolute",
    top: 6,
    right: 8,
    fontSize: 10,
    fontWeight: "800",
    color: colors.textSecondary,
  },
  legend: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md },
  legendItem: { flexDirection: "row", alignItems: "center", gap: 4 },
  legendText: { fontSize: 11, color: colors.textSecondary },
  detail: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    gap: spacing.sm,
  },
  detailHead: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  detailEyebrow: {
    fontSize: 10,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: colors.textSecondary,
    fontWeight: "700",
  },
  detailTitle: { fontSize: 16, fontWeight: "700", color: colors.text },
  detailGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md },
  detailCell: { minWidth: "40%", gap: 1 },
  detailLabel: { fontSize: 11, color: colors.textSecondary },
  detailValue: { fontSize: 14, fontWeight: "700", color: colors.text, textTransform: "capitalize" },
  groupRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  hint: { fontSize: 11, lineHeight: 16, color: colors.textSecondary },
});
