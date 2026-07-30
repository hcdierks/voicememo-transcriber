# ADR 0002: Voiceprint matching for cross-recording speaker identity

## Status
Accepted

## Context
Diarization alone only separates speakers within a single recording (`SPEAKER_00`, `SPEAKER_01`, ...). To recognize "this is the same person as in last week's recording," the system needs some notion of persistent identity. Two options were considered: manual labeling only (no cross-recording memory), or automatic matching via speaker embeddings ("voiceprints").

## Decision
Extract a voiceprint (via pyannote's embedding model) for each distinct speaker in a recording, and compare it via cosine similarity against a local registry of previously-named speakers. Above a similarity threshold, auto-assign the known name; otherwise fall back to a recording-scoped alias (`Speaker N`).

Enrollment is implicit, not a separate step: when the user labels an alias with a real name via `vmt review`, the segment audio behind that alias becomes the registry entry for that name. There is no dedicated "enroll a person" flow in v1.

## Consequences
- No upfront enrollment burden — the registry grows organically as recordings get reviewed.
- First-time match quality depends on how clean/long the labeled segment was; a short or noisy segment may produce a lower-quality voiceprint and more false-negatives (same person mis-aliased) or false-positives (different person wrongly matched) until re-labeled or merged via `vmt speakers merge`.
- Requires persisting embeddings locally (`data/speakers/embeddings/*.npy`) and a similarity threshold that may need manual tuning (`VMT_SIMILARITY_THRESHOLD`).
- A dedicated `vmt enroll <name> <audio>` command is deferred to future work if implicit enrollment proves insufficient.
