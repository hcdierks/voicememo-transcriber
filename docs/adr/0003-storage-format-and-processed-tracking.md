# ADR 0003: Local file storage with a manifest, not a database

## Status
Accepted

## Context
Need to (a) know which Voice Memos have already been processed, so re-runs are cheap and idempotent, and (b) store transcripts in a way that's easy to read, diff, and search without extra tooling.

## Decision
- Transcripts are written as a JSON file (structured) and a Markdown file (readable) per recording under `data/transcripts/`.
- A single `data/manifest.json` tracks processed recordings, keyed by a sha256 content hash of the source audio file (not filename — Voice Memos filenames aren't guaranteed stable/unique).
- The speaker registry (`data/speakers/registry.json` + `.npy` embedding files) is likewise plain files, not a database.

## Consequences
- No database dependency; everything is human-inspectable and versionable with plain diffing tools if the user ever chooses to.
- Content-hash keys mean renaming or re-syncing a Voice Memo doesn't cause reprocessing, but two byte-identical recordings would collide (accepted — Voice Memos audio is effectively unique per recording).
- At personal-scale volumes (dozens to low hundreds of recordings), JSON manifest scanning is fast enough; if volume grows into the thousands, revisit in favor of SQLite (noted in requirements as future work, not built now since it isn't needed yet).
