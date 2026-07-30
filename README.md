# voicememo-transcriber

Local-first CLI that transcribes and diarizes Apple Voice Memos recordings, and
recognizes speakers across recordings by voice — no audio ever leaves the
machine. See [`docs/requirements.md`](docs/requirements.md) and
[`docs/design.md`](docs/design.md) for the full requirements and design.

## Prerequisites (one-time setup)

1. **Full Disk Access.** macOS blocks direct access to the Voice Memos data
   folder. Grant Full Disk Access to whichever app hosts your terminal (e.g.
   Terminal.app, iTerm, or your editor's integrated terminal) under
   **System Settings → Privacy & Security → Full Disk Access**.
2. **ffmpeg:**
   ```
   brew install ffmpeg
   ```
3. **Hugging Face account + token**, for the gated pyannote diarization/embedding
   models:
   - Create a free account at huggingface.co.
   - Accept the model licenses at `hf.co/pyannote/speaker-diarization-3.1` and
     `hf.co/pyannote/embedding` (or whichever current versions `whisperx`/
     `pyannote.audio` resolve to).
   - Create a read-scoped access token and set it: `export HF_TOKEN=hf_...`
     (or put it in `~/.config/vmt/config.toml`, see below).
4. **Python 3.11+** and a virtualenv:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[core,ml,dev]"
   ```
   `ml` pulls in PyTorch/whisperx/pyannote.audio and is only needed to
   actually run transcription — not for running the test suite.

## Usage

```
vmt scan                  # list unprocessed Voice Memos
vmt process                # transcribe + diarize all unprocessed recordings
vmt process --file PATH   # process a single recording
vmt review <recording_id> # rename Speaker N aliases to real names
vmt speakers list
vmt speakers rename OLD NEW
vmt speakers merge SOURCE INTO
```

Transcripts are written to `data/transcripts/<recording_id>.{json,md}`. The
`data/` directory (recordings cache, transcripts, speaker voiceprints,
manifest) is git-ignored — it's private and machine-local. Override its
location with `VMT_DATA_DIR` if desired.

Speaker identity is a growing local registry: the first time a voice shows up
it becomes `Speaker 1`, `Speaker 2`, etc.; running `vmt review` and naming an
alias enrolls that voice, so it's auto-recognized in future recordings.

## Configuration

`~/.config/vmt/config.toml` (all optional, env vars override):

```toml
data_dir = "/path/to/data"
recordings_dir = "/path/to/voice/memos"
whisper_model = "small"          # tiny|base|small|medium|large-v3
similarity_threshold = 0.75      # cosine similarity for speaker matching
hf_token = "hf_..."
```

## Development

```
pip install -e ".[core,dev]"     # no ML deps needed for tests
ruff check src tests
pytest
```

CI runs lint + the unit test suite (manifest, discovery, speaker-matching
math, output formatting, review logic) on every push — see
[`docs/test-plan.md`](docs/test-plan.md) for what is and isn't covered by
automated tests, and why.

## Legal note

Recording conversations may require the consent of all parties depending on
your jurisdiction. This tool does not verify or enforce consent — that's on
whoever operates it.
