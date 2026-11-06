"use client";

import { useEffect, useState } from "react";

import { authenticatedBlobUrl, type Message } from "@/lib/api";

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

function qualityText(image: NonNullable<Message["image"]>): string {
  const flags = image.quality_flags.length
    ? ` (${image.quality_flags.join(", ")})`
    : "";
  return `quality: ${image.quality_result.replaceAll("_", " ")}${flags}`;
}

export function MessageBubble({
  message,
  failed = false,
  onRetry,
  onRetake,
  onAddContext,
  onRequestReview,
  reviewing = false,
}: {
  message: Message;
  failed?: boolean;
  onRetry?: () => void;
  onRetake?: () => void;
  onAddContext?: () => void;
  onRequestReview?: () => void;
  reviewing?: boolean;
}) {
  const isUser = message.role === "user";
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState(false);

  useEffect(() => {
    if (!message.image) return;
    let cancelled = false;
    let objectUrl: string | null = null;
    (async () => {
      try {
        const fetched = await authenticatedBlobUrl(message.image!.preview_url);
        objectUrl = fetched;
        if (!cancelled) setPreviewUrl(fetched);
      } catch {
        if (!cancelled) setPreviewError(true);
      }
    })();
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [message.image]);

  return (
    <li className={isUser ? "message message-user" : "message"}>
      <div className={failed ? "bubble message-failed" : "bubble"}>
        <div className="message-meta">
          <strong>{isUser ? "You" : "Assistant"}</strong>
          <time dateTime={message.created_at} suppressHydrationWarning>
            {formatTime(message.created_at)}
          </time>
          {message.is_demo ? (
            <span className="badge badge-muted">demo</span>
          ) : null}
          {failed ? <span className="chip chip-muted">Not sent</span> : null}
        </div>

        {message.text ? <p>{message.text}</p> : null}

        {message.image ? (
          <figure className="message-photo">
            {previewUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={previewUrl}
                alt={`Uploaded plant photo: ${message.image.filename}`}
                loading="lazy"
              />
            ) : previewError ? (
              <p className="small muted">Preview unavailable.</p>
            ) : (
              <p className="small muted">Loading preview…</p>
            )}
            <figcaption className="small muted">
              {message.image.filename} · {message.image.width}×
              {message.image.height} · {qualityText(message.image)}
            </figcaption>
          </figure>
        ) : message.kind === "image" ? (
          <p className="small muted">
            <span className="chip chip-muted">Photo attached</span> Preview
            unavailable.
          </p>
        ) : null}

        {message.assessment ? (
          <AssessmentCard
            assessment={message.assessment}
            nextSteps={message.next_steps}
            reviewRequest={message.review_request}
            onRetake={onRetake}
            onAddContext={onAddContext}
            onRequestReview={onRequestReview}
            reviewing={reviewing}
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
