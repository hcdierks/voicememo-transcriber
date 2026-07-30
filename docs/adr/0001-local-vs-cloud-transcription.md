# ADR 0001: Local transcription/diarization instead of a cloud API

## Status
Accepted

## Context
Recordings are private, often unplanned conversations, sometimes involving people who aren't aware transcription tooling exists. A cloud ASR/diarization API (AssemblyAI, Deepgram, etc.) gives higher out-of-the-box accuracy and simpler diarization, at the cost of uploading audio to a third party and a per-minute fee.

## Decision
Run everything locally: `faster-whisper` (via `whisperx`) for ASR, pyannote.audio for diarization and speaker embeddings. No audio or transcript ever leaves the machine as part of the core pipeline.

## Consequences
- No per-recording cost, no dependency on an external service being up.
- Requires local setup: `ffmpeg`, PyTorch, and a Hugging Face account + token to use the gated pyannote models.
- Transcription is slower than a cloud API and bounded by local CPU (or GPU/MPS if available).
- Accuracy on diarization/edge cases (overlapping speech, low audio quality) may be lower than a commercial API; acceptable trade-off given the privacy requirement.
