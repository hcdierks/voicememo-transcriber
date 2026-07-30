from pathlib import Path

from vmt.manifest import Manifest


def test_new_recording_is_unprocessed(tmp_path: Path):
    manifest = Manifest(tmp_path / "manifest.json")
    assert not manifest.is_processed("abc123")


def test_mark_processed_persists_and_is_reported(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    manifest = Manifest(manifest_path)
    manifest.mark_processed(
        "abc123", tmp_path / "rec.m4a", tmp_path / "abc123.json", tmp_path / "abc123.md"
    )

    assert manifest.is_processed("abc123")

    reloaded = Manifest(manifest_path)
    assert reloaded.is_processed("abc123")
    assert len(reloaded) == 1


def test_missing_manifest_file_is_treated_as_empty(tmp_path: Path):
    manifest = Manifest(tmp_path / "does-not-exist.json")
    assert len(manifest) == 0


def test_corrupt_manifest_file_is_treated_as_empty(tmp_path: Path):
    path = tmp_path / "manifest.json"
    path.write_text("{not valid json")
    manifest = Manifest(path)
    assert len(manifest) == 0
