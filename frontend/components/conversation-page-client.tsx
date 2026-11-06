"use client";

/** Client-side conversation thread for the authenticated chat surface. */

import Link from "next/link";
import { notFound } from "next/navigation";
import { useEffect, useState } from "react";

import { ChatThread } from "@/components/chat-thread";
import {
  ApiError,
  getConversation,
  listMessages,
  type Conversation,
  type Message,
} from "@/lib/api";

export function ConversationPageClient({ conversationId }: { conversationId: string }) {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [freshConversation, freshMessages] = await Promise.all([
          getConversation(conversationId),
          listMessages(conversationId),
        ]);
        if (cancelled) return;
        setConversation(freshConversation);
        setMessages(freshMessages);
      } catch (caught) {
        if (cancelled) return;
        if (caught instanceof ApiError && caught.status === 404) {
          notFound();
          return;
        }
        setFailed(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  if (failed) {
    return (
      <>
        <h1>Conversation unavailable</h1>
        <div className="card">
          <p className="error" role="alert">
            The conversation could not be loaded. The API may be unreachable.
          </p>
          <p>
            <Link href="/chat">Back to all conversations</Link>
          </p>
        </div>
      </>
    );
  }

  if (!conversation || messages === null) {
    return (
      <>
        <h1>Photo-assessment conversation</h1>
        <p className="small muted">Loading conversation…</p>
      </>
    );
  }

  return <ChatThread conversation={conversation} initialMessages={messages} />;
}
