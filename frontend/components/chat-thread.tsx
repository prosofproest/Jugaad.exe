"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { ChatComposer, type ComposerPayload } from "@/components/chat-composer";
import { MessageBubble } from "@/components/message-bubble";
import {
  ApiError,
  deleteConversation,
  requestReview,
  sendMessage,
  uploadImage,
  type Conversation,
  type Message,
  type SendMessageInput,
  type UploadedImage,
} from "@/lib/api";

function errorText(caught: unknown): string {
  if (caught instanceof ApiError) {
    return `${caught.status} ${caught.problem?.code ?? "request_failed"} — ${
      caught.problem?.detail ?? caught.problem?.title ?? "request failed"
    }`;
  }
  return "Network unavailable. Your message is still here; retry when connected.";
}

function optimisticMessage(
  conversationId: string,
  payload: SendMessageInput,
  image: UploadedImage | null,
): Message {
  return {
    message_id: payload.clientMessageId,
    conversation_id: conversationId,
    role: "user",
    kind: payload.image ? "image" : "text",
    text: payload.text?.trim() ? payload.text : null,
    client_message_id: payload.clientMessageId,
    observation_id: image?.upload_id ?? null,
    image,
    assessment: null,
    review_request: null,
    next_steps: [],
    created_at: new Date().toISOString(),
    is_demo: false,
  };
}

export function ChatThread({
  conversation,
  initialMessages,
}: {
  conversation: Conversation;
  initialMessages: Message[];
}) {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<SendMessageInput | null>(null);
  const [failedId, setFailedId] = useState<string | null>(null);
  const [offline, setOffline] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [focusToken, setFocusToken] = useState(0);
  const [reviewingId, setReviewingId] = useState<string | null>(null);
  const listRef = useRef<HTMLOListElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const update = () => setOffline(!navigator.onLine);
    update();
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "nearest" });
  }, [messages.length]);

  async function post(payload: SendMessageInput): Promise<boolean> {
    setSending(true);
    setError(null);
    setFailedId(null);
    try {
      const result = await sendMessage(conversation.conversation_id, payload);
      setMessages((current) => [
        ...current.filter(
          (message) =>
            message.client_message_id !== payload.clientMessageId &&
            message.message_id !== result.user_message.message_id,
        ),
        result.user_message,
        result.assistant_message,
      ]);
      setPending(null);
      return true;
    } catch (caught) {
      setFailedId(payload.clientMessageId);
      setPending(payload);
      setError(errorText(caught));
      return false;
    } finally {
      setSending(false);
    }
  }

  async function handleSend(input: ComposerPayload): Promise<boolean> {
    const clientMessageId = crypto.randomUUID();
    let uploaded: UploadedImage | null = null;

    if (input.file) {
      setSending(true);
      setError(null);
      setFailedId(null);
      try {
        const descriptor = await uploadImage(input.file);
        uploaded = {
          upload_id: descriptor.upload_id,
          filename: descriptor.filename,
          content_type: descriptor.content_type,
          content_hash: descriptor.content_hash,
          width: descriptor.width,
          height: descriptor.height,
          quality_result: descriptor.quality_result,
          quality_flags: descriptor.quality_flags,
          preview_url: descriptor.preview_url,
        };
      } catch (caught) {
        setError(errorText(caught));
        setSending(false);
        return false;
      }
    }

    const payload: SendMessageInput = {
      clientMessageId,
      text: input.text || undefined,
      image: uploaded
        ? {
            uploadId: uploaded.upload_id,
            filename: uploaded.filename,
            contentType: uploaded.content_type,
            contentHash: uploaded.content_hash,
          }
        : undefined,
    };
    setMessages((current) => [
      ...current,
      optimisticMessage(conversation.conversation_id, payload, uploaded),
    ]);
    return post(payload);
  }

  async function handleReview(messageId: string) {
    setReviewingId(messageId);
    setError(null);
    try {
      const review = await requestReview(conversation.conversation_id, messageId);
      setMessages((current) =>
        current.map((message) =>
          message.message_id === messageId
            ? { ...message, review_request: review }
            : message,
        ),
      );
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setReviewingId(null);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    try {
      await deleteConversation(conversation.conversation_id);
      router.push("/chat");
      router.refresh();
    } catch (caught) {
      setError(errorText(caught));
      setDeleting(false);
      setConfirmDelete(false);
    }
  }

  return (
    <div className="chat-shell">
      <div className="thread-header">
        <div>
          <p className="small muted" style={{ marginBottom: "0.25rem" }}>
            <Link href="/chat">← All conversations</Link>
          </p>
          <h1>{conversation.title}</h1>
          <p className="small muted" style={{ marginBottom: 0 }}>
            Started{" "}
            <time dateTime={conversation.created_at}>
              {new Date(conversation.created_at).toLocaleString()}
            </time>
          </p>
        </div>
        <div className="chip-row">
          {confirmDelete ? (
            <>
              <button
                type="button"
                className="button button-danger"
                disabled={deleting}
                onClick={() => void handleDelete()}
              >
                {deleting ? "Deleting…" : "Confirm delete"}
              </button>
              <button
                type="button"
                className="button-secondary"
                disabled={deleting}
                onClick={() => setConfirmDelete(false)}
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              type="button"
              className="button-secondary"
              onClick={() => setConfirmDelete(true)}
            >
              Delete conversation
            </button>
          )}
        </div>
      </div>

      <p className="notice notice-warning small">
        <span className="badge badge-muted">demo</span> This thread uses a
        deterministic demo engine, not a trained model. Uploaded photos are checked
        by a demo quality gate and replies are synthetic, labelled template output —
        never a diagnosis. Photo assessment and area outlook stay separate; this
        thread never shows an outlook.
      </p>

      {offline ? (
        <p className="notice small" role="status">
          You are offline. Sending will fail until the connection returns; your draft
          stays on this page.
        </p>
      ) : null}

      <section className="card" aria-labelledby="messages-heading">
        <h2 id="messages-heading" className="sr-only">
          Messages
        </h2>
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>
              <strong>No messages yet.</strong>
            </p>
            <p>
              Attach a photo or describe what you see on the plant. You can add both.
            </p>
          </div>
        ) : (
          <ol ref={listRef} className="message-list" aria-live="polite">
            {messages.map((message) => (
              <MessageBubble
                key={message.message_id}
                message={message}
                failed={failedId === message.client_message_id}
                onRetry={
                  failedId === message.client_message_id && pending
                    ? () => void post(pending)
                    : undefined
                }
                onRetake={() => setFocusToken((value) => value + 1)}
                onAddContext={() => setFocusToken((value) => value + 1)}
                onRequestReview={() => void handleReview(message.message_id)}
                reviewing={reviewingId === message.message_id}
              />
            ))}
          </ol>
        )}
        <div ref={bottomRef} />
      </section>

      {error ? (
        <div className="error" role="alert">
          <p>{error}</p>
          {pending ? (
            <button
              type="button"
              className="button-secondary"
              disabled={sending}
              onClick={() => void post(pending)}
            >
              Retry send
            </button>
          ) : null}
        </div>
      ) : null}

      <ChatComposer onSend={handleSend} sending={sending} focusToken={focusToken} />
    </div>
  );
}
