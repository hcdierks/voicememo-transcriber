from __future__ import annotations

from vmt.config import Config
from vmt.speakers import ALIAS_PATTERN, SpeakerRegistry, extract_embedding


def list_aliases(transcript: dict) -> list[str]:
    """Unlabeled aliases (Speaker N), in order of first appearance."""
    seen: list[str] = []
    for seg in transcript["segments"]:
        speaker = seg["speaker"]
        if ALIAS_PATTERN.match(speaker) and speaker not in seen:
            seen.append(speaker)
    return seen


def sample_line(transcript: dict, alias: str) -> str | None:
    for seg in transcript["segments"]:
        if seg["speaker"] == alias:
            return seg["text"]
    return None


def rename_alias(transcript: dict, alias: str, new_name: str) -> dict:
    updated = dict(transcript)
    updated["segments"] = [
        {**seg, "speaker": new_name} if seg["speaker"] == alias else seg
        for seg in transcript["segments"]
    ]
    return updated


def _longest_segment_for_alias(transcript: dict, alias: str) -> dict | None:
    candidates = [seg for seg in transcript["segments"] if seg["speaker"] == alias]
    if not candidates:
        return None
    return max(candidates, key=lambda seg: seg["end"] - seg["start"])


def apply_rename_and_enroll(
    config: Config,
    transcript: dict,
    alias: str,
    new_name: str,
    registry: SpeakerRegistry,
) -> dict:
    """Rename `alias` to `new_name` and enroll a voiceprint for future matching."""
    segment = _longest_segment_for_alias(transcript, alias)
    updated = rename_alias(transcript, alias, new_name)

    if segment is not None:
        source_path = config.recordings_dir / transcript["source_file"]
        if source_path.exists():
            embedding = extract_embedding(
                source_path, segment["start"], segment["end"], config.hf_token
            )
            registry.enroll(new_name, embedding)

    return updated
