"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { SignIn } from "@/components/sign-in";
import { PageHeader } from "@/components/workspace/ui";
import { readSession } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const session = readSession();

  function handleSuccess() {
    router.push("/");
  }

  return (
    <div className="ws-page" style={{ maxWidth: "600px", margin: "2rem auto" }}>
      <PageHeader
        eyebrow="Authentication"
        title="Sign in to CropSentinel"
        lede="Access the early pest warning system, submit field observations, or review verification queues."
      />

      {session ? (
        <div className="ws-panel">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Active session</p>
              <h2>Already signed in</h2>
            </div>
            <span className="badge badge-primary">{session.role}</span>
          </div>
          <p className="ws-muted">You are currently signed in as user ID: {session.userId}.</p>
          <div className="ws-banner-actions" style={{ marginTop: "1rem" }}>
            <Link href="/" className="ws-button ws-button-primary">
              Go to Dashboard
            </Link>
            <Link href="/admin" className="ws-button ws-button-secondary">
              Admin Portal
            </Link>
          </div>
        </div>
      ) : (
        <div>
          <SignIn onSuccess={handleSuccess} />

          <div className="ws-notice ws-notice-info" style={{ marginTop: "1.5rem" }}>
            <p className="ws-small ws-muted" style={{ margin: 0 }}>
              Staff accounts (extension worker, pathologist, agronomist, admin) sign in with email and password. Farmer phone-OTP delivery is in development and has no live SMS gateway yet. Use a provisioned staff account to access protected surfaces.
            </p>
          </div>

          <p className="ws-small ws-muted" style={{ textAlign: "center", marginTop: "1rem" }}>
            Need an account? Contact your extension office or <Link href="/register" className="ws-link">view registration details</Link>.
          </p>
        </div>
      )}
    </div>
  );
}
