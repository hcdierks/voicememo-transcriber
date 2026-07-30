from pathlib import Path

from vmt.models import Segment
from vmt.output import read_transcript, write_transcript


def test_segments_written_in_ascending_start_time(tmp_path: Path):
    segments = [
        Segment(start=5.0, end=6.0, speaker="Jane", text="second"),
        Segment(start=0.0, end=2.0, speaker="Speaker 1", text="first"),
    ]
    json_path, _ = write_transcript(
        recording_id="abc123",
        source_file="memo.m4a",
        recorded_at="2026-07-28T00:00:00+00:00",
        segments=segments,
        transcripts_dir=tmp_path,
    )

    data = read_transcript(json_path)
    assert [s["text"] for s in data["segments"]] == ["first", "second"]


def test_json_round_trips_exactly(tmp_path: Path):
    segments = [Segment(start=0.0, end=1.5, speaker="Bob", text="hello there")]
    json_path, _ = write_transcript(
        recording_id="rec1",
        source_file="memo.m4a",
        recorded_at="2026-07-28T00:00:00+00:00",
        segments=segments,
        transcripts_dir=tmp_path,
    )

    data = read_transcript(json_path)
    assert data["segments"][0] == {"start": 0.0, "end": 1.5, "speaker": "Bob", "text": "hello there"}


def test_markdown_has_one_line_per_segment_with_timestamp(tmp_path: Path):
    segments = [
        Segment(start=0.0, end=1.0, speaker="Speaker 1", text="hi"),
        Segment(start=75.0, end=76.0, speaker="Jane", text="bye"),
    ]
    _, md_path = write_transcript(
        recording_id="rec2",
        source_file="memo.m4a",
        recorded_at="2026-07-28T00:00:00+00:00",
        segments=segments,
        transcripts_dir=tmp_path,
    )

    lines = [line for line in md_path.read_text().splitlines() if line.startswith("**")]
    assert len(lines) == 2
    assert "[00:00]" in lines[0] and "Speaker 1" in lines[0]
    assert "[01:15]" in lines[1] and "Jane" in lines[1]
