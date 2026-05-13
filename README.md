# Flippers Dictionary Pipeline

This workspace owns dictionary source tracking, authoring, validation, and export
for Flippers presets. Keep it outside the iOS app target so source/licensing
metadata, draft entries, and review artifacts do not get bundled accidentally.

## Goals

- Build a traceable in-house dictionary for Jouyou Kanji and default vocabulary.
- Separate official source facts from Flippers-authored Korean meanings and examples.
- Validate completeness before exporting app-ready preset data.
- Make every bundled preset reproducible from reviewed source files.

## Directory Layout

- `sources/official/`: Source notes and raw references for public official data.
- `authoring/`: Human-authored dictionary entries owned by this project.
- `schemas/`: JSON schemas for authored data and exported app presets.
- `scripts/`: Validation and export tooling.
- `exports/`: Generated app-ready preset files. Do not edit by hand.

## Data Ownership Rule

Official Jouyou Kanji facts and project-authored learning content must stay in
separate files.

- Official facts: kanji, official readings, official example words, source labels.
- Project-authored content: Korean meanings, Korean notes, Japanese examples,
  Korean translations, preset tags, and learning metadata.

Do not import third-party dictionary definitions unless the license and required
attribution are recorded in `sources/`.

## Proposed Flow

1. Capture official source metadata under `sources/official/`.
2. Normalize source facts into reviewed authoring rows.
3. Add Flippers-authored Korean meanings and examples under `authoring/`.
4. Run `scripts/validate_dictionary.py`.
5. Export reviewed entries into `exports/` for the iOS app preset importer.

## Current Status

The pipeline scaffold is ready, but the full 2136 Jouyou Kanji dataset has not
been authored yet. The iOS app currently contains only starter sample presets.
