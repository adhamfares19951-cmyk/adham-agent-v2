"""Text-to-speech: Gemini's TTS model, converted to OGG/Opus for Telegram
voice notes. Not an AI tool — main.py calls this directly after a voice
message gets a text reply, so the bot can talk back.
"""
import logging
import subprocess
import tempfile
from pathlib import Path

import config

log = logging.getLogger("tts")

TTS_MODEL = "gemini-2.5-flash-preview-tts"
MAX_CHARS = 800  # keep replies short enough to synthesize quickly and stay cheap


class TTSError(Exception):
    pass


def _ffmpeg_path() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def synthesize_ogg(text: str) -> bytes:
    """Text -> OGG/Opus bytes ready for Telegram's sendVoice."""
    from google import genai
    from google.genai import types

    text = text.strip()
    if not text:
        raise TTSError("empty text")
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS].rsplit(" ", 1)[0] + "..."

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    try:
        resp = client.models.generate_content(
            model=TTS_MODEL,
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
    except Exception as e:
        raise TTSError(str(e)) from e

    return _pcm_to_ogg(pcm_data)


def _pcm_to_ogg(pcm_data: bytes) -> bytes:
    """Gemini TTS returns raw 16-bit PCM at 24kHz mono; wrap+encode to OGG/Opus via ffmpeg."""
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
