# Shared web components

This folder holds shared UI components for the Next.js surfaces (expert review portal and
district dashboard). It is intentionally empty until scaffolding begins.

Rules:

- Components implement the contracts in `../feature-specs/01-design-system.md` and the
  wording/state rules in `../docs-context/ui-context.md`.
- No component may merge photo assessment and area outlook into one visual unit.
- Risk and case status are separate prop namespaces.
- Every component ships with a story/golden for each state in its contract.
- Feature-specific components live beside their route; only genuinely shared components
  belong here.

Surface detail for these components is in `../docs-context/ui-context.md` §12 (farmer app,
expert portal, district dashboard). Approved output wording is in
`../docs-context/appendices.md` (Appendices A and B).

The Flutter equivalents live in `../mobile/lib/ui/components/` once that project exists.
