from __future__ import annotations

from pathlib import Path

from vmt.models import RawSegment


def transcribe_and_diarize(
    audio_path: Path,
    whisper_model: str,
    hf_token: str | None,
    device: str = "cpu",
) -> list[RawSegment]:
    """Run ASR + forced alignment + diarization via whisperx.

    Imported lazily: this module pulls in torch/whisperx (the `ml` extra),
    which unit tests must not require.
    """
    import whisperx

    asr_model = whisperx.load_model(whisper_model, device=device)
    audio = whisperx.load_audio(str(audio_path))
    result = asr_model.transcribe(audio)

    align_model, align_metadata = whisperx.load_align_model(
        language_code=result["language"], device=device
    )
    result = whisperx.align(result["segments"], align_model, align_metadata, audio, device)

    diarize_model = whisperx.diarize.DiarizationPipeline(
        model_name="pyannote/speaker-diarization-3.1", token=hf_token, device=device
    )
    diarize_segments = diarize_model(audio)
    result = whisperx.assign_word_speakers(diarize_segments, result)

    raw_segments = [
        RawSegment(
            start=float(seg["start"]),
            end=float(seg["end"]),
            local_speaker=seg.get("speaker", "SPEAKER_00"),
            text=seg["text"].strip(),
        )
        for seg in result["segments"]
    ]
    return sorted(raw_segments, key=lambda s: s.start)
