#!/usr/bin/env python3
"""Validate Flippers dictionary authoring files without third-party packages."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORING_DIR = ROOT / "authoring"
VALID_KINDS = {"jouyou-kanji-authoring", "basic-vocabulary-authoring"}
VALID_REVIEW_STATUSES = {"draft", "reviewed", "blocked"}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def require_string(errors: list[str], label: str, data: dict, key: str) -> str | None:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}: missing {key}")
        return None
    return value


def validate_file(path: Path) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    source_ids: set[str] = set()
    data = load_json(path)

    require_string(errors, str(path), data, "id")
    kind = data.get("kind")
    version = data.get("version")
    entries = data.get("entries")
    if kind not in VALID_KINDS:
        errors.append(f"{path}: invalid kind {kind!r}")
    if not isinstance(version, int) or version < 1:
        errors.append(f"{path}: version must be a positive integer")
    if not isinstance(entries, list) or not entries:
        errors.append(f"{path}: entries must be a non-empty array")
        return errors, source_ids

    seen_source_ids: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        label = f"{path}:{index}"
        if not isinstance(entry, dict):
            errors.append(f"{label}: entry must be an object")
            continue

        source_id = require_string(errors, label, entry, "sourceID")
        if source_id:
            if source_id in seen_source_ids:
                errors.append(f"{label}: duplicate sourceID {source_id}")
            seen_source_ids.add(source_id)
            source_ids.add(source_id)

        if kind == "jouyou-kanji-authoring":
            kanji = require_string(errors, label, entry, "kanji")
            if kanji and len(kanji) != 1:
                errors.append(f"{label}: kanji must be exactly one character")
            readings = entry.get("officialReadings", {})
            if not isinstance(readings, dict):
                errors.append(f"{label}: officialReadings must be an object")
                readings = {}
            if not readings.get("onyomi") and not readings.get("kunyomi"):
                errors.append(f"{label}: missing official readings")
        elif kind == "basic-vocabulary-authoring":
            require_string(errors, label, entry, "word")
            require_string(errors, label, entry, "reading")

        content = entry.get("flippersContent", {})
        if not isinstance(content, dict):
            errors.append(f"{label}: flippersContent must be an object")
            content = {}
        for field in ("koMeaning", "exampleJP", "exampleKO"):
            if not isinstance(content.get(field), str) or not content[field].strip():
                errors.append(f"{label}: missing flippersContent.{field}")

        review = entry.get("review", {})
        if not isinstance(review, dict):
            errors.append(f"{label}: review must be an object")
            review = {}
        if review.get("status") not in VALID_REVIEW_STATUSES:
            errors.append(f"{label}: invalid review.status")

    return errors, source_ids


def main() -> int:
    files = sorted(AUTHORING_DIR.glob("*.json"))
    if not files:
        print(f"No authoring files found under {AUTHORING_DIR}", file=sys.stderr)
        return 1

    errors: list[str] = []
    all_source_ids: dict[str, Path] = {}
    for path in files:
        file_errors, source_ids = validate_file(path)
        errors.extend(file_errors)
        for source_id in source_ids:
            if source_id in all_source_ids:
                errors.append(
                    f"{path}: duplicate sourceID {source_id} also used in {all_source_ids[source_id]}"
                )
            all_source_ids[source_id] = path

    if errors:
        print("Dictionary validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Dictionary validation passed for {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
