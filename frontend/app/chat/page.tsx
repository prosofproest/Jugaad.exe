import type { Metadata } from "next";

import { ChatIndex } from "@/components/chat-index";
import { ApiError, listConversations, type Conversation } from "@/lib/api";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Photo assessment",
};

export default async function ChatPage() {
  let conversations: Conversation[] = [];
  let error: string | null = null;

  try {
    conversations = await listConversations();
  } catch (caught) {
    error =
      caught instanceof ApiError
        ? `${caught.status} ${caught.problem?.code ?? "api_error"} — ${
            caught.problem?.detail ?? caught.problem?.title ?? "request failed"
          }`
        : "The API is unreachable. Check that the backend is running.";
  }

  return <ChatIndex initialConversations={conversations} initialError={error} />;
}
