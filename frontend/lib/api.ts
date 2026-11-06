/**
 * Typed client for the PS-03 `/v1` API.
 *
 * Rules:
 * - the web app is an API-only client and never touches the database;
 * - errors are the problem-details envelope from final/TRD.md §7.2;
 * - demo/synthetic content is always labelled by the API, never inferred here.
 */

export type AssessmentState = "assessed" | "abstained" | "unsupported_crop" | "failed";

export interface Assessment {
  state: AssessmentState;
  reason_code: string | null;
  reason_text: string | null;
  candidates: { label: string; score: number }[];
  confidence_band: string | null;
  calibrated: boolean;
  model_version: string;
  generated_at: string;
  is_demo: boolean;
}

export interface Message {
  message_id: string;
  conversation_id: string;
  role: "user" | "assistant";
  kind: string;
  text: string | null;
  client_message_id: string | null;
  assessment: Assessment | null;
  next_steps: string[];
  created_at: string;
  is_demo: boolean;
}

export interface Conversation {
  conversation_id: string;
  owner_id: string;
  title: string;
  created_at: string;
  last_message_at: string;
}

export interface SendResult {
  user_message: Message;
  assistant_message: Message;
}

export interface Health {
  status: string;
  service: string;
  version: string;
  environment: string;
  time: string;
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  code: string;
  detail: string | null;
  request_id: string | null;
  retryable: boolean;
  fields: { field: string; message: string }[];
}

export class ApiError extends Error {
  readonly status: number;
  readonly problem: ProblemDetails | null;

  constructor(status: number, problem: ProblemDetails | null) {
    super(problem?.title ?? `API request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.problem = problem;
  }
}

export function apiBaseUrl(): string {
  // Server components must reach the API over the container network, while the
  // browser needs the public origin. API_BASE_URL is server-only.
  return (
    process.env.API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://localhost:8000"
  );
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      "X-Request-ID": crypto.randomUUID(),
      ...init.headers,
    },
  });

  if (!response.ok) {
    let problem: ProblemDetails | null = null;
    try {
      problem = (await response.json()) as ProblemDetails;
    } catch {
      problem = null;
    }
    throw new ApiError(response.status, problem);
  }

  return (await response.json()) as T;
}

export function getHealth(): Promise<Health> {
  return request<Health>("/health");
}

export function createConversation(): Promise<Conversation> {
  return request<Conversation>("/v1/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: "Photo assessment" }),
  });
}

export function sendMessage(
  conversationId: string,
  input: { clientMessageId: string; text?: string },
): Promise<SendResult> {
  return request<SendResult>(`/v1/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": input.clientMessageId,
    },
    body: JSON.stringify({
      client_message_id: input.clientMessageId,
      text: input.text ?? null,
    }),
  });
}
