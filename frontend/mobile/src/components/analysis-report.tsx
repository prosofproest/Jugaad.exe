import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { Badge, Banner, Button, Card, Icon, PhotoTile, ProgressBar, SeverityPill } from "@/components/ui";
import { formatDateTime, partLabel } from "@/lib/format";
import { useWorkspace } from "@/lib/workspace/store";
import type { Analysis } from "@/lib/workspace/types";
import { colors, radius, spacing, type Tone } from "@/theme";

function confidenceLabel(band: Analysis["confidenceBand"]): string {
  switch (band) {
    case "high":
      return "High confidence band";
    case "medium":
      return "Medium confidence band";
    case "low":
      return "Low confidence band";
    case "not_calibrated":
      return "Not yet calibrated";
  }
}

function confidenceTone(band: Analysis["confidenceBand"]): Tone {
  if (band === "high") return "ok";
  if (band === "medium") return "warn";
  if (band === "low") return "bad";
  return "neutral";
}

function ReviewBadge({ analysis }: { analysis: Analysis }) {
  switch (analysis.reviewStatus) {
    case "pending":
      return <Badge tone="purple">Pending expert review</Badge>;
    case "verified":
      return <Badge tone="ok">Expert verified</Badge>;
    case "corrected":
      return <Badge tone="info">Corrected by expert</Badge>;
    case "rejected":
      return <Badge tone="bad">Rejected by expert</Badge>;
    default:
      return <Badge tone="neutral">Not reviewed</Badge>;
  }
}

function Bullet({ children }: { children: string }) {
  return (
    <View style={styles.bullet}>
      <Text style={styles.bulletDot}>•</Text>
      <Text style={styles.bulletText}>{children}</Text>
    </View>
  );
}

export function AnalysisReport({
  analysis,
  onCompare,
}: {
  analysis: Analysis;
  onCompare?: () => void;
}) {
  const { requestVerification } = useWorkspace();
  const [requested, setRequested] = useState(false);
  const subject = analysis.pest ?? analysis.disease ?? "No specific match";
  const isHealthy = analysis.category === "healthy";

  return (
    <View style={styles.wrap}>
      <Card>
        <View style={styles.mediaRow}>
          <View style={styles.media}>
            <PhotoTile
              tone={analysis.imageTone}
              mediaType={analysis.mediaType}
              label={`${analysis.subjectLabel} capture`}
              size="md"
            />
          </View>
          <View style={styles.mediaMeta}>
            <Badge tone="neutral">{analysis.mediaType === "video" ? "Video" : "Photo"}</Badge>
            <Badge tone="neutral">{partLabel(analysis.plantPart)}</Badge>
            <Badge tone="brand">Demo</Badge>
          </View>
        </View>
        <Text style={styles.eyebrow}>Assistive photo assessment</Text>
        <Text style={styles.title}>
          {isHealthy ? "No visible symptoms detected" : `Possible symptom match: ${subject}`}
        </Text>
        <Text style={styles.meta}>
          {analysis.subjectLabel} · {analysis.farmName} · {formatDateTime(analysis.createdAt)}
        </Text>
        <View style={styles.badges}>
          <SeverityPill severity={analysis.severity} />
          <ReviewBadge analysis={analysis} />
        </View>
      </Card>

      <Card>
        <View style={styles.summaryGrid}>
          <View style={styles.summaryCell}>
            <Text style={styles.summaryLabel}>Confidence</Text>
            <Badge tone={confidenceTone(analysis.confidenceBand)}>
              {confidenceLabel(analysis.confidenceBand)}
            </Badge>
            <Text style={styles.meta}>
              {analysis.calibrated
                ? "Calibrated probabilities approved"
                : "Not yet calibrated · shown as a band, not a percentage"}
            </Text>
          </View>
          <View style={styles.summaryCell}>
            <Text style={styles.summaryLabel}>Model</Text>
            <Text style={styles.summaryValue}>{analysis.modelVersion}</Text>
            <Text style={styles.meta}>
              Generated from {analysis.mediaType === "video" ? "video frames" : "one image"} plus crop
              context
            </Text>
          </View>
          <View style={styles.summaryCell}>
            <Text style={styles.summaryLabel}>Category</Text>
            <Text style={[styles.summaryValue, styles.capitalize]}>{analysis.category}</Text>
            <Text style={styles.meta}>Not a laboratory confirmation</Text>
          </View>
        </View>
      </Card>

      <Card>
        <Text style={styles.sectionHead}>Visible symptoms</Text>
        {analysis.symptoms.map((symptom) => (
          <Bullet key={symptom}>{symptom}</Bullet>
        ))}
      </Card>

      <Card>
        <Text style={styles.sectionHead}>Affected plant parts</Text>
        <View style={styles.chipRow}>
          {analysis.affectedParts.length > 0 ? (
            analysis.affectedParts.map((part) => (
              <Badge key={part} tone="neutral">
                {partLabel(part)}
              </Badge>
            ))
          ) : (
            <Badge tone="neutral">None observed</Badge>
          )}
        </View>
        <Text style={[styles.sectionHead, styles.mt]}>Possible causes</Text>
        {analysis.causes.map((cause) => (
          <Bullet key={cause}>{cause}</Bullet>
        ))}
      </Card>

      <Card>
        <Text style={styles.sectionHead}>Alternative possible diagnoses</Text>
        {analysis.alternatives.length > 0 ? (
          analysis.alternatives.map((alternative) => (
            <ProgressBar
              key={alternative.label}
              value={alternative.confidence}
              label={`${alternative.label} · ${alternative.confidence}% relative evidence`}
              tone="warn"
            />
          ))
        ) : (
          <Text style={styles.meta}>No other class cleared the comparison threshold.</Text>
        )}
      </Card>

      <Card>
        <Text style={styles.sectionHead}>Recommended next steps</Text>
        {analysis.nextSteps.map((step) => (
          <View key={step} style={styles.bullet}>
            <Icon name="checkmark-circle-outline" size={16} color={colors.success} />
            <Text style={styles.bulletText}>{step}</Text>
          </View>
        ))}
      </Card>

      {analysis.reviewer ? (
        <Card tone="brand">
          <View style={styles.reviewHead}>
            <Icon name="shield-checkmark-outline" size={20} color={colors.low} />
            <View style={{ flex: 1 }}>
              <Text style={styles.sectionHead}>Expert review · {analysis.reviewer}</Text>
              <Text style={styles.meta}>
                {analysis.reviewStatus === "corrected"
                  ? "Diagnosis corrected"
                  : "Verification recorded"}
              </Text>
            </View>
          </View>
          <Text style={styles.bulletText}>{analysis.reviewerNote}</Text>
          {analysis.expertRecommendation && analysis.expertRecommendation.length > 0
            ? analysis.expertRecommendation.map((item) => <Bullet key={item}>{item}</Bullet>)
            : null}
        </Card>
      ) : null}

      {analysis.notes ? (
        <Card>
          <Text style={styles.meta}>
            <Text style={styles.bold}>Field notes: </Text>
            {analysis.notes}
          </Text>
        </Card>
      ) : null}

      <View style={styles.actions}>
        {analysis.reviewStatus === "not_requested" ? (
          <Button
            label={requested ? "Verification requested" : "Request expert verification"}
            icon="shield-checkmark-outline"
            disabled={requested}
            onPress={() => {
              requestVerification(analysis.id);
              setRequested(true);
            }}
          />
        ) : (
          <Badge tone="info">
            Human review: {analysis.reviewStatus.replace("_", " ")}
          </Badge>
        )}
        {onCompare ? (
          <Button label="Compare with previous" variant="secondary" icon="trending-up-outline" onPress={onCompare} />
        ) : null}
      </View>

      <Banner tone="warn" icon="alert-circle-outline" title="Not a diagnosis">
        This is an automated visual comparison, not a diagnosis. Insect damage, nutrient deficiency
        and disease can look alike. If symptoms are spreading, request an expert visit.
      </Banner>
    </View>
  );
}

export { confidenceTone };

const styles = StyleSheet.create({
  wrap: { gap: spacing.md },
  mediaRow: { flexDirection: "row", gap: spacing.md, alignItems: "center" },
  media: { width: 140 },
  mediaMeta: { flex: 1, flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  eyebrow: {
    fontSize: 10,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: colors.textSecondary,
    fontWeight: "700",
  },
  title: { fontSize: 18, lineHeight: 24, fontWeight: "800", color: colors.text },
  meta: { fontSize: 11, lineHeight: 16, color: colors.textSecondary },
  badges: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  summaryGrid: { gap: spacing.md },
  summaryCell: { gap: 3 },
  summaryLabel: { fontSize: 11, fontWeight: "700", color: colors.textSecondary },
  summaryValue: { fontSize: 14, fontWeight: "700", color: colors.text },
  capitalize: { textTransform: "capitalize" },
  sectionHead: { fontSize: 14, fontWeight: "800", color: colors.text },
  mt: { marginTop: spacing.sm },
  bullet: { flexDirection: "row", gap: spacing.sm, alignItems: "flex-start" },
  bulletDot: { fontSize: 14, color: colors.textSecondary, lineHeight: 18 },
  bulletText: { flex: 1, fontSize: 13, lineHeight: 19, color: colors.textSecondary },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  reviewHead: { flexDirection: "row", gap: spacing.sm, alignItems: "center" },
  bold: { fontWeight: "800", color: colors.text },
  actions: { gap: spacing.sm },
});
