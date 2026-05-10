# MedTech Telemetry Contract

This repository is the authoritative schema registry for MedTech telemetry contracts.
Each contract domain has one canonical schema path that evolves over time. Immutable
contract versions are represented by Git tags and GitHub Releases.

## Repository Structure

```
medtech-telemetry-contract/
├── schemas/
│   └── vitals/
│       └── vitals.schema.json
├── examples/
│   └── vitals/
│       └── vitals.example.json
├── docs/
│   ├── vitals.md
│   └── contract-lifecycle.md
├── scripts/
│   ├── compatibility_guard.py
│   └── extract_release_notes.py
├── CHANGELOG.md
├── VERSION
└── .github/workflows/
        ├── validate.yml
        └── release.yml
```

## Canonical Contract Paths

| Contract | Canonical Schema | Canonical Example | Documentation |
|---|---|---|---|
| Vitals | `schemas/vitals/vitals.schema.json` | `examples/vitals/vitals.example.json` | `docs/vitals.md` |

## Versioning and Immutability

- The canonical schema file is mutable on `main`.
- Releases are immutable and identified by SemVer tags: `vMAJOR.MINOR.PATCH`.
- `VERSION` contains the next release version.
- `CHANGELOG.md` records release notes and compatibility class for each release.

Compatibility classes:

- `BREAKING`: removed/renamed fields, enum narrowing, type narrowing/change, or newly required fields.
- `MINOR`: backward-compatible additions or relaxations.
- `PATCH`: documentation-only or non-contract changes.

## Consumer Guidance

Consumers should pin to a release tag (or commit SHA) and vendor/reference the canonical schema path.

```bash
git submodule add https://github.com/chaithubk/medtech-telemetry-contract contracts/telemetry
cd contracts/telemetry && git checkout v2.1.0
```

Then use:

- `schemas/vitals/vitals.schema.json`

Python:

```python
import json
import jsonschema

with open("contracts/telemetry/schemas/vitals/vitals.schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)


def validate_vitals(payload: dict) -> None:
    jsonschema.validate(instance=payload, schema=schema)
```

JavaScript / TypeScript:

```js
import Ajv from "ajv";
import schema from "./contracts/telemetry/schemas/vitals/vitals.schema.json";

const validate = new Ajv().compile(schema);

export function validateVitals(payload) {
    if (!validate(payload)) {
        throw new Error(JSON.stringify(validate.errors));
    }
}
```

## CI Compatibility Governance

On pull requests, CI:

1. Validates the canonical schema and canonical example.
2. Compares the current schema against the latest released SemVer tag.
3. Detects removed/renamed fields, type changes, enum narrowing, and new required fields.
4. Classifies compatibility as `BREAKING`, `MINOR`, or `PATCH`.
5. Fails if `CHANGELOG.md` and `VERSION` do not match the detected compatibility impact.

## Release Workflow

Release workflow steps:

1. Read version from `VERSION`.
2. Ensure matching changelog entry exists.
3. Create and push tag `v<version>`.
4. Generate release notes from the matching changelog section.
5. Publish GitHub Release.

## Comparing Versions

```bash
git fetch --tags
git diff v2.0.0..v2.1.0 -- schemas/vitals/vitals.schema.json
```

## License

This project is licensed under Apache-2.0. See [LICENSE](LICENSE).

## Architecture Decision Records (ADRs)

Key design and governance decisions are documented as ADRs:

- [Canonical Schema Versioning and Automated Consumer Notification](docs/adr/0001-canonical-semver-and-notify-automation.md)
