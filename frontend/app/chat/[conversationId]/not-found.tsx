import Link from "next/link";

export default function ConversationNotFound() {
  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Photo assessment</p>
        <h1>Conversation not found</h1>
        <p className="page-lede">
          This conversation does not exist, or it belongs to another user.
        </p>
      </header>

      <div className="locked-state">
        <p>
          <strong>Nothing to show here.</strong>
        </p>
        <p className="small muted">
          Conversations are scoped to their owner. A missing conversation is not
          evidence that a report was deleted or reviewed.
        </p>
        <Link href="/chat" className="button">
          Back to all conversations
        </Link>
      </div>
    </div>
  );
}
