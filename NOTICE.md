# Third-party notices

This project is licensed under the [MIT License](LICENSE). It depends on
third-party code and, at runtime, downloads third-party pretrained models.
All are permissively licensed; the one exception requiring explicit
attribution is called out below.

## Runtime models (downloaded from Hugging Face, not vendored)

| Model | License | Attribution required |
|---|---|---|
| [`pyannote/speaker-diarization-3.1`](https://huggingface.co/pyannote/speaker-diarization-3.1) | MIT | No |
| [`pyannote/segmentation-3.0`](https://huggingface.co/pyannote/segmentation-3.0) | MIT | No |
| [`pyannote/embedding`](https://huggingface.co/pyannote/embedding) | MIT | No |
| [`pyannote/speaker-diarization-community-1`](https://huggingface.co/pyannote/speaker-diarization-community-1) | **CC-BY-4.0** | **Yes** |

`speaker-diarization-3.1`'s pipeline depends on `speaker-diarization-community-1`
server-side for its clustering step, even though this project never calls it
directly. Per CC-BY-4.0: this project uses the
[pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)
model, © the pyannote team, licensed under
[CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

All four models require a free Hugging Face account and accepting each
model's access conditions before first use — see the README's Prerequisites
section.

## Key Python dependencies

| Package | License |
|---|---|
| [`pyannote.audio`](https://github.com/pyannote/pyannote-audio) | MIT |
| [`whisperx`](https://github.com/m-bain/whisperX) | BSD-2-Clause |
| [`openai-whisper`](https://github.com/openai/whisper) (via whisperx) | MIT |
| `torch` | BSD-3-Clause |
| `transformers` | Apache-2.0 |
| `numpy` | BSD-3-Clause |
| `typer` | MIT |

The full resolved dependency tree is permissively licensed (MIT / BSD /
Apache-2.0 / PSF-2.0) with no copyleft (GPL/AGPL/LGPL) dependencies, verified
with `pip-licenses` — see `CONTRIBUTING.md` for how to reproduce this scan.
