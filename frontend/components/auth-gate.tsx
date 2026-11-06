"use client";

/**
 * Gate for authenticated web surfaces. Without a session the page shows
 * staff sign-in; with one it renders the children (API calls attach the
 * bearer token automatically). The gate never fetches data itself — children
 * surface 401s as errors, and this gate does not hide them.
 */

import Link from "next/link";
import { useState, type ReactNode } from "react";

import { SignIn } from "@/components/sign-in";
import { logoutSession } from "@/lib/api";
import { clearSession, readSession } from "@/lib/auth";

export function AuthGate({ children }: { children: ReactNode }) {
  const [session, setSession] = useState(() => readSession());

  if (!session) {
    return (
      <div className="page">
        <header className="page-header">
          <p className="eyebrow">Sign-in required</p>
          <h1>Sign in to continue</h1>
          <p className="page-lede">
            This surface needs an authenticated account. Photo-assessment
            history is private to its owner and area layers are served only to
            signed-in users.
          </p>
        </header>
        <SignIn onSuccess={() => setSession(readSession())} />
        <p className="small muted">
          Farmer phone-OTP delivery is not yet configured. Use a provisioned
          staff account (see <Link href="/admin">Admin</Link>). Admins can be
          bootstrapped from the backend environment.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="toolbar">
        <p className="small muted" style={{ marginBottom: 0 }}>
          Signed in as {session.role} ·{" "}
          <button
            type="button"
            className="button-secondary"
            onClick={() => {
              const target = readSession();
              if (target) {
                logoutSession(target.accessToken)
                  .catch(() => undefined)
                  .finally(() => {
                    clearSession();
                    setSession(null);
                  });
              } else {
                clearSession();
                setSession(null);
              }
            }}
          >
            Sign out
          </button>
        </p>
      </div>
      {children}
    </>
  );
}
