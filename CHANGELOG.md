# Changelog

All notable changes to this contract repository are documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

### Compatibility
PATCH

### Changed
- Repository governance and automation updates in progress.

## [2.1.1] - 2026-05-10

### Compatibility
PATCH (documentation-only / repository-governance)

### Changed
- Adopted a canonical schema path at `schemas/vitals/vitals.schema.json`.
- Replaced version-per-file contract management with Git tags/releases as the immutable version record.
- Added CI compatibility classification checks to detect breaking changes, backward-compatible additions, and patch-only updates.
- Added release workflow validation for SemVer tags and changelog-backed release notes.

### Migration Notes
- No payload field migration is required for consumers already aligned to the latest schema shape.
- Consumers should update vendoring/pinning paths from `schemas/vitals/v2.x.json` to `schemas/vitals/vitals.schema.json` and pin by tag/commit.

[Unreleased]: https://github.com/chaithubk/medtech-telemetry-contract/compare/v2.1.1...HEAD
[2.1.1]: https://github.com/chaithubk/medtech-telemetry-contract/releases/tag/v2.1.1
