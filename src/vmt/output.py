from __future__ import annotations

import json
from pathlib import Path

from vmt.models import Segment


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


def _render_markdown(source_file: str, ordered_segments: list[dict]) -> str:
    lines = [f"# {source_file}", ""]
    for seg in ordered_segments:
        lines.append(f"**{seg['speaker']}** [{_format_timestamp(seg['start'])}] {seg['text']}")
    return "\n".join(lines) + "\n"


def write_transcript(
    recording_id: str,
    source_file: str,
    recorded_at: str,
    segments: list[Segment],
    transcripts_dir: Path,
) -> tuple[Path, Path]:
    ordered = sorted(segments, key=lambda s: s.start)
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "recording_id": recording_id,
        "source_file": source_file,
        "recorded_at": recorded_at,
        "segments": [
            {"start": s.start, "end": s.end, "speaker": s.speaker, "text": s.text} for s in ordered
        ],
    }

    json_path = transcripts_dir / f"{recording_id}.json"
    md_path = transcripts_dir / f"{recording_id}.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    md_path.write_text(_render_markdown(source_file, payload["segments"]))

    return json_path, md_path


def rewrite_transcript(json_path: Path, md_path: Path, transcript: dict) -> None:
    """Persist an in-memory transcript dict (e.g. after a `vmt review` rename)."""
    json_path.write_text(json.dumps(transcript, indent=2, ensure_ascii=False))
    md_path.write_text(_render_markdown(transcript["source_file"], transcript["segments"]))


def read_transcript(json_path: Path) -> dict:
    return json.loads(json_path.read_text())
