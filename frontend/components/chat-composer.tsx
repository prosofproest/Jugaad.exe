"use client";

import { useEffect, useMemo, useRef, useState } from "react";

export interface ComposerPayload {
  text: string;
  file: File | null;
}

export function ChatComposer({
  onSend,
  sending,
  focusToken = 0,
}: {
  onSend: (payload: ComposerPayload) => Promise<boolean>;
  sending: boolean;
  focusToken?: number;
}) {
  const [draft, setDraft] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const previewUrl = useMemo(
    () => (file ? URL.createObjectURL(file) : null),
    [file],
  );

  useEffect(() => {
    if (focusToken > 0) {
      textareaRef.current?.focus();
    }
  }, [focusToken]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  function chooseFile(candidate: File | null) {
    setFileError(null);
    if (!candidate) {
      return;
    }
    if (!candidate.type.startsWith("image/")) {
      setFileError("Choose an image file (JPEG, PNG or WebP).");
      return;
    }
    if (candidate.size > 10 * 1024 * 1024) {
      setFileError("Choose an image smaller than 10 MB.");
      return;
    }
    setFile(candidate);
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    if (sending || (!text && !file)) {
      return;
    }
    const ok = await onSend({ text, file });
    if (ok) {
      setDraft("");
      setFile(null);
      setFileError(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }

  return (
    <form className="composer" onSubmit={submit} aria-label="Send a message">
      <div
        className={dragging ? "dropzone dropzone-active" : "dropzone"}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          chooseFile(event.dataTransfer.files?.[0] ?? null);
        }}
      >
        <input
          ref={inputRef}
          id="chat-image"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={(event) => chooseFile(event.target.files?.[0] ?? null)}
        />
        <p className="small">
          Drag a photo here, or{" "}
          <label
            htmlFor="chat-image"
            className="button button-secondary"
            style={{ marginBottom: 0, cursor: "pointer" }}
          >
            choose a photo
          </label>
        </p>
        <p className="small muted">
          JPEG, PNG or WebP, up to 10 MB. The photo is stored on this demo server
          and checked by the demo quality gate. It is not sent to a real model.
        </p>
      </div>

      {fileError ? (
        <p className="small error" role="alert">
          {fileError}
        </p>
      ) : null}

      {file ? (
        <div className="attachment">
          <div className="chip-row" style={{ alignItems: "center" }}>
            {previewUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={previewUrl} alt={`Preview of ${file.name}`} />
            ) : null}
            <div>
              <p className="small" style={{ marginBottom: 0 }}>
                <strong>{file.name}</strong>
              </p>
              <p className="small muted" style={{ marginBottom: 0 }}>
                {Math.max(1, Math.round(file.size / 1024))} KB · ready to upload
              </p>
            </div>
          </div>
          <button
            type="button"
            className="button-ghost"
            onClick={() => {
              setFile(null);
              if (inputRef.current) {
                inputRef.current.value = "";
              }
            }}
          >
            Remove
          </button>
        </div>
      ) : null}

      <div>
        <label htmlFor="chat-message">Message</label>
        <textarea
          ref={textareaRef}
          id="chat-message"
          name="message"
          rows={3}
          maxLength={1000}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Example: brown spots on the lower leaves, spreading for a week"
        />
        <p className="small muted">
          Optional context only. Do not include personal or farm-identifying details.
        </p>
      </div>

      <div className="composer-actions">
        <button
          type="submit"
          className="button-large"
          disabled={sending || (!draft.trim() && !file)}
        >
          {sending ? "Sending…" : "Send for assessment"}
        </button>
      </div>
    </form>
  );
}
