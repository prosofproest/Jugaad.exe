"use client";

import Link from "next/link";

import {
  EmptyState,
  Icon,
  PageHeader,
} from "@/components/workspace/ui";

export default function RegisterPage() {
  return (
    <div className="ws-page" style={{ maxWidth: "600px", margin: "2rem auto" }}>
      <PageHeader
        eyebrow="Account registration"
        title="Account Provisioning"
        lede="User accounts in CropSentinel are provisioned through verified agricultural extension offices and system administrators."
      />

      <div className="ws-banner ws-banner-info">
        <Icon name="shield" size={18} />
        <div>
          <strong>Provisioned Identity Policy (ADR-0010)</strong>
          <p>
            Self-registration is not enabled in this deployment. To ensure data integrity, verifiable audit trails, and strict RBAC controls, accounts are provisioned by an administrator.
          </p>
        </div>
      </div>

      <EmptyState
        title="Self-registration is disabled"
        body="If you are an agricultural extension worker, pathologist, or agronomist, your account is provisioned directly through the Admin Portal. If you are an administrator, sign in with your root credentials."
        action={
          <div className="ws-chip-row">
            <Link href="/login" className="ws-button ws-button-primary">
              Sign in
            </Link>
            <Link href="/admin" className="ws-button ws-button-secondary">
              Admin portal
            </Link>
          </div>
        }
      />
    </div>
  );
}
