from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

AUDIO_EXTENSION = ".m4a"
_HASH_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class Recording:
    recording_id: str
    path: Path

    @property
    def filename(self) -> str:
        return self.path.name


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(_HASH_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def find_recordings(recordings_dir: Path) -> list[Recording]:
    if not recordings_dir.exists():
        return []
    files = sorted(
        p for p in recordings_dir.iterdir() if p.is_file() and p.suffix.lower() == AUDIO_EXTENSION
    )
    return [Recording(recording_id=hash_file(p), path=p) for p in files]
