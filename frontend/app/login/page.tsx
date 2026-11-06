"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Icon, type IconName } from "@/components/workspace/ui";
import { useWorkspace } from "@/lib/workspace/store";
import type { Role } from "@/lib/workspace/types";

const ROLES: { role: Role; label: string; detail: string; icon: IconName; demo: string }[] = [
  {
    role: "farmer",
    label: "Farmer",
    detail: "Scan plants, manage farms, track recovery",
    icon: "plant",
    demo: "Ravi Kumar · Hosur",
  },
  {
    role: "expert",
    label: "Agricultural expert",
    detail: "Verify diagnoses and approve recommendations",
    icon: "expert",
    demo: "Dr. Meera Sundaram · Plant health clinic",
  },
  {
    role: "agent",
    label: "Field agent",
    detail: "Run assigned inspections and farmer reports",
    icon: "location",
    demo: "Arun Prasad · Block extension office",
  },
  {
    role: "admin",
    label: "Administrator",
    detail: "Coverage, backlog and regional oversight",
    icon: "shield",
    demo: "Lakshmi Narayanan · District office",
  },
];

export default function LoginPage() {
  const router = useRouter();
  const { signIn, setLanguage } = useWorkspace();
  const [role, setRole] = useState<Role>("farmer");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (phone.replace(/\D/g, "").length < 10) {
      setError("Enter a 10-digit mobile number, or use a demo account below.");
      return;
    }
    if (password.length < 4) {
      setError("Demo password must be at least 4 characters.");
      return;
    }
    signIn(role);
    router.push("/");
  }

  return (
    <div className="ws-auth">
      <div className="ws-auth-visual">
        <Link href="/login" className="ws-auth-brand">
          <span className="ws-brand-mark"><Icon name="leaf" size={22} /></span>
          <span><strong>CropSentinel</strong><small>Pest & disease network</small></span>
        </Link>
        <div>
          <p className="ws-eyebrow">Field-ready decision support</p>
          <h1>See what is happening on the farm before it spreads.</h1>
          <p>
            Photo triage, farm maps and verified regional signals in one workspace. Every result
            shows its uncertainty, freshness and the next safe step.
          </p>
        </div>
        <div className="ws-auth-points">
          <span><Icon name="camera" size={17} /> Offline-first capture</span>
          <span><Icon name="map" size={17} /> Plot and plant health maps</span>
          <span><Icon name="expert" size={17} /> Human verification</span>
        </div>
        <p className="ws-auth-disclaimer">
          Assistive decision support, not a diagnosis or a confirmed outbreak. Demo data is stored
          on this device only.
        </p>
      </div>

      <div className="ws-auth-panel">
        <div className="ws-auth-card">
          <div className="ws-auth-head">
            <p className="ws-eyebrow">Welcome back</p>
            <h2>Sign in to your workspace</h2>
            <p className="ws-small ws-muted">Choose a role to see its dashboard and permissions.</p>
          </div>

          <div className="ws-role-picker" role="radiogroup" aria-label="Account role">
            {ROLES.map((item) => (
              <button
                key={item.role}
                type="button"
                role="radio"
                aria-checked={role === item.role}
                className={role === item.role ? "ws-role-option ws-role-option-active" : "ws-role-option"}
                onClick={() => setRole(item.role)}
              >
                <span className="ws-role-icon"><Icon name={item.icon} size={18} /></span>
                <span>
                  <strong>{item.label}</strong>
                  <small>{item.detail}</small>
                </span>
                {role === item.role ? <Icon name="check" size={16} /> : null}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="ws-form">
            <label className="ws-field">
              <span>Mobile number</span>
              <input
                type="tel"
                inputMode="numeric"
                placeholder="98420 11223"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                autoComplete="tel"
              />
            </label>
            <label className="ws-field">
              <span>Password</span>
              <input
                type="password"
                placeholder="Demo password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
              />
            </label>
            {error ? <p className="ws-form-error" role="alert">{error}</p> : null}
            <div className="ws-form-row">
              <label className="ws-check">
                <input type="checkbox" defaultChecked /> Remember this device
              </label>
              <button type="button" className="ws-link-button">Forgot password?</button>
            </div>
            <button type="submit" className="ws-button ws-button-primary ws-button-block ws-button-large">
              Sign in as {ROLES.find((item) => item.role === role)?.label}
              <Icon name="arrow" size={17} />
            </button>
          </form>

          <div className="ws-demo-accounts">
            <p className="ws-eyebrow">One-tap demo accounts</p>
            {ROLES.map((item) => (
              <button
                key={item.role}
                type="button"
                className="ws-demo-account"
                onClick={() => {
                  signIn(item.role);
                  router.push("/");
                }}
              >
                <span>
                  <strong>{item.demo}</strong>
                  <small>{item.label}</small>
                </span>
                <span className="ws-demo-use">Use <Icon name="arrow" size={13} /></span>
              </button>
            ))}
          </div>

          <p className="ws-auth-switch">
            New here? <Link href="/register">Create a farmer account</Link>
          </p>
          <div className="ws-auth-lang">
            <Icon name="globe" size={15} />
            <button type="button" onClick={() => setLanguage("en")}>English</button>
            <button type="button" onClick={() => setLanguage("hi")}>हिन्दी</button>
            <button type="button" onClick={() => setLanguage("kn")}>ಕನ್ನಡ</button>
          </div>
        </div>
      </div>
    </div>
  );
}
