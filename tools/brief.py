"""Daily morning brief: today's reminders, new opportunities, one course, weather and prices.
Time is changeable from chat (saved in the settings table); default comes from .env.
"""
import logging
from datetime import datetime, time, timezone

from telegram import Update
from telegram.ext import Application, ContextTypes

import config
import memory
from tools import reminders

log = logging.getLogger("brief")

JOB_NAME = "morning-brief"
_app: Application | None = None

BRIEF_PROMPT = """[طلب داخلي من البوت، مش من أدهم] جهّز الموجز الصباحي لأدهم لليوم.

البيانات:
تذكيرات اليوم:
{reminders}

فرص انبعتتله آخر 24 ساعة:
{opportunities}

المطلوب (مختصر، نص عادي، إيموجي خفيف، بدون مقدمات طويلة):
1. صباح الخير بسطر.
2. الطقس اليوم بخان يونس (استعمل web_search، سطر واحد).
3. سعر الدولار مقابل الشيكل اليوم (web_search، سطر واحد).
4. تذكيرات اليوم (أو "ما في تذكيرات").
5. أهم الفرص الجديدة بسطر لكل وحدة مع الرابط (أو "ما نزل إشي مناسب مبارح").
6. دورة وحدة مقترحة بتسدّ نقص عنده للوظايف (مجانية أو رخيصة، أونلاين)، ابحث عنها بـ web_search وحط رابطها.
7. جملة تحفيز قصيرة.
إذا البحث فشل بأي بند، اكتب "ما قدرت أجيبه هلّق" وبس؛ ممنوع تخمّن أرقام أو أسعار أو طقس."""


def _brief_time() -> str | None:
    """HH:MM, or None if the brief is turned off."""
    value = memory.get_setting("brief_time", config.MORNING_BRIEF_TIME)
    return None if value == "off" else value


def _schedule() -> None:
    for job in _app.job_queue.get_jobs_by_name(JOB_NAME):
        job.schedule_removal()
    hhmm = _brief_time()
    if not hhmm:
        log.info("Morning brief is off")
        return
    hour, minute = map(int, hhmm.split(":"))
    _app.job_queue.run_daily(_send_brief, time=time(hour, minute, tzinfo=reminders.TZ),
                             name=JOB_NAME, chat_id=config.OWNER_ID)
    log.info("Morning brief every day at %s", hhmm)


def setup(app: Application) -> None:
    global _app
    _app = app
    _schedule()


def _data() -> tuple[str, str]:
    now = datetime.now(reminders.TZ)
    end = now.replace(hour=23, minute=59)
    rems = [r for r in memory.list_active_reminders()
            if reminders._parse_utc(r["due_utc"]) <= end.astimezone(timezone.utc)]
    rem_text = "\n".join(f"- {r['text']} ({reminders.fmt_local(reminders._parse_utc(r['due_utc']))})"
                         for r in rems) or "- لا شيء"
    opps = memory.matches_since(24)[:8]
    opp_text = "\n".join(f"- [{o['category']}] {o['title']} (تطابق {o['score']}%) {o['url']}"
                         for o in opps) or "- لا شيء"
    return rem_text, opp_text


async def build_brief() -> str:
    import brain  # avoid a circular import at startup

    rem_text, opp_text = _data()
    answer = await brain.reply(BRIEF_PROMPT.format(reminders=rem_text, opportunities=opp_text),
                               use_history=False, save=False)
    memory.add_message("assistant", answer)  # so follow-up questions about the brief work
    return answer


async def _send_brief(context: ContextTypes.DEFAULT_TYPE) -> None:
    from tg_utils import split_text

    try:
        text = await build_brief()
    except Exception as e:
        log.exception("Morning brief failed")
        text = f"☀️ صباح الخير أدهم! ما قدرت أجهّز الموجز كامل اليوم 😕 ({getattr(e, 'user_message', 'خطأ')})"
    for chunk in split_text(text):
        await context.bot.send_message(config.OWNER_ID, chunk, disable_web_page_preview=True)


async def brief_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/brief — send the brief now."""
    from tg_utils import send_long

    msg = await update.effective_message.reply_text("☀️ عم جهّزلك الموجز...")
    try:
        text = await build_brief()
    except Exception as e:
        log.exception("Manual brief failed")
        text = getattr(e, "user_message", "صار خطأ وأنا بجهّز الموجز 😕 جرّب كمان شوي.")
    await msg.delete()
    await send_long(update, text)


# ---------------------------------------------------------------- AI tool

async def set_morning_brief(args: dict) -> str:
    value = (args.get("time") or "").strip().lower()
    if value in ("off", "stop", "none"):
        memory.set_setting("brief_time", "off")
        _schedule()
        return "تم إيقاف الموجز الصباحي."
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError:
        return "خطأ: الوقت لازم يكون HH:MM (مثلاً 07:30) أو off."
    memory.set_setting("brief_time", parsed.strftime("%H:%M"))
    _schedule()
    return f"تم: الموجز الصباحي صار كل يوم الساعة {parsed:%H:%M} بتوقيت غزة."


TOOLS = [
    {
        "name": "set_morning_brief",
        "description": "Change the daily morning brief time (24h HH:MM, Gaza time) or turn it off with 'off'.",
        "parameters": {
            "type": "object",
            "properties": {"time": {"type": "string", "description": "e.g. '07:30' or 'off'"}},
            "required": ["time"],
        },
        "handler": set_morning_brief,
    },
]
