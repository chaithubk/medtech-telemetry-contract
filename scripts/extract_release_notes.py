#!/usr/bin/env python3
"""Extract a single version section from CHANGELOG.md for release notes."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HEADER_RE = re.compile(r"^## \[(?P<version>\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}$")


def extract_section(changelog: str, version: str) -> str:
    lines = changelog.splitlines()
    collecting = False
    out: list[str] = []

    for line in lines:
        m = HEADER_RE.match(line)
        if m:
            if collecting:
                break
            collecting = m.group("version") == version
            if collecting:
                out.append(line)
            continue
        if collecting:
            out.append(line)

    if not out:
        raise ValueError(f"Version {version} not found in changelog")

    return "\n".join(out).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract changelog section for release notes")
    parser.add_argument("--version", required=True)
    parser.add_argument("--changelog", default="CHANGELOG.md")
    parser.add_argument("--output", default="release-notes.md")
    args = parser.parse_args()

    changelog = Path(args.changelog).read_text(encoding="utf-8")
    try:
        section = extract_section(changelog, args.version)
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1

    Path(args.output).write_text(section, encoding="utf-8")
    print(f"Wrote release notes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
