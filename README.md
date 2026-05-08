# MedTech Telemetry Contract

This repository is the **single source of truth** for all telemetry payload
contracts used across the MedTech platform. Every service that publishes or
consumes telemetry data (vitals-publisher, edge-analytics, clinician-ui, …)
must pin to a versioned schema from this repo to avoid schema drift.

---

## Repository Structure

```
medtech-telemetry-contract/
├── schemas/
│   └── vitals/
│       └── v2.0.json          # JSON Schema — vitals payload v2.0
│       └── v2.1.json          # JSON Schema — vitals payload v2.1 (if present)
├── examples/
│   └── vitals/
│       └── v2.0.example.json  # Canonical example payload for v2.0
│       └── v2.1.example.json  # Canonical example payload for v2.1 (if present)
├── docs/
│   └── vitals-v2.0.md         # Human-readable field docs, units, invariants
└── .github/
    └── workflows/
        └── validate.yml       # CI: validates every example against its schema
        └── release.yml        # CI: workflow to tag and release new schema versions
```

Future contracts (e.g. `schemas/predictions/sepsis/v1.0.json`) follow the same
pattern: schema → example → doc.

---

## Contracts

| Contract          | Schema                           | Documentation              |
|-------------------|----------------------------------|----------------------------|
| Vitals v2.0       | `schemas/vitals/v2.0.json`       | `docs/vitals-v2.0.md`      |

---

## Versioning Policy


- **Versioned filenames:** Each schema and example file is named with its version (e.g. `v2.0.json`, `v2.1.json`). When a new version is released, create new files with the updated version in the filename. Do not overwrite or mutate existing versioned files.
- **Immutable contracts:** Never change a published schema file. Breaking changes require a new versioned file (e.g. `v2.1.json`, `v3.0.json`).
- **Release workflow:** Use the `release.yml` GitHub Actions workflow to tag and release new schema versions. Tags should match the version (e.g. `vitals/v2.1`).
- **Pinning:** Consumers should pin to a specific commit SHA for immutable builds (e.g. Yocto), and may also track the corresponding tag for release notes.

---

## Consuming a Contract

### Option A — Pin by commit SHA (recommended for immutable environments like Yocto)

```bash
# Add as a git submodule pinned to an immutable commit SHA
git submodule add https://github.com/chaithubk/medtech-telemetry-contract contracts/telemetry
cd contracts/telemetry && git checkout <commit-sha>
```

For human-readable contract reporting, maintain a version marker (for example,
`v2.0.0`) alongside your pinned commit in downstream packaging metadata.

### Option B — Vendor (copy) the schema file

1. Copy `schemas/vitals/v2.0.json` into your repository under `contracts/vitals/v2.0.json`.
2. Add a comment at the top of your validation code noting the source tag:
   ```
   # Vendored from chaithubk/medtech-telemetry-contract @ vitals/v2.0
   ```
3. When the contract is updated, repeat the copy step and bump the tag reference.

### Python example

```python
import json, jsonschema

with open("contracts/vitals/v2.0.json") as f:
    VITALS_SCHEMA = json.load(f)

def validate_vitals(payload: dict) -> None:
    jsonschema.validate(instance=payload, schema=VITALS_SCHEMA)
```

### JavaScript / TypeScript example

```js
import Ajv from "ajv";
import schema from "./contracts/vitals/v2.0.json";

const validate = new Ajv().compile(schema);

function validateVitals(payload) {
  if (!validate(payload)) throw new Error(JSON.stringify(validate.errors));
}
```

---

## CI Validation


### CI Validation

Every push and pull-request runs `.github/workflows/validate.yml`, which uses [AJV CLI](https://github.com/ajv-validator/ajv-cli) to validate every example payload in `examples/` against its corresponding schema in `schemas/`. The workflow automatically checks all versioned schemas and examples, ensuring that the example and the schema never diverge.

### Release Workflow

To release a new schema version:
1. Add new versioned schema and example files (e.g. `v2.1.json`, `v2.1.example.json`).
2. Run the `release.yml` workflow from the GitHub Actions tab, specifying the new version (e.g. `v2.1`).
3. The workflow will tag the release and create a GitHub Release entry.

---

## Contributing

1. Add a new schema under `schemas/<domain>/<vX.Y>.json`.
2. Add a canonical example under `examples/<domain>/<vX.Y>.example.json`.
3. Add human-readable docs under `docs/<domain>-<vX.Y>.md`.
4. The CI will automatically validate the example against the schema.
5. Open a PR; tag it `schema:<domain>` for easy discovery.
6. After merge, create a git tag: `git tag <domain>/vX.Y && git push --tags`.

---

## License

This project is licensed under **Apache-2.0**. See [`LICENSE`](./LICENSE).
