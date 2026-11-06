"use client";

/**
 * Shared staff sign-in for authenticated web surfaces.
 *
 * Staff (extension worker, pathologist, agronomist, admin) sign in with
 * email + password; MFA roles then need a 6-digit TOTP code. The resulting
 * access/refresh pair is written to sessionStorage via `@/lib/auth` and
 * picked up automatically by `@/lib/api`. Farmer phone-OTP delivery has no
 * provider yet (dev codes live only in backend memory and are never returned
 * over HTTP), so staff sign-in is the supported local path. This component
 * never logs or renders tokens.
 */

import { useState } from "react";

import { ApiError, loginStaff, verifyMfa } from "@/lib/api";
import { writeSession } from "@/lib/auth";

function errorText(caught: unknown): string {
  if (caught instanceof ApiError) {
    return `${caught.status} ${caught.problem?.code ?? "request_failed"} — ${
      caught.problem?.detail ?? caught.problem?.title ?? "request failed"
    }`;
  }
  return "The API is unreachable. Check that the backend is running and retry.";
}

export function SignIn({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totp, setTotp] = useState("");
  const [challenge, setChallenge] = useState<string | null>(null);
  const [challengeExpiresIn, setChallengeExpiresIn] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitLogin(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const response = await loginStaff(email.trim(), password);
      setPassword("");
      if (response.mfa_required) {
        if (!response.challenge_token) {
          setError("The server requested MFA but returned no challenge.");
          return;
        }
        setChallenge(response.challenge_token);
        setChallengeExpiresIn(response.challenge_expires_in);
        setTotp("");
        return;
      }
      if (!response.tokens) {
        setError("The server returned no tokens.");
        return;
      }
      writeSession({
        accessToken: response.tokens.access_token,
        refreshToken: response.tokens.refresh_token,
        userId: response.tokens.user_id,
        role: response.tokens.role,
      });
      onSuccess();
    } catch (caught) {
      setError(errorText(caught));
      setPassword("");
    } finally {
      setBusy(false);
    }
  }

  async function submitMfa(event: React.FormEvent) {
    event.preventDefault();
    if (!challenge) return;
    setBusy(true);
    setError(null);
    try {
      const tokens = await verifyMfa(challenge, totp.trim());
      setChallenge(null);
      setTotp("");
      writeSession({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        userId: tokens.user_id,
        role: tokens.role,
      });
      onSuccess();
    } catch (caught) {
      setError(errorText(caught));
      setTotp("");
    } finally {
      setBusy(false);
    }
  }

  if (challenge) {
    return (
      <form
        className="card admin-form"
        onSubmit={(event) => void submitMfa(event)}
        aria-label="Authenticator code"
      >
        <h2>Authenticator code</h2>
        <p className="small muted">
          Enter the 6-digit code from the authenticator enrolled for this
          account. The challenge expires in {challengeExpiresIn ?? "under 5"}{" "}
          seconds.
        </p>
        <div className="admin-field">
          <label htmlFor="signin-totp">6-digit code</label>
          <input
            id="signin-totp"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="[0-9]{6}"
            required
            value={totp}
            onChange={(event) =>
              setTotp(event.target.value.replace(/[^0-9]/g, "").slice(0, 6))
            }
            disabled={busy}
          />
        </div>
        {error ? (
          <div className="error" role="alert">
            <p>{error}</p>
          </div>
        ) : null}
        <div className="chip-row">
          <button type="submit" disabled={busy}>
            {busy ? "Verifying…" : "Verify"}
          </button>
          <button
            type="button"
            className="button-secondary"
            disabled={busy}
            onClick={() => {
              setChallenge(null);
              setTotp("");
              setError(null);
            }}
          >
            Back to sign-in
          </button>
        </div>
      </form>
    );
  }

  return (
    <form
      className="card admin-form"
      onSubmit={(event) => void submitLogin(event)}
      aria-label="Staff sign-in"
    >
      <h2>Sign in</h2>
      <p className="small muted">
        Staff accounts sign in with email and password. Farmer phone-OTP
        delivery is not yet wired, so staff sign-in is the supported path for
        this surface. Tokens live in this tab only (15-minute access token)
        and are never stored elsewhere.
      </p>
      <div className="admin-field">
        <label htmlFor="signin-email">Email</label>
        <input
          id="signin-email"
          type="email"
          autoComplete="username"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          disabled={busy}
        />
      </div>
      <div className="admin-field">
        <label htmlFor="signin-password">Password</label>
        <input
          id="signin-password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          disabled={busy}
        />
      </div>
      {error ? (
        <div className="error" role="alert">
          <p>{error}</p>
        </div>
      ) : null}
      <button type="submit" disabled={busy}>
        {busy ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
