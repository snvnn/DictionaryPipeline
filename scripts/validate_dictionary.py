#!/usr/bin/env python3
"""Validate Flippers dictionary authoring files without third-party packages."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORING_DIR = ROOT / "authoring"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    data = load_json(path)

    kind = data.get("kind")
    entries = data.get("entries")
    if kind not in {"jouyou-kanji-authoring", "basic-vocabulary-authoring"}:
        errors.append(f"{path}: invalid kind {kind!r}")
    if not isinstance(entries, list) or not entries:
        errors.append(f"{path}: entries must be a non-empty array")
        return errors

    seen_source_ids: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        label = f"{path}:{index}"
        source_id = entry.get("sourceID")
        if not source_id:
            errors.append(f"{label}: missing sourceID")
        elif source_id in seen_source_ids:
            errors.append(f"{label}: duplicate sourceID {source_id}")
        else:
            seen_source_ids.add(source_id)

        if kind == "jouyou-kanji-authoring":
            if not entry.get("kanji"):
                errors.append(f"{label}: missing kanji")
            readings = entry.get("officialReadings", {})
            if not readings.get("onyomi") and not readings.get("kunyomi"):
                errors.append(f"{label}: missing official readings")
        elif kind == "basic-vocabulary-authoring":
            if not entry.get("word"):
                errors.append(f"{label}: missing word")
            if not entry.get("reading"):
                errors.append(f"{label}: missing reading")

        content = entry.get("flippersContent", {})
        for field in ("koMeaning", "exampleJP", "exampleKO"):
            if not content.get(field):
                errors.append(f"{label}: missing flippersContent.{field}")

        review = entry.get("review", {})
        if review.get("status") not in {"draft", "reviewed", "blocked"}:
            errors.append(f"{label}: invalid review.status")

    return errors


def main() -> int:
    files = sorted(AUTHORING_DIR.glob("*.json"))
    if not files:
        print(f"No authoring files found under {AUTHORING_DIR}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in files:
        errors.extend(validate_file(path))

    if errors:
        print("Dictionary validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Dictionary validation passed for {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
