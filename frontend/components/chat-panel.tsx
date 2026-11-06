"use client";

import { useRef, useState } from "react";

import {
  ApiError,
  createConversation,
  sendMessage,
  type Message,
} from "@/lib/api";

interface Pending {
  clientMessageId: string;
  text: string;
}

export function ChatPanel() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  async function submit(payload: Pending) {
    setSending(true);
    setError(null);
    try {
      const activeId = conversationId ?? (await createConversation()).conversation_id;
      setConversationId(activeId);

      const result = await sendMessage(activeId, {
        clientMessageId: payload.clientMessageId,
        text: payload.text,
      });

      setMessages((current) => [...current, result.user_message, result.assistant_message]);
      setPending(null);
      setDraft("");
      listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
    } catch (caught) {
      // Retry reuses the same clientMessageId, so the API returns the original
      // result instead of creating a duplicate message.
      setPending(payload);
      setError(
        caught instanceof ApiError
          ? `${caught.status} ${caught.problem?.code ?? "request_failed"} — ${
              caught.problem?.detail ?? caught.problem?.title ?? "request failed"
            }`
          : "Network unavailable. The message is still here; retry when connected.",
      );
    } finally {
      setSending(false);
    }
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || sending) {
      return;
    }
    await submit({ clientMessageId: crypto.randomUUID(), text });
  }

  return (
    <section className="card" aria-labelledby="chat-heading">
      <h2 id="chat-heading">Photo-assessment chat</h2>
      <p className="muted">
        <span className="badge badge-muted">demo</span> Template replies only. No
        image model is connected in this phase; nothing here is a diagnosis.
      </p>

      <div
        ref={listRef}
        aria-live="polite"
        aria-label="Conversation"
        style={{ maxHeight: "22rem", overflowY: "auto", marginBottom: "1rem" }}
      >
        {messages.length === 0 ? (
          <p className="muted">
            No messages yet. Describe what you see on the plant. Image upload
            arrives with the media pipeline.
          </p>
        ) : (
          messages.map((message) => <Bubble key={message.message_id} message={message} />)
        )}
      </div>

      {error ? (
        <div className="error" role="alert">
          <p>{error}</p>
          {pending ? (
            <button type="button" disabled={sending} onClick={() => void submit(pending)}>
              Retry
            </button>
          ) : null}
        </div>
      ) : null}

      <form onSubmit={onSubmit}>
        <label htmlFor="message-text">Message</label>
        <textarea
          id="message-text"
          name="message"
          rows={3}
          maxLength={1000}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Example: yellowing between the veins on lower leaves"
        />
        <p>
          <button type="submit" disabled={sending || draft.trim().length === 0}>
            {sending ? "Sending…" : "Send"}
          </button>
        </p>
      </form>
    </section>
  );
}

function Bubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <article className="message">
      <p>
        <strong>{isUser ? "You" : "Assistant"}</strong>{" "}
        <span className="muted">{new Date(message.created_at).toLocaleTimeString()}</span>
        {message.is_demo ? (
          <>
            {" "}
            <span className="badge badge-muted">demo</span>
          </>
        ) : null}
      </p>
      <p>{message.text}</p>
      {message.assessment ? (
        <p className="muted">
          State: <strong>{message.assessment.state}</strong>
          {message.assessment.reason_text ? ` — ${message.assessment.reason_text}` : null}
          <br />
          Model version: {message.assessment.model_version} · Calibrated:{" "}
          {message.assessment.calibrated ? "yes" : "no"}
        </p>
      ) : null}
      {message.next_steps.length > 0 ? (
        <p className="muted">Next steps: {message.next_steps.join(", ")}</p>
      ) : null}
    </article>
  );
}
