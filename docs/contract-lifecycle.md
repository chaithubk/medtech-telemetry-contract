# Contract Lifecycle and Governance

## Source of Truth

- Canonical schema path per domain (vitals): `schemas/vitals/vitals.schema.json`
- Immutable versions: Git tags and GitHub Releases (`vMAJOR.MINOR.PATCH`)
- Human-readable change history: `CHANGELOG.md`

## Versioning Policy

This repository follows SemVer:

- `MAJOR`: breaking contract changes
- `MINOR`: backward-compatible contract additions/relaxations
- `PATCH`: documentation-only or non-contract changes

The `VERSION` file holds the next release version and must match changelog and compatibility checks.

## Pull Request Protection

On pull requests, CI:

1. Validates schema and examples.
2. Compares current schema with the latest released tag.
3. Detects and classifies compatibility impact.
4. Verifies that `CHANGELOG.md` and `VERSION` align with detected impact.

PRs fail when compatibility, version bump, or changelog classification are inconsistent.

## Release Process

1. Update schema/docs/examples as needed.
2. Update `VERSION` and add a matching entry to `CHANGELOG.md`.
3. Merge to main.
4. Run release workflow; it validates version/changelog consistency, creates tag `v<version>`, and publishes release notes from changelog.

## Consumer Guidance

Consumers should:

- pin to release tag or commit SHA
- vendor canonical schema path
- monitor changelog compatibility class before upgrading

## Related ADRs

- `docs/adr/0001-canonical-semver-and-notify-automation.md`
