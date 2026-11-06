"use client";

/**
 * Admin dashboard for the identity slice (spec 03).
 *
 * This surface talks only to real backend endpoints: staff login + MFA
 * (`/v1/auth/login`, `/v1/auth/mfa/verify`), the caller's profile
 * (`/v1/me`) and the identity admin routes (`/v1/admin/users*`,
 * `/v1/admin/maintenance/retention`, `/v1/admin/exports`). It never
 * fabricates users, counts or audit events — every number is computed
 * from the list the server returned, and every admin action is audited
 * server-side with the recorded reason.
 *
 * Two deliberate limits are stated on the page, not hidden:
 * - Identity is in-memory and resets when the backend restarts. This
 *   dashboard never claims durable identity.
 * - The core DB admin surfaces (`/v1/admin/alerts/*`,
 *   `/v1/admin/forecasts/*`, `/v1/admin/models*`, `/v1/admin/config`)
 *   need DB-backed tokens that no public endpoint issues, so they are
 *   marked "not connected" here rather than simulated.
 *
 * Tokens live in `sessionStorage` (see `@/lib/auth`). There is no
 * httpOnly cookie in this scaffold; production must move off
 * sessionStorage before exposing this surface beyond local development.
 */

import { useCallback, useEffect, useState } from "react";

import {
  ApiError,
  exportAggregates,
  getAdminUser,
  getHealth,
  getProfile,
  listAdminUsers,
  loginStaff,
  logoutSession,
  provisionStaff,
  refreshTokens,
  runRetention,
  updateAdminRoles,
  updateAdminStatus,
  verifyMfa,
  type AdminExportSummary,
  type AdminUserDetail,
  type Health,
  type Role,
  type RetentionResult,
  type StaffProvisioned,
  type UserProfile,
  type UserSummary,
} from "@/lib/api";
import { clearSession, readSession, writeSession, type SessionTokens } from "@/lib/auth";

const STAFF_ROLES: Role[] = ["extension_worker", "pathologist", "agronomist", "admin"];
const ALL_ROLES: Role[] = ["farmer", "extension_worker", "pathologist", "agronomist", "admin"];

function errorText(caught: unknown): string {
  if (caught instanceof ApiError) {
    const fieldText = caught.problem?.fields
      .map((item) => `${item.field}: ${item.message}`)
      .join("; ");
    return `${caught.status} ${caught.problem?.code ?? "request_failed"} — ${
      caught.problem?.detail ?? caught.problem?.title ?? "request failed"
    }${fieldText ? ` (${fieldText})` : ""}`;
  }
  return "The API is unreachable. Check that the backend is running and retry.";
}

function isAuthFailure(caught: unknown): boolean {
  return caught instanceof ApiError && caught.status === 401;
}

function formatTime(value: string): string {
  return new Date(value).toLocaleString();
}

export function AdminDashboard() {
  const [session, setSession] = useState<SessionTokens | null>(() => readSession());
  const [phase, setPhase] = useState<"login" | "mfa" | "dashboard">(() =>
    readSession() ? "dashboard" : "login",
  );
  const [health, setHealth] = useState<Health | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [authError, setAuthError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Login form
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  // MFA form
  const [totp, setTotp] = useState("");
  const [challenge, setChallenge] = useState<string | null>(null);
  const [challengeExpiresIn, setChallengeExpiresIn] = useState<number | null>(null);

  // Provision form
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRoles, setNewRoles] = useState<Role[]>(["extension_worker"]);
  const [newMfa, setNewMfa] = useState(true);
  const [newReason, setNewReason] = useState("");
  const [provisioned, setProvisioned] = useState<StaffProvisioned | null>(null);

  // Detail / role / status
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [viewReason, setViewReason] = useState("");
  const [detail, setDetail] = useState<AdminUserDetail | null>(null);
  const [roleEdit, setRoleEdit] = useState<Role[]>([]);
  const [roleReason, setRoleReason] = useState("");
  const [statusEdit, setStatusEdit] = useState<"active" | "disabled">("active");
  const [statusReason, setStatusReason] = useState("");

  // Retention + export
  const [retentionReason, setRetentionReason] = useState("");
  const [retentionResult, setRetentionResult] = useState<RetentionResult | null>(null);
  const [exportPurpose, setExportPurpose] = useState("");
  const [exportResult, setExportResult] = useState<AdminExportSummary | null>(null);

  const withAuth = useCallback(
    async <T,>(task: (accessToken: string) => Promise<T>): Promise<T> => {
      if (!session) throw new ApiError(401, null);
      try {
        return await task(session.accessToken);
      } catch (caught) {
        if (!isAuthFailure(caught)) throw caught;
        // Access tokens live 15 minutes: try one refresh, then retry once.
        const renewed = await refreshTokens(session.refreshToken);
        const next: SessionTokens = {
          accessToken: renewed.access_token,
          refreshToken: renewed.refresh_token,
          userId: renewed.user_id,
          role: renewed.role,
        };
        writeSession(next);
        setSession(next);
        return await task(next.accessToken);
      }
    },
    [session],
  );

  const loadDashboard = useCallback(async () => {
    try {
      const [freshProfile, freshUsers] = await Promise.all([
        withAuth((token) => getProfile(token)),
        withAuth((token) => listAdminUsers(token)),
      ]);
      setProfile(freshProfile);
      setUsers(freshUsers);
      if (!freshProfile.roles.includes("admin")) {
        setError(
          "Signed in, but this token is not an admin. The admin routes require the admin role (403 forbidden). Sign out and use an admin account.",
        );
      } else {
        setError(null);
      }
    } catch (caught) {
      if (isAuthFailure(caught)) {
        clearSession();
        setSession(null);
        setPhase("login");
        setAuthError(
          "Session expired or was revoked. Sign in again to continue (access tokens live 15 minutes).",
        );
        return;
      }
      setError(errorText(caught));
    }
  }, [withAuth]);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  // Data loading runs as an event-driven refresh (after sign-in and after
  // mutations) rather than synchronously in an effect, so no state is set
  // during render/effect paint.
  useEffect(() => {
    if (phase !== "dashboard" || !session) return;
    let cancelled = false;
    (async () => {
      try {
        const [freshProfile, freshUsers] = await Promise.all([
          withAuth((token) => getProfile(token)),
          withAuth((token) => listAdminUsers(token)),
        ]);
        if (cancelled) return;
        setProfile(freshProfile);
        setUsers(freshUsers);
        if (!freshProfile.roles.includes("admin")) {
          setError(
            "Signed in, but this token is not an admin. The admin routes require the admin role (403 forbidden). Sign out and use an admin account.",
          );
        } else {
          setError(null);
        }
      } catch (caught) {
        if (cancelled) return;
        if (isAuthFailure(caught)) {
          clearSession();
          setSession(null);
          setPhase("login");
          setAuthError(
            "Session expired or was revoked. Sign in again to continue (access tokens live 15 minutes).",
          );
          return;
        }
        setError(errorText(caught));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [phase, session, withAuth]);

  function selectUser(user: UserSummary) {
    setSelectedId(user.user_id);
    setDetail(null);
    setRoleEdit(user.roles.filter((role) => STAFF_ROLES.includes(role)));
    setRoleReason("");
    setStatusReason("");
    setStatusEdit(user.status === "active" ? "active" : "disabled");
  }

  async function submitLogin(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setAuthError(null);
    setError(null);
    try {
      const response = await loginStaff(email.trim(), password);
      setPassword("");
      if (response.mfa_required) {
        if (!response.challenge_token) {
          setAuthError("The server requested MFA but returned no challenge.");
          setPhase("login");
          return;
        }
        setChallenge(response.challenge_token);
        setChallengeExpiresIn(response.challenge_expires_in);
        setTotp("");
        setPhase("mfa");
        return;
      }
      if (!response.tokens) {
        setAuthError("The server returned no tokens.");
        setPhase("login");
        return;
      }
      const next: SessionTokens = {
        accessToken: response.tokens.access_token,
        refreshToken: response.tokens.refresh_token,
        userId: response.tokens.user_id,
        role: response.tokens.role,
      };
      writeSession(next);
      setSession(next);
      setPhase("dashboard");
    } catch (caught) {
      setAuthError(errorText(caught));
      setPassword("");
    } finally {
      setBusy(false);
    }
  }

  async function submitMfa(event: React.FormEvent) {
    event.preventDefault();
    if (!challenge) return;
    setBusy(true);
    setAuthError(null);
    try {
      const tokens = await verifyMfa(challenge, totp.trim());
      setChallenge(null);
      setTotp("");
      const next: SessionTokens = {
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        userId: tokens.user_id,
        role: tokens.role,
      };
      writeSession(next);
      setSession(next);
      setPhase("dashboard");
    } catch (caught) {
      setAuthError(errorText(caught));
      setTotp("");
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    setBusy(true);
    try {
      if (session) {
        try {
          await logoutSession(session.accessToken);
        } catch {
          // Best effort: still clear the browser session if the API is gone.
        }
      }
    } finally {
      clearSession();
      setSession(null);
      setProfile(null);
      setUsers([]);
      setDetail(null);
      setSelectedId(null);
      setProvisioned(null);
      setRetentionResult(null);
      setExportResult(null);
      setNotice(null);
      setPhase("login");
      setBusy(false);
    }
  }

  function backToLogin() {
    clearSession();
    setSession(null);
    setChallenge(null);
    setPhase("login");
  }

  async function submitProvision(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const created = await withAuth((token) =>
        provisionStaff(token, {
          email: newEmail.trim(),
          password: newPassword,
          roles: newRoles,
          require_mfa: newMfa,
          reason: newReason,
        }),
      );
      setProvisioned(created);
      setNewEmail("");
      setNewPassword("");
      setNewReason("");
      await loadDashboard();
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setBusy(false);
    }
  }

  async function viewUser(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedId) return;
    setBusy(true);
    setError(null);
    try {
      const row = await withAuth((token) => getAdminUser(token, selectedId, viewReason));
      setDetail(row);
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setBusy(false);
    }
  }

  async function submitRoles(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedId) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await withAuth((token) => updateAdminRoles(token, selectedId, roleEdit, roleReason));
      setRoleReason("");
      setNotice("Roles updated. Every active session for this user is superseded.");
      await loadDashboard();
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setBusy(false);
    }
  }

  async function submitStatus(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedId) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await withAuth((token) =>
        updateAdminStatus(token, selectedId, statusEdit, statusReason),
      );
      setStatusReason("");
      setNotice(statusEdit === "disabled" ? "Account disabled." : "Account re-enabled.");
      await loadDashboard();
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setBusy(false);
    }
  }

  async function submitRetention(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await withAuth((token) => runRetention(token, retentionReason));
      setRetentionResult(result);
      setRetentionReason("");
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setBusy(false);
    }
  }

  async function submitExport(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await withAuth((token) => exportAggregates(token, exportPurpose));
      setExportResult(result);
      setExportPurpose("");
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setBusy(false);
    }
  }

  function toggleRole(list: Role[], role: Role): Role[] {
    return list.includes(role) ? list.filter((item) => item !== role) : [...list, role];
  }

  const selected = users.find((item) => item.user_id === selectedId) ?? null;
  const activeCount = users.filter((item) => item.status === "active").length;
  const adminCount = users.filter((item) => item.roles.includes("admin")).length;
  const mfaCount = users.filter((item) => item.mfa_enabled).length;

  if (phase === "login") {
    return (
      <div className="page">
        <header className="page-header">
          <p className="eyebrow">Admin</p>
          <h1>Admin sign-in</h1>
          <p className="page-lede">
            Staff accounts sign in with email and password. Admin, pathologist
            and agronomist roles also require a 6-digit authenticator code.
            Farmer accounts sign in with phone OTP elsewhere and cannot open
            this surface.
          </p>
        </header>

        <p className="notice notice-warning small">
          <span className="badge badge-muted">identity slice</span> Accounts are
          held in memory by the backend and reset on restart. The first admin
          comes from the backend bootstrap variables (see
          <code>backend/.env.example</code>). Tokens stay in this tab&apos;s
          session storage and live 15 minutes.
        </p>

        {authError ? (
          <div className="error" role="alert">
            <p>{authError}</p>
          </div>
        ) : null}

        <form className="card admin-form" onSubmit={(event) => void submitLogin(event)}>
          <h2>Staff sign-in</h2>
          <div className="admin-field">
            <label htmlFor="admin-email">Email</label>
            <input
              id="admin-email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              disabled={busy}
            />
          </div>
          <div className="admin-field">
            <label htmlFor="admin-password">Password</label>
            <input
              id="admin-password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              disabled={busy}
            />
          </div>
          <button type="submit" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
          <p className="small muted">
            Wrong passwords are counted server-side; repeated failures lock the
            account. The API never reveals whether an email exists beyond the
            generic failure message.
          </p>
        </form>
      </div>
    );
  }

  if (phase === "mfa") {
    return (
      <div className="page">
        <header className="page-header">
          <p className="eyebrow">Admin</p>
          <h1>Authenticator code</h1>
          <p className="page-lede">
            Enter the 6-digit code from the authenticator enrolled for this
            account. The challenge is single-step and expires in{" "}
            {challengeExpiresIn ?? "under 5"} seconds — request a new sign-in if
            it lapses.
          </p>
        </header>

        {authError ? (
          <div className="error" role="alert">
            <p>{authError}</p>
          </div>
        ) : null}

        <form className="card admin-form" onSubmit={(event) => void submitMfa(event)}>
          <h2>Two-factor verification</h2>
          <div className="admin-field">
            <label htmlFor="admin-totp">6-digit code</label>
            <input
              id="admin-totp"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              pattern="[0-9]{6}"
              required
              value={totp}
              onChange={(event) => setTotp(event.target.value.replace(/[^0-9]/g, "").slice(0, 6))}
              disabled={busy}
            />
          </div>
          <div className="chip-row">
            <button type="submit" disabled={busy}>
              {busy ? "Verifying…" : "Verify"}
            </button>
            <button
              type="button"
              className="button-secondary"
              onClick={backToLogin}
              disabled={busy}
            >
              Back to sign-in
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Admin</p>
        <h1>Admin dashboard</h1>
        <p className="page-lede">
          Real identity data from the backend — staff provisioning, role and
          status changes, aggregate exports and credential retention. Every
          admin view and change is audited server-side with its recorded
          reason.
        </p>
      </header>

      <p className="notice notice-warning small">
        <span className="badge badge-muted">in-memory</span> Accounts reset
        when the backend restarts. Phone numbers are always shown masked;
        staff emails are staff contact data. Access tokens live 15 minutes and
        refresh automatically once — after that, sign in again.
      </p>

      {error ? (
        <div className="error" role="alert">
          <p>{error}</p>
        </div>
      ) : null}
      {notice ? (
        <div className="notice" role="status">
          <p>{notice}</p>
        </div>
      ) : null}

      <section aria-labelledby="session-heading" className="card">
        <div className="panel-header">
          <h2 id="session-heading">Signed in</h2>
          <button
            type="button"
            className="button-secondary"
            disabled={busy}
            onClick={() => void signOut()}
          >
            Sign out
          </button>
        </div>
        {profile ? (
          <dl className="admin-meta small">
            <div>
              <dt>Identity</dt>
              <dd className="mono">{profile.email ?? profile.user_id}</dd>
            </div>
            <div>
              <dt>Active role</dt>
              <dd>
                {profile.roles[0] ?? "none"} · roles: {profile.roles.join(", ") || "none"}
              </dd>
            </div>
            <div>
              <dt>User id</dt>
              <dd className="mono">{profile.user_id}</dd>
            </div>
            <div>
              <dt>MFA</dt>
              <dd>{profile.mfa_enabled ? "enabled" : "not enabled"}</dd>
            </div>
          </dl>
        ) : (
          <p className="small muted">Loading profile…</p>
        )}
      </section>

      <section aria-labelledby="system-heading" className="card">
        <div className="panel-header">
          <h2 id="system-heading">System</h2>
          <span className="badge badge-muted">liveness only</span>
        </div>
        {health ? (
          <dl className="admin-meta small">
            <div>
              <dt>Service</dt>
              <dd className="mono">
                {health.service} {health.version} ({health.environment})
              </dd>
            </div>
            <div>
              <dt>Checked</dt>
              <dd>
                <time dateTime={health.time}>{formatTime(health.time)}</time>
              </dd>
            </div>
          </dl>
        ) : (
          <p className="small muted">API unreachable, so no liveness state can be confirmed.</p>
        )}
        <p className="small muted">
          There is no readiness probe in this build: <code>/health</code> reports
          process liveness only and does not check the database, storage or
          model services.
        </p>
      </section>

      <section aria-labelledby="counts-heading" className="card">
        <div className="panel-header">
          <h2 id="counts-heading">Account counts</h2>
          <span className="badge">{users.length} total</span>
        </div>
        <p className="small muted">
          {activeCount} active · {adminCount} with admin role · {mfaCount} with
          MFA enabled. Counts are computed from the returned list — the server
          does not publish a separate aggregate until an export is requested.
        </p>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th scope="col">Role</th>
                <th scope="col">Accounts</th>
              </tr>
            </thead>
            <tbody>
              {ALL_ROLES.map((role) => (
                <tr key={role}>
                  <td>{role}</td>
                  <td>{users.filter((item) => item.roles.includes(role)).length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section aria-labelledby="users-heading" className="card">
        <div className="panel-header">
          <h2 id="users-heading">Accounts</h2>
          <button
            type="button"
            className="button-secondary"
            disabled={busy}
            onClick={() => void loadDashboard()}
          >
            Refresh
          </button>
        </div>
        {users.length === 0 ? (
          <p className="small muted">No accounts returned by the server.</p>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th scope="col">Account</th>
                  <th scope="col">Kind</th>
                  <th scope="col">Roles</th>
                  <th scope="col">Status</th>
                  <th scope="col">MFA</th>
                  <th scope="col">Updated</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.user_id}>
                    <td className="mono">{user.email ?? user.phone_masked ?? user.user_id}</td>
                    <td>{user.kind}</td>
                    <td>{user.roles.join(", ") || "none"}</td>
                    <td>{user.status}</td>
                    <td>{user.mfa_enabled ? "on" : "off"}</td>
                    <td>
                      <time dateTime={user.updated_at}>{formatTime(user.updated_at)}</time>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="button-secondary"
                        onClick={() => selectUser(user)}
                      >
                        Manage
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selected ? (
        <section aria-labelledby="detail-heading" className="card">
          <div className="panel-header">
            <h2 id="detail-heading">Manage account</h2>
            <span className="badge badge-muted">{selected.user_id}</span>
          </div>
          <p className="small muted">
            {selected.kind} · {selected.status} · roles: {selected.roles.join(", ") || "none"}
          </p>

          <form className="admin-form" onSubmit={(event) => void viewUser(event)}>
            <h3>View record (audited)</h3>
            <div className="admin-field">
              <label htmlFor="view-reason">Reason for viewing (min 8 characters)</label>
              <input
                id="view-reason"
                type="text"
                required
                minLength={8}
                maxLength={500}
                value={viewReason}
                onChange={(event) => setViewReason(event.target.value)}
                disabled={busy}
              />
            </div>
            <button type="submit" disabled={busy}>
              {busy ? "Loading…" : "View record"}
            </button>
          </form>

          {detail ? (
            <dl className="admin-meta small">
              <div>
                <dt>Last login</dt>
                <dd>
                  {detail.last_login_at ? (
                    <time dateTime={detail.last_login_at}>{formatTime(detail.last_login_at)}</time>
                  ) : (
                    "never"
                  )}
                </dd>
              </div>
              <div>
                <dt>Consent complete</dt>
                <dd>{detail.consent_complete === null ? "n/a" : detail.consent_complete ? "yes" : "no"}</dd>
              </div>
              <div>
                <dt>Active consents</dt>
                <dd>{detail.active_consents.join(", ") || "none"}</dd>
              </div>
              <div>
                <dt>Masked phone</dt>
                <dd className="mono">{detail.phone_masked ?? "n/a"}</dd>
              </div>
            </dl>
          ) : null}

          <form className="admin-form" onSubmit={(event) => void submitRoles(event)}>
            <h3>Change staff roles</h3>
            <fieldset className="admin-fieldset">
              <legend>Staff roles (farmers cannot be promoted here)</legend>
              {STAFF_ROLES.map((role) => (
                <label key={role} className="admin-check">
                  <input
                    type="checkbox"
                    checked={roleEdit.includes(role)}
                    onChange={() => setRoleEdit(toggleRole(roleEdit, role))}
                    disabled={busy}
                  />
                  {role}
                </label>
              ))}
            </fieldset>
            <div className="admin-field">
              <label htmlFor="role-reason">Reason (min 8 characters)</label>
              <input
                id="role-reason"
                type="text"
                required
                minLength={8}
                maxLength={500}
                value={roleReason}
                onChange={(event) => setRoleReason(event.target.value)}
                disabled={busy}
              />
            </div>
            <button type="submit" disabled={busy}>
              {busy ? "Saving…" : "Update roles"}
            </button>
            <p className="small muted">
              Role changes bump the token version and supersede active sessions.
              You cannot change your own roles, and the last active admin cannot
              be removed.
            </p>
          </form>

          <form className="admin-form" onSubmit={(event) => void submitStatus(event)}>
            <h3>Enable / disable</h3>
            <div className="admin-field">
              <label htmlFor="status-select">Status</label>
              <select
                id="status-select"
                value={statusEdit}
                onChange={(event) => setStatusEdit(event.target.value as "active" | "disabled")}
                disabled={busy}
              >
                <option value="active">active</option>
                <option value="disabled">disabled</option>
              </select>
            </div>
            <div className="admin-field">
              <label htmlFor="status-reason">Reason (min 8 characters)</label>
              <input
                id="status-reason"
                type="text"
                required
                minLength={8}
                maxLength={500}
                value={statusReason}
                onChange={(event) => setStatusReason(event.target.value)}
                disabled={busy}
              />
            </div>
            <button type="submit" disabled={busy}>
              {busy ? "Saving…" : "Update status"}
            </button>
            <p className="small muted">
              Staff accounts only. Disabling revokes all sessions for the
              account. You cannot disable yourself, and the last active admin
              cannot be disabled.
            </p>
          </form>
        </section>
      ) : null}

      <section aria-labelledby="provision-heading" className="card">
        <div className="panel-header">
          <h2 id="provision-heading">Provision staff</h2>
          <span className="badge badge-muted">staff only</span>
        </div>
        <form className="admin-form" onSubmit={(event) => void submitProvision(event)}>
          <div className="admin-field">
            <label htmlFor="new-email">Staff email</label>
            <input
              id="new-email"
              type="email"
              autoComplete="off"
              required
              value={newEmail}
              onChange={(event) => setNewEmail(event.target.value)}
              disabled={busy}
            />
          </div>
          <div className="admin-field">
            <label htmlFor="new-password">Initial password (min 12 characters)</label>
            <input
              id="new-password"
              type="password"
              autoComplete="new-password"
              required
              minLength={12}
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              disabled={busy}
            />
          </div>
          <fieldset className="admin-fieldset">
            <legend>Roles</legend>
            {STAFF_ROLES.map((role) => (
              <label key={role} className="admin-check">
                <input
                  type="checkbox"
                  checked={newRoles.includes(role)}
                  onChange={() => setNewRoles(toggleRole(newRoles, role))}
                  disabled={busy}
                />
                {role}
              </label>
            ))}
          </fieldset>
          <label className="admin-check">
            <input
              type="checkbox"
              checked={newMfa}
              onChange={(event) => setNewMfa(event.target.checked)}
              disabled={busy}
            />
            Require MFA (always required for pathologist, agronomist and admin)
          </label>
          <div className="admin-field">
            <label htmlFor="new-reason">Reason (min 8 characters)</label>
            <input
              id="new-reason"
              type="text"
              required
              minLength={8}
              maxLength={500}
              value={newReason}
              onChange={(event) => setNewReason(event.target.value)}
              disabled={busy}
            />
          </div>
          <button type="submit" disabled={busy}>
            {busy ? "Provisioning…" : "Provision staff"}
          </button>
        </form>

        {provisioned ? (
          <div className="admin-result" role="status">
            <p>
              <strong>Created {provisioned.user.email ?? provisioned.user.user_id}</strong> —
              roles: {provisioned.user.roles.join(", ")}. The MFA secret below is
              shown once and is never retrievable later.
            </p>
            {provisioned.mfa_secret ? (
              <>
                <p className="small">
                  Authenticator secret: <code className="mono">{provisioned.mfa_secret}</code>
                </p>
                {provisioned.otpauth_uri ? (
                  <p className="small muted">
                    otpauth URI: <code className="mono">{provisioned.otpauth_uri}</code>
                  </p>
                ) : null}
              </>
            ) : (
              <p className="small muted">No MFA secret was generated for this account.</p>
            )}
            <button
              type="button"
              className="button-secondary"
              onClick={() => setProvisioned(null)}
            >
              Dismiss (secret hidden)
            </button>
          </div>
        ) : null}
      </section>

      <section aria-labelledby="maintenance-heading" className="card">
        <div className="panel-header">
          <h2 id="maintenance-heading">Retention &amp; exports</h2>
        </div>
        <form className="admin-form" onSubmit={(event) => void submitRetention(event)}>
          <h3>Purge expired credentials</h3>
          <div className="admin-field">
            <label htmlFor="retention-reason">Reason (min 8 characters)</label>
            <input
              id="retention-reason"
              type="text"
              required
              minLength={8}
              maxLength={500}
              value={retentionReason}
              onChange={(event) => setRetentionReason(event.target.value)}
              disabled={busy}
            />
          </div>
          <button type="submit" disabled={busy}>
            {busy ? "Running…" : "Run retention"}
          </button>
          {retentionResult ? (
            <p className="small" role="status">
              Removed {retentionResult.expired_otp_challenges} OTP challenges and{" "}
              {retentionResult.expired_refresh_tokens} refresh tokens.{" "}
              <span className="muted">{retentionResult.note}</span>
            </p>
          ) : null}
        </form>

        <form className="admin-form" onSubmit={(event) => void submitExport(event)}>
          <h3>Aggregate export</h3>
          <div className="admin-field">
            <label htmlFor="export-purpose">Purpose (min 8 characters)</label>
            <input
              id="export-purpose"
              type="text"
              required
              minLength={8}
              maxLength={500}
              value={exportPurpose}
              onChange={(event) => setExportPurpose(event.target.value)}
              disabled={busy}
            />
          </div>
          <button type="submit" disabled={busy}>
            {busy ? "Exporting…" : "Export aggregates"}
          </button>
          {exportResult ? (
            <div className="admin-result" role="status">
              <p className="small">
                {exportResult.total_users} accounts · exported{" "}
                <time dateTime={exportResult.exported_at}>
                  {formatTime(exportResult.exported_at)}
                </time>{" "}
                (limit {exportResult.row_limit}).
              </p>
              <dl className="admin-meta small">
                <div>
                  <dt>By role</dt>
                  <dd>{Object.entries(exportResult.counts_by_role).map(([role, count]) => `${role}: ${count}`).join(" · ")}</dd>
                </div>
                <div>
                  <dt>By status</dt>
                  <dd>{Object.entries(exportResult.counts_by_status).map(([status, count]) => `${status}: ${count}`).join(" · ")}</dd>
                </div>
              </dl>
              <p className="small muted">{exportResult.note}</p>
            </div>
          ) : null}
        </form>
      </section>

      <section aria-labelledby="gaps-heading" className="card">
        <div className="panel-header">
          <h2 id="gaps-heading">Not connected here</h2>
          <span className="badge badge-muted">honest gaps</span>
        </div>
        <ul className="small">
          <li>
            Forecast, model-registry, config and alert-policy admin routes need
            database-backed tokens with no issuer endpoint. This dashboard does
            not call them and never simulates their counts.
          </li>
          <li>
            The demo photo-assessment chat still uses a single demo owner and
            is not per-user authenticated. Admin actions here do not change
            that.
          </li>
          <li>
            Password reset, session lists, device binding and durable identity
            storage are not built. Identity resets when the backend restarts.
          </li>
        </ul>
      </section>
    </div>
  );
}
