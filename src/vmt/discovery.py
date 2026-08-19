from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

AUDIO_EXTENSION = ".m4a"
_HASH_CHUNK_SIZE = 1024 * 1024

# recording_id is always a sha256 hex digest (see hash_file below). Any value not
# matching this shape is untrusted input and must never be used to build a path.
RECORDING_ID_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def is_valid_recording_id(recording_id: str) -> bool:
    return bool(RECORDING_ID_PATTERN.match(recording_id))


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
