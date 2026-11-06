import type { Inspection, ReviewStatus, Role, Severity, SyncState } from "./types";
import type { Tone } from "@/theme";

export function roleLabel(role: Role): string {
  switch (role) {
    case "farmer":
      return "Farmer";
    case "expert":
      return "Expert";
    case "agent":
      return "Field agent";
    case "admin":
      return "Administrator";
  }
}

export function reviewStatusLabel(status: ReviewStatus): string {
  switch (status) {
    case "not_requested":
      return "Not reviewed";
    case "pending":
      return "Pending review";
    case "verified":
      return "Verified";
    case "corrected":
      return "Corrected";
    case "rejected":
      return "Rejected";
  }
}

export function reviewStatusTone(status: ReviewStatus): Tone {
  switch (status) {
    case "pending":
      return "purple";
    case "verified":
      return "ok";
    case "corrected":
      return "info";
    case "rejected":
      return "bad";
    default:
      return "neutral";
  }
}

export function syncTone(sync: SyncState): Tone {
  switch (sync) {
    case "queued":
      return "warn";
    case "syncing":
      return "info";
    case "synced":
      return "ok";
    case "failed":
      return "bad";
  }
}

export function inspectionTone(status: Inspection["status"]): Tone {
  switch (status) {
    case "scheduled":
      return "info";
    case "in_progress":
      return "warn";
    case "completed":
      return "ok";
    case "overdue":
      return "bad";
  }
}

export function inspectionLabel(status: Inspection["status"]): string {
  switch (status) {
    case "scheduled":
      return "Scheduled";
    case "in_progress":
      return "In progress";
    case "completed":
      return "Completed";
    case "overdue":
      return "Overdue";
  }
}

export function severityRank(severity: Severity): number {
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
