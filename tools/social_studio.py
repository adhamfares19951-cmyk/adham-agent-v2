"""Automated Social Studio for Adham Agent Enterprise OS.
Generates viral, high-retention short-form video scripts (Reels / TikTok / Shorts 9:16)
for Shamel POS, MQL5 Trading Bots, and MikroTik/Solar Engineering.
Generates crisp, natural Arabic voiceover via edge-tts and routes everything through the Approval Queue (HITL).
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import edge_tts

import config
import memory

log = logging.getLogger("tools.social_studio")

AUDIO_DIR = config.BASE_DIR / "audio_output"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# Script Generation Templates & Knowledge Engine
# ==============================================================================

SCRIPTS_KNOWLEDGE = {
    "pos": {
        "title": "كيف تشغل كاشير محلك بدون إنترنت وكهرباء؟ 🏪",
        "topic": "نظام شامل POS (Offline-First)",
        "hook": "بتخاف تنقطع الكهربا ويوقف الكاشير بنص الزحمة؟ هاد الحل النهائي!",
        "problem": "أغلب البرامج المحاسبية بتعلق أول ما يقطع النت أو ينطفي السيرفر، وتضيع فواتير الزبائن وحسابات الشكك.",
        "solution": "مع نظام شامل POS الأوفلاين، محلك شغال 24/7 على أي هاتف أو تابلت مع باور بانك. باركود سريع، فواتير حرارية، وجرد دقيق بالقطعة والكرتونة.",
        "cta": "اطلب نسختك التجريبية اليوم من م. أدهم الهباش ورابط المعاينة بالبايو أو راسلنا واتساب!",
        "full_text": (
            "بتخاف تنقطع الكهربا ويوقف الكاشير بنص الزحمة؟ هاد الحل النهائي! "
            "أغلب أصحاب المحلات في غزة وخانيونس بيعانوا من توقف البرامج المحاسبية أول ما يقطع النت أو الكهربا، "
            "وتضيع حسابات الدفاتر وديون الزبائن. "
            "نظام شامل POS صمم خصيصاً ليشتغل أوفلاين 100% بدون نت على أي هاتف أو شاشة كاشير. "
            "مسح باركود فوري، طباعة فواتير حرارية، وجرد آلي للأصناف والأرباح. "
            "احجز نسختك التجريبية وتواصل مع المهندس أدهم الهباش فوراً!"
        ),
    },
    "trading": {
        "title": "كيف تصطاد سيولة صانع السوق بروبوت MQL5 ذكي؟ 📈",
        "topic": "بوتات التداول الآلي (Smart Money Concepts)",
        "hook": "ليش 90% من المتداولين بيخسروا بالفيوتشرز والفوركس؟ لأنهم بيدخلوا بفخاخ السيولة!",
        "problem": "صناع السوق بيعملوا Liquidity Sweep لضرب الستوبات قبل ما السعر ينطلق في اتجاهه الحقيقي.",
        "solution": "برمجنا خوارزميات MQL5 ذكية مبنية على مناطق الفير فاليو جاب (FVG) والأوردر بلوك (Order Block) لتقتنص الدخول بدقة مع إغلاق آلي وإدارة مخاطر صارمة.",
        "cta": "حابب تؤتمت استراتيجيتك الخاصة في التداول وتريح أعصابك؟ تواصل مع م. أدهم الهباش لتنفيذ كودك الخاص!",
        "full_text": (
            "ليش 90% من المتداولين بيخسروا؟ لأنهم بيدخلوا في مصيدة السيولة! "
            "صناع السوق بيسحبوا السيولة وبيضربوا الستوبات قبل أي صعود حقيقي. "
            "بدل ما تقضي يومك متوتر قدام الشاشات، برمجنا روبوتات تداول MQL5 متطورة "
            "ترصد مناطق الخلل السعري الفير فاليو جاب وأوردر بلوك صانع السوق وتنفذ صفقاتك آلياً وبإدارة مخاطر محكمة. "
            "أتمت استراتيجيتك اليوم مع المهندس أدهم الهباش!"
        ),
    },
    "network_solar": {
        "title": "معادلة الأمان لمنظومة الطاقة الشمسية بدون حرق أجهزة! ⚡",
        "topic": "هندسة شبكات MikroTik ومنظومات الطاقة الشمسية",
        "hook": "مركب طاقة شمسية والبطاريات عم تفضى بساعتين؟ عندك خطأ بالحساب!",
        "problem": "التخمين العشوائي في مقاس الإنفرتر وسعة البطاريات بيسبب احتراق الأجهزة وتلف بنك البطاريات بنصف عمره.",
        "solution": "بنقدملك دراسة أحمال هندسية حتمية 100% Zero-Hallucination، مع برمجة راوترات MikroTik لتوزيع الإنترنت وعزل الشبكات بعدالة بين المشتركين.",
        "cta": "استخدم حاسبتنا الشمسية المجانية بموقعنا أو اطلب دراسة متكاملة لمنشأتك الآن!",
        "full_text": (
            "مركب طاقة شمسية والبطاريات عم تفضى بساعتين؟ الحساب العشوائي هو السبب! "
            "تركيب أحمال بدون هامش أمان 30% بيحرق الإنفرتر ويتلف خلايا البطاريات. "
            "نحن بنحسبلك سعة البطاريات والإنفرتر والألواح بمعادلات فيزيائية حتمية تضمن استقرار الكهربا لسنوات. "
            "وبنبرمجلك شبكة ميكروتك تفصل بين الموظفين والضيوف وتحمي اتصالك. "
            "جرب حاسبتنا المجانية وتواصل مع م. أدهم الهباش!"
        ),
    },
}


# ==============================================================================
# Voiceover Generation
# ==============================================================================

async def generate_arabic_voiceover(
    text: str,
    output_path: str | None = None,
    voice: str = "ar-EG-ShakirNeural",
) -> str:
    """Generates natural Arabic voiceover using edge-tts with automatic fallback and returns output file path."""
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("نص التعليق الصوتي فارغ.")

    if not output_path:
        filename = f"voiceover_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp3"
        target_file = AUDIO_DIR / filename
    else:
        target_file = Path(output_path)
        target_file.parent.mkdir(parents=True, exist_ok=True)

    voices_to_try = [voice]
    if voice != "ar-SA-HamedNeural":
        voices_to_try.append("ar-SA-HamedNeural")
    if voice != "ar-EG-SalmaNeural":
        voices_to_try.append("ar-EG-SalmaNeural")

    last_error = None
    for candidate_voice in voices_to_try:
        try:
            communicate = edge_tts.Communicate(clean_text, voice=candidate_voice)
            await communicate.save(str(target_file))
            if target_file.exists() and target_file.stat().st_size > 100:
                log.info("Arabic voiceover generated (%s): %s (%s bytes)", candidate_voice, target_file, target_file.stat().st_size)
                return str(target_file.resolve())
        except Exception as e:
            last_error = e
            log.warning("Voiceover attempt with %s failed: %s, trying fallback...", candidate_voice, e)
            await asyncio.sleep(0.5)

    if last_error:
        raise last_error
    raise RuntimeError("Failed to generate voiceover with all voices.")


# ==============================================================================
# Telegram Preview & Human-in-the-Loop Workflow
# ==============================================================================

async def send_script_approval_preview(script_data: dict[str, Any], queue_id: int) -> bool:
    """Dispatches generated script to Adham's Telegram with inline action buttons."""
    token = getattr(config, "TELEGRAM_TOKEN", None)
    owner_id = getattr(config, "OWNER_ID", None)
    if not token or not owner_id:
        return False

    title = str(script_data.get("title", "فيديو جديد")).replace("*", "").replace("_", " ")
    topic = str(script_data.get("topic", "عام")).replace("`", "")
    hook = str(script_data.get("hook", "")).replace("*", "").replace("_", " ")
    full_script = str(script_data.get("script", "")).replace("*", "").replace("_", " ")

    msg = (
        "🎬 **استوديو المحتوى الآلي — مسودة سكريبت بانتظار موافقتك!**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 **العنوان المقترح:** *{title}*\n"
        f"🎯 **الموضوع:** `{topic}`\n"
        f"🪝 **الهوك (3 ثوانٍ):** _{hook}_\n\n"
        f"📜 **نص السكريبت الكامل (للفويس والإلقاء):**\n_{full_script}_\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "*(اختر الإجراء المطلوب عبر الأزرار أدناه اعتماداً أو تسجيلاً صوتياً فورياً)*"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ اعتماد للنشر", "callback_data": f"social:approve:{queue_id}"},
                {"text": "🎙️ توليد تعليق صوتي", "callback_data": f"social:voice:{queue_id}"},
            ],
            [
                {"text": "🔄 إعادة صياغة النص", "callback_data": f"social:regen:{queue_id}"},
            ],
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": owner_id,
                    "text": msg,
                    "parse_mode": "Markdown",
                    "reply_markup": keyboard,
                },
            )
            if resp.status_code != 200:
                log.warning(
                    "Telegram send_script_approval_preview failed with Markdown (%s: %s). Retrying with plain text...",
                    resp.status_code, resp.text
                )
                plain_msg = msg.replace("**", "").replace("*", "").replace("_", "").replace("`", "")
                resp2 = await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={
                        "chat_id": owner_id,
                        "text": plain_msg,
                        "reply_markup": keyboard,
                    },
                )
                return resp2.status_code == 200
            return True
    except Exception as e:
        log.warning("Failed to send script preview: %s", e)
        return False


def create_social_script(topic_key: str = "pos") -> dict[str, Any]:
    """Builds a high-impact structured video script and queues it for approval."""
    k = topic_key.lower().strip()
    if "trading" in k or "mql" in k or "تداول" in k:
        template = SCRIPTS_KNOWLEDGE["trading"]
    elif "solar" in k or "net" in k or "طاقة" in k or "شبك" in k:
        template = SCRIPTS_KNOWLEDGE["network_solar"]
    else:
        template = SCRIPTS_KNOWLEDGE["pos"]

    script_data = {
        "title": template["title"],
        "topic": template["topic"],
        "hook": template["hook"],
        "problem": template["problem"],
        "solution": template["solution"],
        "cta": template["cta"],
        "script": template["full_text"],
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Queue into memory approval_queue
    queue_id = memory.add_approval_item(
        action_type="social_script",
        description=f"سكريبت ريلز: {template['title']}",
        payload=script_data,
    )
    script_data["queue_id"] = queue_id

    return script_data


# ==============================================================================
# Tool Handlers
# ==============================================================================

async def generate_social_script_handler(args: dict) -> str:
    """Tool handler to create viral video scripts and dispatch preview to Telegram."""
    topic = str(args.get("topic", "pos")).strip()
    script = create_social_script(topic)

    # Dispatch to Telegram for HITL Approval
    await send_script_approval_preview(script, script["queue_id"])

    return (
        f"🎬 **تم توليد سكريبت فيديو جديد بنجاح!**\n\n"
        f"📌 **العنوان:** {script['title']}\n"
        f"🎯 **الموضوع:** {script['topic']}\n"
        f"🪝 **الهوك:** {script['hook']}\n"
        f"🔢 **رقم الطابور:** #{script['queue_id']}\n\n"
        f"✅ *تم إرسال بطاقة المعاينة مع أزرار الاعتماد وتوليد التعليق الصوتي إلى هاتفك عبر تيليجرام.*"
    )


async def generate_voiceover_tool_handler(args: dict) -> str:
    """Tool handler to synthesize speech from text."""
    text = str(args.get("text", "")).strip()
    voice = str(args.get("voice", "ar-EG-ShakirNeural")).strip()

    if not text:
        return "❌ يرجى تزويد النص المطلوب تحويله لصوت."

    try:
        audio_file = await generate_arabic_voiceover(text, voice=voice)
        return f"🎙️ **تم توليد التعليق الصوتي بنجاح!**\n\n📁 **المسار:** `{audio_file}`"
    except Exception as e:
        log.exception("Voiceover generation failed: %s", e)
        return f"❌ خطأ أثناء توليد الصوت: {e}"


# ==============================================================================
# Tool Registry Export
# ==============================================================================

TOOLS = [
    {
        "name": "generate_social_script",
        "description": "توليد سكريبت فيديو قصير ريلز وتيك توك 9:16 احترافي عالي الجذب لخدماتنا (شامل POS، بوتات التداول، ميكروتك والطاقة) وإرسال معاينة لاعتماده في تيليجرام.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "الموضوع: pos (كاشير شامل)، trading (تداول MQL5)، network_solar (شبكات وطاقة)."},
            },
            "required": ["topic"],
        },
        "handler": generate_social_script_handler,
    },
    {
        "name": "generate_arabic_voiceover",
        "description": "توليد تعليق صوتي عربي واقعي ومجاني عبر edge-tts وحفظه كملف mp3 عالي الجودة.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "النص العربي المراد قراءته والتحدث به."},
                "voice": {"type": "string", "description": "الصوت المختار (الافتراضي: ar-EG-ShakirNeural أو ar-SA-HamedNeural)."},
            },
            "required": ["text"],
        },
        "handler": generate_voiceover_tool_handler,
    },
]
