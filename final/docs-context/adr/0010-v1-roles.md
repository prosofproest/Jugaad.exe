# ADR-010 — v1 roles are farmer, extension_worker and admin

- **Status:** Accepted
- **Date:** 2026-11-06
- **Deciders:** Project owner, Engineering lead
- **Supersedes:** the four-role model in `feature-specs/03-auth-and-roles.md` §2 and the
  `pathologist` role
- **Related:** R4 (human verification), R5 (no chemical advice), ADR-007

---

## Context

The documented model had four roles: `farmer`, `extension_worker`, `pathologist`, `admin`.
The target architecture described only farmer and admin. R4 requires that a human reviewer,
not the model, sets verification status; R5 requires approved, non-chemical advisory
content. A four-role build adds workflow and staffing that a v1 pilot cannot carry, while a
two-role build gives the admin both operations and review duty, which breaks separation of
duties.

## Decision

v1 has exactly **three roles**:

| Role | Purpose |
|---|---|
| `farmer` | Submits reports, uploads images, reads assessments and advisories |
| `extension_worker` | Reviews and verifies reports, captures on behalf of farmers, shares advisories |
| `admin` | Users, roles, crops/targets, thresholds, exports, audit |

Two scoped permissions replace the `pathologist` role:

- **`can_confirm`** — held by designated senior extension workers. Required to set
  verification state `confirmed`. Granted by an admin; every grant and use is audited.
- **`can_approve_advisory`** — held by a designated agronomist or senior extension worker.
  Required to approve advisory content. High-risk content requires a second approver.

Rules preserved:

- Model output is never auto-promoted to verified (R4).
- `admin` does not verify cases (separation of duties); admins grant permissions instead.
- No public self-registration for `extension_worker` or `admin`; they are provisioned.
- One user may hold multiple roles; the active role is explicit in the session.
- Role and permission changes are audited and take effect on the next token refresh.

## Consequences

- `feature-specs/03` permission matrix shrinks to three columns plus the two scoped
  permissions.
- The `pathologist` persona remains in the PRD as an external advisory approver, not as an
  application role.
- The `confirmed` state depends on `can_confirm` being seeded during onboarding; if no
  account holds it, cases stop at `probable` and the UI must say so.
- Onboarding must provision at least one `can_confirm` holder per pilot area.

## Follow-ups

1. Update `feature-specs/03-auth-and-roles.md` §2–3.
2. Update `PRD.md` §4.2 role list.
3. Replace the `pathologist` column in the permission matrix with `can_confirm` /
   `can_approve_advisory` notes.
4. Add permission-grant events to the audit spec.
