"""Voice Studio & Neural TTS Generator for adham-agent.
Uses edge-tts (Microsoft Azure Neural Voices) to produce ultra-realistic, studio-grade
Arabic and English voiceovers for TikTok, YouTube Shorts, and Reels with zero API keys or costs.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import edge_tts

log = logging.getLogger("voice_studio")

BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_DIR = BASE_DIR / "audio_output"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

VOICES = {
    "ar_male_egypt": "ar-EG-ShakirNeural",       # حماسي وواضح ومناسب جداً للشروحات والتيك توك
    "ar_male_gulf": "ar-SA-HamedNeural",        # فخم ورسمي خليجي
    "ar_female": "ar-EG-SalmaNeural",           # صوت أنثوي طبيعي
    "en_male_tech": "en-US-ChristopherNeural",   # صوت أمريكي نشط جداً لمقاطع التقنية والتريند
    "en_female_tech": "en-US-JennyNeural",       # صوت أمريكي نقي ومحترف
}


async def generate_speech(text: str, voice_key: str = "ar_male_egypt", rate: str = "+0%", pitch: str = "+0Hz") -> Path:
    """Generates an MP3 audio voiceover from text."""
    voice_name = VOICES.get(voice_key, VOICES["ar_male_egypt"])
    filename = f"voice_{int(time.time())}.mp3"
    target_path = AUDIO_DIR / filename

    communicate = edge_tts.Communicate(text=text, voice=voice_name, rate=rate, pitch=pitch)
    await communicate.save(str(target_path))
    return target_path


async def voice_studio_handler(args: dict) -> str:
    """Handler for AI voice generator tool."""
    text = (args.get("text") or "").strip()
    voice_key = (args.get("voice") or "ar_male_egypt").strip().lower()

    if not text:
        return (
            "يرجى تحديد النص المراد تحويله لتعليق صوتي. الأصوات المتاحة:\n"
            + "\n".join(f"• `{k}`: {v}" for k, v in VOICES.items())
            + "\n\n💡 مثال: `/voice ar_male_egypt مرحباً بكم في أسرار الذكاء الاصطناعي!`"
        )

    try:
        audio_file = await generate_speech(text, voice_key=voice_key)
        return (
            f"🎙️ **تم توليد التعليق الصوتي العصبي بنجاح!**\n\n"
            f"👤 **الصوت المستخدم:** `{voice_key}` ({VOICES.get(voice_key)})\n"
            f"📁 **مسار الملف الصوتي:** `{audio_file}`\n"
            f"⚡ **الحجم:** {audio_file.stat().st_size / 1024:.1f} KB\n\n"
            f"💡 *أصبح الملف الصوتي جاهزاً للدمج في مقطع الفيديو.*"
        )
    except Exception as e:
        return f"❌ خطأ أثناء توليد الصوت: {e}"


TOOLS = [
    {
        "name": "generate_ai_voiceover",
        "description": (
            "توليد تعليق صوتي فائق النقاء والواقعية (Neural TTS) باللغة العربية أو الإنجليزية "
            "لفيديوهات تيك توك، يوتيوب شورتس، وريلز بدون أي مفاتيح أو تكاليف."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "النص المراد تحويله لصوت"},
                "voice": {
                    "type": "string",
                    "enum": list(VOICES.keys()),
                    "description": "معرف الصوت: ar_male_egypt (الأكثر حماساً)، ar_male_gulf، ar_female، en_male_tech، en_female_tech",
                    "default": "ar_male_egypt",
                },
            },
            "required": ["text"],
        },
        "handler": voice_studio_handler,
    }
]
