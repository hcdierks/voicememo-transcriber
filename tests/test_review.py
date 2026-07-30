from vmt.review import list_aliases, rename_alias, sample_line


def _transcript():
    return {
        "recording_id": "rec1",
        "source_file": "memo.m4a",
        "recorded_at": "2026-07-28T00:00:00+00:00",
        "segments": [
            {"start": 0.0, "end": 1.0, "speaker": "Speaker 1", "text": "hi"},
            {"start": 1.5, "end": 2.0, "speaker": "Speaker 2", "text": "hello"},
            {"start": 2.5, "end": 3.0, "speaker": "Speaker 1", "text": "how are you"},
        ],
    }


def test_list_aliases_returns_unique_in_first_appearance_order():
    assert list_aliases(_transcript()) == ["Speaker 1", "Speaker 2"]


def test_sample_line_returns_first_matching_segment_text():
    assert sample_line(_transcript(), "Speaker 2") == "hello"


def test_sample_line_returns_none_for_unknown_speaker():
    assert sample_line(_transcript(), "Speaker 99") is None


def test_rename_alias_updates_only_matching_segments():
    updated = rename_alias(_transcript(), "Speaker 1", "Jane")
    assert [s["speaker"] for s in updated["segments"]] == ["Jane", "Speaker 2", "Jane"]


def test_rename_alias_does_not_mutate_original():
    original = _transcript()
    rename_alias(original, "Speaker 1", "Jane")
    assert original["segments"][0]["speaker"] == "Speaker 1"
