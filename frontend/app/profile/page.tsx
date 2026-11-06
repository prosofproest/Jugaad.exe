"use client";

import Link from "next/link";
import { useState } from "react";

import {
  Badge,
  Field,
  Icon,
  PageHeader,
  StatCard,
} from "@/components/workspace/ui";
import { formatDate } from "@/lib/format";
import { useWorkspace } from "@/lib/workspace/store";
import type { Language, Role } from "@/lib/workspace/types";

const ROLE_LABEL: Record<Role, string> = {
  farmer: "Farmer",
  expert: "Agricultural expert",
  agent: "Field agent",
  admin: "Administrator",
};

export default function ProfilePage() {
  const { state, role, updateProfile, setLanguage, setRole } = useWorkspace();
  const user = state.currentUser;
  const [form, setForm] = useState({
    name: user.name,
    phone: user.phone,
    email: user.email,
    village: user.village,
    district: user.district,
  });
  const [saved, setSaved] = useState(false);
  const farms = state.farms.filter((farm) => farm.ownerId === user.id);
  const myAnalyses = state.analyses.filter((analysis) => role !== "farmer" || analysis.reviewStatus !== "rejected");

  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!form.name.trim()) return;
    updateProfile(form);
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2500);
  }

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Profile & account"
        title="Your account"
        lede="Manage the details that appear on observations, review records and verification requests."
        actions={
          <Link href="/settings" className="ws-button ws-button-secondary">
            <Icon name="settings" size={16} /> Account settings
          </Link>
        }
      />

      <div className="ws-profile-hero">
        <span className="ws-avatar ws-avatar-xl">{user.initials}</span>
        <div className="ws-profile-hero-body">
          <div>
            <h2>{user.name}</h2>
            <p className="ws-muted">{user.organisation}</p>
          </div>
          <div className="ws-chip-row">
            <Badge tone="brand">{ROLE_LABEL[role]}</Badge>
            <Badge tone="ok"><Icon name="check" size={12} /> Verified account</Badge>
            <Badge tone="neutral">{user.district}, {user.village}</Badge>
          </div>
        </div>
        <div className="ws-profile-contact">
          <span><Icon name="user" size={15} /> {user.phone}</span>
          <span><Icon name="assistant" size={15} /> {user.email}</span>
          <span><Icon name="globe" size={15} /> {user.language === "en" ? "English" : user.language === "hi" ? "Hindi" : "Kannada"}</span>
        </div>
      </div>

      <div className="ws-stat-grid">
        <StatCard label="Farms owned" value={farms.length} detail={`${state.plants.filter((plant) => farms.some((farm) => farm.id === plant.farmId)).length} plants tracked`} icon="farm" tone="brand" />
        <StatCard label="Observations" value={myAnalyses.length} detail="Photo and video assessments" icon="analysis" />
        <StatCard label="Reviews completed" value={state.analyses.filter((analysis) => analysis.reviewer === user.name).length} detail="Verification and corrections" icon="shield" tone="ok" />
        <StatCard label="Member since" value={formatDate("2026-02-14T06:30:00Z")} detail="Hosur Sunrise Farm" icon="calendar" />
      </div>

      <div className="ws-two-col">
        <section className="ws-panel">
          <div className="ws-panel-head">
            <div><p className="ws-eyebrow">Personal details</p><h2>Edit profile</h2></div>
            <Badge tone="neutral">Stored locally</Badge>
          </div>
          <form onSubmit={submit} className="ws-form">
            <Field label="Full name"><input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></Field>
            <div className="ws-form-grid">
              <Field label="Mobile number"><input type="tel" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} /></Field>
              <Field label="Email"><input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></Field>
            </div>
            <div className="ws-form-grid">
              <Field label="Village"><input value={form.village} onChange={(event) => setForm({ ...form, village: event.target.value })} /></Field>
              <Field label="District">
                <select value={form.district} onChange={(event) => setForm({ ...form, district: event.target.value })}>
                  <option>Krishnagiri</option><option>Dharmapuri</option><option>Salem</option>
                </select>
              </Field>
            </div>
            <Field label="Preferred language">
              <select value={user.language} onChange={(event) => setLanguage(event.target.value as Language)}>
                <option value="en">English</option>
                <option value="hi">हिन्दी (Hindi)</option>
                <option value="kn">ಕನ್ನಡ (Kannada)</option>
              </select>
            </Field>
            <div className="ws-form-actions">
              {saved ? <span className="ws-saved"><Icon name="check" size={15} /> Profile saved</span> : <span />}
              <button type="submit" className="ws-button ws-button-primary">Save changes</button>
            </div>
          </form>
        </section>

        <div className="ws-stack">
          <section className="ws-panel">
            <div className="ws-panel-head"><h2>Farm memberships</h2><Link href="/farms" className="ws-link">All farms</Link></div>
            <ul className="ws-membership-list">
              {state.farms.map((farm) => (
                <li key={farm.id}>
                  <span className="ws-crop-icon"><Icon name="farm" size={17} /></span>
                  <div><strong>{farm.name}</strong><span className="ws-small ws-muted">{farm.village} · {farm.areaAcres} acres</span></div>
                  <Badge tone={farm.ownerId === user.id ? "brand" : "neutral"}>{farm.ownerId === user.id ? "Owner" : "Member"}</Badge>
                </li>
              ))}
            </ul>
          </section>

          <section className="ws-panel">
            <div className="ws-panel-head"><h2>Demo role</h2><Badge tone="info">RBAC preview</Badge></div>
            <p className="ws-small ws-muted">Switch roles to preview permissions. In production, roles are assigned by an administrator and enforced by the API.</p>
            <div className="ws-role-switch">
              {(Object.keys(ROLE_LABEL) as Role[]).map((option) => (
                <button key={option} type="button" className={role === option ? "ws-role-chip ws-role-chip-active" : "ws-role-chip"} onClick={() => setRole(option)}>
                  {ROLE_LABEL[option]}
                  {role === option ? <Icon name="check" size={14} /> : null}
                </button>
              ))}
            </div>
            <Link href="/login" className="ws-button ws-button-secondary ws-button-block ws-mt">
              <Icon name="logout" size={16} /> Switch account
            </Link>
          </section>

          <section className="ws-panel">
            <div className="ws-panel-head"><h2>Account status</h2></div>
            <dl className="ws-detail-list">
              <div><dt>Mobile verified</dt><dd><Badge tone="ok">Yes</Badge></dd></div>
              <div><dt>Data consent</dt><dd>Granted 14 Feb 2026</dd></div>
              <div><dt>Notifications</dt><dd>In-app + review updates</dd></div>
              <div><dt>Data location</dt><dd>This device (demo)</dd></div>
            </dl>
            <Link href="/help" className="ws-link">Privacy and data use <Icon name="arrow" size={13} /></Link>
          </section>
        </div>
      </div>
    </div>
  );
}
