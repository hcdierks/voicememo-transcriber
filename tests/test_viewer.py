import re

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


def test_audio_src_uses_the_given_url():
    out = render_html("rec1", _transcript(), audio_url="/audio/rec1")
    assert 'src="/audio/rec1"' in out


def test_recording_id_embedded_for_client_side_use():
    out = render_html("abc123", _transcript(), audio_url="/audio/abc123")
    assert 'RECORDING_ID = "abc123"' in out


def test_each_segment_rendered_with_timestamp_and_text():
    out = render_html("rec1", _transcript(), audio_url="/audio/rec1")
    assert "00:00" in out
    assert "00:04" in out
    assert "00:09" in out
    assert "hi there" in out
    assert "hello back" in out
    assert "how are you" in out


def test_same_speaker_gets_same_color_across_segments():
    out = render_html("rec1", _transcript(), audio_url="/audio/rec1")
    matches = _SPEAKER_COLOR_RE.findall(out)
    speaker_1_colors = {color for color, name in matches if name == "Speaker 1"}
    assert len(speaker_1_colors) == 1


def test_different_speakers_get_different_colors():
    out = render_html("rec1", _transcript(), audio_url="/audio/rec1")
    colors = _speaker_colors_in(out)
    assert colors["Speaker 1"] != colors["Jane"]


def test_text_is_html_escaped():
    transcript = {
        "source_file": "memo.m4a",
        "segments": [
            {"start": 0.0, "end": 1.0, "speaker": "Speaker 1", "text": "<script>alert(1)</script>"},
        ],
    }
    out = render_html("rec1", transcript, audio_url="/audio/rec1")
    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;" in out


def test_unlabeled_alias_gets_rename_link_but_named_speaker_does_not():
    out = render_html("rec1", _transcript(), audio_url="/audio/rec1")
    assert 'data-alias="Speaker 1"' in out
    assert 'data-alias="Jane"' not in out
