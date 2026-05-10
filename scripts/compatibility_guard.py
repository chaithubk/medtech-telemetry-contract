#!/usr/bin/env python3
"""Classify contract compatibility and enforce version/changelog governance."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
CHANGELOG_HEADER_RE = re.compile(r"^## \[(?P<version>\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}$")
COMPAT_LINE_RE = re.compile(r"^\s*(BREAKING|MINOR|PATCH|.*backward.*|.*documentation.*)$", re.IGNORECASE)


@dataclass
class Finding:
    kind: str
    path: str
    details: str


@dataclass
class ComparisonResult:
    compatibility: str
    findings: list[Finding]


def run_git_show(ref_path: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "show", ref_path],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out
    except subprocess.CalledProcessError:
        return None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema_from_tag(tag: str) -> dict[str, Any] | None:
    candidates = [
        f"{tag}:schemas/vitals/vitals.schema.json",
        f"{tag}:schemas/vitals/v2.1.json",
        f"{tag}:schemas/vitals/v2.0.json",
    ]
    for candidate in candidates:
        content = run_git_show(candidate)
        if content is not None:
            return json.loads(content)
    return None


def normalize_types(schema: dict[str, Any]) -> set[str]:
    if "type" in schema:
        t = schema["type"]
        if isinstance(t, list):
            return set(str(v) for v in t)
        return {str(t)}
    if "const" in schema:
        v = schema["const"]
        if v is None:
            return {"null"}
        if isinstance(v, bool):
            return {"boolean"}
        if isinstance(v, int):
            return {"integer"}
        if isinstance(v, float):
            return {"number"}
        if isinstance(v, str):
            return {"string"}
    if "enum" in schema and schema["enum"]:
        enum_types = set()
        for v in schema["enum"]:
            if v is None:
                enum_types.add("null")
            elif isinstance(v, bool):
                enum_types.add("boolean")
            elif isinstance(v, int):
                enum_types.add("integer")
            elif isinstance(v, float):
                enum_types.add("number")
            elif isinstance(v, str):
                enum_types.add("string")
        return enum_types
    for keyword in ("oneOf", "anyOf"):
        if keyword in schema and isinstance(schema[keyword], list):
            merged: set[str] = set()
            for item in schema[keyword]:
                if isinstance(item, dict):
                    merged |= normalize_types(item)
            if merged:
                return merged
    return set()


def schema_signature(schema: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    types = tuple(sorted(normalize_types(schema)))
    enum_values = tuple(sorted(str(v) for v in schema.get("enum", [])))
    return (types, enum_values)


def compare_schema_nodes(old: dict[str, Any], new: dict[str, Any], path: str, findings: list[Finding]) -> None:
    old_types = normalize_types(old)
    new_types = normalize_types(new)

    if old_types and new_types and not old_types.issubset(new_types):
        findings.append(
            Finding("breaking", path, f"Type narrowing/change: {sorted(old_types)} -> {sorted(new_types)}")
        )
    elif old_types and new_types and not new_types.issubset(old_types):
        findings.append(
            Finding("minor", path, f"Type widened: {sorted(old_types)} -> {sorted(new_types)}")
        )

    old_enum = old.get("enum")
    new_enum = new.get("enum")
    if isinstance(old_enum, list) and isinstance(new_enum, list):
        old_set = set(old_enum)
        new_set = set(new_enum)
        if not old_set.issubset(new_set):
            findings.append(
                Finding("breaking", path, f"Enum narrowed: removed {sorted(old_set - new_set)}")
            )
        elif not new_set.issubset(old_set):
            findings.append(
                Finding("minor", path, f"Enum expanded: added {sorted(new_set - old_set)}")
            )

    old_props = old.get("properties") if isinstance(old.get("properties"), dict) else {}
    new_props = new.get("properties") if isinstance(new.get("properties"), dict) else {}

    old_required = set(old.get("required", [])) if isinstance(old.get("required"), list) else set()
    new_required = set(new.get("required", [])) if isinstance(new.get("required"), list) else set()

    for name in sorted(old_props.keys() - new_props.keys()):
        findings.append(Finding("breaking", f"{path}/properties/{name}", "Removed field"))

    added_props = sorted(new_props.keys() - old_props.keys())
    for name in added_props:
        kind = "breaking" if name in new_required else "minor"
        details = "New required field" if kind == "breaking" else "New optional field"
        findings.append(Finding(kind, f"{path}/properties/{name}", details))

    # Heuristic rename detection: removed + added field with similar signature in same object scope.
    removed = old_props.keys() - new_props.keys()
    if removed and added_props:
        removed_sigs = {name: schema_signature(old_props[name]) for name in removed}
        added_sigs = {name: schema_signature(new_props[name]) for name in added_props}
        for old_name, old_sig in removed_sigs.items():
            for new_name, new_sig in added_sigs.items():
                if old_sig == new_sig:
                    findings.append(
                        Finding(
                            "breaking",
                            f"{path}/properties/{old_name}",
                            f"Possible rename to '{new_name}'",
                        )
                    )

    new_required_fields = sorted(new_required - old_required)
    if new_required_fields:
        findings.append(
            Finding(
                "breaking",
                f"{path}/required",
                f"New required fields: {new_required_fields}",
            )
        )

    for name in sorted(old_props.keys() & new_props.keys()):
        compare_schema_nodes(old_props[name], new_props[name], f"{path}/properties/{name}", findings)


def classify(findings: list[Finding]) -> str:
    if any(f.kind == "breaking" for f in findings):
        return "BREAKING"
    if any(f.kind == "minor" for f in findings):
        return "MINOR"
    return "PATCH"


def parse_semver(version: str) -> tuple[int, int, int]:
    m = SEMVER_RE.fullmatch(version.strip())
    if not m:
        raise ValueError(f"Invalid SemVer: {version}")
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def semver_bump_class(old: str, new: str) -> str:
    old_v = parse_semver(old)
    new_v = parse_semver(new)
    if new_v <= old_v:
        raise ValueError(f"Version must increase: {old} -> {new}")
    if new_v[0] > old_v[0]:
        return "BREAKING"
    if new_v[1] > old_v[1]:
        return "MINOR"
    return "PATCH"


def extract_version_entry(changelog_text: str, version: str) -> str:
    lines = changelog_text.splitlines()
    in_target = False
    collected: list[str] = []
    for line in lines:
        header_match = CHANGELOG_HEADER_RE.match(line)
        if header_match:
            if in_target:
                break
            in_target = header_match.group("version") == version
            continue
        if in_target:
            collected.append(line)
    if not collected:
        raise ValueError(f"No changelog entry for version {version}")
    return "\n".join(collected)


def normalize_compat_label(text: str) -> str:
    upper = text.upper()
    if "BREAKING" in upper:
        return "BREAKING"
    if "MINOR" in upper or "BACKWARD" in upper:
        return "MINOR"
    if "PATCH" in upper or "DOC" in upper:
        return "PATCH"
    raise ValueError(f"Unable to parse compatibility label: {text}")


def extract_changelog_compat(entry_text: str) -> str:
    lines = [line.strip() for line in entry_text.splitlines() if line.strip()]
    for idx, line in enumerate(lines):
        if line.lower().startswith("### compatibility"):
            if idx + 1 < len(lines):
                return normalize_compat_label(lines[idx + 1])
    for line in lines:
        if COMPAT_LINE_RE.match(line):
            try:
                return normalize_compat_label(line)
            except ValueError:
                continue
    raise ValueError("Missing compatibility label in changelog entry")


def validate_schema_metadata(
    schema: dict[str, Any],
    detected_class: str,
    current_version: str,
    base_tag: str | None,
) -> None:
    """
    Validate that schema metadata (x-breaking-changes-from, x-contract-metadata, etc.)
    is consistent with detected breaking changes and declared compatibility.
    """
    # Check $schemaVersion matches current version
    schema_version = schema.get("$schemaVersion", "")
    if schema_version and schema_version != current_version:
        raise ValueError(
            f"Schema metadata mismatch: $schemaVersion={schema_version}, but current VERSION={current_version}"
        )

    # Check x-contract-metadata.version matches current version
    metadata = schema.get("x-contract-metadata", {})
    metadata_version = metadata.get("version", "")
    if metadata_version and metadata_version != current_version:
        raise ValueError(
            f"Schema metadata mismatch: x-contract-metadata.version={metadata_version}, but current VERSION={current_version}"
        )

    # Check x-contract-metadata.compatibility-class matches detected class
    declared_compat = metadata.get("compatibility-class", "")
    if declared_compat and declared_compat != detected_class:
        raise ValueError(
            f"Schema metadata mismatch: x-contract-metadata.compatibility-class={declared_compat}, but detected={detected_class}"
        )

    # If this is a BREAKING release, validate x-breaking-changes-from is populated
    if detected_class == "BREAKING":
        breaking_from = schema.get("x-breaking-changes-from", {})
        if not breaking_from or all(not v for v in breaking_from.values()):
            raise ValueError(
                "Schema declares BREAKING compatibility but x-breaking-changes-from is empty. "
                "Must document breaking changes from previous versions."
            )

    # If this is not a BREAKING release, x-breaking-changes-in-this-version should be empty
    if detected_class != "BREAKING":
        breaking_in_this = schema.get("x-breaking-changes-in-this-version", [])
        if breaking_in_this:
            raise ValueError(
                f"Schema declares {detected_class} compatibility but has entries in x-breaking-changes-in-this-version. "
                "Remove entries or reclassify as BREAKING."
            )


def validate_governance(
    detected_class: str,
    version_file: Path,
    changelog_file: Path,
    base_tag: str | None,
    schema: dict[str, Any] | None = None,
) -> None:
    current_version = version_file.read_text(encoding="utf-8").strip()
    parse_semver(current_version)

    changelog = changelog_file.read_text(encoding="utf-8")
    entry = extract_version_entry(changelog, current_version)
    changelog_class = extract_changelog_compat(entry)

    if changelog_class != detected_class:
        raise ValueError(
            f"Changelog compatibility mismatch: detected {detected_class}, changelog says {changelog_class}"
        )

    if base_tag:
        base_version = base_tag[1:] if base_tag.startswith("v") else base_tag
        bump = semver_bump_class(base_version, current_version)
        if bump != detected_class:
            raise ValueError(
                f"Version bump mismatch: base {base_version}, current {current_version}, bump={bump}, detected={detected_class}"
            )

    # Validate schema metadata consistency (new validation)
    if schema is not None:
        validate_schema_metadata(schema, detected_class, current_version, base_tag)


def print_report(result: ComparisonResult) -> None:
    print(f"Compatibility class: {result.compatibility}")
    if not result.findings:
        print("- No schema compatibility changes detected")
        return
    for finding in result.findings:
        print(f"- [{finding.kind.upper()}] {finding.path}: {finding.details}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Contract compatibility guard")
    parser.add_argument(
        "--current-schema",
        default="schemas/vitals/vitals.schema.json",
        help="Path to current schema file (default: schemas/vitals/vitals.schema.json)",
    )
    parser.add_argument(
        "--base-tag",
        default="",
        help="Git tag to compare against (e.g., v2.1.0)",
    )
    parser.add_argument(
        "--version-file",
        default="VERSION",
        help="Path to VERSION file",
    )
    parser.add_argument(
        "--changelog-file",
        default="CHANGELOG.md",
        help="Path to CHANGELOG file",
    )
    parser.add_argument(
        "--domain",
        default="vitals",
        help="Domain name for multi-domain support (e.g., vitals, predictions, labs)",
    )
    parser.add_argument(
        "--report-file",
        default="",
        help="Optional: write JSON report to file",
    )
    parser.add_argument(
        "--validate-metadata",
        action="store_true",
        help="Validate schema metadata declarations (x-breaking-changes-from, x-contract-metadata, etc.)",
    )
    args = parser.parse_args()

    current_schema = load_json(Path(args.current_schema))
    base_tag = args.base_tag.strip() or None

    findings: list[Finding] = []
    if base_tag:
        base_schema = load_schema_from_tag(base_tag)
        if base_schema is None:
            print(
                f"::error::Unable to load baseline schema from tag {base_tag}. Expected schemas/{args.domain}/{args.domain}.schema.json or legacy v2.x path.",
                file=sys.stderr,
            )
            return 1
        compare_schema_nodes(base_schema, current_schema, "#", findings)
    compatibility = classify(findings)
    result = ComparisonResult(compatibility=compatibility, findings=findings)

    if args.report_file:
        Path(args.report_file).write_text(
            json.dumps(
                {
                    "compatibility": result.compatibility,
                    "findings": [
                        {"kind": f.kind, "path": f.path, "details": f.details} for f in result.findings
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    print_report(result)

    try:
        # Pass schema for metadata validation
        validate_governance(
            detected_class=result.compatibility,
            version_file=Path(args.version_file),
            changelog_file=Path(args.changelog_file),
            base_tag=base_tag,
            schema=current_schema if args.validate_metadata else None,
        )
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
