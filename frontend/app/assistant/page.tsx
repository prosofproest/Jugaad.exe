"use client";

import { useEffect, useRef, useState } from "react";

import {
  Badge,
  Icon,
  PageHeader,
  PhotoTile,
} from "@/components/workspace/ui";
import { formatDateTime, relativeTime } from "@/lib/format";
import { useWorkspace } from "@/lib/workspace/store";
import type { ChatMessage } from "@/lib/workspace/types";

interface SpeechResultEvent {
  results: ArrayLike<ArrayLike<{ transcript: string }>>;
}

interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((event: SpeechResultEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
}

type SpeechConstructor = new () => SpeechRecognitionLike;

const SUGGESTIONS = [
  "Why are pests appearing on my tomato now?",
  "Ask about biological control for thrips",
  "What preventive measures should I take after rain?",
  "Show crop-specific management for mango",
  "Can you explain chemical control safety?",
];

const TOPIC_PROMPTS = [
  { icon: "alert" as const, label: "Why is this happening?", prompt: "Why are these pests appearing now?" },
  { icon: "shield" as const, label: "How do I control it?", prompt: "How do I control this safely?" },
  { icon: "leaf" as const, label: "Biological control", prompt: "What biological control options are available?" },
  { icon: "water" as const, label: "Preventive measures", prompt: "What preventive measures should I take?" },
  { icon: "plant" as const, label: "Crop-specific management", prompt: "Give me crop-specific management guidance for tomato." },
];

export default function AssistantPage() {
  const { state, sendChat, newThread } = useWorkspace();
  const [threadId, setThreadId] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [imageTone, setImageTone] = useState<number | null>(null);
  const [voiceNote, setVoiceNote] = useState("");
  const [listening, setListening] = useState(false);
  const [showContext, setShowContext] = useState(true);
  const fileRef = useRef<HTMLInputElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  const activeThreadId = threadId ?? state.threads[0]?.id ?? "";
  const thread = state.threads.find((item) => item.id === activeThreadId) ?? state.threads[0];
  const latestAnalyses = state.analyses.slice(0, 3);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [thread?.messages.length, activeThreadId]);

  function startNew() {
    const id = newThread(`New conversation ${state.threads.length + 1}`);
    setThreadId(id);
    setText("");
  }

  function submit(event?: React.FormEvent) {
    event?.preventDefault();
    if (!thread) return;
    const trimmed = text.trim();
    if (!trimmed && imageTone === null) return;
    sendChat(thread.id, trimmed || "Please look at this plant photo and suggest a safe next step.", imageTone ?? undefined);
    setText("");
    setImageTone(null);
    setVoiceNote("");
  }

  function startVoice() {
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    const speechWindow = window as unknown as {
      SpeechRecognition?: SpeechConstructor;
      webkitSpeechRecognition?: SpeechConstructor;
    };
    const Constructor = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!Constructor) {
      setVoiceNote("Voice input is not supported in this browser. Type your question instead.");
      return;
    }
    const recognition = new Constructor();
    recognition.lang = state.currentUser.language === "hi" ? "hi-IN" : state.currentUser.language === "kn" ? "kn-IN" : "en-IN";
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript ?? "";
      if (transcript) setText((current) => `${current} ${transcript}`.trim());
    };
    recognition.onerror = () => setVoiceNote("Voice capture stopped. You can type your question.");
    recognition.onend = () => setListening(false);
    recognition.start();
    recognitionRef.current = recognition;
    setListening(true);
    setVoiceNote("Listening… speak your question.");
  }

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="AI assistant"
        title="Ask about a pest, disease or next step"
        lede="A guarded conversation surface. It explains uncertainty, cites your farm context and never confirms a diagnosis or recommends a product dose."
        actions={
          <button type="button" className="ws-button ws-button-primary" onClick={startNew}>
            <Icon name="plus" size={16} /> New conversation
          </button>
        }
      />

      <div className="ws-assistant-layout">
        <aside className="ws-panel ws-thread-list">
          <div className="ws-panel-head"><h2>Conversations</h2><Badge tone="neutral">{state.threads.length}</Badge></div>
          <ul>
            {state.threads.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className={item.id === thread?.id ? "ws-thread-item ws-thread-item-active" : "ws-thread-item"}
                  onClick={() => setThreadId(item.id)}
                >
                  <span className="ws-thread-icon"><Icon name="assistant" size={16} /></span>
                  <span>
                    <strong>{item.title}</strong>
                    <small>{relativeTime(item.updatedAt)} · {item.messages.length} messages</small>
                  </span>
                </button>
              </li>
            ))}
          </ul>
          <div className="ws-thread-note">
            <Icon name="shield" size={16} />
            <p>Chat is a wrapper, not an authority. Replies use the same cautious language as the assessment card.</p>
          </div>
        </aside>

        <section className="ws-chat-panel">
          <div className="ws-chat-head">
            <div>
              <h2>{thread?.title ?? "New conversation"}</h2>
              <p className="ws-small ws-muted">
                {thread?.farmId ? state.farms.find((farm) => farm.id === thread.farmId)?.name : "No farm context"}
                {" · "}
                {state.currentUser.language === "en" ? "English" : state.currentUser.language === "hi" ? "हिन्दी" : "ಕನ್ನಡ"}
              </p>
            </div>
            <div className="ws-chip-row">
              <span className="ws-chip"><Icon name="shield" size={13} /> Safety guardrails on</span>
              <button type="button" className="ws-chip ws-chip-button" onClick={() => setShowContext((value) => !value)}>
                <Icon name="analysis" size={13} /> {showContext ? "Hide" : "Show"} farm context
              </button>
            </div>
          </div>

          <div className="ws-chat-body">
            <div className="ws-chat-messages">
              {thread?.messages.length === 0 ? (
                <div className="ws-chat-welcome">
                  <span className="ws-chat-avatar"><Icon name="assistant" size={24} /></span>
                  <h3>What would you like to understand?</h3>
                  <p className="ws-small ws-muted">
                    Ask about a symptom, upload a photo, or start from one of your recent observations.
                    I will keep the answer cautious and actionable.
                  </p>
                  <div className="ws-prompt-grid">
                    {TOPIC_PROMPTS.map((prompt) => (
                      <button
                        key={prompt.label}
                        type="button"
                        className="ws-prompt"
                        onClick={() => setText(prompt.prompt)}
                      >
                        <Icon name={prompt.icon} size={16} />
                        <span>{prompt.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                thread?.messages.map((message) => <MessageBubble key={message.id} message={message} />)
              )}
              <div ref={endRef} />
            </div>

            {showContext ? (
              <aside className="ws-chat-context">
                <p className="ws-eyebrow">Farm context</p>
                <h3>Recent observations</h3>
                <p className="ws-small ws-muted">Use one of these to ask a follow-up question.</p>
                <ul>
                  {latestAnalyses.map((analysis) => (
                    <li key={analysis.id}>
                      <button
                        type="button"
                        className="ws-context-item"
                        onClick={() =>
                          setText(
                            `My recent observation on ${analysis.subjectLabel} showed possible ${analysis.pest ?? analysis.disease} with ${analysis.confidenceBand} confidence. What should I check next?`,
                          )
                        }
                      >
                        <PhotoTile tone={analysis.imageTone} mediaType={analysis.mediaType} label={analysis.subjectLabel} size="sm" />
                        <span>
                          <strong>{analysis.subjectLabel}</strong>
                          <small>{analysis.pest ?? analysis.disease}</small>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
                <div className="ws-context-facts">
                  <div><span>Farm</span><strong>{state.farms[0]?.name}</strong></div>
                  <div><span>Blocks</span><strong>{state.cropGroups.length}</strong></div>
                  <div><span>Pending review</span><strong>{state.analyses.filter((item) => item.reviewStatus === "pending").length}</strong></div>
                </div>
              </aside>
            ) : null}
          </div>

          <div className="ws-chat-composer">
            {imageTone !== null ? (
              <div className="ws-chat-attachment">
                <PhotoTile tone={imageTone} label="Attached plant photo" size="sm" />
                <span className="ws-small">Plant photo attached · image-based question</span>
                <button type="button" className="ws-icon-button" onClick={() => setImageTone(null)} aria-label="Remove image">
                  <Icon name="close" size={15} />
                </button>
              </div>
            ) : null}
            {voiceNote ? <p className="ws-small ws-voice-note">{voiceNote}</p> : null}
            <form onSubmit={submit} className="ws-composer">
              <button
                type="button"
                className="ws-icon-button ws-composer-icon"
                onClick={() => fileRef.current?.click()}
                aria-label="Attach a plant image"
              >
                <Icon name="camera" size={19} />
              </button>
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="ws-hidden-input"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) setImageTone(file.name.length % 8);
                }}
              />
              <button
                type="button"
                className={listening ? "ws-icon-button ws-composer-icon ws-listening" : "ws-icon-button ws-composer-icon"}
                onClick={startVoice}
                aria-label="Voice input"
              >
                <Icon name="assistant" size={19} />
              </button>
              <textarea
                rows={1}
                value={text}
                onChange={(event) => setText(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    submit();
                  }
                }}
                placeholder="Ask about a pest, disease or next step…"
                aria-label="Message"
              />
              <button type="submit" className="ws-button ws-button-primary" disabled={!text.trim() && imageTone === null}>
                Send <Icon name="arrow" size={16} />
              </button>
            </form>
            <div className="ws-chat-suggestions">
              {SUGGESTIONS.slice(0, 3).map((suggestion) => (
                <button key={suggestion} type="button" className="ws-suggestion" onClick={() => setText(suggestion)}>
                  {suggestion}
                </button>
              ))}
            </div>
            <p className="ws-chat-disclaimer">
              No pesticide, fungicide or fertiliser names, doses or intervals. Contact your extension
              officer or an approved advisory for treatment decisions.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={isUser ? "ws-message ws-message-user" : "ws-message"}>
      <span className="ws-message-avatar">
        <Icon name={isUser ? "user" : "assistant"} size={17} />
      </span>
      <div className="ws-message-content">
        {message.imageTone !== undefined ? (
          <PhotoTile tone={message.imageTone} label="Attached plant photo" size="sm" />
        ) : null}
        <div className="ws-bubble">{message.text}</div>
        <span className="ws-message-meta">
          {isUser ? "You" : "Assistant"} · {formatDateTime(message.at)}
          {!isUser ? <Badge tone="info">Guardrailed</Badge> : null}
        </span>
      </div>
    </div>
  );
}
