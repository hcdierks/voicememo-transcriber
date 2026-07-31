from __future__ import annotations

import html as html_lib
import urllib.parse
from pathlib import Path

_PALETTE = [
    "#4C6EF5", "#12B886", "#F59F00", "#E64980",
    "#7048E8", "#15AABF", "#FA5252", "#82C91E",
]


def _speaker_colors(segments: list[dict]) -> dict[str, str]:
    colors: dict[str, str] = {}
    for seg in segments:
        speaker = seg["speaker"]
        if speaker not in colors:
            colors[speaker] = _PALETTE[len(colors) % len(_PALETTE)]
    return colors


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


def render_html(transcript: dict, audio_path: Path) -> str:
    """Render a self-contained HTML page: audio player + transcript, color-coded
    by speaker, click-to-seek, with the currently-playing segment highlighted."""
    segments = transcript["segments"]
    colors = _speaker_colors(segments)
    audio_url = "file://" + urllib.parse.quote(str(audio_path.resolve()))
    source_file = html_lib.escape(transcript["source_file"])

    rows = []
    for seg in segments:
        speaker = html_lib.escape(seg["speaker"])
        text = html_lib.escape(seg["text"])
        color = colors[seg["speaker"]]
        rows.append(
            f'<div class="segment" data-start="{seg["start"]}" data-end="{seg["end"]}" '
            f'style="border-left-color:{color}" onclick="seek({seg["start"]})">'
            f'<span class="ts">{_format_timestamp(seg["start"])}</span>'
            f'<span class="speaker" style="color:{color}">{speaker}</span>'
            f'<span class="text">{text}</span>'
            f"</div>"
        )

    legend = "".join(
        f'<span class="legend-item"><span class="dot" style="background:{c}"></span>{html_lib.escape(s)}</span>'
        for s, c in colors.items()
    )

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{source_file}</title>
<style>
  body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; background: #fff; }}
  audio {{ width: 100%; margin-bottom: 1rem; position: sticky; top: 0; background: #fff; padding: 0.5rem 0; }}
  .legend {{ margin-bottom: 1rem; font-size: 0.85rem; color: #555; }}
  .legend-item {{ margin-right: 1rem; }}
  .dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; }}
  .segment {{ border-left: 4px solid #ccc; padding: 0.4rem 0.75rem; margin-bottom: 2px; cursor: pointer; border-radius: 4px; }}
  .segment:hover {{ background: #f2f2f2; }}
  .segment.active {{ background: #fff3bf; }}
  .ts {{ font-family: ui-monospace, monospace; color: #888; margin-right: 0.75rem; font-size: 0.85rem; }}
  .speaker {{ font-weight: 600; margin-right: 0.5rem; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #1a1a1a; color: #eee; }}
    audio {{ background: #1a1a1a; }}
    .segment:hover {{ background: #2a2a2a; }}
    .segment.active {{ background: #4a3f00; }}
  }}
</style>
</head>
<body>
<h2>{source_file}</h2>
<audio id="player" controls src="{audio_url}"></audio>
<div class="legend">{legend}</div>
<div id="segments">
{"".join(rows)}
</div>
<script>
  const player = document.getElementById('player');
  const segments = Array.from(document.querySelectorAll('.segment'));
  function seek(t) {{
    player.currentTime = t;
    player.play();
  }}
  player.addEventListener('timeupdate', () => {{
    const t = player.currentTime;
    segments.forEach(el => {{
      const start = parseFloat(el.dataset.start);
      const end = parseFloat(el.dataset.end);
      el.classList.toggle('active', t >= start && t < end);
    }});
  }});
</script>
</body>
</html>
"""
