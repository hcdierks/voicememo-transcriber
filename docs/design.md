# Design

## Overview

`vmt` is a Python CLI. It has four responsibilities, kept in separate modules: find new recordings, run them through ASR + diarization, resolve speaker identity across recordings, and write ordered transcripts.

```
Voice Memos folder ──> discovery.py ──> manifest.py (dedup)
                                             │
                                             v
                                     transcribe.py (whisperx:
                                     ASR + alignment + diarization)
                                             │
                                             v
                                      speakers.py (embed each local
                                      speaker, match vs registry.json)
                                             │
                                             v
                                       output.py (write JSON + MD,
                                       ordered by start time)
```

`vmt review` reads a written transcript, lets the user rename an alias, and writes the corresponding segment's audio embedding into the speaker registry via `speakers.py`, closing the loop for future `vmt process` runs.

## Modules

- **discovery.py** — locates the Voice Memos recordings directory (default: `~/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings`, overridable via config), lists `.m4a` files, computes a content hash (sha256) per file as its stable recording ID.
- **manifest.py** — reads/writes `data/manifest.json`: `{recording_id: {source_path, processed_at, transcript_json, transcript_md}}`. `vmt scan` = files from discovery not present in the manifest.
- **transcribe.py** — wraps `whisperx`: loads the ASR model once, transcribes, aligns word-level timestamps, runs pyannote-based diarization, and returns a list of segments `{start, end, text, local_speaker}` where `local_speaker` is whisperx's raw label (e.g. `SPEAKER_00`).
- **speakers.py** — owns `data/speakers/registry.json` (`{speaker_id: {name, embedding_file}}`) and `data/speakers/embeddings/*.npy`. For each distinct `local_speaker` in a recording, picks its longest contiguous segment, extracts a voiceprint via pyannote's embedding model, and compares (cosine similarity) against the registry. A match above `SIMILARITY_THRESHOLD` (default 0.75, configurable) resolves to that speaker's name; otherwise the local label is renumbered into a recording-scoped alias (`Speaker 1`, `Speaker 2`, ...) in order of first appearance.
- **output.py** — merges resolved speaker labels back into the segment list (already time-ordered from whisperx), writes `data/transcripts/<recording_id>.json` (full structured data) and `.md` (readable `**Speaker 1** [00:01:23] text` per line).
- **review.py** — loads a transcript JSON, presents aliases and a sample line of dialogue for each, prompts for a real name (or skip), rewrites the transcript files with the new name, and calls into `speakers.py` to save that alias's embedding under the given name.
- **viewer.py** — renders a self-contained HTML page for a transcript: an `<audio>` element pointing directly at the original recording (`file://`, nothing copied) plus the segment list below it, color-coded by speaker, each line clickable to seek playback there, with the currently-playing segment auto-highlighted via `timeupdate`. Used to visually validate diarization/speaker-matching accuracy against the real audio.
- **config.py** — resolves settings from `~/.config/vmt/config.toml`, falling back to env vars (`VMT_DATA_DIR`, `HF_TOKEN`, `VMT_WHISPER_MODEL`, `VMT_SIMILARITY_THRESHOLD`) and then defaults. Default data dir: `<repo>/data`.
- **cli.py** — Typer app wiring `scan`, `process`, `review`, `view`, `speakers list/rename/merge` to the modules above.

## Data formats

`data/transcripts/<id>.json`:
```json
{
  "recording_id": "sha256:...",
  "source_file": "20260728 143210.m4a",
  "recorded_at": "2026-07-28T14:32:10",
  "segments": [
    {"start": 0.0, "end": 4.2, "speaker": "Speaker 1", "text": "..."},
    {"start": 4.4, "end": 9.1, "speaker": "Jane", "text": "..."}
  ]
}
```
Markdown mirrors the same segments as `**Speaker** [mm:ss] text`, one line per segment, in order.

## Why whisperx instead of separate Whisper + pyannote glue code

Combining raw Whisper output with raw pyannote diarization output requires aligning word/segment timestamps against diarization time ranges — a nontrivial and error-prone step. `whisperx` already implements this (ASR → forced alignment → diarization → speaker-tagged segments) using faster-whisper and pyannote under the hood, which matches the "local Whisper + pyannote" decision while avoiding reimplementing the alignment logic. See [ADR 0001](adr/0001-local-vs-cloud-transcription.md).

## Why identity is resolved via embeddings rather than diarization labels alone

pyannote's diarization only distinguishes speakers *within* one recording (`SPEAKER_00`, `SPEAKER_01`, ...) — it has no concept of identity across files. Cross-recording identity requires comparing voiceprints. See [ADR 0002](adr/0002-voiceprint-matching-for-speaker-id.md).
