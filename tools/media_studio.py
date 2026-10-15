"""Autonomous Media Studio Superpower for adham-agent.
1. Free Keyless AI Image Generation (Flux.1 / SDXL via Pollinations AI) in 1080x1920 (Reel/Story), 16:9, or 1:1.
2. Viral Video Repurposer: Downloads any TikTok / Shorts / Reels URL via yt-dlp, extracts audio, transcribes & translates.
3. Audio Ducking & BGM Mixer: Mixes background ambient tech beats dynamically under voiceover at 15% volume using FFmpeg.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import time
import urllib.parse
from pathlib import Path
from typing import Any

import httpx
import imageio_ffmpeg

log = logging.getLogger("media_studio")

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = BASE_DIR / "repos_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR = BASE_DIR / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


def _get_ffmpeg() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


async def generate_flux_image(
    prompt: str,
    aspect_ratio: str = "9:16",
    model: str = "flux",
    seed: int | None = None
) -> dict[str, Any]:
    """Generates a photorealistic AI image via Pollinations AI without API keys.
    
    Aspect ratios:
    - 9:16: 1080x1920 (Shorts, Reels, Stories)
    - 16:9: 1920x1080 (YouTube Thumbnail, Landscape)
    - 1:1: 1024x1024 (Instagram Post, Square)
    """
    dim_map = {
        "9:16": (1080, 1920),
        "16:9": (1920, 1080),
        "1:1": (1024, 1024),
        "story": (1080, 1920),
        "reel": (1080, 1920),
        "thumbnail": (1920, 1080),
    }
    width, height = dim_map.get(aspect_ratio.lower(), (1080, 1920))
    encoded_prompt = urllib.parse.quote(prompt.strip())
    
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&model={model}"
    if seed:
        url += f"&seed={seed}"

    ts = int(time.time())
    output_file = SCREENSHOTS_DIR / f"ai_art_{ts}.jpg"

    async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        if resp.status_code != 200:
            raise RuntimeError(f"Image generation failed with HTTP {resp.status_code}")
        
        output_file.write_bytes(resp.content)

    size_kb = round(len(resp.content) / 1024, 1)
    return {
        "success": True,
        "image_path": str(output_file),
        "prompt": prompt,
        "width": width,
        "height": height,
        "size_kb": size_kb,
        "model": model,
    }


async def download_and_repurpose_video(video_url: str) -> dict[str, Any]:
    """Downloads an external short video (TikTok, YouTube Shorts, Reels) using yt-dlp and extracts audio."""
    import yt_dlp

    ts = int(time.time())
    out_template = str(CACHE_DIR / f"dl_video_{ts}.%(ext)s")

    ydl_opts = {
        "outtmpl": out_template,
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "max_filesize": 50 * 1024 * 1024,  # max 50MB
    }

    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            return info, filename

    info, downloaded_path = await asyncio.to_thread(_download)
    vpath = Path(downloaded_path)

    # Extract audio to mp3 for transcription
    audio_path = CACHE_DIR / f"audio_extracted_{ts}.mp3"
    ffmpeg = _get_ffmpeg()
    cmd = [
        ffmpeg, "-y",
        "-i", str(vpath),
        "-vn",
        "-acodec", "libmp3lame",
        "-ar", "16000",
        "-ac", "1",
        str(audio_path)
    ]
    await asyncio.to_thread(subprocess.run, cmd, capture_output=True)

    title = info.get("title", "فيديو خارجي")
    desc = info.get("description", "")
    duration = info.get("duration", 0)

    return {
        "success": True,
        "title": title,
        "description": desc[:500],
        "duration": duration,
        "video_path": str(vpath),
        "audio_path": str(audio_path) if audio_path.exists() else None,
        "url": video_url,
    }


async def mix_audio_with_ambient_bgm(voice_audio_path: Path, output_audio_path: Path, bgm_volume: float = 0.12) -> Path:
    """Mixes a speech audio track with an ambient synthesizer/lofi background using FFmpeg audio ducking."""
    ffmpeg = _get_ffmpeg()
    
    # Generate a procedural gentle background ambient drone using lavfi synthesizer if no local mp3 exists
    # Creates a pleasant 432Hz ambient low-tone tech bed that fits tech tutorials
    filter_complex = (
        f"[0:a]volume=1.0[v];"
        f"aevalsrc=sin(216*2*PI*t)*0.06+sin(108*2*PI*t)*0.08:s=44100[bgm];"
        f"[bgm]volume={bgm_volume}[bgmv];"
        f"[v][bgmv]amix=inputs=2:duration=first:dropout_transition=2[out]"
    )
    cmd = [
        ffmpeg, "-y",
        "-i", str(voice_audio_path),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_audio_path)
    ]
    await asyncio.to_thread(subprocess.run, cmd, capture_output=True, check=True)
    return output_audio_path


# ==============================================================================
# AI Agent Tool Handlers
# ==============================================================================

async def generate_ai_image_handler(args: dict) -> str:
    """Tool handler for AI image generation."""
    prompt = args.get("prompt", "").strip()
    if not prompt:
        return "يرجى كتابة وصف الصورة المطلوبة بالإنجليزية أو العربية (Prompt)."

    aspect = args.get("aspect_ratio", "9:16")
    try:
        res = await generate_flux_image(prompt=prompt, aspect_ratio=aspect)
        return (
            f"🎨 **تم توليد الصورة بنجاح عبر محرك FLUX.1!**\n\n"
            f"🖼️ **مسار الصورة المحفوظة:** `{res['image_path']}`\n"
            f"📐 **الأبعاد:** {res['width']}x{res['height']} ({aspect})\n"
            f"⚖️ **الحجم:** {res['size_kb']} KB\n"
            f"📝 **الوصف:** {prompt}"
        )
    except Exception as e:
        log.exception("Image generation error")
        return f"❌ فشل توليد الصورة: {e}"


async def repurpose_video_handler(args: dict) -> str:
    """Tool handler for downloading and repurposing external videos."""
    url = args.get("url", "").strip()
    if not url:
        return "يرجى تحديد رابط الفيديو الخارجي (تيك توك / شورتس / ريلز)."

    try:
        res = await download_and_repurpose_video(url)
        return (
            f"📹 **تم سحب وتحليل الفيديو الخارجي بنجاح!**\n\n"
            f"📌 **العنوان:** `{res['title']}`\n"
            f"⏱️ **المدة:** {res['duration']} ثانية\n"
            f"📁 **مسار الفيديو المحلي:** `{res['video_path']}`\n"
            f"🎙️ **المسار الصوتي المستخرج للترجمة والتفريغ:** `{res['audio_path']}`\n\n"
            f"💡 *يمكنك الآن طلب تفريغ نصه أو إعادة كتابته كاسكريبت عربي ونشره عبر استوديو الفيديوهات (/video)!*"
        )
    except Exception as e:
        log.exception("Repurpose video error")
        return f"❌ فشل سحب وتحليل الفيديو: {e}"


TOOLS = [
    {
        "name": "generate_ai_image",
        "description": "توليد صور واقعية وتصاميم وبوسترات بالذكاء الاصطناعي مجاناً بأعلى جودة عبر محرك FLUX.1 بأبعاد مخصصة (9:16 للريلز، 16:9 لليوتيوب، أو 1:1).",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "وصف المشهد التفصيلي المراد رسمه (يفضل كتابة تفاصيل بصرية دقيقة)"},
                "aspect_ratio": {
                    "type": "string",
                    "description": "نسبة الأبعاد: 9:16 (ريلز وتيك توك)، 16:9 (يوتيوب عريض)، 1:1 (مربع انستقرام)",
                },
            },
            "required": ["prompt"],
        },
        "handler": generate_ai_image_handler,
    },
    {
        "name": "repurpose_social_video",
        "description": "سحب وتحميل وتفريغ أي مقطع فيديو من تيك توك، يوتيوب شورتس، أو إنستقرام ريلز لاستخراج أفكاره وترجمتها وإعادة صناعة محتوى عربي فيروسي منه.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "رابط مقطع الفيديو على تيك توك أو يوتيوب شورتس أو ريلز"},
            },
            "required": ["url"],
        },
        "handler": repurpose_video_handler,
    },
]
