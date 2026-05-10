# Vitals Telemetry Contract (Canonical)

## Overview

This repository exposes a single canonical schema path for the vitals contract:

- `schemas/vitals/vitals.schema.json`

The file at that path evolves over time. Immutable versions are represented by Git tags and releases (for example `v2.1.0`).

## Contract Fields

The canonical schema defines required and optional semantics directly. It preserves:

- `additionalProperties: false`
- explicit `required` fields
- strict enum/value constraints where applicable

Use the schema itself as the executable source of truth and this document as companion guidance.

## Consumer Usage

1. Pin this repository by SemVer tag (or commit SHA for immutable builds).
2. Vendor or reference `schemas/vitals/vitals.schema.json`.
3. Validate payloads in CI/runtime against the vendored schema.
4. Track release notes in `CHANGELOG.md` to understand compatibility impact.

### Python Example

```python
import json
import jsonschema

with open("contracts/vitals/vitals.schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)


def validate_vitals(payload: dict) -> None:
    jsonschema.validate(instance=payload, schema=schema)
```

### JavaScript / TypeScript Example

```js
import Ajv from "ajv";
import schema from "./contracts/vitals/vitals.schema.json";

const validate = new Ajv().compile(schema);

export function validateVitals(payload) {
  if (!validate(payload)) {
    throw new Error(JSON.stringify(validate.errors));
  }
}
```

## Compatibility Rules

A change is classified as:

- `BREAKING`: removed/renamed fields, enum narrowing, type narrowing/change, or newly required fields.
- `MINOR`: backward-compatible additions (new optional fields, enum expansion, relaxed constraints).
- `PATCH`: documentation-only or non-contract repository changes.

## How To Compare Versions

To compare two released contract versions:

```bash
git fetch --tags
git diff v2.0.0..v2.1.0 -- schemas/vitals/vitals.schema.json
```

This repo's CI performs this comparison automatically for pull requests against the latest release tag.
