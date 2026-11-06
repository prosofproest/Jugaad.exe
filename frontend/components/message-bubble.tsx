import type { Message } from "@/lib/api";

import { AssessmentCard } from "@/components/assessment-card";

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function MessageBubble({
  message,
  failed = false,
  onRetry,
  onRetake,
  onAddContext,
}: {
  message: Message;
  failed?: boolean;
  onRetry?: () => void;
  onRetake?: () => void;
  onAddContext?: () => void;
}) {
  const isUser = message.role === "user";

  return (
    <li className={isUser ? "message message-user" : "message"}>
      <div className={failed ? "bubble message-failed" : "bubble"}>
        <div className="message-meta">
          <strong>{isUser ? "You" : "Assistant"}</strong>
          <time dateTime={message.created_at}>{formatTime(message.created_at)}</time>
          {message.is_demo ? (
            <span className="badge badge-muted">demo</span>
          ) : null}
          {failed ? <span className="chip chip-muted">Not sent</span> : null}
        </div>

        {message.text ? <p>{message.text}</p> : null}

        {message.kind === "image" ? (
          <p className="small muted">
            <span className="chip chip-muted">Photo attached</span>{" "}
            Capture metadata only in this phase; the content is not uploaded or
            analysed.
          </p>
        ) : null}

        {message.assessment ? (
          <AssessmentCard
            assessment={message.assessment}
            nextSteps={message.next_steps}
            onRetake={onRetake}
            onAddContext={onAddContext}
          />
        ) : null}

        {failed && onRetry ? (
          <div className="chip-row">
            <button type="button" className="button-secondary" onClick={onRetry}>
              Retry send
            </button>
          </div>
        ) : null}
      </div>
    </li>
  );
}
