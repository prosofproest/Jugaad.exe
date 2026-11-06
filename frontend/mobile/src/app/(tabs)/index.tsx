import { useRouter } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import {
  Avatar,
  Badge,
  Banner,
  Button,
  Card,
  EmptyState,
  HealthPill,
  Icon,
  IconButton,
  PhotoTile,
  SectionTitle,
  StatCard,
  styles as ui,
} from "@/components/ui";
import { relativeTime } from "@/lib/format";
import { roleLabel } from "@/lib/workspace/labels";
import { useWorkspace } from "@/lib/workspace/store";
import { colors, radius, spacing, type Tone } from "@/theme";

export default function DashboardScreen() {
  const router = useRouter();
  const { state, role } = useWorkspace();
  const user = state.currentUser;
  const farm = state.farms[0];
  const unread = state.notifications.filter((item) => !item.read).length;
  const pending = state.analyses.filter((item) => item.reviewStatus === "pending").length;
  const queued = state.captures.filter((item) => item.syncState !== "synced").length;
  const activeInspections = state.inspections.filter(
    (item) => item.status === "scheduled" || item.status === "in_progress" || item.status === "overdue",
  );
  const attention = [...state.analyses]
    .filter((item) => item.severity === "high" || item.severity === "critical" || item.reviewStatus === "pending")
    .sort((a, b) => (b.createdAt > a.createdAt ? 1 : -1))
    .slice(0, 3);

  const quickActions: {
    label: string;
    detail: string;
    icon: Parameters<typeof Icon>[0]["name"];
    href: string;
    tone: Tone;
  }[] = [
    { label: "Scan a plant", detail: "Photo or video, GPS tagged", icon: "scan-outline", href: "/scan", tone: "brand" },
    { label: "Farm health map", detail: "Layers and plant status", icon: "map-outline", href: "/map", tone: "info" },
    { label: "Pest hotspots", detail: "Regional risk and reports", icon: "radio-outline", href: "/hotspots", tone: "warn" },
    { label: "Monitoring", detail: "Before-after recovery", icon: "trending-up-outline", href: "/monitoring", tone: "ok" },
  ];

  return (
    <View style={ui.flex}>
      <View style={styles.topBar}>
        <View style={styles.identity}>
          <Avatar initials={user.initials} size={42} />
          <View>
            <Text style={styles.greeting}>Hello, {user.name.split(" ")[0]}</Text>
            <Text style={styles.role}>
              {roleLabel(role)} · {user.village}, {user.district}
            </Text>
          </View>
        </View>
        <View style={styles.topActions}>
          <IconButton
            icon="notifications-outline"
            label="Notifications"
            badge={unread}
            onPress={() => router.push("/notifications")}
          />
          <IconButton icon="person-outline" label="Profile" onPress={() => router.push("/profile")} />
        </View>
      </View>

      <View style={styles.content}>
        <Banner tone="info" icon="information-circle-outline" title="Demo workspace">
          All records are simulated for this prototype. Automated results are assistive, not a
          diagnosis, and no chemical doses are given.
        </Banner>

        <Card tone="brand" onPress={() => (farm ? router.push(`/farm/${farm.id}`) : router.push("/farms"))}>
          <View style={styles.farmHead}>
            <View style={{ flex: 1 }}>
              <Text style={styles.eyebrow}>Primary farm</Text>
              <Text style={styles.farmName}>{farm?.name ?? "Add your first farm"}</Text>
              <Text style={styles.meta}>
                {farm ? `${farm.village}, ${farm.district} · ${farm.areaAcres} acres` : "Set up plots and crops to begin"}
              </Text>
            </View>
            <Icon name="chevron-forward" size={20} color={colors.low} />
          </View>
          <View style={styles.farmStats}>
            <View style={styles.farmStat}>
              <Text style={styles.farmStatValue}>
                {farm ? state.plots.filter((plot) => plot.farmId === farm.id).length : 0}
              </Text>
              <Text style={styles.meta}>Plots</Text>
            </View>
            <View style={styles.farmStat}>
              <Text style={styles.farmStatValue}>
                {farm ? state.cropGroups.filter((group) => group.farmId === farm.id).length : 0}
              </Text>
              <Text style={styles.meta}>Crop groups</Text>
            </View>
            <View style={styles.farmStat}>
              <Text style={styles.farmStatValue}>
                {farm ? state.plants.filter((plant) => plant.farmId === farm.id).length : 0}
              </Text>
              <Text style={styles.meta}>Plants</Text>
            </View>
          </View>
        </Card>

        <View style={styles.statRow}>
          <StatCard label="Farms" value={state.farms.length} icon="leaf-outline" tone="brand" onPress={() => router.push("/farms")} />
          <StatCard label="Pending review" value={pending} icon="shield-outline" tone={pending ? "warn" : "default"} onPress={() => router.push("/expert")} />
          <StatCard label="Offline queue" value={queued} icon="cloud-offline-outline" tone={queued ? "warn" : "default"} onPress={() => router.push("/scan")} />
        </View>

        <View style={styles.actionGrid}>
          {quickActions.map((action) => (
            <Card key={action.href} style={styles.actionCard} onPress={() => router.push(action.href)}>
              <View style={[styles.actionIcon, { backgroundColor: colors.surfaceSunken }]}>
                <Icon name={action.icon} size={20} color={colors.text} />
              </View>
              <Text style={styles.actionLabel}>{action.label}</Text>
              <Text style={styles.meta}>{action.detail}</Text>
            </Card>
          ))}
        </View>

        <SectionTitle
          title="Needs attention"
          detail="Highest priority observations and reviews"
          action={<Button label="All analysis" compact variant="ghost" onPress={() => router.push("/analysis")} />}
        />
        {attention.length === 0 ? (
          <EmptyState title="Nothing urgent" body="No high-severity observations or pending reviews right now." />
        ) : (
          attention.map((analysis) => (
            <Card key={analysis.id} onPress={() => router.push(`/analysis/${analysis.id}`)}>
              <View style={styles.analysisRow}>
                <View style={styles.analysisMedia}>
                  <PhotoTile tone={analysis.imageTone} mediaType={analysis.mediaType} label={analysis.subjectLabel} size="sm" />
                </View>
                <View style={{ flex: 1, gap: 3 }}>
                  <Text style={styles.analysisTitle}>
                    {analysis.pest ?? analysis.disease ?? "Possible nutrient issue"}
                  </Text>
                  <Text style={styles.meta}>
                    {analysis.subjectLabel} · {analysis.farmName}
                  </Text>
                  <View style={styles.badgeRow}>
                    <Badge tone={analysis.reviewStatus === "pending" ? "purple" : "warn"}>
                      {analysis.reviewStatus === "pending" ? "Pending review" : "Needs a look"}
                    </Badge>
                    <Badge tone={analysis.severity === "critical" ? "critical" : "high"}>
                      {analysis.severity}
                    </Badge>
                  </View>
                </View>
              </View>
            </Card>
          ))
        )}

        <SectionTitle
          title="Upcoming inspections"
          detail={`${activeInspections.length} active`}
          action={<Button label="Monitoring" compact variant="ghost" onPress={() => router.push("/monitoring")} />}
        />
        {activeInspections.length === 0 ? (
          <EmptyState title="No inspections scheduled" body="Schedule a scouting visit from the monitoring screen." />
        ) : (
          activeInspections.slice(0, 3).map((inspection) => (
            <Card key={inspection.id}>
              <View style={styles.inspectionRow}>
                <View style={styles.dateChip}>
                  <Text style={styles.dateDay}>{new Date(inspection.scheduledFor).getDate()}</Text>
                  <Text style={styles.dateMonth}>
                    {new Date(inspection.scheduledFor).toLocaleString("en-IN", { month: "short" })}
                  </Text>
                </View>
                <View style={{ flex: 1, gap: 2 }}>
                  <Text style={styles.analysisTitle}>{inspection.title}</Text>
                  <Text style={styles.meta}>
                    {inspection.farmName} · {inspection.crop} · {inspection.assignee}
                  </Text>
                </View>
                <Badge tone={inspection.status === "overdue" ? "bad" : "info"}>
                  {inspection.status.replace("_", " ")}
                </Badge>
              </View>
            </Card>
          ))
        )}

        <SectionTitle title="Recent activity" detail="Latest observations and notifications" />
        {state.notifications.slice(0, 4).map((notification) => (
          <Card key={notification.id} onPress={() => router.push("/notifications")}>
            <View style={styles.notificationRow}>
              <View style={styles.notificationIcon}>
                <Icon
                  name={
                    notification.kind === "alert"
                      ? "warning-outline"
                      : notification.kind === "review"
                        ? "shield-checkmark-outline"
                        : notification.kind === "reminder"
                          ? "calendar-outline"
                          : "sync-outline"
                  }
                  size={17}
                  color={colors.textSecondary}
                />
              </View>
              <View style={{ flex: 1, gap: 1 }}>
                <Text style={styles.analysisTitle}>{notification.title}</Text>
                <Text style={styles.meta}>{notification.body}</Text>
              </View>
              <Text style={styles.time}>{relativeTime(notification.at)}</Text>
            </View>
          </Card>
        ))}

        {role === "expert" || role === "agent" ? (
          <Card tone="warn" onPress={() => router.push("/expert")}>
            <View style={styles.farmHead}>
              <View style={{ flex: 1 }}>
                <Text style={styles.eyebrow}>Expert workflow</Text>
                <Text style={styles.farmName}>{pending} assessments awaiting verification</Text>
                <Text style={styles.meta}>Confirm, correct or reject automated comparisons and schedule visits.</Text>
              </View>
              <Icon name="arrow-forward" size={20} color={colors.warning} />
            </View>
          </Card>
        ) : null}

        <View style={styles.footerRow}>
          <Button label="Help & support" variant="secondary" icon="help-circle-outline" onPress={() => router.push("/help")} />
          <Button label="Settings" variant="secondary" icon="settings-outline" onPress={() => router.push("/settings")} />
        </View>
        <Text style={styles.safety}>
          Safety: confirm uncertain cases with an extension worker. Never mix or apply products
          without approved local guidance.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
    backgroundColor: colors.surfaceSunken,
  },
  identity: { flexDirection: "row", alignItems: "center", gap: spacing.sm, flex: 1 },
  greeting: { fontSize: 18, fontWeight: "800", color: colors.text },
  role: { fontSize: 11, color: colors.textSecondary },
  topActions: { flexDirection: "row", gap: 6 },
  content: { paddingHorizontal: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md },
  eyebrow: {
    fontSize: 10,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: colors.textSecondary,
    fontWeight: "700",
  },
  farmHead: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  farmName: { fontSize: 18, fontWeight: "800", color: colors.text },
  meta: { fontSize: 11, lineHeight: 16, color: colors.textSecondary },
  farmStats: {
    flexDirection: "row",
    gap: spacing.md,
    borderTopWidth: 1,
    borderTopColor: "rgba(47,111,78,0.18)",
    paddingTop: spacing.sm,
  },
  farmStat: { flex: 1, gap: 1 },
  farmStatValue: { fontSize: 20, fontWeight: "800", color: colors.text },
  statRow: { flexDirection: "row", gap: spacing.sm },
  actionGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  actionCard: { width: "48%", flexGrow: 1, gap: 4 },
  actionIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 2,
  },
  actionLabel: { fontSize: 13, fontWeight: "800", color: colors.text },
  analysisRow: { flexDirection: "row", gap: spacing.md, alignItems: "center" },
  analysisMedia: { width: 64 },
  analysisTitle: { fontSize: 13, fontWeight: "700", color: colors.text },
  badgeRow: { flexDirection: "row", flexWrap: "wrap", gap: 4, marginTop: 2 },
  inspectionRow: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  dateChip: {
    width: 44,
    height: 44,
    borderRadius: radius.control,
    backgroundColor: colors.surfaceSunken,
    alignItems: "center",
    justifyContent: "center",
  },
  dateDay: { fontSize: 17, fontWeight: "800", color: colors.text },
  dateMonth: { fontSize: 9, fontWeight: "700", color: colors.textSecondary, textTransform: "uppercase" },
  notificationRow: { flexDirection: "row", gap: spacing.sm, alignItems: "center" },
  notificationIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: colors.surfaceSunken,
    alignItems: "center",
    justifyContent: "center",
  },
  time: { fontSize: 10, color: colors.textDisabled },
  footerRow: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.sm },
  safety: { fontSize: 11, lineHeight: 16, color: colors.textSecondary, marginTop: spacing.xs },
});
