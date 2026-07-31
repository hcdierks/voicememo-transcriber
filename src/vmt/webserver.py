from __future__ import annotations

import json
import mimetypes
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from vmt.config import Config, load_config
from vmt.output import read_transcript, rewrite_transcript
from vmt.review import apply_rename_and_enroll, list_aliases
from vmt.speakers import SpeakerRegistry
from vmt.viewer import render_html

HEALTHZ_BODY = b"vmt-viewer"

_write_lock = threading.Lock()


def _guess_mime(suffix: str) -> str:
    if suffix.lower() == ".m4a":
        return "audio/mp4"
    mime, _ = mimetypes.guess_type(f"file{suffix}")
    return mime or "application/octet-stream"


def _transcript_paths(config: Config, recording_id: str) -> tuple[Path, Path]:
    return (
        config.transcripts_dir / f"{recording_id}.json",
        config.transcripts_dir / f"{recording_id}.md",
    )


class ViewerHandler(BaseHTTPRequestHandler):
    config: Config  # bound per-instance via make_server's handler subclass
    _head_only = False

    def log_message(self, format: str, *args) -> None:
        pass  # keep the terminal quiet; errors still raised to the client

    def do_HEAD(self) -> None:
        # Some browsers (notably Safari) probe <audio>/<video> resources with a
        # HEAD request before issuing GET; without this, media loading silently
        # fails on 501 with no visible error.
        self._head_only = True
        try:
            self.do_GET()
        finally:
            self._head_only = False

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]

        if parsed.path == "/healthz":
            self._respond(200, HEALTHZ_BODY, "text/plain")
        elif len(parts) == 2 and parts[0] == "view":
            self._serve_view(parts[1])
        elif len(parts) == 2 and parts[0] == "audio":
            self._serve_audio(parts[1])
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/rename":
            self.send_error(404)
            return
        self._handle_rename()

    def _serve_view(self, recording_id: str) -> None:
        json_path, _ = _transcript_paths(self.config, recording_id)
        if not json_path.exists():
            self.send_error(404, "Unknown recording_id")
            return
        transcript = read_transcript(json_path)
        html = render_html(recording_id, transcript, audio_url=f"/audio/{recording_id}")
        self._respond(200, html.encode("utf-8"), "text/html; charset=utf-8")

    def _serve_audio(self, recording_id: str) -> None:
        json_path, _ = _transcript_paths(self.config, recording_id)
        if not json_path.exists():
            self.send_error(404, "Unknown recording_id")
            return
        transcript = read_transcript(json_path)
        audio_path = self.config.recordings_dir / transcript["source_file"]
        if not audio_path.exists():
            self.send_error(404, "Source audio file missing")
            return
        data = audio_path.read_bytes()
        self._respond(200, data, _guess_mime(audio_path.suffix))

    def _handle_rename(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length))
            recording_id = payload["recording_id"]
            alias = payload["alias"]
            name = payload["name"].strip()
        except (KeyError, ValueError, json.JSONDecodeError):
            self._json_response(400, {"error": "invalid request"})
            return
        if not name:
            self._json_response(400, {"error": "name must not be empty"})
            return

        json_path, md_path = _transcript_paths(self.config, recording_id)
        if not json_path.exists():
            self._json_response(404, {"error": "unknown recording_id"})
            return

        with _write_lock:
            transcript = read_transcript(json_path)
            if alias not in list_aliases(transcript):
                self._json_response(400, {"error": f"{alias!r} is not an unlabeled speaker"})
                return
            registry = SpeakerRegistry(self.config.registry_path, self.config.embeddings_dir)
            transcript = apply_rename_and_enroll(self.config, transcript, alias, name, registry)
            rewrite_transcript(json_path, md_path, transcript)

        self._json_response(200, {"status": "ok"})

    def _respond(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # Transcripts mutate server-side (renames); never let the browser serve
        # a stale cached /view or /audio response after a reload.
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if not self._head_only:
            self.wfile.write(body)

    def _json_response(self, status: int, payload: dict) -> None:
        self._respond(status, json.dumps(payload).encode("utf-8"), "application/json")


def make_server(config: Config, port: int) -> ThreadingHTTPServer:
    bound_handler = type("BoundViewerHandler", (ViewerHandler,), {"config": config})
    return ThreadingHTTPServer(("127.0.0.1", port), bound_handler)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8743
    config = load_config()
    server = make_server(config, port)
    server.serve_forever()


if __name__ == "__main__":
    main()
