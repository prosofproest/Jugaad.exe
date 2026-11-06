/**
 * Mobile design tokens. Mirrors frontend/app/globals.css and design/tokens.json.
 * Risk and status remain separate namespaces; colour is always paired with a label.
 */

export const colors = {
  surface: "#ffffff",
  surfaceRaised: "#ffffff",
  surfaceSunken: "#e8ebe6",
  surfaceOverlay: "#0e0f0c",

  text: "#0e0f0c",
  textSecondary: "#454745",
  textDisabled: "#868685",
  textInverse: "#ffffff",

  border: "#dfe4da",
  borderStrong: "#b9c1b3",
  focus: "#0b5fff",

  brand: "#9fe870",
  brandHover: "#8bd85c",
  onBrand: "#0e0f0c",
  brandSoft: "#e2f8d2",

  low: "#2f6f4e",
  moderate: "#9a6700",
  high: "#c2410c",
  urgent: "#b42318",
  insufficient: "#5f6b7a",

  success: "#067647",
  warning: "#9a6700",
  error: "#b42318",
  info: "#175cd3",
  purple: "#7c3aed",
  alert: "#c2410c",
  neutral: "#5f6b7a",

  healthy: "#9fe870",
  watch: "#f5c542",
  pest: "#e88b3a",
  diseased: "#cf5b4a",
  recovering: "#7fb3e8",
  idle: "#d7dcd2",
} as const;

export type Tone =
  | "neutral"
  | "ok"
  | "warn"
  | "bad"
  | "alert"
  | "info"
  | "purple"
  | "brand"
  | "low"
  | "moderate"
  | "high"
  | "critical"
  | "urgent";

export const toneStyles: Record<Tone, { bg: string; fg: string }> = {
  neutral: { bg: "#eef0ec", fg: "#454745" },
  ok: { bg: "#e6f4ea", fg: "#067647" },
  warn: { bg: "#fdf3d7", fg: "#9a6700" },
  bad: { bg: "#fde8e4", fg: "#b42318" },
  alert: { bg: "#fde8e4", fg: "#c2410c" },
  info: { bg: "#e5efff", fg: "#175cd3" },
  purple: { bg: "#f1e9fe", fg: "#7c3aed" },
  brand: { bg: "#e2f8d2", fg: "#2f6f4e" },
  low: { bg: "#e6f4ea", fg: "#2f6f4e" },
  moderate: { bg: "#fdf3d7", fg: "#9a6700" },
  high: { bg: "#fde8e4", fg: "#c2410c" },
  critical: { bg: "#fbe4e2", fg: "#b42318" },
  urgent: { bg: "#fbe4e2", fg: "#b42318" },
};

export function healthColor(health: string): string {
  switch (health) {
    case "healthy":
      return colors.healthy;
    case "watch":
      return colors.watch;
    case "pest":
      return colors.pest;
    case "diseased":
      return colors.diseased;
    case "recovering":
      return colors.recovering;
    default:
      return colors.idle;
  }
}

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radius = {
  control: 10,
  card: 14,
  chip: 999,
} as const;

export const shadow = {
  shadowColor: "#0e0f0c",
  shadowOpacity: 0.06,
  shadowRadius: 10,
  shadowOffset: { width: 0, height: 3 },
  elevation: 2,
} as const;
