from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_RECORDINGS_DIR = (
    Path.home()
    / "Library"
    / "Group Containers"
    / "group.com.apple.VoiceMemos.shared"
    / "Recordings"
)

CONFIG_PATH = Path.home() / ".config" / "vmt" / "config.toml"


@dataclass(frozen=True)
class Config:
    data_dir: Path
    recordings_dir: Path
    whisper_model: str
    similarity_threshold: float
    hf_token: str | None
    viewer_port: int

    @property
    def manifest_path(self) -> Path:
        return self.data_dir / "manifest.json"

    @property
    def transcripts_dir(self) -> Path:
        return self.data_dir / "transcripts"

    @property
    def speakers_dir(self) -> Path:
        return self.data_dir / "speakers"

    @property
    def registry_path(self) -> Path:
        return self.speakers_dir / "registry.json"

    @property
    def embeddings_dir(self) -> Path:
        return self.speakers_dir / "embeddings"


def _load_toml() -> dict:
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("rb") as f:
            return tomllib.load(f)
    return {}


def load_config(repo_root: Path | None = None) -> Config:
    toml_cfg = _load_toml()
    repo_root = repo_root or Path(__file__).resolve().parents[2]

    data_dir = Path(
        os.environ.get("VMT_DATA_DIR", toml_cfg.get("data_dir", str(repo_root / "data")))
    ).expanduser()
    recordings_dir = Path(
        os.environ.get(
            "VMT_RECORDINGS_DIR",
            toml_cfg.get("recordings_dir", str(DEFAULT_RECORDINGS_DIR)),
        )
    ).expanduser()
    whisper_model = os.environ.get("VMT_WHISPER_MODEL", toml_cfg.get("whisper_model", "small"))
    similarity_threshold = float(
        os.environ.get("VMT_SIMILARITY_THRESHOLD", toml_cfg.get("similarity_threshold", 0.75))
    )
    hf_token = os.environ.get("HF_TOKEN", toml_cfg.get("hf_token"))
    viewer_port = int(os.environ.get("VMT_VIEWER_PORT", toml_cfg.get("viewer_port", 8743)))

    return Config(
        data_dir=data_dir,
        recordings_dir=recordings_dir,
        whisper_model=whisper_model,
        similarity_threshold=similarity_threshold,
        hf_token=hf_token,
        viewer_port=viewer_port,
    )
