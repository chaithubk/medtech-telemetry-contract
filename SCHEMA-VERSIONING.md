# Schema Versioning & Governance Quick Reference

## Overview

This repository uses a **clean, maintainable schema versioning model** with three key files:

1. **vitals.schema.json** — The canonical JSON Schema (validates payloads)
2. **vitals.schema-manifest.yml** — Governance metadata (version, breaking changes, migration guides)
3. **CHANGELOG.md** — Release notes (what shipped in each version)

## For Consumers (Using This Schema)

### 📦 Load Version-Specific Schema

```python
# Extract version from payload
version = payload['version']  # e.g., "2.1.1"

# Load exact schema from Git tag
schema = subprocess.check_output([
    'git', 'show', f'v{version}:schemas/vitals/vitals.schema.json'
], text=True)

# Validate payload
ajv.validate(payload, json.loads(schema))
```

### ⚠️ Check Breaking Changes Before Upgrade

```yaml
# Read schemas/vitals/vitals.schema-manifest.yml
breaking_changes_from:
  "2.0.0":
    - field: creatinine
      breaking_since: "2.1.0"
      migration: "Publishers must compute creatinine value..."
```

**Rule**: If upgrading from version X → Y, check `manifest.breaking_changes_from[X]` for required migrations.

### 🔄 Safe Upgrade Path

1. Check `vitals.schema-manifest.yml` for breaking changes
2. Read migration guides (in manifest or CHANGELOG)
3. Update your code if needed
4. Load new version's schema
5. Validate payloads against new schema

---

## For Publishers (Producing Payloads)

### 📝 Include Version in Payload

```json
{
  "version": "2.1.1",
  "patient_id": "...",
  ...
}
```

**Always use SemVer format**: MAJOR.MINOR.PATCH

### 📦 Pin Schema Version

**Option 1: Clone with Git submodule (recommended)**
```bash
git submodule add https://github.com/chaithubk/medtech-telemetry-contract.git deps/contract
# Pin to specific version:
cd deps/contract && git checkout v2.1.1
```

**Option 2: Copy schema for immutability**
```bash
# Download schema from specific Git tag
curl -o vitals.schema.json \
  "https://raw.githubusercontent.com/chaithubk/medtech-telemetry-contract/v2.1.1/schemas/vitals/vitals.schema.json"
```

### ✅ Validate Before Publishing

```python
import json
import ajv

schema = json.load(open('vitals.schema.json'))
payload = {...your payload...}

ajv.validate(payload, schema)  # Throws error if invalid
publish_to_mqtt(payload)
```

---

## For Maintainers (Evolving This Schema)

### 📋 Making Schema Changes

1. **Edit** `schemas/vitals/vitals.schema.json`
2. **Update** `schemas/vitals/vitals.schema-manifest.yml`
   - Add entries to `breaking_changes_from[old_version]` if schema changes
   - Update `current_version`, `compatibility_class`, `migration` guides
3. **Update** `VERSION` file (increment SemVer)
4. **Update** `CHANGELOG.md` (document release, include compatibility class)
5. **Run CI**: `python3 scripts/compatibility_guard.py --validate-metadata` validates consistency

### 🔍 CI Validation

```bash
# Detect schema changes and classify compatibility
python3 scripts/compatibility_guard.py --base-tag v2.1.0

# Output: "Compatibility class: BREAKING|MINOR|PATCH"

# Validate that manifest + changelog match detected class
# (script fails if mismatch detected)
```

### 🏷️ Release Workflow

1. Ensure `VERSION`, `CHANGELOG.md`, schema, and manifest are all consistent
2. Run: `./release.sh` (or use GitHub Actions)
3. Automatic Git tag created: `v{VERSION}`
4. Release notes published to GitHub

---

## File Descriptions

### vitals.schema.json
**What**: JSON Schema (Draft 7) defining the vitals payload contract  
**When to edit**: When adding/removing/renaming fields or changing field types  
**Immutability**: Mutable on main branch, immutable by Git tag  
**Usage**: Consumers load version-specific schema for payload validation  

### vitals.schema-manifest.yml
**What**: Governance metadata (breaking changes, migration guides, compatibility matrix)  
**When to edit**: When updating version, documenting breaking changes, or adding migration guides  
**Format**: YAML (human-readable, tooling-friendly)  
**Usage**: Developers consult for upgrade paths, tooling parses for automation  

### CHANGELOG.md
**What**: Release notes (Keep-a-Changelog format)  
**When to edit**: On every release (before tagging)  
**Format**: Markdown with section for each version  
**Usage**: End users / release notes, CI validates compatibility-class consistency  

### VERSION
**What**: Next release version (SemVer)  
**When to edit**: Before release (after final changes)  
**Format**: `MAJOR.MINOR.PATCH` (e.g., `2.1.1`)  
**Usage**: Release workflow reads this to create Git tag and release notes  

---

## Multi-Domain (Future)

When adding new domains (e.g., predictions, labs), follow the same pattern:

```
schemas/
├── vitals/
│   ├── vitals.schema.json
│   ├── vitals.schema-manifest.yml
│   └── DOMAIN-CHANGELOG.md
│
├── predictions/              # NEW
│   ├── predictions.schema.json
│   ├── predictions.schema-manifest.yml
│   └── DOMAIN-CHANGELOG.md
```

- All domains share global `VERSION` file (single SemVer for repository)
- Unified `CHANGELOG.md` aggregates all domain releases
- CI validates each changed domain independently
- Single Git tag applies to all domains

---

## Key Design Principles

✅ **Schema is clean** — No governance metadata cluttering the payload definition  
✅ **Governance is explicit** — Breaking changes documented in manifest + changelog  
✅ **Version is portable** — Payload carries version; consumers load exact schema  
✅ **Immutability via Git** — Released schemas are tagged and never change  
✅ **Multi-domain ready** — Isolated evolution per domain, coordinated versioning  
✅ **Consumer-friendly** — Clear upgrade paths, migration guides, safety checks  

---

## See Also

- [Schema Design Strategy](docs/schema-design-strategy.md) — Detailed rationale and patterns
- [Contract Lifecycle](docs/contract-lifecycle.md) — Full governance model
- [CHANGELOG.md](CHANGELOG.md) — Release history and breaking changes
- [README.md](README.md) — Project overview
