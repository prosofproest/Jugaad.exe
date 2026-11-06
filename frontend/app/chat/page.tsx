import type { Metadata } from "next";

import { AuthGate } from "@/components/auth-gate";
import { ChatListPage } from "@/components/chat-list-page";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Photo assessment",
};

export default function ChatPage() {
  return (
    <AuthGate>
      <ChatListPage />
    </AuthGate>
  );
}
