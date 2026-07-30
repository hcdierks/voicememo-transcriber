# Requirements

## Problem

Conversations are recorded on iPhone via Voice Memos and synced to this Mac. There is currently no way to get a searchable, speaker-attributed transcript of them without manual work.

## Goals (v1)

1. Detect Voice Memos recordings that haven't been processed yet.
2. Transcribe each recording's audio to text.
3. Split the conversation by speaker (diarization).
4. Attach a name to each speaker where known; otherwise assign a stable alias (`Speaker 1`, `Speaker 2`, ...) scoped to that recording.
5. Produce an exact, ordered transcript: every contribution, in the order it occurred, tagged with a timestamp and a speaker.
6. Let previously-unknown speakers be named after the fact, and have that identity carry forward to future recordings of the same voice.

## Non-goals (v1)

- Real-time/streaming transcription.
- A GUI. This is a CLI tool.
- Automated background processing (no watcher/daemon) — runs are user-triggered.
- Cloud transcription or any upload of audio/transcripts to third-party services.
- Multi-user / multi-machine sync of speaker registry or transcripts.

## Functional requirements

- FR1: `vmt scan` lists Voice Memos recordings not yet present in the local processed-manifest.
- FR2: `vmt process` transcribes and diarizes unprocessed recordings (or a specific file), writing a transcript.
- FR3: Transcript output includes, per segment: start timestamp (relative to recording start), speaker label, and exact text — in chronological order.
- FR4: Each recording is written as both a machine-readable JSON file and a human-readable Markdown file.
- FR5: Speakers with no registry match get a per-recording alias (`Speaker 1`, `Speaker 2`, ...); numbering is stable within a recording.
- FR6: `vmt review <recording>` lets the user rename an alias to a real name for that recording; the underlying voice sample is retained so future recordings of the same voice are auto-labeled.
- FR7: Re-running `vmt process` never re-processes a recording already in the manifest (idempotent, based on content hash).
- FR8: `vmt speakers list|rename|merge` manages the known-speaker registry (e.g. merging two aliases discovered to be the same person).

## Non-functional requirements

- NFR1: All audio processing happens on-device. No network calls to transcribe or diarize audio.
- NFR2: Raw audio, transcripts, and the speaker registry are never committed to the git repository (only code is).
- NFR3: The tool must not modify or delete the original Voice Memos recordings.
- NFR4: Processing must be resumable/interruptible without corrupting the manifest or partially-written transcripts.

## Constraints / external dependencies

- Requires macOS Full Disk Access granted to the terminal/host process, to read `~/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings`.
- Requires a Hugging Face account + accepted license + access token for the gated pyannote diarization/embedding models.
- Requires `ffmpeg` installed on the machine.

## Legal/ethical note (not enforced in software)

Some jurisdictions require the consent of all parties to record a conversation. This tool does not attempt to verify or enforce consent — that responsibility rests with the person operating it.

## Open questions / future work

- Background/automated processing (launchd watcher).
- Exporting transcripts to other tools (e.g. Obsidian, search index).
