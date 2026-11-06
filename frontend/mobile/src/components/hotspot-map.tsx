import { useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { Badge, HealthDot, Icon, RiskPill, SectionTitle } from "@/components/ui";
import { formatDate } from "@/lib/format";
import { severityTone, useWorkspace } from "@/lib/workspace/store";
import type { HotspotCase, RiskBand, Severity } from "@/lib/workspace/types";
import { colors, radius, spacing, type Tone } from "@/theme";

const riskColor: Record<RiskBand, string> = {
  low: "#2f6f4e",
  moderate: "#d4a017",
  high: "#c2410c",
  urgent: "#b42318",
  insufficient: "#5f6b7a",
};

function unique<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}

function FilterRow({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <View style={styles.filterGroup}>
      <Text style={styles.filterLabel}>{label}</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterOptions}>
        {options.map((option) => {
          const active = option.value === value;
          return (
            <Pressable
              key={option.value}
              onPress={() => onChange(option.value)}
              accessibilityRole="button"
              accessibilityState={{ selected: active }}
              style={[styles.filterChip, active && styles.filterChipActive]}
            >
              <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>
                {option.label}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
}

export function HotspotMap() {
  const { state } = useWorkspace();
  const [pest, setPest] = useState("all");
  const [crop, setCrop] = useState("all");
  const [district, setDistrict] = useState("all");
  const [windowDays, setWindowDays] = useState("14");
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [severity, setSeverity] = useState("all");
  const [selected, setSelected] = useState<HotspotCase | null>(null);

  const pests = unique(state.cases.map((item) => item.pest));
  const crops = unique(state.cases.map((item) => item.crop));
  const districts = unique(state.cases.map((item) => item.district));

  const cutoff = useMemo(() => {
    const date = new Date();
    date.setDate(date.getDate() - Number(windowDays));
    return date;
  }, [windowDays]);

  const cases = useMemo(
    () =>
      state.cases.filter((item) => {
        if (new Date(item.reportedAt) < cutoff) return false;
        if (pest !== "all" && item.pest !== pest) return false;
        if (crop !== "all" && item.crop !== crop) return false;
        if (district !== "all" && item.district !== district) return false;
        if (verifiedOnly && !item.verified) return false;
        if (severity !== "all" && item.severity !== severity) return false;
        return true;
      }),
    [state.cases, cutoff, pest, crop, district, verifiedOnly, severity],
  );

  const regions = useMemo(
    () =>
      state.riskRegions.filter((region) => {
        if (pest !== "all" && region.pest !== pest) return false;
        if (crop !== "all" && region.crop !== crop) return false;
        if (district !== "all" && region.district !== district) return false;
        return true;
      }),
    [state.riskRegions, pest, crop, district],
  );

  const totalCases = cases.reduce((sum, item) => sum + item.cases, 0);
  const verifiedCases = cases.filter((item) => item.verified).reduce((sum, item) => sum + item.cases, 0);
  const nearby = [...cases].sort((a, b) => b.cases - a.cases).slice(0, 4);

  return (
    <View style={styles.wrap}>
      <View style={styles.statRow}>
        <View style={styles.statCell}>
          <Text style={styles.statValue}>{totalCases}</Text>
          <Text style={styles.statLabel}>Reported cases</Text>
        </View>
        <View style={styles.statCell}>
          <Text style={styles.statValue}>{verifiedCases}</Text>
          <Text style={styles.statLabel}>Verified cases</Text>
        </View>
        <View style={styles.statCell}>
          <Text style={styles.statValue}>{cases.length}</Text>
          <Text style={styles.statLabel}>Hotspots</Text>
        </View>
      </View>

      <FilterRow
        label="Pest"
        value={pest}
        onChange={setPest}
        options={[{ value: "all", label: "All pests" }, ...pests.map((item) => ({ value: item, label: item }))]}
      />
      <FilterRow
        label="Crop"
        value={crop}
        onChange={setCrop}
        options={[{ value: "all", label: "All crops" }, ...crops.map((item) => ({ value: item, label: item }))]}
      />
      <FilterRow
        label="District"
        value={district}
        onChange={setDistrict}
        options={[
          { value: "all", label: "All districts" },
          ...districts.map((item) => ({ value: item, label: item })),
        ]}
      />
      <FilterRow
        label="Reported"
        value={windowDays}
        onChange={setWindowDays}
        options={[
          { value: "7", label: "Last 7 days" },
          { value: "14", label: "Last 14 days" },
          { value: "30", label: "Last 30 days" },
        ]}
      />
      <FilterRow
        label="Severity"
        value={severity}
        onChange={setSeverity}
        options={[
          { value: "all", label: "All" },
          { value: "low", label: "Low" },
          { value: "moderate", label: "Moderate" },
          { value: "high", label: "High" },
          { value: "critical", label: "Critical" },
        ]}
      />
      <Pressable
        onPress={() => setVerifiedOnly((current) => !current)}
        accessibilityRole="checkbox"
        accessibilityState={{ checked: verifiedOnly }}
        style={styles.checkRow}
      >
        <View style={[styles.checkbox, verifiedOnly && styles.checkboxOn]}>
          {verifiedOnly ? <Icon name="checkmark" size={13} color={colors.onBrand} /> : null}
        </View>
        <Text style={styles.checkLabel}>Expert-verified only</Text>
      </Pressable>

      <View style={styles.map} accessibilityLabel="Regional pest hotspot map">
        <View style={styles.regionOutline} />
        <View style={styles.regionLineOne} />
        <View style={styles.regionLineTwo} />
        <View style={styles.regionLineThree} />
        <Text style={[styles.regionLabel, { left: "8%", top: "6%" }]}>Krishnagiri</Text>
        <Text style={[styles.regionLabel, { right: "8%", top: "6%" }]}>Dharmapuri</Text>
        <Text style={[styles.regionLabel, { left: "44%", bottom: "2%" }]}>Salem</Text>

        {regions.map((region) => {
          const size = region.band === "insufficient" ? 30 : 34 + region.verified * 3;
          return (
            <View
              key={region.id}
              style={{
                position: "absolute",
                left: `${region.x}%`,
                top: `${region.y}%`,
                width: size,
                height: size,
                marginLeft: -size / 2,
                marginTop: -size / 2,
                borderRadius: size / 2,
                backgroundColor: `${riskColor[region.band]}33`,
                borderWidth: 1,
                borderColor: riskColor[region.band],
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <View
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: riskColor[region.band],
                }}
              />
            </View>
          );
        })}
        {cases.map((item) => (
          <Pressable
            key={item.id}
            onPress={() => setSelected(item)}
            accessibilityRole="button"
            accessibilityLabel={`${item.pest} in ${item.village}`}
            style={{
              position: "absolute",
              left: `${item.x}%`,
              top: `${item.y}%`,
              width: 14,
              height: 14,
              marginLeft: -7,
              marginTop: -7,
              borderRadius: 7,
              backgroundColor: item.verified ? colors.text : colors.surface,
              borderWidth: 2,
              borderColor: item.verified ? colors.text : colors.textSecondary,
            }}
          />
        ))}
      </View>

      <View style={styles.legend}>
        {(["low", "moderate", "high", "urgent", "insufficient"] as RiskBand[]).map((band) => (
          <View key={band} style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: riskColor[band] }]} />
            <Text style={styles.legendText}>{band === "insufficient" ? "Insufficient" : band}</Text>
          </View>
        ))}
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: colors.text }]} />
          <Text style={styles.legendText}>Verified case</Text>
        </View>
      </View>

      {selected ? (
        <View style={styles.caseCard}>
          <View style={styles.caseHead}>
            <View style={{ flex: 1 }}>
              <Text style={styles.eyebrow}>Selected report</Text>
              <Text style={styles.caseTitle}>{selected.pest}</Text>
            </View>
            <Pressable onPress={() => setSelected(null)} accessibilityLabel="Clear selection">
              <Icon name="close" size={18} color={colors.textSecondary} />
            </Pressable>
          </View>
          <View style={styles.caseGrid}>
            <View style={styles.caseCell}>
              <Text style={styles.statLabel}>Crop</Text>
              <Text style={styles.caseValue}>{selected.crop}</Text>
            </View>
            <View style={styles.caseCell}>
              <Text style={styles.statLabel}>Location</Text>
              <Text style={styles.caseValue}>
                {selected.village}, {selected.district}
              </Text>
            </View>
            <View style={styles.caseCell}>
              <Text style={styles.statLabel}>Reported</Text>
              <Text style={styles.caseValue}>{formatDate(selected.reportedAt)}</Text>
            </View>
            <View style={styles.caseCell}>
              <Text style={styles.statLabel}>Cases</Text>
              <Text style={styles.caseValue}>{selected.cases}</Text>
            </View>
          </View>
          <Badge tone={selected.verified ? "ok" : "warn"}>
            {selected.verified ? "Verified signal" : "Unverified report"}
          </Badge>
          <Text style={styles.hint}>
            A verified case is not the same as an area risk score. They are shown as separate layers.
          </Text>
        </View>
      ) : null}

      <View style={styles.panel}>
        <SectionTitle title="Predicted risk" detail="Next 48 hours" />
        {regions
          .slice()
          .sort((a, b) => b.reports - a.reports)
          .slice(0, 5)
          .map((region) => (
            <View key={region.id} style={styles.rankRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.rankTitle}>{region.district}</Text>
                <Text style={styles.hint}>
                  {region.crop} · {region.pest}
                </Text>
              </View>
              <RiskPill band={region.band} />
            </View>
          ))}
        <Text style={styles.hint}>
          Low risk does not mean the disease is absent. Coverage is shown separately.
        </Text>
      </View>

      <View style={styles.panel}>
        <SectionTitle title="Nearby affected regions" detail="Highest case counts" />
        {nearby.map((item) => (
          <View key={item.id} style={styles.rankRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.rankTitle}>{item.village}</Text>
              <Text style={styles.hint}>
                {item.pest} · {item.crop}
              </Text>
            </View>
            <Text style={styles.rankCount}>{item.cases}</Text>
          </View>
        ))}
      </View>

      <View style={styles.coverage}>
        <Icon name="shield-checkmark-outline" size={18} color={colors.info} />
        <View style={{ flex: 1 }}>
          <Text style={styles.coverageTitle}>Coverage and freshness</Text>
          <Text style={styles.hint}>
            Risk bands are shown only where inputs are fresh. Regions with fewer than 3 verified
            reports show insufficient data rather than a low-risk colour.
          </Text>
        </View>
      </View>

      <View style={styles.panel}>
        <SectionTitle title="Reports" detail={`${cases.length} match these filters`} />
        {cases.length === 0 ? (
          <Text style={styles.hint}>No reports match these filters.</Text>
        ) : (
          cases.map((item) => (
            <View key={item.id} style={styles.reportRow}>
              <View style={{ flex: 1, gap: 2 }}>
                <Text style={styles.rankTitle}>{item.pest}</Text>
                <Text style={styles.hint}>
                  {item.crop} · {item.village}, {item.district}
                </Text>
                <Text style={styles.hint}>{formatDate(item.reportedAt)}</Text>
              </View>
              <View style={styles.reportTags}>
                <Badge tone={severityTone(item.severity) as Tone}>{item.severity}</Badge>
                <Badge tone={item.verified ? "ok" : "warn"}>
                  {item.verified ? "Verified" : "Pending"}
                </Badge>
                <Text style={styles.rankCount}>{item.cases}</Text>
              </View>
            </View>
          ))
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.md },
  statRow: {
    flexDirection: "row",
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  statCell: { flex: 1, alignItems: "center", gap: 1 },
  statValue: { fontSize: 22, fontWeight: "800", color: colors.text },
  statLabel: { fontSize: 11, color: colors.textSecondary, textAlign: "center" },
  filterGroup: { gap: 5 },
  filterLabel: { fontSize: 11, fontWeight: "700", color: colors.textSecondary },
  filterOptions: { flexDirection: "row", gap: spacing.xs },
  filterChip: {
    borderWidth: 1,
    borderColor: colors.borderStrong,
    borderRadius: radius.chip,
    paddingHorizontal: 10,
    paddingVertical: 5,
    backgroundColor: colors.surface,
  },
  filterChipActive: { backgroundColor: colors.text, borderColor: colors.text },
  filterChipText: { fontSize: 11, color: colors.textSecondary, fontWeight: "600" },
  filterChipTextActive: { color: colors.textInverse },
  checkRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 5,
    borderWidth: 1,
    borderColor: colors.borderStrong,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.surface,
  },
  checkboxOn: { backgroundColor: colors.brand, borderColor: colors.brand },
  checkLabel: { fontSize: 12, color: colors.textSecondary, fontWeight: "600" },
  map: {
    width: "100%",
    aspectRatio: 1,
    backgroundColor: "#eef2e8",
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: "hidden",
  },
  regionOutline: {
    position: "absolute",
    left: "6%",
    top: "8%",
    right: "6%",
    bottom: "8%",
    borderWidth: 2,
    borderColor: "#a9b59e",
    borderRadius: 40,
  },
  regionLineOne: {
    position: "absolute",
    left: "30%",
    top: "8%",
    height: "84%",
    width: 1,
    backgroundColor: "#c3ccba",
    transform: [{ rotate: "10deg" }],
  },
  regionLineTwo: {
    position: "absolute",
    left: "68%",
    top: "8%",
    height: "84%",
    width: 1,
    backgroundColor: "#c3ccba",
  },
  regionLineThree: {
    position: "absolute",
    left: "6%",
    right: "6%",
    top: "55%",
    height: 1,
    backgroundColor: "#c3ccba",
  },
  regionLabel: { position: "absolute", fontSize: 10, fontWeight: "700", color: "#5f6b5a" },
  legend: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md },
  legendItem: { flexDirection: "row", alignItems: "center", gap: 4 },
  legendDot: { width: 9, height: 9, borderRadius: 5 },
  legendText: { fontSize: 10, color: colors.textSecondary, textTransform: "capitalize" },
  caseCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    gap: spacing.sm,
  },
  caseHead: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  eyebrow: {
    fontSize: 10,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: colors.textSecondary,
    fontWeight: "700",
  },
  caseTitle: { fontSize: 16, fontWeight: "700", color: colors.text },
  caseGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md },
  caseCell: { minWidth: "40%", gap: 1 },
  caseValue: { fontSize: 13, fontWeight: "700", color: colors.text },
  panel: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    gap: spacing.sm,
  },
  rankRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingVertical: 5,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  rankTitle: { fontSize: 13, fontWeight: "700", color: colors.text },
  rankCount: { fontSize: 16, fontWeight: "800", color: colors.text },
  hint: { fontSize: 11, lineHeight: 16, color: colors.textSecondary },
  coverage: {
    flexDirection: "row",
    gap: spacing.sm,
    padding: spacing.md,
    backgroundColor: "#e5efff",
    borderRadius: radius.card,
    alignItems: "flex-start",
  },
  coverageTitle: { fontSize: 12, fontWeight: "800", color: colors.info, marginBottom: 2 },
  reportRow: {
    flexDirection: "row",
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  reportTags: { alignItems: "flex-end", gap: 4 },
});
