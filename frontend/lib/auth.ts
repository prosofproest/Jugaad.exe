/**
 * Browser-only session storage for identity tokens.
 *
 * The backend issues bearer access + refresh pairs (15-minute access TTL,
 * 30-day refresh TTL). There is no httpOnly cookie or CSRF handling in this
 * scaffold, so the Admin page keeps the pair in `sessionStorage` (cleared
 * when the tab closes) and never touches `localStorage`. Tokens are never
 * logged or rendered. Production must move to httpOnly cookies before
 * exposing the Admin surface beyond local development.
 *
 * This module must only be imported from client components.
 */

export interface SessionTokens {
  accessToken: string;
  refreshToken: string;
  userId: string;
  role: string;
}

const STORAGE_KEY = "ps03.identity.session";

export function readSession(): SessionTokens | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<SessionTokens>;
    if (
      typeof parsed.accessToken !== "string" ||
      !parsed.accessToken ||
      typeof parsed.refreshToken !== "string" ||
      !parsed.refreshToken ||
      typeof parsed.userId !== "string" ||
      typeof parsed.role !== "string"
    ) {
      return null;
    }
    return {
      accessToken: parsed.accessToken,
      refreshToken: parsed.refreshToken,
      userId: parsed.userId,
      role: parsed.role,
    };
  } catch {
    return null;
  }
}

export function writeSession(tokens: SessionTokens): void {
  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(tokens));
}

export function clearSession(): void {
  window.sessionStorage.removeItem(STORAGE_KEY);
}
