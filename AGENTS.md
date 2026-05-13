# DictionaryPipeline Agent Guide

This repository is managed separately from the Flippers iOS app. Do not move
authoring files, source notes, draft data, or validation artifacts into the app
target.

## Data Boundaries

- Keep official source facts under `sources/official/` or in authoring fields
  that are explicitly official facts.
- Keep Flippers-authored Korean meanings, examples, translations, notes, and
  preset curation under `authoring/`.
- Do not add KANJIDIC2 or other third-party dictionary data until license review
  and attribution requirements are recorded.
- Do not fabricate the 2136 Jouyou Kanji dataset. Add only official facts and
  reviewed project-authored content.

## Export Rules

- `exports/` is generated. Do not edit export JSON by hand.
- Production exports include only entries with `review.status == "reviewed"`.
- Draft sample exports must be written as `*.sample.json` and marked with
  `"exportMode": "sample"`.
- Generated output must be deterministic: sorted inputs, stable `presetID`
  values, and formatted JSON.
- Before bundling the full Jouyou Kanji preset, require exactly 2136 exported
  kanji cards.

## Tooling

- Keep validation and export scripts on the Python standard library unless the
  project intentionally adopts dependencies.
- Run `python3 scripts/validate_dictionary.py` before export.
- Run `python3 scripts/export_presets.py --mode sample` for draft sample output.
- Run `python3 scripts/export_presets.py --mode production --require-complete`
  only when the reviewed Jouyou Kanji set is expected to be complete.
