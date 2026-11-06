"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Badge, Icon, PageHeader, StatCard, Tabs } from "@/components/workspace/ui";
import { formatDateTime, relativeTime } from "@/lib/format";
import { useWorkspace } from "@/lib/workspace/store";

type Filter = "all" | "unread" | "alert" | "reminder" | "review" | "system";

const KIND_META = {
  alert: { label: "Alert", tone: "bad" as const, icon: "alert" as const },
  reminder: { label: "Reminder", tone: "warn" as const, icon: "calendar" as const },
  review: { label: "Review", tone: "purple" as const, icon: "expert" as const },
  system: { label: "System", tone: "neutral" as const, icon: "settings" as const },
};

export default function NotificationsPage() {
  const { state, markNotificationRead, markAllNotificationsRead } = useWorkspace();
  const [filter, setFilter] = useState<Filter>("all");

  const filtered = useMemo(
    () =>
      state.notifications.filter((notification) => {
        if (filter === "all") return true;
        if (filter === "unread") return !notification.read;
        return notification.kind === filter;
      }),
    [state.notifications, filter],
  );

  const unread = state.notifications.filter((item) => !item.read).length;
  const alerts = state.notifications.filter((item) => item.kind === "alert").length;

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Notifications & alerts"
        title="Everything that needs your attention"
        lede="Alerts, inspection reminders, review requests and system messages. Each item links to the exact screen where action happens."
        actions={
          <button type="button" className="ws-button ws-button-secondary" onClick={markAllNotificationsRead} disabled={unread === 0}>
            <Icon name="check" size={16} /> Mark all as read
          </button>
        }
      />

      <div className="ws-stat-grid">
        <StatCard label="Unread" value={unread} detail="Across all channels" icon="bell" tone={unread > 0 ? "warn" : "ok"} />
        <StatCard label="Risk alerts" value={alerts} detail="Regional outlooks and verified cases" icon="alert" tone="bad" />
        <StatCard label="Review requests" value={state.notifications.filter((item) => item.kind === "review").length} detail="Expert verification workflow" icon="expert" tone="brand" />
        <StatCard label="Reminders" value={state.notifications.filter((item) => item.kind === "reminder").length} detail="Scheduled inspections" icon="calendar" />
      </div>

      <Tabs
        label="Notification filters"
        value={filter}
        onChange={setFilter}
        tabs={[
          { value: "all", label: "All", count: state.notifications.length },
          { value: "unread", label: "Unread", count: unread },
          { value: "alert", label: "Alerts" },
          { value: "reminder", label: "Reminders" },
          { value: "review", label: "Review" },
          { value: "system", label: "System" },
        ]}
      />

      <section className="ws-panel">
        <ul className="ws-notification-page-list">
          {filtered.map((notification) => {
            const meta = KIND_META[notification.kind];
            return (
              <li key={notification.id} className={notification.read ? "ws-notification-row" : "ws-notification-row ws-notification-row-unread"}>
                <span className={`ws-notification-icon ws-notif-${notification.kind}`}>
                  <Icon name={meta.icon} size={18} />
                </span>
                <div className="ws-notification-body">
                  <div className="ws-notification-top">
                    <strong>{notification.title}</strong>
                    <Badge tone={meta.tone}>{meta.label}</Badge>
                    {!notification.read ? <Badge tone="info">Unread</Badge> : null}
                  </div>
                  <p>{notification.body}</p>
                  <span className="ws-small ws-muted" title={formatDateTime(notification.at)}>
                    {relativeTime(notification.at)} · {formatDateTime(notification.at)}
                  </span>
                </div>
                <div className="ws-notification-actions">
                  <Link href={notification.href} className="ws-button ws-button-secondary" onClick={() => markNotificationRead(notification.id)}>
                    Open
                  </Link>
                  {!notification.read ? (
                    <button type="button" className="ws-link-button" onClick={() => markNotificationRead(notification.id)}>
                      Mark read
                    </button>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ul>
        {filtered.length === 0 ? <p className="ws-empty-inline">No notifications in this view.</p> : null}
      </section>

      <div className="ws-two-col">
        <section className="ws-panel">
          <div className="ws-panel-head"><h2>Alert delivery settings</h2><Link href="/settings" className="ws-link">Manage</Link></div>
          <dl className="ws-detail-list">
            <div><dt>In-app alerts</dt><dd>On</dd></div>
            <div><dt>Expert review updates</dt><dd>On</dd></div>
            <div><dt>Inspection reminders</dt><dd>24 hours before</dd></div>
            <div><dt>Regional hotspot digest</dt><dd>Daily, 07:00</dd></div>
            <div><dt>Language</dt><dd>{state.currentUser.language === "en" ? "English" : state.currentUser.language === "hi" ? "Hindi" : "Kannada"}</dd></div>
          </dl>
        </section>
        <section className="ws-panel">
          <div className="ws-panel-head"><h2>Alert safety</h2><Badge tone="info">Read me</Badge></div>
          <p className="ws-small">
            A risk alert is an area outlook, not a confirmed outbreak. A verification request is
            not a diagnosis. Open the linked screen to see the evidence, timestamp and coverage
            before making a field decision.
          </p>
          <div className="ws-notice">
            <Icon name="shield" size={17} />
            <p>Low risk does not mean the disease is absent. Unverified reports are always labelled.</p>
          </div>
        </section>
      </div>
    </div>
  );
}
