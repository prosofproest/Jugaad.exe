import type { Metadata } from "next";

import { AuthGate } from "@/components/auth-gate";
import { ConversationPageClient } from "@/components/conversation-page-client";

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

  return (
    <AuthGate>
      <ConversationPageClient conversationId={conversationId} />
    </AuthGate>
  );
}
