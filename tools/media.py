"""Voice, image and PDF understanding. Turns media into text that brain.py can work with.
- Voice: Groq Whisper (free), then Gemini as a fallback.
- Images/PDF: Gemini (backup model first, it has its own quota), then xKiro for images.
"""
import base64
import logging

import httpx

import config

log = logging.getLogger("media")

MAX_BYTES = 20 * 1024 * 1024  # Telegram bots can download up to 20 MB
_client = httpx.AsyncClient(timeout=180)

DESCRIBE_PROMPT = (
    "Adham sent this file on Telegram. Describe what it is and extract all important text exactly "
    "(names, numbers, dates, links, error messages, job details). If it is a job ad, list title, "
    "organization, requirements and deadline. Answer in Arabic, keep original English terms as they are."
)


class MediaError(Exception):
    """Error with a ready Arabic message for the user."""

    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message


def _gemini_models() -> list[str]:
    return [m for m in (config.GEMINI_BACKUP_MODEL, config.MODEL) if m] if config.GEMINI_API_KEY else []


async def _gemini(data: bytes, mime: str, prompt: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    last = None
    for model in _gemini_models():
        try:
            resp = await client.aio.models.generate_content(
                model=model,
                contents=[types.Part.from_bytes(data=data, mime_type=mime), prompt],
                config=types.GenerateContentConfig(
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)),
            )
            if resp.text:
                return resp.text.strip()
        except Exception as e:
            log.warning("Gemini %s failed on %s: %s", model, mime, str(e)[:200])
            last = e
    raise RuntimeError(f"Gemini could not read the file: {last}")


async def transcribe(audio: bytes, filename: str = "voice.ogg") -> str:
    """Speech to text (Arabic first)."""
    if len(audio) > MAX_BYTES:
        raise MediaError("التسجيل كبير كتير، ابعت تسجيل أقصر 🙏")
    key = config.BACKUP_KEYS.get("Groq", ("", ""))[0]
    if key:
        try:
            resp = await _client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {key}"},
                files={"file": (filename, audio)},
                data={"model": "whisper-large-v3", "language": "ar"},
            )
            resp.raise_for_status()
            text = (resp.json().get("text") or "").strip()
            if text:
                return text
        except Exception as e:
            log.warning("Groq transcription failed: %s", str(e)[:200])
    try:
        return await _gemini(audio, "audio/ogg", "Transcribe this voice message exactly, in its language. "
                                                 "Output only the transcript.")
    except Exception:
        raise MediaError("ما قدرت أفهم التسجيل الصوتي هالمرة 😕 جرّب كمان مرة أو اكتبلي.")


async def _xkiro_image(data: bytes, mime: str) -> str:
    key, model = config.BACKUP_KEYS.get("xKiro", ("", ""))
    if not key or not model:
        raise RuntimeError("xKiro not configured")
    url = "data:" + mime + ";base64," + base64.b64encode(data).decode()
    resp = await _client.post(
        "https://api.xkiro.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "max_tokens": 2000, "messages": [{"role": "user", "content": [
            {"type": "text", "text": DESCRIBE_PROMPT},
            {"type": "image_url", "image_url": {"url": url}},
        ]}]},
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"].get("content") or ""
    if not text.strip():
        raise RuntimeError("empty answer")
    return text.strip()


VIDEO_PROMPT = (
    "Adham sent this video / screen recording on Telegram. Carefully analyze the visual actions, "
    "on-screen text, code, terminal outputs, errors, UI behavior, and bugs shown in the video. "
    "Provide a comprehensive, senior-engineer breakdown in Arabic with clear steps, root causes, "
    "and actionable code/system fixes."
)


async def describe_video(data: bytes, mime: str = "video/mp4") -> str:
    """Read a video file, screen recording, or video note and extract visual events & logs."""
    if len(data) > MAX_BYTES:
        raise MediaError("الفيديو كبير كتير (أكثر من 20 ميغا) 🙏 حاول تبعت مقطع أقصر أو أقل جودة.")
    try:
        return await _gemini(data, mime, VIDEO_PROMPT)
    except Exception as e:
        log.warning("Video describe failed: %s", str(e)[:200])
        raise MediaError(f"ما قدرت أحلل الفيديو هالمرة 😕 ({e})")


async def describe(data: bytes, mime: str) -> str:
    """Read an image, PDF, or video and return its description + extracted text."""
    if len(data) > MAX_BYTES:
        raise MediaError("الملف كبير كتير (أكثر من 20 ميغا) 🙏")
    if mime.startswith("video/"):
        return await describe_video(data, mime)
    engines = [lambda: _gemini(data, mime, DESCRIBE_PROMPT)]
    if mime.startswith("image/"):
        engines.append(lambda: _xkiro_image(data, mime))
    for engine in engines:
        try:
            return await engine()
        except Exception as e:
            log.warning("Describe failed: %s", str(e)[:200])
    raise MediaError("ما قدرت أقرأ الملف هالمرة 😕 جرّب كمان شوي.")

