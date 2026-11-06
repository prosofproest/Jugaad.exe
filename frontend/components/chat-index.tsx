"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import {
  ApiError,
  createConversation,
  deleteConversation,
  type Conversation,
} from "@/lib/api";

function errorText(caught: unknown): string {
  if (caught instanceof ApiError) {
    return `${caught.status} ${caught.problem?.code ?? "request_failed"} — ${
      caught.problem?.detail ?? caught.problem?.title ?? "request failed"
    }`;
  }
  return "The API is unreachable. Check that the backend is running and retry.";
}

export function ChatIndex({
  initialConversations,
  initialError,
}: {
  initialConversations: Conversation[];
  initialError: string | null;
}) {
  const router = useRouter();
  const [conversations, setConversations] = useState(initialConversations);
  const [error, setError] = useState(initialError);
  const [creating, setCreating] = useState(false);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function startConversation() {
    setCreating(true);
    setError(null);
    try {
      const conversation = await createConversation();
      router.push(`/chat/${conversation.conversation_id}`);
    } catch (caught) {
      setError(errorText(caught));
      setCreating(false);
    }
  }

  async function removeConversation(conversationId: string) {
    setDeletingId(conversationId);
    setError(null);
    try {
      await deleteConversation(conversationId);
      setConversations((current) =>
        current.filter((item) => item.conversation_id !== conversationId),
      );
      setConfirmingId(null);
      router.refresh();
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Photo assessment</p>
        <h1>Photo assessment</h1>
        <p className="page-lede">
          <span className="badge badge-muted">separate output</span> This is the
          photo-assessment track only. It never shows an area outlook or a merged
          risk number.
        </p>
      </header>
      <p className="notice notice-warning small">
        <span className="badge badge-muted">demo</span> A deterministic demo engine
        is connected, not a trained model. Uploaded photos pass a demo quality gate
        and replies are synthetic, labelled template output — never a diagnosis.
      </p>

      <div className="toolbar">
        <p className="small muted" style={{ marginBottom: 0 }}>
          {conversations.length}{" "}
          {conversations.length === 1 ? "conversation" : "conversations"}
        </p>
        <button
          type="button"
          className="button-large"
          disabled={creating}
          onClick={() => void startConversation()}
        >
          {creating ? "Starting…" : "New conversation"}
        </button>
      </div>

      {error ? (
        <div className="error" role="alert">
          <p>{error}</p>
          <button
            type="button"
            className="button-secondary"
            disabled={creating}
            onClick={() => void startConversation()}
          >
            Retry
          </button>
        </div>
      ) : null}

      {conversations.length === 0 ? (
        <div className="empty-state">
          <p>
            <strong>No conversations yet.</strong>
          </p>
          <p>Start one to describe a plant problem and attach a photo.</p>
          <button
            type="button"
            className="button-large"
            disabled={creating}
            onClick={() => void startConversation()}
          >
            Start a conversation
          </button>
        </div>
      ) : (
        <ul className="conversation-list">
          {conversations.map((conversation) => (
            <li key={conversation.conversation_id} className="conversation-item">
              <Link href={`/chat/${conversation.conversation_id}`}>
                <strong>{conversation.title}</strong>
                <span className="conversation-meta">
                  Last activity{" "}
                  <time
                    dateTime={conversation.last_message_at}
                    suppressHydrationWarning
                  >
                    {new Date(conversation.last_message_at).toLocaleString()}
                  </time>
                </span>
              </Link>
              {confirmingId === conversation.conversation_id ? (
                <div className="chip-row">
                  <button
                    type="button"
                    className="button button-danger"
                    disabled={deletingId === conversation.conversation_id}
                    onClick={() => void removeConversation(conversation.conversation_id)}
                  >
                    {deletingId === conversation.conversation_id
                      ? "Deleting…"
                      : "Confirm delete"}
                  </button>
                  <button
                    type="button"
                    className="button-secondary"
                    disabled={deletingId === conversation.conversation_id}
                    onClick={() => setConfirmingId(null)}
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  className="button-secondary"
                  onClick={() => setConfirmingId(conversation.conversation_id)}
                >
                  Delete
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      <p className="small muted" style={{ marginTop: "1rem" }}>
        An area outlook is a different output with its own data, model version and
        timestamp. It is not available in this phase.
      </p>
    </div>
  );
}
