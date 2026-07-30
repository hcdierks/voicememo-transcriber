from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class ManifestEntry:
    source_path: str
    processed_at: str
    transcript_json: str
    transcript_md: str


class Manifest:
    """Tracks which recordings (by content hash) have already been processed."""

    def __init__(self, path: Path):
        self._path = path
        self._entries: dict[str, ManifestEntry] = self._load()

    def _load(self) -> dict[str, ManifestEntry]:
        if not self._path.exists():
            return {}
        try:
            raw = json.loads(self._path.read_text())
        except json.JSONDecodeError:
            return {}
        return {recording_id: ManifestEntry(**data) for recording_id, data in raw.items()}

    def is_processed(self, recording_id: str) -> bool:
        return recording_id in self._entries

    def mark_processed(
        self,
        recording_id: str,
        source_path: Path,
        transcript_json: Path,
        transcript_md: Path,
    ) -> None:
        self._entries[recording_id] = ManifestEntry(
            source_path=str(source_path),
            processed_at=datetime.now(UTC).isoformat(),
            transcript_json=str(transcript_json),
            transcript_md=str(transcript_md),
        )
        self._save()

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {recording_id: vars(entry) for recording_id, entry in self._entries.items()}
        self._path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, recording_id: str) -> bool:
        return recording_id in self._entries
