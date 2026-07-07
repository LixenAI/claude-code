"""
Short-video renderer: turns a generated reel script into a vertical
1080x1920 MP4 with an AI voiceover (edge-tts) and animated captions
(ffmpeg). Fully self-contained — no paid video APIs.

Pipeline per post:
  script -> spoken segments -> TTS mp3 per segment -> per-segment clip
  (dark background + centered caption, sized to the audio) -> concat.

If TTS is unreachable, falls back to a silent video with timed captions
so the pipeline never hard-blocks on network.
"""

import asyncio
import os
import re
import subprocess
import tempfile
import textwrap
from datetime import datetime, timezone

from app import models

WIDTH, HEIGHT = 1080, 1920
BG_COLOR = "0x0F1117"
ACCENT_COLOR = "0x7CFC00"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SILENT_SECONDS_PER_SEGMENT = 3.0
MAX_SEGMENTS = 14

MEDIA_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "media"
)


def media_root() -> str:
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    return MEDIA_ROOT


def extract_script_segments(post: models.Post) -> list[str]:
    """
    Pull spoken lines from the generated post: HOOK first, then BODY.
    Strips markdown, [b-roll/text-on-screen cues], and carousel numbering.
    """
    raw = post.raw_generated or ""
    hook = (post.hook or "").strip()

    body_lines: list[str] = []
    capture = False
    for line in raw.split("\n"):
        if "---BODY---" in line:
            capture = True
            continue
        if "---CTA---" in line or "---HASHTAGS---" in line:
            if "---CTA---" in line:
                capture = "cta"
                continue
            break
        if capture:
            body_lines.append(line)

    segments: list[str] = []
    if hook:
        segments.append(hook)
    for line in body_lines:
        text = re.sub(r"\[[^\]]*\]", "", line)          # [cues]
        text = re.sub(r"^[*#>\-\d.\s]+", "", text)      # markdown/list prefixes
        text = text.replace("**", "").strip()
        if not text or len(text) < 3:
            continue
        # split long lines into speakable chunks
        for chunk in re.split(r"(?<=[.!?])\s+", text):
            chunk = chunk.strip()
            if chunk and len(chunk) >= 3:
                segments.append(chunk)

    # dedupe hook repetition and cap length
    if len(segments) > 1 and segments[1].lower() == segments[0].lower():
        segments.pop(1)
    return segments[:MAX_SEGMENTS] or [hook or (post.caption or "Follow for more.")[:120]]


async def _tts_segment(text: str, voice: str, out_path: str) -> None:
    import edge_tts

    tts = edge_tts.Communicate(text, voice)
    await tts.save(out_path)


def _audio_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def _escape_drawtext(text: str) -> str:
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def _render_segment_clip(
    text: str,
    duration: float,
    handle: str,
    audio_path: str | None,
    out_path: str,
    index: int,
    total: int,
) -> None:
    wrapped = _escape_drawtext("\n".join(textwrap.wrap(text, width=22)))
    handle_txt = _escape_drawtext(handle)
    font_size = 72 if len(text) <= 90 else 58

    draw = (
        f"drawtext=fontfile={FONT_BOLD}:text='{wrapped}':fontcolor=white:fontsize={font_size}:"
        f"line_spacing=18:x=(w-text_w)/2:y=(h-text_h)/2,"
        f"drawtext=fontfile={FONT_REGULAR}:text='{handle_txt}':fontcolor=white@0.6:fontsize=40:"
        f"x=(w-text_w)/2:y=h-220,"
        # accent progress bar
        f"drawbox=x=0:y=ih-8:w=iw*{(index + 1) / total:.3f}:h=8:color={ACCENT_COLOR}@0.9:t=fill"
    )

    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={BG_COLOR}:s={WIDTH}x{HEIGHT}:d={duration:.2f}:r=30"]
    if audio_path:
        cmd += ["-i", audio_path]
    cmd += ["-vf", draw, "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "veryfast"]
    if audio_path:
        cmd += ["-c:a", "aac", "-b:a", "128k", "-shortest"]
    cmd += ["-t", f"{duration:.2f}", out_path]
    subprocess.run(cmd, capture_output=True, check=True)


def render_video(post: models.Post, brand: models.Brand) -> str:
    """
    Render the post's short video. Returns path relative to data/
    (e.g. "media/rennewme/post12_20260707.mp4"). Raises on failure.
    """
    segments = extract_script_segments(post)
    voice = brand.tts_voice or "en-US-AndrewNeural"
    handle = brand.name if brand.name.startswith("@") else f"@{brand.slug}"

    out_dir = os.path.join(media_root(), brand.slug)
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    final_path = os.path.join(out_dir, f"post{post.id}_{stamp}.mp4")

    with tempfile.TemporaryDirectory() as tmp:
        # 1) TTS per segment (graceful fallback to silent captions)
        audio_paths: list[str | None] = []
        durations: list[float] = []
        tts_ok = True
        for i, seg in enumerate(segments):
            mp3 = os.path.join(tmp, f"seg{i}.mp3")
            if tts_ok:
                try:
                    asyncio.run(_tts_segment(seg, voice, mp3))
                    durations.append(_audio_duration(mp3) + 0.25)
                    audio_paths.append(mp3)
                    continue
                except Exception:
                    tts_ok = False  # one failure -> silent mode for the rest
            audio_paths.append(None)
            durations.append(max(SILENT_SECONDS_PER_SEGMENT, len(seg) * 0.055))

        # keep audio presence uniform for clean concat
        if not tts_ok:
            audio_paths = [None] * len(segments)

        # 2) render per-segment clips
        clips = []
        for i, seg in enumerate(segments):
            clip = os.path.join(tmp, f"clip{i}.mp4")
            _render_segment_clip(
                seg, durations[i], handle, audio_paths[i], clip, i, len(segments)
            )
            clips.append(clip)

        # 3) concat
        concat_list = os.path.join(tmp, "list.txt")
        with open(concat_list, "w") as f:
            for clip in clips:
                f.write(f"file '{clip}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
             "-c", "copy", final_path],
            capture_output=True, check=True,
        )

    return os.path.relpath(final_path, os.path.dirname(media_root()))
