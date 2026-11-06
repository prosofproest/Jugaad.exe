import { Ionicons } from "@expo/vector-icons";
import type { ComponentProps, ReactNode } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  type StyleProp,
  type TextInputProps,
  type ViewStyle,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { healthLabel, healthTone, severityTone } from "@/lib/workspace/store";
import type { Health, RiskBand, Severity } from "@/lib/workspace/types";
import { riskLabel, severityLabel } from "@/lib/format";
import { colors, healthColor, radius, shadow, spacing, toneStyles, type Tone } from "@/theme";

export type IconName = ComponentProps<typeof Ionicons>["name"];

export function Icon({
  name,
  size = 20,
  color = colors.text,
}: {
  name: IconName;
  size?: number;
  color?: string;
}) {
  return <Ionicons name={name} size={size} color={color} />;
}

export function Screen({
  children,
  scroll = true,
  padded = true,
  footer,
  contentStyle,
}: {
  children: ReactNode;
  scroll?: boolean;
  padded?: boolean;
  footer?: ReactNode;
  contentStyle?: StyleProp<ViewStyle>;
}) {
  const body = (
    <View style={[padded ? styles.screenPad : null, contentStyle]}>{children}</View>
  );
  return (
    <SafeAreaView style={styles.safe} edges={["left", "right", "bottom"]}>
      {scroll ? (
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {body}
        </ScrollView>
      ) : (
        <View style={styles.flex}>{body}</View>
      )}
      {footer ? <View style={styles.footer}>{footer}</View> : null}
    </SafeAreaView>
  );
}

export function PageHeader({
  eyebrow,
  title,
  lede,
  right,
  onBack,
}: {
  eyebrow?: string;
  title: string;
  lede?: string;
  right?: ReactNode;
  onBack?: () => void;
}) {
  return (
    <View style={styles.pageHeader}>
      <View style={styles.pageHeaderRow}>
        {onBack ? (
          <Pressable
            onPress={onBack}
            accessibilityRole="button"
            accessibilityLabel="Go back"
            style={styles.backButton}
          >
            <Icon name="chevron-back" size={22} />
          </Pressable>
        ) : null}
        <View style={styles.flex}>
          {eyebrow ? <Text style={styles.eyebrow}>{eyebrow}</Text> : null}
          <Text style={styles.h1}>{title}</Text>
          {lede ? <Text style={styles.lede}>{lede}</Text> : null}
        </View>
        {right ? <View style={styles.pageHeaderRight}>{right}</View> : null}
      </View>
    </View>
  );
}

export function SectionTitle({
  title,
  detail,
  action,
}: {
  title: string;
  detail?: string;
  action?: ReactNode;
}) {
  return (
    <View style={styles.sectionTitle}>
      <View style={styles.flex}>
        <Text style={styles.h2}>{title}</Text>
        {detail ? <Text style={styles.small}>{detail}</Text> : null}
      </View>
      {action}
    </View>
  );
}

export function Card({
  children,
  style,
  onPress,
  tone,
}: {
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
  onPress?: () => void;
  tone?: "default" | "brand" | "warn" | "bad";
}) {
  const filled =
    tone === "brand"
      ? { backgroundColor: "#f2fbe9" }
      : tone === "warn"
        ? { backgroundColor: "#fff9ea" }
        : tone === "bad"
          ? { backgroundColor: "#fff3f1" }
          : null;
  const content = <View style={[styles.card, filled, style]}>{children}</View>;
  if (!onPress) return content;
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => (pressed ? styles.pressed : undefined)}
    >
      {content}
    </Pressable>
  );
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: Tone }) {
  const t = toneStyles[tone] ?? toneStyles.neutral;
  return (
    <View style={[styles.badge, { backgroundColor: t.bg }]}>
      <Text style={[styles.badgeText, { color: t.fg }]}>{children}</Text>
    </View>
  );
}

export function HealthPill({ health }: { health: Health }) {
  return <Badge tone={healthTone(health) as Tone}>{healthLabel(health)}</Badge>;
}

export function SeverityPill({ severity }: { severity: Severity }) {
  return <Badge tone={severityTone(severity) as Tone}>{severityLabel(severity)}</Badge>;
}

export function RiskPill({ band }: { band: RiskBand }) {
  const tone = band === "insufficient" ? "neutral" : band;
  return <Badge tone={tone as Tone}>{riskLabel(band)}</Badge>;
}

export function StatCard({
  label,
  value,
  detail,
  icon,
  tone = "default",
  onPress,
}: {
  label: string;
  value: string | number;
  detail?: string;
  icon?: IconName;
  tone?: "default" | "ok" | "warn" | "bad" | "brand";
  onPress?: () => void;
}) {
  const accent: Record<string, string> = {
    default: colors.text,
    ok: colors.success,
    warn: colors.warning,
    bad: colors.error,
    brand: colors.low,
  };
  return (
    <Card onPress={onPress} style={styles.stat}>
      <View style={styles.statTop}>
        <Text style={styles.statLabel}>{label}</Text>
        {icon ? <Icon name={icon} size={17} color={accent[tone]} /> : null}
      </View>
      <Text style={[styles.statValue, { color: accent[tone] }]}>{value}</Text>
      {detail ? <Text style={styles.statDetail}>{detail}</Text> : null}
    </Card>
  );
}

export function ProgressBar({
  value,
  label,
  tone = "brand",
}: {
  value: number;
  label?: string;
  tone?: "brand" | "ok" | "warn" | "bad";
}) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  const fill: Record<string, string> = {
    brand: colors.brandHover,
    ok: colors.success,
    warn: colors.warning,
    bad: colors.error,
  };
  return (
    <View style={styles.progressWrap}>
      {label ? (
        <View style={styles.progressLabel}>
          <Text style={styles.small}>{label}</Text>
          <Text style={styles.smallStrong}>{clamped}%</Text>
        </View>
      ) : null}
      <View
        style={styles.progressTrack}
        accessibilityRole="progressbar"
        accessibilityValue={{ min: 0, max: 100, now: clamped }}
        accessibilityLabel={label ?? "Progress"}
      >
        <View style={[styles.progressFill, { width: `${clamped}%`, backgroundColor: fill[tone] }]} />
      </View>
    </View>
  );
}

const toneSwatches = ["#dfe4da", "#cfe4c2", "#f3e3bd", "#e9c7bf", "#c9d8ec", "#d9cff0", "#c6e4d8", "#ead7bf"];

export function PhotoTile({
  tone,
  label,
  mediaType = "image",
  size = "md",
}: {
  tone: number;
  label: string;
  mediaType?: "image" | "video";
  size?: "sm" | "md" | "lg";
}) {
  const bg = toneSwatches[Math.abs(tone) % toneSwatches.length];
  const height = size === "sm" ? 56 : size === "lg" ? 180 : 110;
  return (
    <View
      style={[styles.photo, { backgroundColor: bg, height }]}
      accessibilityRole="image"
      accessibilityLabel={label}
    >
      <Icon name="leaf" size={size === "sm" ? 22 : size === "lg" ? 54 : 34} color="#2f6f4e" />
      {mediaType === "video" ? (
        <View style={styles.photoPlay}>
          <Icon name="videocam" size={13} color={colors.textInverse} />
          <Text style={styles.photoPlayText}>Video</Text>
        </View>
      ) : null}
    </View>
  );
}

export function Button({
  label,
  onPress,
  variant = "primary",
  icon,
  disabled,
  loading,
  style,
  compact,
}: {
  label: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  icon?: IconName;
  disabled?: boolean;
  loading?: boolean;
  style?: StyleProp<ViewStyle>;
  compact?: boolean;
}) {
  const variantStyle =
    variant === "primary"
      ? { backgroundColor: colors.brand, borderColor: colors.brand }
      : variant === "secondary"
        ? { backgroundColor: colors.surface, borderColor: colors.borderStrong }
        : variant === "danger"
          ? { backgroundColor: "#fff3f1", borderColor: "#e9c7bf" }
          : { backgroundColor: "transparent", borderColor: "transparent" };
  const fg =
    variant === "primary"
      ? colors.onBrand
      : variant === "danger"
        ? colors.error
        : variant === "ghost"
          ? colors.info
          : colors.text;
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: Boolean(disabled || loading) }}
      style={({ pressed }) => [
        styles.button,
        compact && styles.buttonCompact,
        variantStyle,
        (disabled || loading) && styles.buttonDisabled,
        pressed && styles.pressed,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator size="small" color={fg} />
      ) : icon ? (
        <Icon name={icon} size={17} color={fg} />
      ) : null}
      <Text style={[styles.buttonText, compact && styles.buttonTextCompact, { color: fg }]}>
        {label}
      </Text>
    </Pressable>
  );
}

export function IconButton({
  icon,
  onPress,
  label,
  badge,
}: {
  icon: IconName;
  onPress: () => void;
  label: string;
  badge?: number;
}) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={label}
      style={({ pressed }) => [styles.iconButton, pressed && styles.pressed]}
    >
      <Icon name={icon} size={20} />
      {badge ? (
        <View style={styles.iconBadge}>
          <Text style={styles.iconBadgeText}>{badge > 9 ? "9+" : badge}</Text>
        </View>
      ) : null}
    </Pressable>
  );
}

export function Field({
  label,
  hint,
  multiline,
  ...props
}: TextInputProps & { label: string; hint?: string; multiline?: boolean }) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        placeholderTextColor={colors.textDisabled}
        style={[styles.input, multiline && styles.inputMultiline]}
        multiline={multiline}
        {...props}
      />
      {hint ? <Text style={styles.fieldHint}>{hint}</Text> : null}
    </View>
  );
}

export function Chip({
  label,
  selected,
  onPress,
}: {
  label: string;
  selected?: boolean;
  onPress?: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: Boolean(selected) }}
      style={({ pressed }) => [styles.chip, selected && styles.chipSelected, pressed && styles.pressed]}
    >
      <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{label}</Text>
    </Pressable>
  );
}

export function Segmented<T extends string>({
  value,
  onChange,
  options,
  label,
}: {
  value: T;
  onChange: (value: T) => void;
  options: { value: T; label: string }[];
  label: string;
}) {
  return (
    <View style={styles.segmented} accessibilityRole="radiogroup" accessibilityLabel={label}>
      {options.map((option) => {
        const active = value === option.value;
        return (
          <Pressable
            key={option.value}
            onPress={() => onChange(option.value)}
            accessibilityRole="radio"
            accessibilityState={{ checked: active }}
            style={[styles.segment, active && styles.segmentActive]}
          >
            <Text style={[styles.segmentText, active && styles.segmentTextActive]}>{option.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export function EmptyState({
  title,
  body,
  icon = "leaf-outline",
  action,
}: {
  title: string;
  body: string;
  icon?: IconName;
  action?: ReactNode;
}) {
  return (
    <View style={styles.empty}>
      <View style={styles.emptyIcon}>
        <Icon name={icon} size={26} color={colors.low} />
      </View>
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={styles.emptyBody}>{body}</Text>
      {action ? <View style={styles.emptyAction}>{action}</View> : null}
    </View>
  );
}

export function Banner({
  tone = "info",
  title,
  children,
  icon = "information-circle-outline",
}: {
  tone?: "info" | "warn" | "bad" | "ok" | "brand";
  title?: string;
  children: ReactNode;
  icon?: IconName;
}) {
  const t = toneStyles[tone];
  return (
    <View style={[styles.banner, { backgroundColor: t.bg }]}>
      <Icon name={icon} size={18} color={t.fg} />
      <View style={styles.flex}>
        {title ? <Text style={[styles.bannerTitle, { color: t.fg }]}>{title}</Text> : null}
        <Text style={[styles.bannerText, { color: t.fg }]}>{children}</Text>
      </View>
    </View>
  );
}

export function ListRow({
  title,
  subtitle,
  right,
  icon,
  onPress,
  tone,
}: {
  title: string;
  subtitle?: string;
  right?: ReactNode;
  icon?: IconName;
  onPress?: () => void;
  tone?: Tone;
}) {
  const t = tone ? toneStyles[tone] : null;
  const content = (
    <View style={styles.listRow}>
      {icon ? (
        <View style={[styles.listIcon, t ? { backgroundColor: t.bg } : null]}>
          <Icon name={icon} size={18} color={t ? t.fg : colors.textSecondary} />
        </View>
      ) : null}
      <View style={styles.flex}>
        <Text style={styles.listTitle}>{title}</Text>
        {subtitle ? <Text style={styles.small}>{subtitle}</Text> : null}
      </View>
      {right ?? (onPress ? <Icon name="chevron-forward" size={18} color={colors.textDisabled} /> : null)}
    </View>
  );
  if (!onPress) return content;
  return (
    <Pressable onPress={onPress} accessibilityRole="button" style={({ pressed }) => (pressed ? styles.pressed : null)}>
      {content}
    </Pressable>
  );
}

export function Divider() {
  return <View style={styles.divider} />;
}

export function KeyValue({ label, value }: { label: string; value: ReactNode }) {
  return (
    <View style={styles.keyValue}>
      <Text style={styles.small}>{label}</Text>
      <Text style={styles.keyValueText}>{value}</Text>
    </View>
  );
}

export function Avatar({ initials, size = 44 }: { initials: string; size?: number }) {
  return (
    <View
      style={[
        styles.avatar,
        { width: size, height: size, borderRadius: size / 2 },
      ]}
    >
      <Text style={[styles.avatarText, { fontSize: size * 0.36 }]}>{initials}</Text>
    </View>
  );
}

export function HealthDot({ health, size = 10 }: { health: Health; size?: number }) {
  return (
    <View
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
        backgroundColor: healthColor(health),
        borderWidth: 1,
        borderColor: "rgba(0,0,0,0.12)",
      }}
    />
  );
}

export const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.surfaceSunken },
  flex: { flex: 1 },
  scrollContent: { flexGrow: 1 },
  screenPad: { padding: spacing.lg, gap: spacing.md },
  footer: {
    padding: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.surface,
  },
  pageHeader: { marginBottom: spacing.xs },
  pageHeaderRow: { flexDirection: "row", alignItems: "flex-start", gap: spacing.sm },
  pageHeaderRight: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  eyebrow: {
    fontSize: 11,
    letterSpacing: 1,
    textTransform: "uppercase",
    fontWeight: "700",
    color: colors.textSecondary,
  },
  h1: { fontSize: 26, lineHeight: 32, fontWeight: "700", color: colors.text, marginTop: 2 },
  h2: { fontSize: 18, lineHeight: 24, fontWeight: "700", color: colors.text },
  h3: { fontSize: 15, fontWeight: "700", color: colors.text },
  lede: { fontSize: 14, lineHeight: 20, color: colors.textSecondary, marginTop: spacing.xs },
  small: { fontSize: 12, lineHeight: 17, color: colors.textSecondary },
  smallStrong: { fontSize: 12, fontWeight: "700", color: colors.textSecondary },
  sectionTitle: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    gap: spacing.sm,
    ...shadow,
  },
  pressed: { opacity: 0.75 },
  badge: {
    alignSelf: "flex-start",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: radius.chip,
  },
  badgeText: { fontSize: 11, fontWeight: "700" },
  stat: { flex: 1, minWidth: 120 },
  statTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  statLabel: { fontSize: 12, color: colors.textSecondary, fontWeight: "600" },
  statValue: { fontSize: 26, fontWeight: "800" },
  statDetail: { fontSize: 11, color: colors.textSecondary },
  progressWrap: { gap: spacing.xs },
  progressLabel: { flexDirection: "row", justifyContent: "space-between" },
  progressTrack: {
    height: 8,
    borderRadius: 999,
    backgroundColor: colors.surfaceSunken,
    overflow: "hidden",
  },
  progressFill: { height: "100%", borderRadius: 999 },
  photo: {
    borderRadius: radius.card,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
    borderWidth: 1,
    borderColor: colors.border,
  },
  photoPlay: {
    position: "absolute",
    bottom: 6,
    left: 6,
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "rgba(14,15,12,0.78)",
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 999,
  },
  photoPlayText: { color: colors.textInverse, fontSize: 10, fontWeight: "700" },
  button: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    borderWidth: 1,
    borderRadius: radius.control,
    paddingVertical: 11,
    paddingHorizontal: spacing.md,
    minHeight: 44,
  },
  buttonCompact: { paddingVertical: 6, paddingHorizontal: 10, minHeight: 34 },
  buttonDisabled: { opacity: 0.5 },
  buttonText: { fontSize: 14, fontWeight: "700" },
  buttonTextCompact: { fontSize: 12 },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  iconBadge: {
    position: "absolute",
    top: -3,
    right: -3,
    minWidth: 17,
    height: 17,
    borderRadius: 9,
    backgroundColor: colors.error,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 3,
  },
  iconBadgeText: { color: "#fff", fontSize: 9, fontWeight: "800" },
  field: { gap: 5 },
  fieldLabel: { fontSize: 12, fontWeight: "700", color: colors.textSecondary },
  input: {
    borderWidth: 1,
    borderColor: colors.borderStrong,
    borderRadius: radius.control,
    paddingHorizontal: spacing.md,
    paddingVertical: 10,
    backgroundColor: colors.surface,
    color: colors.text,
    fontSize: 14,
    minHeight: 44,
  },
  inputMultiline: { minHeight: 88, textAlignVertical: "top" },
  fieldHint: { fontSize: 11, color: colors.textDisabled },
  chip: {
    borderWidth: 1,
    borderColor: colors.borderStrong,
    borderRadius: radius.chip,
    paddingHorizontal: 11,
    paddingVertical: 6,
    backgroundColor: colors.surface,
  },
  chipSelected: { backgroundColor: colors.brand, borderColor: colors.brand },
  chipText: { fontSize: 12, color: colors.textSecondary, fontWeight: "600" },
  chipTextSelected: { color: colors.onBrand, fontWeight: "800" },
  segmented: {
    flexDirection: "row",
    backgroundColor: colors.surfaceSunken,
    borderRadius: radius.control,
    padding: 3,
    gap: 2,
  },
  segment: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 7,
    borderRadius: radius.control - 2,
  },
  segmentActive: { backgroundColor: colors.surface, ...shadow },
  segmentText: { fontSize: 12, fontWeight: "600", color: colors.textSecondary },
  segmentTextActive: { color: colors.text, fontWeight: "800" },
  empty: {
    alignItems: "center",
    padding: spacing.xl,
    gap: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderStyle: "dashed",
  },
  emptyIcon: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.brandSoft,
  },
  emptyTitle: { fontSize: 16, fontWeight: "700", color: colors.text, textAlign: "center" },
  emptyBody: { fontSize: 13, color: colors.textSecondary, textAlign: "center", lineHeight: 19 },
  emptyAction: { marginTop: spacing.xs },
  banner: {
    flexDirection: "row",
    gap: spacing.sm,
    padding: spacing.md,
    borderRadius: radius.card,
    alignItems: "flex-start",
  },
  bannerTitle: { fontSize: 13, fontWeight: "800", marginBottom: 2 },
  bannerText: { fontSize: 12, lineHeight: 18 },
  listRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    paddingVertical: spacing.sm,
  },
  listIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.surfaceSunken,
  },
  listTitle: { fontSize: 14, fontWeight: "600", color: colors.text },
  divider: { height: 1, backgroundColor: colors.border, marginVertical: spacing.xs },
  keyValue: { gap: 1 },
  keyValueText: { fontSize: 14, fontWeight: "700", color: colors.text },
  avatar: {
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.brand,
  },
  avatarText: { fontWeight: "800", color: colors.onBrand },
});
