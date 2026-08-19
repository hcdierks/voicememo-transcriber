import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

from vmt.config import Config
from vmt.output import read_transcript
from vmt.webserver import make_server

# Valid-shaped recording_ids (64 lowercase hex chars, matching hash_file's sha256
# output) so tests exercise the real "known"/"unknown" paths rather than tripping
# the malformed-id validation added for the path-traversal/XSS fix.
REC1 = "a" * 64
REC_UNKNOWN = "b" * 64


@pytest.fixture
def config(tmp_path: Path) -> Config:
    recordings_dir = tmp_path / "recordings"
    recordings_dir.mkdir()
    return Config(
        data_dir=tmp_path / "data",
        recordings_dir=recordings_dir,
        whisper_model="small",
        similarity_threshold=0.75,
        hf_token=None,
        viewer_port=0,
    )


@pytest.fixture
def running_server(config: Config):
    server = make_server(config, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    yield config, port
    server.shutdown()
    thread.join(timeout=2)


def _write_transcript(config: Config, recording_id: str, segments: list[dict], source_file="memo.m4a"):
    config.transcripts_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "recording_id": recording_id,
        "source_file": source_file,
        "recorded_at": "2026-07-28T00:00:00+00:00",
        "segments": segments,
    }
    (config.transcripts_dir / f"{recording_id}.json").write_text(json.dumps(payload))
    (config.transcripts_dir / f"{recording_id}.md").write_text("placeholder")
    return payload


def test_healthz(running_server):
    _, port = running_server
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz") as resp:
        assert resp.status == 200
        assert resp.read() == b"vmt-viewer"


def test_head_request_on_audio_returns_headers_without_body(running_server):
    # Safari probes <audio>/<video> sources with HEAD before GET; without
    # support for it, media loading fails silently in that browser.
    config, port = running_server
    _write_transcript(config, REC1, [{"start": 0.0, "end": 1.0, "speaker": "Speaker 1", "text": "hi"}])
    (config.recordings_dir / "memo.m4a").write_bytes(b"fake-audio-bytes")

    req = urllib.request.Request(f"http://127.0.0.1:{port}/audio/{REC1}", method="HEAD")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert resp.headers["Content-Type"] == "audio/mp4"
        assert resp.headers["Content-Length"] == str(len(b"fake-audio-bytes"))
        assert resp.read() == b""


def test_view_serves_rendered_transcript(running_server):
    config, port = running_server
    _write_transcript(
        config, REC1, [{"start": 0.0, "end": 1.0, "speaker": "Speaker 1", "text": "hello world"}]
    )

    with urllib.request.urlopen(f"http://127.0.0.1:{port}/view/{REC1}") as resp:
        body = resp.read().decode()

    assert "hello world" in body
    assert f"/audio/{REC1}" in body


def test_view_unknown_recording_404s(running_server):
    _, port = running_server
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/view/{REC_UNKNOWN}")
    assert exc_info.value.code == 404


@pytest.mark.parametrize(
    "malformed_id",
    [
        "../../../../etc/passwd",
        'x";alert(document.title);//',
        "not-a-hash",
        "a" * 63,  # one short
        "A" * 64,  # uppercase not accepted -- must match hash_file's lowercase hexdigest
    ],
)
def test_view_malformed_recording_id_returns_400(running_server, malformed_id):
    _, port = running_server
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/view/{urllib.parse.quote(malformed_id, safe='')}")
    assert exc_info.value.code == 400


def test_audio_malformed_recording_id_returns_400(running_server):
    _, port = running_server
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(
            f"http://127.0.0.1:{port}/audio/{urllib.parse.quote('../../etc/passwd', safe='')}"
        )
    assert exc_info.value.code == 400


def test_audio_streams_the_source_file_with_correct_mime(running_server):
    config, port = running_server
    _write_transcript(config, REC1, [{"start": 0.0, "end": 1.0, "speaker": "Speaker 1", "text": "hi"}])
    (config.recordings_dir / "memo.m4a").write_bytes(b"fake-audio-bytes")

    with urllib.request.urlopen(f"http://127.0.0.1:{port}/audio/{REC1}") as resp:
        assert resp.status == 200
        assert resp.read() == b"fake-audio-bytes"
        assert resp.headers["Content-Type"] == "audio/mp4"


def test_audio_missing_source_file_404s(running_server):
    config, port = running_server
    _write_transcript(config, REC1, [{"start": 0.0, "end": 1.0, "speaker": "Speaker 1", "text": "hi"}])
    # deliberately do not create recordings_dir/memo.m4a

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/audio/{REC1}")
    assert exc_info.value.code == 404


def test_rename_updates_transcript(running_server):
    config, port = running_server
    # No source audio file is created: apply_rename_and_enroll only calls into
    # the ML-dependent embedding extraction when the source audio exists, so
    # this exercises the rename/rewrite path without needing torch/pyannote.
    _write_transcript(
        config,
        REC1,
        [
            {"start": 0.0, "end": 1.0, "speaker": "Speaker 1", "text": "hi"},
            {"start": 1.5, "end": 3.0, "speaker": "Speaker 1", "text": "how are you"},
            {"start": 3.5, "end": 4.0, "speaker": "Speaker 2", "text": "fine thanks"},
        ],
    )

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/rename",
        data=json.dumps({"recording_id": REC1, "alias": "Speaker 1", "name": "Jane"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert json.loads(resp.read()) == {"status": "ok"}

    updated = read_transcript(config.transcripts_dir / f"{REC1}.json")
    speakers = [s["speaker"] for s in updated["segments"]]
    assert speakers == ["Jane", "Jane", "Speaker 2"]


def test_rename_unknown_alias_returns_400(running_server):
    config, port = running_server
    _write_transcript(config, REC1, [{"start": 0.0, "end": 1.0, "speaker": "Jane", "text": "hi"}])

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/rename",
        data=json.dumps({"recording_id": REC1, "alias": "Speaker 1", "name": "Bob"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 400


def test_rename_empty_name_returns_400(running_server):
    config, port = running_server
    _write_transcript(config, REC1, [{"start": 0.0, "end": 1.0, "speaker": "Speaker 1", "text": "hi"}])

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/rename",
        data=json.dumps({"recording_id": REC1, "alias": "Speaker 1", "name": "   "}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 400


def test_rename_malformed_recording_id_returns_400(running_server):
    _, port = running_server

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/rename",
        data=json.dumps(
            {"recording_id": "../../etc/passwd", "alias": "Speaker 1", "name": "Bob"}
        ).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 400


def test_rename_rejects_cross_origin_request(running_server):
    _, port = running_server

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/rename",
        data=json.dumps({"recording_id": REC1, "alias": "Speaker 1", "name": "Bob"}).encode(),
        headers={"Content-Type": "application/json", "Origin": "http://evil.example"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 403
