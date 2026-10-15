"""Karaoke Auto-Caption & Word-by-Word Subtitle Burner for adham-agent.
Inspired by AutoCaption-Pro & stable-whisper.
Transcribes spoken audio at millisecond word precision via Groq Whisper large-v3,
formats high-aesthetic ASS Karaoke subtitle scripts (word-level highlighting),
and burns them directly onto 9:16 vertical Reels/Shorts with FFmpeg 7.1.
"""
from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx
import imageio_ffmpeg
import config

log = logging.getLogger("video_autocaption")

BASE_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = BASE_DIR / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = BASE_DIR / "repos_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _format_ass_time(seconds: float) -> str:
    """Formats float seconds into ASS time format: H:MM:SS.CC"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    csecs = int(round((seconds - int(seconds)) * 100))
    if csecs >= 100:
        secs += 1
        csecs = 0
    return f"{hrs}:{mins:02d}:{secs:02d}.{csecs:02d}"


async def extract_audio_from_video(video_path: Path, output_wav: Path) -> Path:
    """Extracts 16kHz mono audio from video for optimal Whisper transcription."""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg, "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(output_wav)
    ]
    proc = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Audio extraction failed: {proc.stderr}")
    return output_wav


async def transcribe_words_groq(audio_path: Path, language: str = "ar") -> list[dict[str, Any]]:
    """Transcribes audio with word-level millisecond timestamps via Groq Whisper API."""
    key = config.BACKUP_KEYS.get("Groq", ("", ""))[0]
    if not key:
        raise RuntimeError("مفتاح Groq غير متوفر في الإعدادات لتفريغ الصوت بدقة الكلمات.")

    async with httpx.AsyncClient(timeout=60) as client:
        with open(audio_path, "rb") as f:
            resp = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {key}"},
                files={"file": (audio_path.name, f.read())},
                data={
                    "model": "whisper-large-v3",
                    "response_format": "verbose_json",
                    "timestamp_granularities[]": "word",
                    "language": language
                }
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Groq Whisper error ({resp.status_code}): {resp.text}")
            
            data = resp.json()
            return data.get("words", [])


def build_ass_karaoke(words: list[dict[str, Any]], words_per_phrase: int = 4) -> str:
    """Generates an Advanced SubStation Alpha (.ass) script with dynamic karaoke effects."""
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: KaraokeWord,Arial,52,&H00FFFFFF,&H0000FFFF,&H00110F0B,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,340,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    # Chunk words into small punchy phrases (3-5 words)
    for i in range(0, len(words), words_per_phrase):
        chunk = words[i : i + words_per_phrase]
        if not chunk:
            continue

        phrase_start = chunk[0].get("start", 0.0)
        phrase_end = chunk[-1].get("end", phrase_start + 1.5)
        start_str = _format_ass_time(phrase_start)
        end_str = _format_ass_time(phrase_end)

        # Build karaoke text: {\k<duration_in_centiseconds>}word
        karaoke_parts = []
        for w in chunk:
            dur = max(0.1, (w.get("end", 0.0) - w.get("start", 0.0)))
            csec = int(round(dur * 100))
            cleaned_word = w.get("word", "").strip()
            karaoke_parts.append(f"{{\\k{csec}}}{cleaned_word} ")

        event_text = "".join(karaoke_parts).strip()
        lines.append(f"Dialogue: 0,{start_str},{end_str},KaraokeWord,,0,0,0,,{event_text}")

    return header + "\n".join(lines)


async def burn_karaoke_subtitles(
    video_path: Path,
    output_path: Path | None = None,
    language: str = "ar",
) -> dict[str, Any]:
    """Generates word-synchronized karaoke subtitles and burns them onto the video."""
    ts = int(time.time())
    if not output_path:
        output_path = VIDEOS_DIR / f"subtitled_{video_path.stem}_{ts}.mp4"

    temp_wav = CACHE_DIR / f"audio_{ts}.wav"
    temp_ass = CACHE_DIR / f"karaoke_{ts}.ass"

    try:
        # 1. Extract audio
        log.info("Extracting audio from %s ...", video_path)
        await extract_audio_from_video(video_path, temp_wav)

        # 2. Transcribe word timestamps with Groq Whisper
        log.info("Transcribing words with Groq Whisper large-v3 ...")
        words = await transcribe_words_groq(temp_wav, language=language)
        if not words:
            raise RuntimeError("لم يتم العثور على كلمات منطوقة في الفيديو لتوليد الكابشن.")

        # 3. Build ASS karaoke file
        log.info("Generating ASS karaoke subtitles (%d words) ...", len(words))
        ass_content = build_ass_karaoke(words, words_per_phrase=4)
        temp_ass.write_text(ass_content, encoding="utf-8")

        # 4. Burn subtitles with FFmpeg libass
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        escaped_ass = str(temp_ass.resolve()).replace("\\", "/").replace(":", "\\:")

        log.info("Burning subtitles via FFmpeg: %s", ffmpeg)
        cmd_burn = [
            ffmpeg, "-y",
            "-i", str(video_path),
            "-vf", f"ass='{escaped_ass}'",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            str(output_path)
        ]

        proc = await asyncio.to_thread(subprocess.run, cmd_burn, capture_output=True, text=True)
        if proc.returncode != 0 or not output_path.exists():
            raise RuntimeError(f"FFmpeg subtitle burn failed: {proc.stderr[-400:]}")

        return {
            "status": "success",
            "video_path": str(output_path.resolve()),
            "total_words": len(words),
            "file_size": output_path.stat().st_size,
            "ass_path": str(temp_ass.resolve()),
            "message": f"تم حرق كابشن الكاراوكي المتحرك (كلمة بكلمة) بنجاح على الفيديو ({len(words)} كلمة)!"
        }

    finally:
        try:
            if temp_wav.exists():
                temp_wav.unlink()
        except Exception:
            pass


async def _handle_autocaption(args: dict) -> str:
    path_str = args.get("video_path", "")
    if not path_str:
        return "يرجى تحديد مسار ملف الفيديو المراد توليد كابشن الكاراوكي له."

    vpath = Path(path_str)
    if not vpath.exists():
        return f"ملف الفيديو غير موجود في المسار: `{path_str}`"

    try:
        res = await burn_karaoke_subtitles(vpath)
        return (
            f"🎬 **تم توليد وحرق كابشن الكاراوكي على الفيديو بنجاح!**\n\n"
            f"• **الفيديو الناتج:** `{res['video_path']}`\n"
            f"• **عدد الكلمات المزامنة بدقة:** {res['total_words']} كلمة\n"
            f"• **الحجم:** {res['file_size'] / (1024*1024):.2f} MB\n"
            f"• **الأسلوب:** إضاءة الكلمة الحالية باللون الأصفر المشع مع نطقها (AutoCaption Word-by-Word)"
        )
    except Exception as e:
        return f"❌ خطأ أثناء توليد الكابشن: {e}"


TOOLS = [
    {
        "name": "burn_karaoke_subtitles_on_video",
        "description": "توليد كابشن وترجمة متحركة كلمة بكلمة بتأثير الكاراوكي (Karaoke Word-by-Word Animation) لأي فيديو ريلز/تيك توك/شورتس وحرقه مباشرة على الفيديو بدقة الميلي ثانية.",
        "parameters": {
            "type": "object",
            "properties": {
                "video_path": {"type": "string", "description": "المسار الكامل لملف الفيديو MP4 المراد إضافة الكابشن إليه"}
            },
            "required": ["video_path"]
        },
        "handler": _handle_autocaption,
    }
]
