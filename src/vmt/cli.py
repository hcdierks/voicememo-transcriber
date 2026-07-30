from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import typer

from vmt.config import load_config
from vmt.discovery import Recording, find_recordings, hash_file
from vmt.manifest import Manifest
from vmt.output import read_transcript, rewrite_transcript, write_transcript
from vmt.review import apply_rename_and_enroll, list_aliases, sample_line
from vmt.speakers import SpeakerRegistry, extract_embedding, resolve_speakers

app = typer.Typer(help="Local transcription and speaker diarization for Voice Memos.")
speakers_app = typer.Typer(help="Manage the known-speaker registry.")
app.add_typer(speakers_app, name="speakers")


def _mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()


@app.command()
def scan() -> None:
    """List Voice Memos recordings that haven't been processed yet."""
    config = load_config()
    manifest = Manifest(config.manifest_path)
    unprocessed = [
        r for r in find_recordings(config.recordings_dir) if not manifest.is_processed(r.recording_id)
    ]

    if not unprocessed:
        typer.echo("No new recordings.")
        return
    for rec in unprocessed:
        typer.echo(f"{rec.recording_id[:12]}  {rec.filename}")


@app.command()
def process(
    file: Path = typer.Option(  # noqa: B008 -- required pattern for Typer options
        None, "--file", help="Process a single recording instead of all new ones."
    ),
) -> None:
    """Transcribe, diarize, and identify speakers in unprocessed recordings."""
    config = load_config()
    manifest = Manifest(config.manifest_path)
    registry = SpeakerRegistry(config.registry_path, config.embeddings_dir)

    if file is not None:
        targets = [Recording(recording_id=hash_file(file), path=file)]
    else:
        targets = [
            r
            for r in find_recordings(config.recordings_dir)
            if not manifest.is_processed(r.recording_id)
        ]

    if not targets:
        typer.echo("No new recordings.")
        return

    from vmt.transcribe import transcribe_and_diarize

    for rec in targets:
        typer.echo(f"Processing {rec.filename}...")
        raw_segments = transcribe_and_diarize(rec.path, config.whisper_model, config.hf_token)

        embeddings_by_local_speaker = {}
        for local_speaker in {s.local_speaker for s in raw_segments}:
            longest = max(
                (s for s in raw_segments if s.local_speaker == local_speaker),
                key=lambda s: s.end - s.start,
            )
            embeddings_by_local_speaker[local_speaker] = extract_embedding(
                rec.path, longest.start, longest.end, config.hf_token
            )

        segments = resolve_speakers(
            raw_segments, embeddings_by_local_speaker, registry, config.similarity_threshold
        )

        json_path, md_path = write_transcript(
            recording_id=rec.recording_id,
            source_file=rec.filename,
            recorded_at=_mtime_iso(rec.path),
            segments=segments,
            transcripts_dir=config.transcripts_dir,
        )
        manifest.mark_processed(rec.recording_id, rec.path, json_path, md_path)
        typer.echo(f"  -> {md_path}")


@app.command()
def review(recording_id: str) -> None:
    """Interactively rename Speaker N aliases to real names for one recording."""
    config = load_config()
    json_path = config.transcripts_dir / f"{recording_id}.json"
    md_path = config.transcripts_dir / f"{recording_id}.md"
    if not json_path.exists():
        typer.echo(f"No transcript found for {recording_id}.", err=True)
        raise typer.Exit(code=1)

    transcript = read_transcript(json_path)
    registry = SpeakerRegistry(config.registry_path, config.embeddings_dir)

    aliases = list_aliases(transcript)
    if not aliases:
        typer.echo("No unlabeled speakers in this transcript.")
        return

    for alias in aliases:
        example = sample_line(transcript, alias) or ""
        typer.echo(f'\n{alias}: "{example[:120]}"')
        new_name = typer.prompt(f"Name for {alias} (blank to skip)", default="", show_default=False)
        if not new_name:
            continue
        transcript = apply_rename_and_enroll(config, transcript, alias, new_name, registry)
        rewrite_transcript(json_path, md_path, transcript)
        typer.echo(f"Saved {alias} -> {new_name}")


@speakers_app.command("list")
def speakers_list() -> None:
    """List known (named) speakers in the registry."""
    config = load_config()
    registry = SpeakerRegistry(config.registry_path, config.embeddings_dir)
    names = registry.names()
    if not names:
        typer.echo("No known speakers yet.")
        return
    for name in names:
        typer.echo(name)


@speakers_app.command("rename")
def speakers_rename(old_name: str, new_name: str) -> None:
    """Rename a known speaker in the registry."""
    config = load_config()
    registry = SpeakerRegistry(config.registry_path, config.embeddings_dir)
    registry.rename(old_name, new_name)
    typer.echo(f"Renamed {old_name} -> {new_name}")


@speakers_app.command("merge")
def speakers_merge(source_name: str, into_name: str) -> None:
    """Merge two registry entries discovered to be the same person."""
    config = load_config()
    registry = SpeakerRegistry(config.registry_path, config.embeddings_dir)
    registry.merge(source_name, into_name)
    typer.echo(f"Merged {source_name} into {into_name}")


if __name__ == "__main__":
    app()
