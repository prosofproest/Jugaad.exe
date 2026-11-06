import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ChatThread } from "@/components/chat-thread";
import {
  ApiError,
  getConversation,
  listMessages,
  type Conversation,
  type Message,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Photo-assessment conversation",
};

export default async function ConversationPage({
  params,
}: {
  params: Promise<{ conversationId: string }>;
}) {
  const { conversationId } = await params;

  let conversation: Conversation;
  let messages: Message[];

  try {
    [conversation, messages] = await Promise.all([
      getConversation(conversationId),
      listMessages(conversationId),
    ]);
  } catch (caught) {
    if (caught instanceof ApiError && caught.status === 404) {
      notFound();
    }
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

  return <ChatThread conversation={conversation} initialMessages={messages} />;
}
