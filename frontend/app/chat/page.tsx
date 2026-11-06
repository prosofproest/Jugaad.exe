import { ChatPanel } from "@/components/chat-panel";

export const metadata = {
  title: "Photo assessment — PS-03",
};

export default function ChatPage() {
  return (
    <>
      <h1>Photo assessment</h1>
      <p>
        <span className="badge badge-muted">separate output</span> This screen is
        the photo-assessment track only. It never shows area outlook or a merged
        risk number.
      </p>
      <ChatPanel />
      <p className="muted">
        An area outlook is a different output with its own data, model version and
        timestamp. It is not available in this phase.
      </p>
    </>
  );
}
