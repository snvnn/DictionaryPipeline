#!/usr/bin/env python3
"""Export reviewed Flippers dictionary authoring files into app-ready presets."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUTHORING_DIR = ROOT / "authoring"
EXPORTS_DIR = ROOT / "exports"

PRESET_CONFIG = {
    "jouyou-kanji-authoring": {
        "id": "jouyou-kanji-v1",
        "title": "상용 한자 2136",
        "subtitle": "상용 한자표 기반 한자 프리셋",
        "sourceLabel": "Flippers authored content + official Jouyou Kanji facts",
        "expectedCardCount": 2136,
        "cardType": "kanji",
    },
    "basic-vocabulary-authoring": {
        "id": "basic-vocabulary-v1",
        "title": "기본 단어",
        "subtitle": "초기 학습용 일본어 기본 단어 세트",
        "sourceLabel": "Flippers authored content",
        "expectedCardCount": None,
        "cardType": "word",
    },
}


class ExportError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")


def normalized_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def make_example(content: dict[str, Any]) -> str:
    parts = [
        normalized_text(content.get("exampleJP")),
        normalized_text(content.get("exampleReading")),
        normalized_text(content.get("exampleKO")),
    ]
    return " / ".join(part for part in parts if part)


def preset_id_for(preset_id: str, source_id: str) -> str:
    match = re.search(r"(\d+)$", source_id)
    if match:
        return f"{preset_id}-{match.group(1)}"
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", source_id).strip("-").lower()
    return f"{preset_id}-{slug}"


def export_card(kind: str, preset_id: str, preset_version: int, entry: dict[str, Any]) -> dict[str, Any]:
    content = entry.get("flippersContent", {})
    source_id = normalized_text(entry.get("sourceID"))
    card = {
        "presetID": preset_id_for(preset_id, source_id),
        "presetVersion": preset_version,
        "sourceLabel": PRESET_CONFIG[kind]["sourceLabel"],
        "type": PRESET_CONFIG[kind]["cardType"],
    }

    if kind == "jouyou-kanji-authoring":
        readings = entry.get("officialReadings", {})
        card.update(
            {
                "kanji": normalized_text(entry.get("kanji")),
                "meaning": normalized_text(content.get("koMeaning")),
                "onyomi": ", ".join(readings.get("onyomi", [])),
                "kunyomi": ", ".join(readings.get("kunyomi", [])),
                "example": make_example(content),
            }
        )
    elif kind == "basic-vocabulary-authoring":
        card.update(
            {
                "word": normalized_text(entry.get("word")),
                "reading": normalized_text(entry.get("reading")),
                "meaning": normalized_text(content.get("koMeaning")),
                "example": make_example(content),
            }
        )
    else:
        raise ExportError(f"Unsupported authoring kind: {kind}")

    return card


def reviewed_entries(data: dict[str, Any], include_drafts: bool) -> list[dict[str, Any]]:
    entries = data.get("entries", [])
    selected: list[dict[str, Any]] = []
    for entry in entries:
        status = entry.get("review", {}).get("status")
        if status == "reviewed" or (include_drafts and status == "draft"):
            selected.append(entry)
    return sorted(selected, key=lambda item: normalized_text(item.get("sourceID")))


def validate_export(preset: dict[str, Any], require_complete: bool) -> list[str]:
    errors: list[str] = []
    cards = preset.get("cards", [])
    seen_preset_ids: set[str] = set()

    if (
        require_complete
        and preset["exportMode"] == "production"
        and preset["id"] == "jouyou-kanji-v1"
        and len(cards) != 2136
    ):
        errors.append(f"{preset['id']}: expected 2136 cards, found {len(cards)}")

    for index, card in enumerate(cards, start=1):
        label = f"{preset['id']}:{index}"
        preset_id = normalized_text(card.get("presetID"))
        if not preset_id:
            errors.append(f"{label}: missing presetID")
        elif preset_id in seen_preset_ids:
            errors.append(f"{label}: duplicate presetID {preset_id}")
        seen_preset_ids.add(preset_id)

        for field in ("presetVersion", "sourceLabel", "type", "meaning", "example"):
            if card.get(field) in (None, ""):
                errors.append(f"{label}: missing {field}")

        if card.get("type") == "word":
            for field in ("word", "reading"):
                if not normalized_text(card.get(field)):
                    errors.append(f"{label}: missing {field}")
        elif card.get("type") == "kanji":
            for field in ("kanji", "onyomi", "kunyomi"):
                if field in {"onyomi", "kunyomi"}:
                    continue
                if not normalized_text(card.get(field)):
                    errors.append(f"{label}: missing {field}")
        else:
            errors.append(f"{label}: invalid type {card.get('type')!r}")

    return errors


def export_file(path: Path, mode: str, require_complete: bool) -> tuple[Path, int, str] | None:
    data = load_json(path)
    kind = data.get("kind")
    if kind not in PRESET_CONFIG:
        raise ExportError(f"{path}: unsupported kind {kind!r}")

    config = PRESET_CONFIG[kind]
    include_drafts = mode == "sample"
    cards = [
        export_card(kind, config["id"], data["version"], entry)
        for entry in reviewed_entries(data, include_drafts)
    ]
    if mode == "production" and not cards:
        return None
    preset = {
        "id": config["id"],
        "title": config["title"],
        "subtitle": config["subtitle"],
        "version": data["version"],
        "sourceLabel": config["sourceLabel"],
        "expectedCardCount": config["expectedCardCount"] or len(cards),
        "exportMode": mode,
        "cards": cards,
    }

    errors = validate_export(preset, require_complete)
    if errors:
        raise ExportError("\n".join(errors))

    suffix = ".sample" if mode == "sample" else ""
    output_path = EXPORTS_DIR / f"{config['id']}{suffix}.json"
    write_json(output_path, preset)
    return output_path, len(cards), config["id"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("production", "sample"),
        default="production",
        help="production exports reviewed rows only; sample also includes draft rows and writes *.sample.json",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="fail unless the Jouyou Kanji production export contains exactly 2136 cards",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = sorted(AUTHORING_DIR.glob("*.json"))
    if not files:
        print(f"No authoring files found under {AUTHORING_DIR}", file=sys.stderr)
        return 1

    try:
        results = [
            result
            for path in files
            if (result := export_file(path, args.mode, args.require_complete)) is not None
        ]
    except (ExportError, KeyError, TypeError, json.JSONDecodeError) as error:
        print("Preset export failed:", file=sys.stderr)
        print(error, file=sys.stderr)
        return 1

    exported_ids = {preset_id for _, _, preset_id in results}
    if args.mode == "production" and args.require_complete and "jouyou-kanji-v1" not in exported_ids:
        print("Preset export failed:", file=sys.stderr)
        print("jouyou-kanji-v1: expected 2136 cards, found no production export", file=sys.stderr)
        return 1

    for output_path, card_count, _ in results:
        print(f"Exported {card_count} card(s) to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
