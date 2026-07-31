import re
from pathlib import Path

from vmt.viewer import render_html

_SPEAKER_COLOR_RE = re.compile(r'<span class="speaker" style="color:(#[0-9A-Fa-f]{6})">([^<]+)</span>')


def _speaker_colors_in(html: str) -> dict[str, str]:
    return {name: color for color, name in _SPEAKER_COLOR_RE.findall(html)}


def _transcript():
    return {
        "recording_id": "rec1",
        "source_file": "memo.m4a",
        "recorded_at": "2026-07-28T00:00:00+00:00",
        "segments": [
            {"start": 0.0, "end": 4.2, "speaker": "Speaker 1", "text": "hi there"},
            {"start": 4.4, "end": 9.1, "speaker": "Jane", "text": "hello back"},
            {"start": 9.5, "end": 12.0, "speaker": "Speaker 1", "text": "how are you"},
        ],
    }


def test_audio_src_is_file_url_with_encoded_path(tmp_path: Path):
    audio_path = tmp_path / "20260630 101502.m4a"
    audio_path.write_bytes(b"fake audio")

    out = render_html(_transcript(), audio_path)

    assert "file://" in out
    assert "20260630%20101502.m4a" in out


def test_each_segment_rendered_with_timestamp_and_text(tmp_path: Path):
    audio_path = tmp_path / "memo.m4a"
    audio_path.write_bytes(b"x")

    out = render_html(_transcript(), audio_path)

    assert "00:00" in out
    assert "00:04" in out
    assert "00:09" in out
    assert "hi there" in out
    assert "hello back" in out
    assert "how are you" in out


def test_same_speaker_gets_same_color_across_segments(tmp_path: Path):
    audio_path = tmp_path / "memo.m4a"
    audio_path.write_bytes(b"x")

    out = render_html(_transcript(), audio_path)

    # "Speaker 1" appears in segments 0 and 2 -- both occurrences must match.
    matches = _SPEAKER_COLOR_RE.findall(out)
    speaker_1_colors = {color for color, name in matches if name == "Speaker 1"}
    assert len(speaker_1_colors) == 1


def test_different_speakers_get_different_colors(tmp_path: Path):
    audio_path = tmp_path / "memo.m4a"
    audio_path.write_bytes(b"x")

    out = render_html(_transcript(), audio_path)

    colors = _speaker_colors_in(out)
    assert colors["Speaker 1"] != colors["Jane"]


def test_text_is_html_escaped(tmp_path: Path):
    audio_path = tmp_path / "memo.m4a"
    audio_path.write_bytes(b"x")
    transcript = {
        "source_file": "memo.m4a",
        "segments": [
            {"start": 0.0, "end": 1.0, "speaker": "Speaker 1", "text": "<script>alert(1)</script>"},
        ],
    }

    out = render_html(transcript, audio_path)

    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;" in out
