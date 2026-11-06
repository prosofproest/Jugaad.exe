# 03 — Auth, roles and consent

**Status:** Draft — backend §5.2 slice implemented in memory (2026-11-06). Persistence,
retrofitting the existing demo routes, and the D10/D11-dependent behaviour remain open.
**Owner:** Backend lead (TBD)
**Depends on:** `05-data-layer.md`
**Implements:** identity, session management, role-based access, consent capture, privacy
requests.

---

## 1. Goal

Ensure that only the right people can see or change the right records, that consent is
explicit and auditable, and that no farmer can ever read another farmer's case.

Five roles in v1. `agronomist` was added by decision D13 so that advisory content and risk
bands can be approved by a named qualified person, without inventing a second permission
system. It carries no verification rights. More granular permissions are deferred until an
operational need is demonstrated.

---

## 2. Roles

| Role | Description | Default surface |
|---|---|---|
| `farmer` | Field user who submits reports and reads advisories | Mobile |
| `extension_worker` | Verifies reports, captures on behalf of farmers, shares advisories | Mobile + expert portal |
| `pathologist` | Escalation reviewer, taxonomy owner, label correction, advisory approval | Expert portal |
| `agronomist` | Advisory author and second approver, risk-band approval, read-only area visibility. **Cannot** verify cases. | Expert portal |
| `admin` | Configuration, users, thresholds, exports, audit | District dashboard |

Rules:

- One user may hold multiple roles (e.g. extension worker + pathologist), but the active
  role is explicit in the session and shown in the UI.
- There is **no public self-registration** for `extension_worker`, `pathologist`,
  `agronomist` or `admin`. They are provisioned by an admin or partner onboarding.
- `farmer` accounts may self-register via phone OTP.
- `agronomist` exists separately from `pathologist` so that author ≠ approver is achievable
  with two people. One person may hold both roles, but a single account can never both
  author and approve the same advisory (`07-advisory-and-alerts.md` §3).
- `agronomist` cannot set verification status. Confirmation stays pathologist-only, which
  preserves the separation of duties in §3.
- Role changes are audited and take effect on the next token refresh, not silently
  mid-session.

---

## 3. Permission matrix

`own` = records the user created; `area` = records within assigned administrative units;
`all` = all records.

| Capability | farmer | extension_worker | pathologist | agronomist | admin |
|---|---|---|---|---|---|
| Create observation | own | own + on-behalf | no | no | no |
| Read observation | own | area | area + escalated | area (read-only) | all (audited) |
| Upload image | own | own + on-behalf | no | no | no |
| Request review | own | area | no | no | no |
| Record sentinel visit | no | area (scheduled) | area (scheduled) | no | no (manages panel) |
| Read own assessment | own | own | — | — | — |
| Read queue | no | area | area + escalations | area (read-only) | all |
| Assign case | no | self only | area | no | all |
| Set verification status | no | area (probable/needs_visit/duplicate) | area (all states incl. confirmed) | no | no |
| Correct label | no | no | yes | no | no |
| Author advisory | no | no | yes | yes | no |
| Approve advisory | no | no | yes (if not author) | yes (if not author) | no |
| Approve risk bands/thresholds | no | no | no | yes (second approver) | no (proposes only) |
| Manage crops/targets/areas | no | no | no | no | yes |
| Manage users/roles | no | no | no | no | yes |
| Configure thresholds/alert policy | no | no | no | no | yes (requires second approver) |
| View map layers | own area summary | area | area | area | all |
| Export aggregates | no | no | no | no | yes (audited) |
| Read audit log | no | no | no | no | yes |
| Delete own account | yes | yes | yes | yes | yes (via admin) |

Notes:

- `confirmed` requires the `pathologist` role. Extension workers can record `probable`,
  `needs_visit`, `duplicate` and `unresolved`; they escalate for confirmation.
- Admin cannot verify cases (separation of duties).
- `agronomist` cannot verify cases or correct labels. Its write surface is limited to
  advisory content and risk-band approval, which keeps it separate from the evidence path.
- Author ≠ approver is enforced per advisory and per risk-band change, not per role. A user
  holding both `pathologist` and `agronomist` is still blocked from approving their own
  submission; the check is `author_id != approver_id` on the record.
- Admin may propose threshold values but cannot approve its own proposal; the second
  approver must hold `agronomist`.
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
- MFA (TOTP) is **required** for `pathologist`, `agronomist` and `admin`; strongly
  recommended for `extension_worker`.
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
- OTP codes, sessions, presigned URLs: short TTL.
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
- [ ] An extension worker cannot set `confirmed`; a pathologist can — tested.
- [ ] An admin cannot set verification status — tested.
- [ ] An agronomist cannot set verification status or correct a label — tested.
- [ ] A single account holding both `pathologist` and `agronomist` cannot author and approve
      the same advisory — tested.
- [ ] Risk-band and threshold changes cannot be approved by their proposer — tested.
- [ ] MFA is enforced for pathologist, agronomist and admin accounts.
- [ ] Refresh-token reuse revokes the family and forces re-login.
- [ ] Consent is required before the first report and after a version change.
- [ ] Withdrawing optional research consent does not block reporting.
- [ ] Account deletion requires resolving/discarding queued reports.
- [ ] Every role change, export and admin record view writes an audit event.
- [ ] No endpoint returns farmer PII to an unauthorised role.
- [ ] Passwords, OTPs and tokens never appear in logs.

### 10.1 Implementation evidence (2026-11-06)

Implemented in `backend/app/modules/identity/` with routes in `app/api/v1/auth.py`,
`me.py` and `admin.py`. Storage is process-local (see the gap list below), so this is
evidence for the HTTP/service contract, not for durable production behaviour.

Verified by `backend/tests/test_identity_*.py` (64 tests) and the full suite
(`294 passed`):

- Phone OTP registration/sign-in with expiry, attempt caps and per-phone/IP throttling;
  the code never appears in a response or audit detail.
- Provisioned staff accounts only for the four staff roles; farmers self-register.
  `farmer` cannot be assigned by an admin, and staff cannot be promoted to `farmer`.
- Five roles only, deny-by-default dependencies on `/v1/me` and `/v1/admin`, and a
  `403` for a role that is not named on the route.
- Password + TOTP login for staff. `pathologist`, `agronomist` and `admin` cannot be
  assigned without an MFA secret, and their sessions require a TOTP challenge.
- Rotating refresh tokens with reuse detection that revokes the whole family; role and
  status changes invalidate existing sessions.
- Versioned, plain-language consent records capturing version, timestamp, channel and
  text hash; required consent blocks gated actions; optional research consent does not.
- Privacy requests, self-export with a recorded written purpose, soft account deletion
  with queued-report guard, and a credential-only retention job.
- Audited role changes, admin record views (reason required) and exports (purpose
  required), with no full phone numbers, emails, passwords or MFA secrets in details.

**Not yet satisfied (do not read the checklist above as complete):**

- Persistence: there is no SQLAlchemy model or Alembic migration for identity. A process
  restart loses users, sessions, OTPs and consents.
- The existing demo routes (`/v1/conversations`, assessments, advisories, map) are still
  unauthenticated, so the object-level and area-scoping criteria cannot be proven yet.
- D10 is open, so case/image/derived-data retention and hard deletion are not implemented;
  deletion is soft and only schedules `hard_delete_after` when a policy is supplied.
- D11 is open, so on-behalf capture and offline-session semantics are not implemented.
- Real SMS delivery and password reset by email need providers that are not chosen; the
  production OTP adapter fails closed.
- Password hashing uses stdlib `scrypt` instead of the specified Argon2id, to avoid an
  unapproved dependency. This deviation is recorded in the progress tracker.

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
