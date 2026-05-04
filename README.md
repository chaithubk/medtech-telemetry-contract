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
├── examples/
│   └── vitals/
│       └── v2.0.example.json  # Canonical example payload for v2.0
├── docs/
│   └── vitals-v2.0.md         # Human-readable field docs, units, invariants
└── .github/
    └── workflows/
        └── validate.yml       # CI: validates every example against its schema
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

- Each schema lives at a **fixed, immutable path** (e.g. `schemas/vitals/v2.0.json`).
- Breaking changes introduce a new file (`v2.1.json`, `v3.0.json`), **never** mutate an existing one.
- Releases are tagged: `vitals/v2.0`, `vitals/v2.1`, etc.
- Consumers should pin to a **git tag** (recommended) or a specific commit SHA.

---

## Consuming a Contract

### Option A — Pin by git tag (recommended for all environments)

```bash
# Add as a git submodule pinned to the vitals/v2.0 tag
git submodule add https://github.com/chaithubk/medtech-telemetry-contract contracts/telemetry
cd contracts/telemetry && git checkout vitals/v2.0
```

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

Every push and pull-request runs `.github/workflows/validate.yml`, which uses
[AJV CLI](https://github.com/ajv-validator/ajv-cli) to validate every example
payload in `examples/` against its corresponding schema in `schemas/`. This
ensures that the example and the schema never diverge.

---

## Contributing

1. Add a new schema under `schemas/<domain>/<vX.Y>.json`.
2. Add a canonical example under `examples/<domain>/<vX.Y>.example.json`.
3. Add human-readable docs under `docs/<domain>-<vX.Y>.md`.
4. The CI will automatically validate the example against the schema.
5. Open a PR; tag it `schema:<domain>` for easy discovery.
6. After merge, create a git tag: `git tag <domain>/vX.Y && git push --tags`.
