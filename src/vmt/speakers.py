from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from vmt.models import RawSegment, Segment

ALIAS_PATTERN = re.compile(r"^Speaker \d+$")


class SpeakerRegistry:
    """Persists known speakers as name -> voiceprint (.npy) file."""

    def __init__(self, registry_path: Path, embeddings_dir: Path):
        self.registry_path = registry_path
        self.embeddings_dir = embeddings_dir
        self._names_to_file: dict[str, str] = self._load()

    def _load(self) -> dict[str, str]:
        if not self.registry_path.exists():
            return {}
        try:
            return json.loads(self.registry_path.read_text())
        except json.JSONDecodeError:
            return {}

    def _save(self) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(json.dumps(self._names_to_file, indent=2, sort_keys=True))

    def names(self) -> list[str]:
        return list(self._names_to_file.keys())

    def embedding_for(self, name: str) -> np.ndarray | None:
        filename = self._names_to_file.get(name)
        if filename is None:
            return None
        path = self.embeddings_dir / filename
        if not path.exists():
            return None
        return np.load(path)

    def enroll(self, name: str, embedding: np.ndarray) -> None:
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{_slug(name)}.npy"
        np.save(self.embeddings_dir / filename, embedding)
        self._names_to_file[name] = filename
        self._save()

    def rename(self, old_name: str, new_name: str) -> None:
        if old_name not in self._names_to_file:
            raise KeyError(old_name)
        filename = self._names_to_file.pop(old_name)
        self._names_to_file[new_name] = filename
        self._save()

    def merge(self, source_name: str, into_name: str) -> None:
        """Drop `source_name`; `into_name` remains the canonical identity.

        Existing transcripts already written under `source_name` are not
        rewritten automatically -- re-run `vmt review` on them if needed.
        """
        if source_name not in self._names_to_file:
            raise KeyError(source_name)
        if into_name not in self._names_to_file:
            raise KeyError(into_name)
        del self._names_to_file[source_name]
        self._save()


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "speaker"


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def match_speaker(embedding: np.ndarray, registry: SpeakerRegistry, threshold: float) -> str | None:
    """Return the best-matching known speaker name above `threshold`, or None."""
    best_name: str | None = None
    best_score = threshold
    for name in registry.names():
        candidate = registry.embedding_for(name)
        if candidate is None:
            continue
        score = cosine_similarity(embedding, candidate)
        if score >= best_score:
            best_name = name
            best_score = score
    return best_name


def resolve_speakers(
    raw_segments: list[RawSegment],
    embeddings_by_local_speaker: dict[str, np.ndarray],
    registry: SpeakerRegistry,
    threshold: float,
) -> list[Segment]:
    """Map each segment's local (per-recording) speaker label to either a
    known registry name or a stable alias, assigned in order of first
    appearance, then return segments in chronological order."""
    ordered = sorted(raw_segments, key=lambda s: s.start)

    resolved: dict[str, str] = {}
    alias_counter = 0
    for raw in ordered:
        if raw.local_speaker in resolved:
            continue
        embedding = embeddings_by_local_speaker.get(raw.local_speaker)
        matched = match_speaker(embedding, registry, threshold) if embedding is not None else None
        if matched:
            resolved[raw.local_speaker] = matched
        else:
            alias_counter += 1
            resolved[raw.local_speaker] = f"Speaker {alias_counter}"

    return [
        Segment(start=raw.start, end=raw.end, speaker=resolved[raw.local_speaker], text=raw.text)
        for raw in ordered
    ]


def _load_waveform(audio_path: Path, sample_rate: int = 16000) -> dict:
    """Decode audio to an in-memory mono waveform via an ffmpeg subprocess.

    Bypasses pyannote's built-in file decoding (torchcodec), which requires
    ffmpeg 4-7 and is incompatible with newer Homebrew ffmpeg builds. This
    mirrors how whisperx itself loads audio.
    """
    import subprocess

    import torch

    cmd = [
        "ffmpeg",
        "-nostdin",
        "-threads",
        "0",
        "-i",
        str(audio_path),
        "-f",
        "s16le",
        "-ac",
        "1",
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(sample_rate),
        "-",
    ]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    samples = np.frombuffer(out, np.int16).astype(np.float32) / 32768.0
    waveform = torch.from_numpy(samples).unsqueeze(0)  # (channel, time)
    return {"waveform": waveform, "sample_rate": sample_rate}


def extract_embedding(audio_path: Path, start: float, end: float, hf_token: str | None) -> np.ndarray:
    """Extract a voiceprint for a time range using pyannote's embedding model.

    Imported lazily so unit tests for matching logic don't need torch/pyannote.
    """
    from pyannote.audio import Inference, Model
    from pyannote.core import Segment as PyannoteSegment

    model = Model.from_pretrained("pyannote/embedding", token=hf_token)
    inference = Inference(model, window="whole")
    file = _load_waveform(audio_path)

    duration = file["waveform"].shape[-1] / file["sample_rate"]
    end = min(end, duration - (1 / file["sample_rate"]))
    start = min(start, end)

    return np.asarray(inference.crop(file, PyannoteSegment(start, end))).reshape(-1)
