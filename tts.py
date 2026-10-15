"""Text-to-speech engine for Telegram voice notes.
Uses Microsoft Azure Neural TTS (via edge-tts) with zero API keys and ultra-realistic Arabic voices.
Falls back to Gemini TTS if needed. Encodes output to Telegram OGG/Opus.
"""
import asyncio
import logging
import os
import subprocess
import tempfile
from pathlib import Path

import config
import imageio_ffmpeg

log = logging.getLogger("tts")

PRIMARY_VOICE = "ar-EG-ShakirNeural"  # Professional, warm, and natural Arabic
BACKUP_VOICE = "ar-SA-HamedNeural"
MAX_CHARS = 1000


class TTSError(Exception):
    pass


def _ffmpeg_path() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


async def synthesize_ogg_async(text: str) -> bytes:
    """Asynchronously synthesizes Arabic text to Telegram-compatible OGG/Opus bytes."""
    text = text.strip()
    if not text:
        raise TTSError("empty text")
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS].rsplit(" ", 1)[0] + "..."

    # 1. Try Microsoft Azure Neural TTS via edge-tts
    try:
        import edge_tts
        with tempfile.TemporaryDirectory() as tmp:
            mp3_path = Path(tmp) / "speech.mp3"
            ogg_path = Path(tmp) / "speech.ogg"

            communicate = edge_tts.Communicate(text, voice=PRIMARY_VOICE, rate="+5%")
            await communicate.save(str(mp3_path))

            if mp3_path.exists() and mp3_path.stat().st_size > 100:
                # Convert MP3 to OGG/Opus for Telegram
                cmd = [
                    _ffmpeg_path(), "-y",
                    "-i", str(mp3_path),
                    "-c:a", "libopus",
                    "-b:a", "32k",
                    str(ogg_path)
                ]
                proc = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
                if proc.returncode == 0 and ogg_path.exists():
                    return ogg_path.read_bytes()
    except Exception as e:
        log.warning("edge-tts primary synthesis failed: %s; falling back...", e)

    # 2. Fallback to Gemini TTS if configured
    if config.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=config.GEMINI_API_KEY)
            resp = await client.aio.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=f"Say in a natural, warm voice, in Arabic: {text}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
                        )
                    ),
                ),
            )
            part = resp.candidates[0].content.parts[0]
            pcm_data = part.inline_data.data
            return _pcm_to_ogg(pcm_data)
        except Exception as e:
            log.warning("Gemini TTS fallback failed: %s", e)

    raise TTSError("All TTS engines failed to synthesize audio.")


def synthesize_ogg(text: str) -> bytes:
    """Synchronous wrapper for synthesize_ogg_async."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(synthesize_ogg_async(text))
        return asyncio.run(synthesize_ogg_async(text))
    except Exception:
        # Fallback runner
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(synthesize_ogg_async(text))
        finally:
            new_loop.close()


def _pcm_to_ogg(pcm_data: bytes) -> bytes:
    """Wrap raw 16-bit PCM at 24kHz mono to OGG/Opus via ffmpeg."""
    with tempfile.TemporaryDirectory() as tmp:
        pcm_path = Path(tmp) / "in.pcm"
        ogg_path = Path(tmp) / "out.ogg"
        pcm_path.write_bytes(pcm_data)
        cmd = [
            _ffmpeg_path(), "-y", "-f", "s16le", "-ar", "24000", "-ac", "1",
            "-i", str(pcm_path), "-c:a", "libopus", str(ogg_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not ogg_path.exists():
            raise TTSError(f"ffmpeg failed: {result.stderr[-300:]}")
        return ogg_path.read_bytes()
