"use client";

import { useEffect, useState } from "react";

import {
  Badge,
  PageHeader,
} from "@/components/workspace/ui";
import {
  listNotificationPreferences,
  updateNotificationPreference,
  type NotificationPreference,
} from "@/lib/api";
import { useWorkspace } from "@/lib/workspace/store";
import type { Language } from "@/lib/workspace/types";
import { readSession } from "@/lib/auth";

const LANGUAGES: { value: Language; label: string }[] = [
  { value: "en", label: "English" },
  { value: "hi", label: "हिन्दी (Hindi)" },
  { value: "kn", label: "ಕನ್ನಡ (Kannada)" },
];

export default function SettingsPage() {
  const session = readSession();
  const { state, setLanguage } = useWorkspace();
  const [preferences, setPreferences] = useState<NotificationPreference[]>([]);
  const [loading, setLoading] = useState(Boolean(session));
  const [savedMessage, setSavedMessage] = useState("");

  useEffect(() => {
    if (!session) return;
    let ignore = false;
    listNotificationPreferences()
      .then((res) => {
        if (!ignore) {
          setPreferences(res.preferences || []);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!ignore) {
          setLoading(false);
        }
      });
    return () => {
      ignore = true;
    };
  }, [session]);

  async function handleToggleChannel(channel: string, currentlyEnabled: boolean) {
    try {
      const updated = await updateNotificationPreference({
        channel,
        enabled: !currentlyEnabled,
      });
      setPreferences((prev) =>
        prev.map((p) => (p.channel === channel ? updated : p)),
      );
      setSavedMessage(`Updated ${channel} preferences`);
      setTimeout(() => setSavedMessage(""), 2000);
    } catch {
      setSavedMessage("Failed to update preference");
    }
  }

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Preferences & configuration"
        title="Settings"
        lede="Configure interface language and notification delivery channels for outbreak alerts."
      />

      <div className="ws-two-col">
        <section className="ws-panel">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Localisation</p>
              <h2>Interface language</h2>
            </div>
            <Badge tone="ok">Active</Badge>
          </div>
          <p className="ws-muted ws-small">
            Select the interface language. Translations are stored locally and apply across all pages.
          </p>

          <div className="ws-chip-row" style={{ marginTop: "1rem" }}>
            {LANGUAGES.map((lang) => (
              <button
                key={lang.value}
                type="button"
                className={state.currentUser.language === lang.value ? "ws-button ws-button-primary" : "ws-button ws-button-secondary"}
                onClick={() => setLanguage(lang.value)}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </section>

        <section className="ws-panel">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Alert subscriptions</p>
              <h2>Delivery channels</h2>
            </div>
            {session ? <Badge tone="ok">Connected</Badge> : <Badge tone="neutral">Sign in required</Badge>}
          </div>

          {session ? (
            <div>
              <p className="ws-muted ws-small">
                Alerts are triggered when predicted risk exceeds policy thresholds in your assigned area.
              </p>

              {loading ? (
                <p className="ws-muted ws-small">Loading preferences...</p>
              ) : (
                <div className="ws-risk-list" style={{ marginTop: "1rem" }}>
                  {["in_app", "sms", "whatsapp"].map((channel) => {
                    const pref = preferences.find((p) => p.channel === channel);
                    const isEnabled = pref ? pref.enabled : channel === "in_app";
                    return (
                      <div key={channel} className="ws-risk-row">
                        <div>
                          <strong>{channel.replace("_", "-").toUpperCase()}</strong>
                          <span className="ws-small ws-muted" style={{ display: "block" }}>
                            {channel === "in_app" ? "In-app feed notifications" : `${channel.toUpperCase()} dispatch gateway`}
                          </span>
                        </div>
                        <button
                          type="button"
                          className={isEnabled ? "ws-button ws-button-primary" : "ws-button ws-button-secondary"}
                          onClick={() => void handleToggleChannel(channel, isEnabled)}
                        >
                          {isEnabled ? "Enabled" : "Disabled"}
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}

              {savedMessage && <p className="ws-small ws-muted" style={{ marginTop: "0.5rem" }}>{savedMessage}</p>}
            </div>
          ) : (
            <p className="ws-muted ws-small">Sign in to manage server-side alert delivery preferences.</p>
          )}
        </section>
      </div>

      <section className="ws-panel" style={{ marginTop: "1.5rem" }}>
        <div className="ws-panel-head">
          <div>
            <p className="ws-eyebrow">Privacy & data security</p>
            <h3>Clinical data guarantees</h3>
          </div>
        </div>
        <p className="ws-muted ws-small">
          CropSentinel does not store user data or observations in local storage. All records are persisted in PostgreSQL with strict access control and immutable audit trails.
        </p>
      </section>
    </div>
  );
}
