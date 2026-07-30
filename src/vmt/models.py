from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RawSegment:
    """A transcribed segment before cross-recording speaker identity is resolved."""

    start: float
    end: float
    local_speaker: str
    text: str


@dataclass(frozen=True)
class Segment:
    """A transcribed segment with its final speaker name or alias."""

    start: float
    end: float
    speaker: str
    text: str
