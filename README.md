# voicememo-transcriber

Local-first CLI that transcribes and diarizes Apple Voice Memos recordings, and
recognizes speakers across recordings by voice — no audio ever leaves the
machine. See [`docs/requirements.md`](docs/requirements.md) and
[`docs/design.md`](docs/design.md) for the full requirements and design.

## Prerequisites (one-time setup)

1. **Full Disk Access.** macOS blocks direct access to the Voice Memos data
   folder. Grant Full Disk Access under **System Settings → Privacy &
   Security → Full Disk Access** to whichever app *actually* runs your
   terminal process — not necessarily "Terminal". If you use an editor's
   integrated terminal (VS Code, etc.), grant access to the editor app
   itself, then fully quit and reopen it (permission changes need a
   restart). If unsure what's running your shell, run:
   `ps -o pid,ppid,comm -p $$` and walk up the `ppid` chain.
2. **ffmpeg:**
   ```
   brew install ffmpeg
   ```
3. **Hugging Face account + token**, for the gated pyannote models this
   pipeline uses:
   - Create a free account at huggingface.co.
   - Accept the model licenses (each is an instant "Agree and access
     repository" click, not manual review) at:
     - `hf.co/pyannote/speaker-diarization-3.1`
     - `hf.co/pyannote/segmentation-3.0`
     - `hf.co/pyannote/embedding`
     - `hf.co/pyannote/speaker-diarization-community-1` — a newer model
       that `speaker-diarization-3.1`'s pipeline config now depends on
       server-side for its clustering step, even though we don't call it
       directly. Easy to miss; you'll hit a `GatedRepoError` mentioning it
       if you skip this one.
   - Create a **Read**-scoped access token at huggingface.co/settings/tokens
     and save it — don't paste it into a chat/AI session. Either:
     `export HF_TOKEN=hf_...`, or write it directly to
     `~/.config/vmt/config.toml` yourself (see Configuration below).
4. **Python 3.11+ SSL certificates**, if you're on the python.org installer
   build (not Homebrew's Python): it ships without a wired-up CA bundle,
   which breaks HTTPS downloads (you'll see
   `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`
   the first time a model downloads). Fix once with:
   ```
   "/Applications/Python 3.11/Install Certificates.command"
   ```
5. **Python 3.11+** and a virtualenv:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[core,ml,dev]"
   ```
   `ml` pulls in PyTorch/whisperx/pyannote.audio and is only needed to
   actually run transcription — not for running the test suite.

## Usage

### 1. See what's new

```
source .venv/bin/activate
vmt scan
```
Lists Voice Memos not yet in the local manifest, e.g.:
```
9336c71c079f  20260624 192043-08C0ECF2.m4a
```

### 2. Process them

```
vmt process                # transcribe + diarize every unprocessed recording
vmt process --file PATH    # or just one, by path
```
This is CPU-bound and slow — on a CPU-only Mac, expect roughly **2x real-time**
per recording (a 10-minute memo takes ~20 minutes) with the default `small`
Whisper model. Safe to interrupt (Ctrl-C): already-completed recordings are
marked processed in the manifest and won't be redone; re-run the same command
to pick up where you left off. For a large backlog, consider running it in
the background/overnight, e.g.:
```
nohup vmt process > process.log 2>&1 &
```
then check progress with `tail -f process.log` or `vmt scan` (shrinking list
= progress). Switching `whisper_model` to `base` or `tiny` in
`~/.config/vmt/config.toml` trades accuracy for speed if the backlog is large.

Output lands at `data/transcripts/<recording_id>.json` and `.md` — the
`.md` is the one to just read; the `.json` is for scripting against. The
`recording_id` is a content hash, printed by `vmt scan`/`vmt process` and
also usable as a filename prefix (`ls data/transcripts/`). The whole `data/`
directory (recordings cache, transcripts, speaker voiceprints, manifest) is
git-ignored — private and machine-local. Override its location with
`VMT_DATA_DIR` if desired.

### 3. Teach it who's speaking

Every recording starts with unlabeled aliases (`Speaker 1`, `Speaker 2`, ...).
Naming one *enrolls* that voice, so it's auto-recognized in future recordings
without you having to label it again:

```
vmt review <recording_id>
```
Interactively walks through each unlabeled alias in that transcript, shows a
sample line, and prompts for a real name (blank = skip). Or, non-interactively
for a specific alias:
```
vmt review <recording_id> --alias "Speaker 1" --name "Jane"
```
Both rewrite that recording's `.json`/`.md` in place and save a voiceprint
under `data/speakers/embeddings/`. From then on, `vmt process` on any *new*
recording containing Jane's voice will label her segments `Jane` directly
instead of a fresh alias (similarity threshold configurable, see below).

Manage the registry directly with:
```
vmt speakers list
vmt speakers rename OLD NEW
vmt speakers merge SOURCE INTO   # two aliases turned out to be the same person
```

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
