# 03 — Auth, roles and consent

**Status:** Draft
**Owner:** Backend lead (TBD)
**Depends on:** `05-data-layer.md`
**Implements:** identity, session management, role-based access, consent capture, privacy
requests.

---

## 1. Goal

Ensure that only the right people can see or change the right records, that consent is
explicit and auditable, and that no farmer can ever read another farmer's case.

Three roles only in v1 (ADR-010). Confirmation is gated by the scoped `can_confirm`
permission rather than a fourth role. More granular permissions are deferred until an
operational need is demonstrated.

---

## 2. Roles

| Role | Description | Default surface |
|---|---|---|
| `farmer` | Field user who submits reports and reads advisories | Mobile |
| `extension_worker` | Verifies reports, captures on behalf of farmers, shares advisories | Mobile + expert portal |
| `admin` | Configuration, users, thresholds, exports, audit | District dashboard |

Two **scoped permissions** replace the former `pathologist` role:

| Permission | Grants | Granted by |
|---|---|---|
| `can_confirm` | Set verification state `confirmed`; correct labels | Admin, audited |
| `can_approve_advisory` | Approve advisory content (second approver for high-risk content) | Admin, audited |

Rules:

- One user may hold multiple roles (e.g. extension worker + admin), but the active role is
  explicit in the session and shown in the UI.
- There is **no public self-registration** for `extension_worker` or `admin`. They are
  provisioned by an admin or partner onboarding.
- `farmer` accounts may self-register via phone OTP.
- Role and permission changes are audited and take effect on the next token refresh, not
  silently mid-session.

---

## 3. Permission matrix

`own` = records the user created; `area` = records within assigned administrative units;
`all` = all records.

| Capability | farmer | extension_worker | admin |
|---|---|---|---|
| Create observation | own | own + on-behalf | no |
| Read observation | own | area | all (audited) |
| Upload image | own | own + on-behalf | no |
| Request review | own | area | no |
| Read own assessment | own | own | — |
| Read queue | no | area | all |
| Assign case | no | self only | all |
| Set verification status | no | area (probable/needs_visit/duplicate/unresolved); `can_confirm` required for confirmed | no |
| Correct label | no | `can_confirm` only | no |
| Approve advisory | no | `can_approve_advisory` only | no |
| Manage crops/targets/areas | no | no | yes |
| Manage users/roles | no | no | yes |
| Configure thresholds/alert policy | no | no | yes (requires second approver) |
| Grant `can_confirm` / `can_approve_advisory` | no | no | yes (audited) |
| View map layers | own area summary | area | all |
| Export aggregates | no | no | yes (audited) |
| Read audit log | no | no | yes |
| Delete own account | yes | yes | yes (via admin) |

Notes:

- `confirmed` requires the `can_confirm` permission **and** at least one evidence item.
- Extension workers can record `probable`, `needs_visit`, `duplicate` and `unresolved`
  without the permission; they escalate for confirmation.
- Admin cannot verify cases (separation of duties).
- `can_confirm` and `can_approve_advisory` are permissions, not roles; every grant and every
  use is audited.
- Export requires a written purpose field and is audited.

---

## 4. Authentication flows

### 4.1 Farmer — phone OTP

```
enter phone → POST /v1/auth/otp/request
  → rate limit per phone + IP
  → send 6-digit code (SMS), TTL 5 min, max 5 attempts
  → POST /v1/auth/otp/verify {phone, code, device_id}
  → access token (15 min) + refresh token (30 days, rotating)
  → if new user: consent screen before any report
```

- Codes are stored hashed; never logged.
- Enumeration-safe responses: always "if this number is registered, a code was sent".
- No password for farmers.
- Optional device binding: a new device requires OTP again; existing sessions remain until
  revoked.

### 4.2 Staff — email + password + MFA

```
POST /v1/auth/login {email, password}
  → if MFA enabled: short-lived challenge token
  → POST /v1/auth/mfa/verify {challenge, totp}
  → access + refresh tokens
```

- Passwords hashed with Argon2id.
- MFA (TOTP) is **required** for `admin` and strongly recommended for `can_confirm`
  holders; recommended for all `extension_worker` accounts.
- Lockout after 10 failed attempts in 15 minutes; unlock via admin.
- Password reset via emailed single-use token (30 min TTL), never reveals account existence.

### 4.3 Tokens

| Token | TTL | Storage | Notes |
|---|---|---|---|
| Access | 15 min | memory / secure storage | JWT with `sub`, `role`, `session_id`, `exp` |
| Refresh | 30 days | secure storage (mobile), httpOnly cookie (web) | Rotating, single-use, reuse detection revokes the family |
| MFA challenge | 5 min | memory | Cannot access any other route |

- Logout revokes the refresh family; "log out all devices" revokes all families for the user.
- Role changes increment a `token_version`; old tokens are rejected on refresh.
- No secrets in tokens beyond identifiers and role.

---

## 5. Consent

Consent is captured before the first report and re-confirmed when the consent version
changes.

| Consent | Required | Plain-language summary |
|---|---|---|
| Service terms + privacy | Yes | What we collect, why, retention, who sees it |
| Image use for assessment | Yes | Photo is analysed and stored with the case |
| Approximate location | Yes | Block-level area, not exact farm coordinates |
| Optional research / model improvement | No | Separately opt-in, revocable, never bundled |
| Optional contact by extension worker | No | For follow-up on a case |

Rules:

- Consent records store: user_id, consent_type, version, granted/revoked, timestamp,
  channel, and the exact text hash shown.
- Withdrawal is as easy as granting; it stops future processing but does not delete
  historical records unless a deletion request is made.
- Optional research consent must not gate core functionality.
- Consent text is versioned; changing it requires re-consent before the next submission.

---

## 6. Authorisation enforcement

- Route-level role dependency on every endpoint; deny by default.
- Object-level checks for farmer resources: `observation.user_id == current_user.id`.
- Area-scoped checks for staff: assignment table (`user_area_assignments`) joined in the
  query, not filtered after fetch.
- Admin access to individual farmer records requires a reason and writes an audit event
  **before** returning data.
- Exports: role check + purpose + row-limit + audit; no PII columns.
- Tests must prove 403/404 for cross-user and cross-area access, not just 200 for the
  happy path.

---

## 7. Privacy requests

| Request | Behaviour |
|---|---|
| Access / export own data | Machine-readable export within a documented SLA |
| Correct own profile | Self-service |
| Delete account | Soft-delete + schedule hard delete per retention policy; queued reports must be resolved or explicitly discarded first |
| Withdraw optional consent | Immediate for future processing; audited |
| Object to processing | Route to programme owner; documented response |

Retention:

- Images and case records: per programme policy (set with legal; not fixed here).
- Audit events: longer than case data, immutable.
- OTP codes, sessions, signed URLs: short TTL.
- Backups: documented rotation; deletion propagates on the next restore cycle.

---

## 8. API touchpoints

| Method | Path | Auth |
|---|---|---|
| `POST` | `/v1/auth/otp/request` | public, rate-limited |
| `POST` | `/v1/auth/otp/verify` | public, rate-limited |
| `POST` | `/v1/auth/login` | public, rate-limited |
| `POST` | `/v1/auth/mfa/verify` | challenge token |
| `POST` | `/v1/auth/refresh` | refresh token |
| `POST` | `/v1/auth/logout` | authenticated |
| `POST` | `/v1/auth/logout-all` | authenticated |
| `GET` | `/v1/me` | authenticated |
| `GET` | `/v1/me/consents` | authenticated |
| `POST` | `/v1/me/consents` | authenticated |
| `DELETE` | `/v1/me` | authenticated + confirmation |
| `GET` | `/v1/admin/users` | admin |
| `PATCH` | `/v1/admin/users/{id}/roles` | admin, audited |

Error codes: `invalid_credentials`, `mfa_required`, `otp_expired`, `otp_rate_limited`,
`consent_required`, `forbidden`, `account_locked`, `token_reused`.

---

## 9. Edge cases

| Case | Behaviour |
|---|---|
| OTP requested repeatedly | Rate limit per phone/IP; exponential backoff; no account enumeration |
| Phone number recycled by carrier | Re-verification + support path; do not merge histories silently |
| Refresh token reuse | Revoke entire family; force re-login; audit |
| Role removed mid-session | Access token expires within 15 min; refresh rejected immediately |
| Staff leaves programme | Admin disables account; sessions revoked; assignments reassigned |
| Farmer loses device | "Log out all devices" from another session or support-assisted |
| Consent version changed | Block new submissions until re-consent; existing cases readable |
| Admin views a case | Reason required; audit event written before response |
| Extension worker assigned to two areas | Active area selector; queries scoped to selected area |

---

## 10. Acceptance criteria

- [ ] A farmer can register and log in with phone OTP; codes expire and are rate-limited.
- [ ] A farmer cannot read another farmer's observation (403/404) — tested.
- [ ] An extension worker without `can_confirm` cannot set `confirmed`; one with it can —
      tested.
- [ ] An admin cannot set verification status — tested.
- [ ] MFA is enforced for `admin` accounts and for `can_confirm` holders.
- [ ] Refresh-token reuse revokes the family and forces re-login.
- [ ] Consent is required before the first report and after a version change.
- [ ] Withdrawing optional research consent does not block reporting.
- [ ] Account deletion requires resolving/discarding queued reports.
- [ ] Every role change, export and admin record view writes an audit event.
- [ ] No endpoint returns farmer PII to an unauthorised role.
- [ ] Passwords, OTPs and tokens never appear in logs.

---

## 11. Audit events

`auth.login_succeeded`, `auth.login_failed`, `auth.mfa_challenged`, `auth.token_refreshed`,
`auth.token_reuse_detected`, `auth.logout_all`, `user.role_changed`, `user.disabled`,
`consent.granted`, `consent.withdrawn`, `privacy.export_requested`, `privacy.deleted`,
`admin.record_viewed`, `export.generated`.

Include actor, target, timestamp, request_id, reason where applicable. Never include
credentials or full phone numbers.

---

## 12. Out of scope

- Social login.
- Organisation-level multi-tenancy.
- Fine-grained per-field permissions.
- Biometric login.
- Self-service role elevation.

---

## 13. Open questions

1. Which SMS provider is available to the pilot partner, and what is the per-message cost?
2. Is a smartphone the only farmer identity, or do feature-phone users need an SMS-only
   account path?
3. Who is the data controller for the pilot — the implementing organisation or the
   agriculture department? Determines consent wording and retention.
4. Is MFA operationally feasible for extension workers, or does it block field use?

---

## 14. Blueprint traceability

| Blueprint chapter | Where this spec uses it |
|---|---|
| 43 — Security architecture | §4 authentication, §6 enforcement, §11 audit |
| 44 — Privacy and responsible AI | §5 consent, §7 privacy requests |
| 16 — Expert review portal | Staff login/MFA states in `ui-context.md` §5 |

Architecture placement of these controls is in
`../docs-context/architecture-context.md` §14. Hard stops on weakening auth, RBAC or audit
are in `../docs-context/AGENTS.md` §8.
