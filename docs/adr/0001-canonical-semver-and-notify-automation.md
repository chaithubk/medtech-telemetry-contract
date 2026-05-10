# ADR 0001: Canonical Schema Versioning and Automated Consumer Notification

- Status: Accepted
- Date: 2026-05-10
- Deciders: Contract maintainers

## Context

The repository previously used version-per-file contract paths (for example, `v2.0`, `v2.1`).
That model made maintenance harder as versions grew and created friction in consumer pinning,
governance checks, and release automation.

We also needed a reliable way to notify downstream consumer repositories on release, and a safe
way to test that notification flow without publishing real GitHub Releases/release notes.

## Decision

1. Adopt one canonical schema path per domain on main (for vitals: `schemas/vitals/vitals.schema.json`).
2. Use Git tags/GitHub Releases as the immutable version record (`vMAJOR.MINOR.PATCH`).
3. Enforce SemVer/changelog governance in CI with `scripts/compatibility_guard.py`.
4. Automate downstream notification in `.github/workflows/notify-consumers-on-release.yml`:
   - Production path: trigger on `release.published` and dispatch `contract-release-published` to consumers.
   - Test path: allow `workflow_dispatch` with `test_tag` and `dry_run` inputs.
5. Enable release workflow test mode in `.github/workflows/release.yml`:
   - `test_mode=true` skips governance gate, tag push, and GitHub Release creation.
   - `test_mode=true` still triggers notify workflow with real dispatch behavior (`dry_run=false`) to mirror production notification flow.

## Consequences

- Positive:
  - Versioning is simpler and cleaner for maintainers and consumers.
  - Immutable contract versions are explicit and auditable via tags/releases.
  - Consumer notification is automatic for real releases.
  - Notification flow can be tested end-to-end without creating real release notes.

- Trade-offs:
  - Test mode does not execute the exact `release.published` event path; it uses a workflow-dispatch simulation with equivalent dispatch payload semantics.
  - Release governance checks are intentionally skipped in `test_mode=true` to avoid forced version bumps during dispatch testing.

## Operational Notes

- Use normal release mode for production publishing.
- Use `test_mode=true` only to validate workflow wiring and downstream dispatch behavior.
- If governance behavior must also be validated, run the guard directly (or in a non-test release run).
