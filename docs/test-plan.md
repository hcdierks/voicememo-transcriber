# Test Plan

## Scope

Unit tests cover the deterministic, non-ML parts of the pipeline: manifest tracking, speaker-matching math, and output formatting. They run in CI on every push and require no model downloads, no Hugging Face token, and no real audio.

ASR/diarization itself (`transcribe.py`'s use of `whisperx`) is integration-tested manually against real Voice Memos, since it needs gated models and meaningful audio input — not something worth mocking convincingly in CI.

## Automated (CI): `pytest`, `.[core,dev]` only

| Area | What's verified |
|---|---|
| `manifest.py` | New recording → not in manifest → `scan` reports it. After `mark_processed`, `scan` no longer reports it. Manifest round-trips through JSON. Corrupt/missing manifest file is treated as empty, not a crash. |
| `discovery.py` | Content hash is stable for identical bytes and differs for different bytes. Non-`.m4a` files are ignored. |
| `speakers.py` (matching logic) | Given synthetic embedding vectors: a near-identical vector matches an existing registry entry above threshold; an orthogonal/dissimilar vector does not match and falls back to alias; ties/multiple candidates resolve to the closest match; empty registry never matches. |
| `output.py` | Segments are written in ascending `start` time regardless of input order. JSON round-trips exactly. Markdown contains one line per segment with speaker name/alias and `mm:ss` timestamp. Alias numbering is stable and starts at 1, assigned in order of first appearance. |
| `review.py` (rename logic) | Renaming an alias updates all segments with that alias in both JSON and Markdown outputs, and only those segments. |

## Manual / local verification (not in CI)

1. Grant Full Disk Access, set `HF_TOKEN`, install `ffmpeg`.
2. `vmt scan` against real Voice Memos shows the expected unprocessed recordings.
3. `vmt process` on one short multi-speaker recording produces a JSON+MD transcript with correct chronological order and plausible speaker splits.
4. `vmt review` renames an alias; re-running `vmt process` on a *different* recording of the same person auto-matches that name.
5. Re-running `vmt process`/`vmt scan` after a successful run shows zero new work (idempotency).

## CI

`.github/workflows/ci.yml` runs on every push/PR: install `.[core,dev]`, `ruff check`, `pytest`.
