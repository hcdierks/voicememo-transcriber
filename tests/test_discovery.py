from pathlib import Path

from vmt.discovery import find_recordings, hash_file


def test_hash_is_stable_for_identical_bytes(tmp_path: Path):
    a = tmp_path / "a.m4a"
    b = tmp_path / "b.m4a"
    a.write_bytes(b"same audio bytes")
    b.write_bytes(b"same audio bytes")
    assert hash_file(a) == hash_file(b)


def test_hash_differs_for_different_bytes(tmp_path: Path):
    a = tmp_path / "a.m4a"
    b = tmp_path / "b.m4a"
    a.write_bytes(b"one")
    b.write_bytes(b"two")
    assert hash_file(a) != hash_file(b)


def test_non_m4a_files_are_ignored(tmp_path: Path):
    (tmp_path / "note.txt").write_text("not audio")
    (tmp_path / "memo.m4a").write_bytes(b"audio")
    recordings = find_recordings(tmp_path)
    assert [r.filename for r in recordings] == ["memo.m4a"]


def test_missing_directory_returns_empty_list(tmp_path: Path):
    assert find_recordings(tmp_path / "nope") == []
