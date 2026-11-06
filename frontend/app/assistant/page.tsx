"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import {
  Badge,
  Icon,
  PageHeader,
} from "@/components/workspace/ui";
import { formatDateTime } from "@/lib/format";
import {
  createConversation,
  listConversations,
  listMessages,
  sendMessage,
  type Conversation,
  type Message,
} from "@/lib/api";

const TOPIC_PROMPTS = [
  { icon: "alert" as const, label: "Why is this happening?", prompt: "Why are these symptoms appearing now?" },
  { icon: "shield" as const, label: "How do I manage it?", prompt: "What safe IPM management options are available?" },
  { icon: "leaf" as const, label: "Biological control", prompt: "What biological control options are available?" },
  { icon: "water" as const, label: "Preventive measures", prompt: "What preventive cultural measures should I take?" },
  { icon: "plant" as const, label: "Crop guidance", prompt: "Give me safe non-chemical management guidance for tomato." },
];

function AssistantContent() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let ignore = false;
    listConversations()
      .then((convs) => {
        if (!ignore) {
          setConversations(convs);
          if (convs.length > 0) {
            setSelectedId((current) => current || convs[0]?.conversation_id || null);
          }
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load conversations");
          setLoading(false);
        }
      });
    return () => {
      ignore = true;
    };
  }, []);

  const activeId = selectedId || conversations[0]?.conversation_id || null;

  useEffect(() => {
    if (!activeId) return;
    let ignore = false;
    listMessages(activeId)
      .then((msgs) => {
        if (!ignore) setMessages(msgs);
      })
      .catch(() => {
        if (!ignore) setMessages([]);
      });
    return () => {
      ignore = true;
    };
  }, [activeId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length]);

  async function handleStartNew() {
    try {
      const created = await createConversation(`Triage session ${conversations.length + 1}`);
      setConversations((prev) => [created, ...prev]);
      setSelectedId(created.conversation_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create conversation");
    }
  }

  async function handleSend(promptText?: string) {
    const toSend = (promptText || text).trim();
    if (!toSend || sending) return;

    let targetConvId = activeId;
    if (!targetConvId) {
      try {
        const created = await createConversation("Triage session");
        setConversations([created]);
        targetConvId = created.conversation_id;
        setSelectedId(targetConvId);
      } catch {
        return;
      }
    }

    setSending(true);
    setError(null);
    try {
      const clientMessageId = crypto.randomUUID();
      const result = await sendMessage(targetConvId, {
        clientMessageId,
        text: toSend,
      });
      setMessages((prev) => [...prev, result.user_message, result.assistant_message]);
      setText("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Conversational triage"
        title="Pest & Plant Health Assistant"
        lede="Engage with the decision-support assistant backed by the real conversation engine. All advice adheres to Safety Rule R5: zero chemical or synthetic pesticide prescriptions."
        actions={
          <button type="button" className="ws-button ws-button-primary" onClick={() => void handleStartNew()}>
            <Icon name="plus" size={17} /> New conversation
          </button>
        }
      />

      <div className="ws-two-col ws-assistant-layout">
        <aside className="ws-panel ws-thread-list">
          <div className="ws-panel-head">
            <h3>Conversations</h3>
            <Badge tone="neutral">{conversations.length}</Badge>
          </div>
          {loading ? (
            <p className="ws-muted ws-small">Loading conversations...</p>
          ) : conversations.length === 0 ? (
            <p className="ws-muted ws-small">No conversations yet. Start a new one below.</p>
          ) : (
            <div className="ws-thread-scroll">
              {conversations.map((c) => (
                <button
                  key={c.conversation_id}
                  type="button"
                  className={c.conversation_id === activeId ? "ws-thread-card ws-thread-card-active" : "ws-thread-card"}
                  onClick={() => setSelectedId(c.conversation_id)}
                >
                  <strong>{c.title}</strong>
                  <span className="ws-small ws-muted">{formatDateTime(c.last_message_at || c.created_at)}</span>
                </button>
              ))}
            </div>
          )}
        </aside>

        <section className="ws-panel ws-chat-pane">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Interactive dialogue</p>
              <h2>{conversations.find((c) => c.conversation_id === activeId)?.title || "Assistant"}</h2>
            </div>
            <Link href="/chat" className="ws-link ws-small">
              Open photo chat view
            </Link>
          </div>

          <div className="ws-chip-row" style={{ marginBottom: "1rem" }}>
            {TOPIC_PROMPTS.map((item) => (
              <button
                key={item.label}
                type="button"
                className="ws-chip"
                onClick={() => void handleSend(item.prompt)}
                disabled={sending}
              >
                <Icon name={item.icon} size={14} /> {item.label}
              </button>
            ))}
          </div>

          {error && (
            <div className="ws-notice ws-notice-bad" style={{ marginBottom: "1rem" }}>
              <strong>Error:</strong> {error}
            </div>
          )}

          <div className="ws-chat-messages" style={{ minHeight: "300px", maxHeight: "500px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "1rem" }}>
            {messages.length === 0 ? (
              <p className="ws-muted ws-small">No messages in this conversation. Ask a question or pick a prompt above.</p>
            ) : (
              messages.map((msg) => {
                const isUser = msg.role === "user";
                return (
                  <div
                    key={msg.message_id}
                    style={{
                      alignSelf: isUser ? "flex-end" : "flex-start",
                      maxWidth: "80%",
                      padding: "0.75rem 1rem",
                      borderRadius: "0.75rem",
                      background: isUser ? "var(--brand-primary, #9fe870)" : "var(--ws-bg, #f4f6f1)",
                      color: "var(--ws-ink, #14210f)",
                    }}
                  >
                    <p style={{ margin: 0, fontSize: "0.95rem" }}>{msg.text}</p>
                    <span className="ws-small ws-muted" style={{ display: "block", marginTop: "0.25rem", fontSize: "0.75rem" }}>
                      {formatDateTime(msg.created_at)}
                    </span>
                  </div>
                );
              })
            )}
            <div ref={endRef} />
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              void handleSend();
            }}
            style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}
          >
            <input
              type="text"
              className="ws-input"
              placeholder="Ask about visible symptoms, crop protection or IPM..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={sending}
              style={{ flex: 1 }}
            />
            <button type="submit" className="ws-button ws-button-primary" disabled={sending || !text.trim()}>
              {sending ? "Sending..." : "Send"}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}

export default function AssistantPage() {
  return (
    <AuthGate>
      <AssistantContent />
    </AuthGate>
  );
}
