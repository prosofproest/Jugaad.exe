"use client";

/** Client-side conversation list for the authenticated chat surface. */

import { useEffect, useState } from "react";

import { ChatIndex } from "@/components/chat-index";
import { ApiError, listConversations, type Conversation } from "@/lib/api";

export function ChatListPage() {
  const [conversations, setConversations] = useState<Conversation[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const fetched = await listConversations();
        if (!cancelled) setConversations(fetched);
      } catch (caught) {
        if (cancelled) return;
        setError(
          caught instanceof ApiError
            ? `${caught.status} ${caught.problem?.code ?? "api_error"} — ${
                caught.problem?.detail ?? caught.problem?.title ?? "request failed"
              }`
            : "The API is unreachable. Check that the backend is running.",
        );
        setConversations([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (conversations === null) {
    return (
      <div className="page">
        <header className="page-header">
          <p className="eyebrow">Photo assessment</p>
          <h1>Photo assessment</h1>
        </header>
        <p className="small muted">Loading your conversations…</p>
      </div>
    );
  }

  return <ChatIndex initialConversations={conversations} initialError={error} />;
}
