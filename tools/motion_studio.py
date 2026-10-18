"""Motion Video Studio Bridge for adham-agent.
Integrates the Remotion 60FPS motion graphics engine (motion-video-studio)
into adham-agent tools and Telegram commands.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("motion_studio")

BASE_DIR = Path(__file__).resolve().parent.parent
STUDIO_DIR = BASE_DIR.parent / "motion-video-studio"
STUDIO_SCRIPT = STUDIO_DIR / "studio.py"
PORTABLE_PY = BASE_DIR / "python_runtime" / "python.exe"


async def generate_motion_masterclass(
    topic: str = "استراتيجية صيد السيولة والأوردر بلوك للذهب",
    ratio: str = "16:9",
    voice: str = "ar_male",
) -> dict[str, Any]:
    """Runs the motion-video-studio Remotion pipeline and returns the output video path."""
    if not STUDIO_SCRIPT.exists():
        raise FileNotFoundError(f"Motion Video Studio not found at: {STUDIO_SCRIPT}")

    python_bin = str(PORTABLE_PY) if PORTABLE_PY.exists() else sys.executable
    cmd = [
        python_bin,
        str(STUDIO_SCRIPT),
        "--topic", topic,
        "--ratio", ratio,
        "--voice", voice,
    ]

    log.info("Launching Motion Video Studio: %s", " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(STUDIO_DIR),
    )

    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err_msg = stderr.decode("utf-8", errors="replace")
        log.error("Motion Video Studio failed: %s", err_msg)
        raise RuntimeError(f"فشل إنتاج فيديو الموشن جرافيك: {err_msg[:400]}")

    out_dir = STUDIO_DIR / "out"
    pattern = "masterclass_*.mp4" if ratio == "16:9" else "masterclass_*_9x16.mp4"
    matching = sorted(out_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matching:
        # Fallback to any recent mp4
        matching = sorted(out_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not matching:
        raise FileNotFoundError("لم يتم العثور على ملف الفيديو الناتج في مجلد out.")

    output_video = matching[0]
    return {
        "success": True,
        "video_path": str(output_video),
        "topic": topic,
        "ratio": ratio,
        "size_mb": round(output_video.stat().st_size / (1024 * 1024), 2),
        "message": f"تم إنتاج ماستركلاس الموشن جرافيك بنجاح! الملف: {output_video.name}"
    }


async def generate_talking_fruit_short(
    topic: str = "مستر برتقال في خطر",
    character: str = "orange",
    voice: str = "ar_fruit_funny",
) -> dict[str, Any]:
    """Runs the talking fruit/character short production pipeline."""
    if not STUDIO_SCRIPT.exists():
        raise FileNotFoundError(f"Motion Video Studio not found at: {STUDIO_SCRIPT}")

    python_bin = str(PORTABLE_PY) if PORTABLE_PY.exists() else sys.executable
    cmd = [
        python_bin,
        str(STUDIO_SCRIPT),
        "--mode", "fruit",
        "--character", character,
        "--topic", topic,
        "--voice", voice,
    ]

    log.info("Launching Talking Fruit Studio: %s", " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(STUDIO_DIR),
    )

    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err_msg = stderr.decode("utf-8", errors="replace")
        log.error("Talking Fruit Studio failed: %s", err_msg)
        raise RuntimeError(f"فشل إنتاج فيديو الفواكه المتكلمة: {err_msg[:400]}")

    out_dir = STUDIO_DIR / "out"
    matching = sorted(out_dir.glob(f"talking_{character}_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matching:
        matching = sorted(out_dir.glob("talking_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not matching:
        raise FileNotFoundError("لم يتم العثور على ملف فيديو الفاكهة في مجلد out.")

    output_video = matching[0]
    return {
        "success": True,
        "video_path": str(output_video),
        "character": character,
        "topic": topic,
        "size_mb": round(output_video.stat().st_size / (1024 * 1024), 2),
    }


async def _handle_motion_masterclass(args: dict[str, Any]) -> str:
    """Agent tool handler for generating 60FPS motion graphics videos."""
    topic = args.get("topic", "أسرار السيولة المؤسساتية وتداول الذهب")
    ratio = args.get("ratio", "16:9")
    voice = args.get("voice", "ar_male")

    try:
        res = await generate_motion_masterclass(topic=topic, ratio=ratio, voice=voice)
        return (
            f"🏆 **تم إنتاج فيديو الموشن جرافيك الاحترافي بنجاح!**\n\n"
            f"📌 **الموضوع:** {res['topic']}\n"
            f"📐 **الأبعاد:** {res['ratio']}\n"
            f"⚡ **التقنية:** Remotion 60FPS + شموع حركية + كروت ديناميكية تنبثق وتتحرك\n"
            f"📁 **مسار الملف:** `{res['video_path']}`\n"
            f"💾 **الحجم:** {res['size_mb']} MB"
        )
    except Exception as e:
        log.exception("Motion masterclass error")
        return f"❌ خطأ أثناء إنتاج فيديو الموشن جرافيك: {e}"


async def generate_fruit_fight_match(
    output_filename: str | None = None,
) -> dict[str, Any]:
    """Runs the 3-round fruit wrestling match production pipeline."""
    if not STUDIO_SCRIPT.exists():
        raise FileNotFoundError(f"Motion Video Studio not found at: {STUDIO_SCRIPT}")

    python_bin = str(PORTABLE_PY) if PORTABLE_PY.exists() else sys.executable
    cmd = [
        python_bin,
        str(STUDIO_SCRIPT),
        "--mode", "fight",
    ]

    log.info("Launching Fruit Wrestling Match: %s", " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(STUDIO_DIR),
    )

    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err_msg = stderr.decode("utf-8", errors="replace")
        log.error("Fruit Wrestling Match failed: %s", err_msg)
        raise RuntimeError(f"فشل إنتاج فيديو مصارعة الفواكه: {err_msg[:400]}")

    out_dir = STUDIO_DIR / "out"
    matching = sorted(out_dir.glob("fruit_fight_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matching:
        matching = sorted(out_dir.glob("fruit_wrestling_match.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not matching:
        raise FileNotFoundError("لم يتم العثور على ملف فيديو نزال الفواكه في مجلد out.")

    output_video = matching[0]
    return {
        "success": True,
        "video_path": str(output_video),
        "title": "المعركة الكبرى: أفوكادو ضد تفاحة (3 جولات)",
        "size_mb": round(output_video.stat().st_size / (1024 * 1024), 2),
    }


async def _handle_talking_fruit_short(args: dict[str, Any]) -> str:
    """Agent tool handler for generating talking fruit / object comedy shorts."""
    topic = args.get("topic", "مستر برتقال في خطر")
    character = args.get("character", "orange")
    voice = args.get("voice", "ar_fruit_funny")

    try:
        res = await generate_talking_fruit_short(topic=topic, character=character, voice=voice)
        return (
            f"🍊 **تم إنتاج فيديو الفاكهة المتكلمة (Talking Character) بنجاح!**\n\n"
            f"🎭 **الشخصية:** {res['character']}\n"
            f"📌 **الموضوع:** {res['topic']}\n"
            f"✨ **الميزات:** عيون واقعية ترمش وتتحرك + فم يتزامن مع مخارج الحروف + صوت كرتوني مرح + كروت تيك توك قافزة\n"
            f"📁 **مسار الملف:** `{res['video_path']}`\n"
            f"💾 **الحجم:** {res['size_mb']} MB"
        )
    except Exception as e:
        log.exception("Talking fruit short error")
        return f"❌ خطأ أثناء إنتاج فيديو الفاكهة المتكلمة: {e}"


async def _handle_fruit_fight_match(args: dict[str, Any]) -> str:
    """Agent tool handler for generating the 3-round fruit wrestling brawl."""
    try:
        res = await generate_fruit_fight_match()
        return (
            f"🥊 **تم إنتاج فيديو نزال المصارعة بين الأفوكادو والتفاحة بنجاح!**\n\n"
            f"🏟️ **الحلبة:** حلبة مصارعة كاملة + حبال ديناميكية + كشافات ستاديوم + جمهور يهتف ويرفع لافتات\n"
            f"⚡ **النزال:** 3 جولات كاملة (Round 1 + Round 2 + Final K.O.)\n"
            f"🥑 **المقاتل 1:** الأفوكادو بقفازات ملاكمة حمراء\n"
            f"🍎 **المقاتل 2:** التفاحة بقفازات ملاكمة زرقاء وعصابة رأس مقاتل\n"
            f"🍋 **الحكم:** ليمونة بقميص الحكام المقلم وصفارة يقف بينهما ويحسم النتيجة\n"
            f"📊 **الـ HUD:** أشرطة صحة (Health Bars) تنقص مع كل ضربة + مؤثرات POW! و BAM! و K.O.!\n"
            f"🎙️ **التعليق:** تعليق حماسي احترافي بنبرة معلقي المصارعة العالمية\n"
            f"📁 **مسار الملف:** `{res['video_path']}`\n"
            f"💾 **الحجم:** {res['size_mb']} MB"
        )
    except Exception as e:
        log.exception("Fruit fight match error")
        return f"❌ خطأ أثناء إنتاج فيديو نزال الفواكه: {e}"


TOOLS = [
    {
        "name": "create_motion_masterclass",
        "description": "ينتج فيديوهات طويلة (Masterclass / وثائقية) أو شورتس بتقنية الموشن جرافيك 60FPS عبر Remotion مع شموع تداول مرسومة لايف، كروت تطفو وتنزلق، تقسيم فصول، وصوت عصبي احترافي.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "موضوع الماستركلاس أو الفيديو"},
                "ratio": {"type": "string", "enum": ["16:9", "9:16"], "description": "أبعاد الفيديو: 16:9 لليوتيوب أو 9:16 للشورتس وتيك توك"},
                "voice": {"type": "string", "description": "الصوت العصبي (ar_male, ar_egypt, en_male)"}
            },
            "required": ["topic"]
        },
        "handler": _handle_motion_masterclass
    },
    {
        "name": "create_talking_fruit_short",
        "description": "ينتج فيديوهات كوميدية شورتس وتيك توك للفواكه والأشياء المتكلمة (Talking Fruits / Talking Objects) مثل البرتقال، الأفوكادو، التفاح، الموز، الليمون، والبيتكوين المتكلم مع عيون ترمش وتتحرك وفم يتكلم بحركات شفاه واقعية وصوت كرتوني مضحك.",
        "parameters": {
            "type": "object",
            "properties": {
                "character": {
                    "type": "string",
                    "enum": ["orange", "apple", "avocado", "banana", "lemon", "bitcoin", "coffee"],
                    "description": "نوع الشخصية أو الفاكهة المتكلمة"
                },
                "topic": {"type": "string", "description": "موضوع أو قصة الفيديو الكوميدي"},
                "voice": {"type": "string", "description": "نمط الصوت (ar_fruit_funny, ar_fruit_cute, ar_fruit_deep, ar_fruit_panicked, en_cartoon)"}
            },
            "required": ["character"]
        },
        "handler": _handle_talking_fruit_short
    },
    {
        "name": "create_fruit_fight_match",
        "description": "ينتج فيديو ملحمي لنزال مصارعة وملاكمة متكامل بين الفواكه (أفوكادو ضد تفاحة) في حلبة مصارعة مع حبال وأضواء وجمهور يهتف، وحكم رسمي، وأشرطة صحة Health Bars، وقتال على 3 جولات ينتهي بالضربة القاضية K.O. وتعليق حماسي.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "handler": _handle_fruit_fight_match
    }
]
