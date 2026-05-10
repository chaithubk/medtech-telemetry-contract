# Schema Design Strategy: Futuristic Versioning & Multi-Domain Scalability

## Overview

This document describes the **schema metadata architecture** that makes breaking changes explicit, version-aware, and machine-readable — enabling safe consumer upgrades and seamless multi-domain scaling.

---

## 1. Schema-Level Version Information

### The Problem
Version information existed **only in payload** (`"version": "2.1.1"` field). Consumers had no clear governance model for schema evolution.

### The Solution: Clean Separation of Concerns

**The schema stays LEAN and focused on validation:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/chaithubk/medtech-telemetry-contract/schemas/vitals/vitals.schema.json",
  "title": "MedTech Vitals Telemetry Payload",
  "description": "Canonical JSON Schema for vitals. See CHANGELOG.md for version history and breaking changes.",
  "type": "object",
  "properties": { ... }
}
```

**Governance metadata lives in a separate manifest (vitals.schema-manifest.yml):**
```yaml
domain: vitals
current_version: "2.1.1"
release_date: "2026-05-10"
compatibility_class: PATCH
schema_stability: stable

breaking_changes_from:
  "2.0.0":
    - type: field-added-required
      field: creatinine
      migration: "Publishers must compute creatinine..."
```

### Why This Works
- ✅ **Schema is readable** (focused on payload structure, not governance)
- ✅ **Governance is explicit** (manifest documents version, breaking changes, migration paths)
- ✅ **Separation of concerns** (validators only load schema; governance tools read manifest + CHANGELOG)
- ✅ **Maintainable** (schema doesn't get cluttered with metadata as it evolves)

---

## 2. Breaking-Change Signaling Strategy

### The Problem
Currently, breaking changes are **detected in CI** (schema diff comparison), but consumers don't have a clear, documented way to understand what broke and how to migrate.

### The Solution: Manifest-Based Breaking-Change Documentation

**Breaking changes are documented in vitals.schema-manifest.yml:**

```yaml
breaking_changes_from:
  "2.0.0":
    - type: field-added-required
      field: creatinine
      description: Serum creatinine (mg/dL) - organ dysfunction marker for sepsis
      breaking_since: "2.1.0"
      migration: |
        Publishers must compute or provide creatinine value.
        Consumers receiving 2.0.0 payloads will fail validation against 2.1.0+ schema.
        Plan payload version negotiation or implement dual-schema validation.
```

**Changelog (CHANGELOG.md) records the release:**

```markdown
## [2.1.1] - 2026-05-10
### Compatibility
PATCH (documentation-only / repository-governance)

### Breaking Changes From 2.0.0
- **creatinine** (required): Added in 2.1.0. Producers must compute this value.
- **altered_mentation** (required): Added in 2.1.0. Producers must compute from GCS.
```

### Why This Works
- ✅ **Consumers see breaking changes in manifest** (not buried in schema JSON)
- ✅ **CI detects breaking changes** (schema diff comparison) and validates consistency with manifest + changelog
- ✅ **Migration guides are explicit** (step-by-step instructions for each breaking field)
- ✅ **Changelog is the source of truth** for release notes (what actually shipped)
- ✅ **Manifest is the developer reference** (how to migrate between versions)

---

## 3. Multi-Domain Scalability

### The Vision
Support multiple contract domains (vitals, predictions, labs, alerts) while maintaining:
- Isolated evolution per domain
- Coordinated versioning (one global VERSION file)
- Unified governance (one release process for all domains)

### Directory Structure

```
schemas/
├── vitals/
│   ├── vitals.schema.json              # Mutable schema (versions tagged in Git)
│   ├── vitals.schema-manifest.yml      # Governance metadata
│   └── DOMAIN-CHANGELOG.md             # Domain-specific release notes
│
├── predictions/                        # Next domain (future)
│   ├── predictions.schema.json
│   ├── predictions.schema-manifest.yml
│   └── DOMAIN-CHANGELOG.md
│
└── labs/                               # Future domain
    ├── labs.schema.json
    ├── labs.schema-manifest.yml
    └── DOMAIN-CHANGELOG.md

VERSION                                # Global: single SemVer for all domains
CHANGELOG.md                           # Unified: aggregates all domain releases
```

### How It Works

**1. Each domain evolves independently:**
- Schema is mutable at `main` branch, immutable by Git tag
- Manifest documents version, breaking changes, compatibility
- Domain changelog records that domain's releases

**2. Global VERSION file coordinates releases:**
```bash
# VERSION file
2.1.1
```
- Incremented on ANY domain change
- Single SemVer applies to entire repository (not per-domain)
- Release tag = v{VERSION}

**3. Unified CHANGELOG aggregates all domains:**
```markdown
## [2.1.1] - 2026-05-10

### Vitals
- Compatibility: PATCH
- No breaking changes

### Predictions (new domain)
- Compatibility: MINOR
- Added support for model predictions

### Labs
- Compatibility: BREAKING
- Removed legacy lab result format
```

### Multi-Domain CI Workflow

**validate.yml detects changed domains:**
```yaml
- name: Detect changed domains
  run: |
    CHANGED=$(git diff origin/main --name-only | grep "schemas/" | cut -d'/' -f2 | sort -u)
    echo "DOMAINS=$CHANGED" >> $GITHUB_ENV

- name: Validate each domain
  run: |
    for domain in $DOMAINS; do
      python3 scripts/compatibility_guard.py --domain "$domain" --base-tag v2.1.0
    done
```

**release.yml handles multi-domain release:**
```yaml
- name: Extract manifests for all changed domains
  run: |
    for domain in $CHANGED_DOMAINS; do
      cat "schemas/$domain/${domain}.schema-manifest.yml" >> unified-manifest.yml
    done

- name: Generate unified release notes
  run: |
    python3 scripts/aggregate_release_notes.py \
      --domains $CHANGED_DOMAINS \
      --version 2.1.1
```

### Why This Scales
- ✅ Each domain has isolated schema + manifest + changelog
- ✅ Global VERSION keeps all domains in sync
- ✅ CI validates each changed domain independently
- ✅ Release is atomic (one tag, all domains)
- ✅ Easy to add new domains (just create schemas/DOMAIN/ folder)

---

## 5. Governance: Enhanced compatibility_guard.py

The updated script now supports:

1. **Multi-domain validation** (--domain flag):
   ```bash
   python3 scripts/compatibility_guard.py --domain vitals --base-tag v2.1.0
   ```

2. **Manifest validation** (--validate-metadata flag):
   ```bash
   python3 scripts/compatibility_guard.py --validate-metadata
   ```
   - Checks that schema version matches VERSION file
   - Verifies breaking-change declarations align with detected changes
   - Ensures changelog consistency

3. **Domain-scoped schema discovery**:
   ```bash
   python3 scripts/compatibility_guard.py --domain predictions \
     --current-schema schemas/predictions/predictions.schema.json
   ```

### Validation Rules

- ✅ If detected class is BREAKING: manifest must have `breaking_changes_from` entries
- ✅ If detected class is not BREAKING: `breaking_changes_in_this_version` must be empty
- ✅ Changelog entry must match detected class (BREAKING, MINOR, PATCH)
- ✅ VERSION file must be incremented for release
- ✅ All changed domains must pass validation

---

## 4. Consumer Integration Examples

### Example 1: Load Version-Specific Schema

```python
# Consumer: edge-analytics service ingesting vitals from MQTT
import json
import subprocess

def validate_vitals_payload(payload_json):
    """Validate payload against version-specific schema."""
    payload = json.loads(payload_json)
    version = payload['version']  # e.g., "2.1.1"
    
    # Load schema for this exact version from Git
    schema_content = subprocess.check_output(
        ['git', 'show', f'v{version}:schemas/vitals/vitals.schema.json'],
        text=True
    )
    schema = json.loads(schema_content)
    
    # Validate using AJV or similar
    ajv.validate(payload, schema)
    return True
```

### Example 2: Check Breaking Changes Before Upgrade

```python
def can_upgrade_version(current_version, target_version):
    """Determine if upgrade is safe."""
    import yaml
    
    # Load manifest for target version
    manifest_content = subprocess.check_output(
        ['git', 'show', f'v{target_version}:schemas/vitals/vitals.schema-manifest.yml'],
        text=True
    )
    manifest = yaml.safe_load(manifest_content)
    
    # Check breaking changes from current version
    breaking = manifest['breaking_changes_from'].get(current_version, [])
    
    if breaking:
        print(f"⚠️  BREAKING changes from {current_version}:")
        for change in breaking:
            print(f"  - {change['field']}: {change['migration']}")
        return False
    
    print(f"✅ Safe to upgrade {current_version} → {target_version}")
    return True
```

### Example 3: Auto-Generate Migration Guide

```python
def generate_migration_guide(from_version, to_version, domain='vitals'):
    """Auto-generate migration steps from manifest."""
    import yaml
    
    manifest_file = f'schemas/{domain}/{domain}.schema-manifest.yml'
    manifest = yaml.safe_load(open(manifest_file))
    
    breaking = manifest['breaking_changes_from'].get(from_version, [])
    
    guide = f"# Migration: {domain} {from_version} → {to_version}\n\n"
    if not breaking:
        guide += "✅ No breaking changes—upgrade is backward compatible.\n"
    else:
        guide += "⚠️  BREAKING CHANGES:\n\n"
        for change in breaking:
            guide += f"### {change['field']}\n"
            guide += f"**Type**: {change['type']}\n"
            guide += f"**Migration**:\n{change['migration']}\n\n"
    
    return guide
```

---

## 6. Summary: Futuristic Schema Design (Simplified)

| Aspect | Strategy | Benefit |
|--------|----------|---------|
| **Schema file** | Clean JSON Schema (validates payload structure only) | Readable, maintainable, focused |
| **Payload versioning** | `"version": "2.1.1"` field (SemVer) | Runtime version selection |
| **Governance** | Separate manifest file (.schema-manifest.yml) | Clear separation of concerns |
| **Breaking changes** | Documented in manifest + CHANGELOG.md | Explicit, machine-readable, consumer-friendly |
| **Compatibility** | Manifest compatibility_matrix + upgrade_paths | Consumers know upgrade safety upfront |
| **Multi-domain** | Domain-scoped schemas/manifests + global VERSION | Scalable, isolated evolution, unified versioning |
| **CI validation** | Enhanced compatibility_guard.py with --domain flag | Validates each domain independently |
| **Consumer safety** | Manifest.consumer_safety_check section + examples | Step-by-step upgrade guidance |

---

## 7. Implementation Roadmap

### Phase 1 (Current) ✅
- [x] Add schema metadata (x-contract-metadata, x-breaking-changes-from, etc.)
- [x] Document design strategy (this file)
- [ ] Enhance compatibility_guard.py to validate metadata

### Phase 2 (Next Sprint)
- [ ] Create prediction domain schema (schemas/predictions/predictions.schema.json)
- [ ] Enhanced CI workflow (detect_changed_domains.py)
- [ ] Multi-domain validation in release.yml

### Phase 3 (Future)
- [ ] Consumer integration examples (SDK/library guidance)
- [ ] Auto-generated migration guides (from metadata)
- [ ] Contract broker dashboard (schema catalog)

---

## 8. References

- [JSON Schema Specification](https://json-schema.org/draft-07/)
- [SemVer](https://semver.org/) — Semantic Versioning
- [Keep a Changelog](https://keepachangelog.com/) — Changelog Format
- [OpenAPI Vendor Extensions](https://spec.openapis.org/oas/v3.0.3#specification-extensions) — Pattern for x-* metadata
