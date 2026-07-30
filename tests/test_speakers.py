from pathlib import Path

import numpy as np

from vmt.models import RawSegment
from vmt.speakers import SpeakerRegistry, match_speaker, resolve_speakers


def _registry(tmp_path: Path) -> SpeakerRegistry:
    return SpeakerRegistry(tmp_path / "registry.json", tmp_path / "embeddings")


def test_near_identical_vector_matches(tmp_path: Path):
    registry = _registry(tmp_path)
    registry.enroll("Jane", np.array([1.0, 0.0, 0.0]))

    assert match_speaker(np.array([0.99, 0.01, 0.0]), registry, threshold=0.75) == "Jane"


def test_dissimilar_vector_does_not_match(tmp_path: Path):
    registry = _registry(tmp_path)
    registry.enroll("Jane", np.array([1.0, 0.0, 0.0]))

    assert match_speaker(np.array([0.0, 1.0, 0.0]), registry, threshold=0.75) is None


def test_empty_registry_never_matches(tmp_path: Path):
    registry = _registry(tmp_path)
    assert match_speaker(np.array([1.0, 0.0, 0.0]), registry, threshold=0.75) is None


def test_multiple_candidates_resolve_to_closest_match(tmp_path: Path):
    registry = _registry(tmp_path)
    registry.enroll("Jane", np.array([1.0, 0.0, 0.0]))
    registry.enroll("Bob", np.array([0.9, 0.1, 0.0]))

    assert match_speaker(np.array([1.0, 0.0, 0.0]), registry, threshold=0.5) == "Jane"


def test_resolve_speakers_matches_known_and_aliases_unknown(tmp_path: Path):
    registry = _registry(tmp_path)
    registry.enroll("Jane", np.array([1.0, 0.0, 0.0]))

    raw_segments = [
        RawSegment(start=0.0, end=2.0, local_speaker="SPEAKER_00", text="hi"),
        RawSegment(start=2.5, end=4.0, local_speaker="SPEAKER_01", text="hello back"),
        RawSegment(start=4.5, end=5.0, local_speaker="SPEAKER_00", text="how are you"),
    ]
    embeddings = {
        "SPEAKER_00": np.array([0.99, 0.01, 0.0]),  # matches Jane
        "SPEAKER_01": np.array([0.0, 1.0, 0.0]),  # unknown
    }

    resolved = resolve_speakers(raw_segments, embeddings, registry, threshold=0.75)

    assert [s.speaker for s in resolved] == ["Jane", "Speaker 1", "Jane"]


def test_alias_numbering_is_stable_by_first_appearance(tmp_path: Path):
    registry = _registry(tmp_path)
    raw_segments = [
        RawSegment(start=0.0, end=1.0, local_speaker="SPEAKER_01", text="a"),
        RawSegment(start=1.5, end=2.0, local_speaker="SPEAKER_00", text="b"),
    ]
    embeddings = {
        "SPEAKER_01": np.array([1.0, 0.0]),
        "SPEAKER_00": np.array([0.0, 1.0]),
    }

    resolved = resolve_speakers(raw_segments, embeddings, registry, threshold=0.75)

    assert resolved[0].speaker == "Speaker 1"
    assert resolved[1].speaker == "Speaker 2"


def test_rename_and_merge_update_registry(tmp_path: Path):
    registry = _registry(tmp_path)
    registry.enroll("Jane", np.array([1.0, 0.0]))
    registry.enroll("Jane2", np.array([0.98, 0.02]))

    registry.rename("Jane2", "Jane (backup mic)")
    assert "Jane (backup mic)" in registry.names()

    registry.merge("Jane (backup mic)", "Jane")
    assert registry.names() == ["Jane"]
