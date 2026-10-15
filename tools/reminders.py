"""Reminders: one-off and repeating, sent by the bot at the right time (Asia/Gaza).
Stored in SQLite so they survive restarts; scheduled with python-telegram-bot's JobQueue.
"""
import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, ContextTypes

import config
import memory

log = logging.getLogger("reminders")

TZ = ZoneInfo(config.TIMEZONE)
DAY_CODES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]  # index = Python weekday()
AR_DAYS = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
REPEAT_AR = {"none": "مرة وحدة", "daily": "كل يوم", "weekly": "كل أسبوع", "monthly": "كل شهر"}

_app: Application | None = None


def setup(app: Application) -> None:
    """Called once at startup: re-schedule every active reminder from the database."""
    global _app
    _app = app
    active = memory.list_active_reminders()
    for r in active:
        _schedule(r["id"], _parse_utc(r["due_utc"]))
    log.info("Scheduled %d active reminders", len(active))


# ---------------------------------------------------------------- time helpers

def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def _utc_str(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def fmt_local(dt: datetime) -> str:
    d = dt.astimezone(TZ)
    return f"{AR_DAYS[d.weekday()]} {d:%Y-%m-%d} الساعة {d:%H:%M}"


def _days(days_str: str) -> list[int]:
    return [int(x) for x in days_str.split(",") if x != ""]


def _repeat_text(repeat: str, days_str: str) -> str:
    if repeat == "weekly" and days_str:
        short = ["اثنين", "ثلاثاء", "أربعاء", "خميس", "جمعة", "سبت", "أحد"]
        return "كل " + " و".join(short[d] for d in _days(days_str))
    return REPEAT_AR.get(repeat, repeat)


def _at(d: date, like: datetime) -> datetime:
    """Date `d` at the same wall-clock time as `like`, in Gaza time."""
    return datetime(d.year, d.month, d.day, like.hour, like.minute, tzinfo=TZ)


def _next_after(local: datetime, repeat: str, days: list[int]) -> datetime:
    d = local.date()
    if repeat == "daily":
        d += timedelta(days=1)
    elif repeat == "weekly":
        d += timedelta(days=1 if days else 7)
        while days and d.weekday() not in days:
            d += timedelta(days=1)
    elif repeat == "monthly":
        year, month = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
        for day in (d.day, 30, 29, 28):  # clamp e.g. the 31st to the month's last day
            try:
                d = date(year, month, day)
                break
            except ValueError:
                continue
    return _at(d, local)


def _next_future(due: datetime, repeat: str, days: list[int]) -> datetime:
    local, now = due.astimezone(TZ), datetime.now(TZ)
    while local <= now:
        local = _next_after(local, repeat, days)
    return local.astimezone(timezone.utc)


# ---------------------------------------------------------------- scheduling

def _job_name(rem_id: int) -> str:
    return f"reminder-{rem_id}"


def _unschedule(rem_id: int) -> None:
    if _app:
        for job in _app.job_queue.get_jobs_by_name(_job_name(rem_id)):
            job.schedule_removal()


def _schedule(rem_id: int, due_utc: datetime) -> None:
    if not _app:
        raise RuntimeError("reminders.setup() was not called")
    _unschedule(rem_id)
    when = max(due_utc, datetime.now(timezone.utc) + timedelta(seconds=2))
    _app.job_queue.run_once(_fire, when=when, data=rem_id, name=_job_name(rem_id),
                            chat_id=config.OWNER_ID)


def _buttons(rem_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ تمام", callback_data=f"rem:done:{rem_id}"),
        InlineKeyboardButton("⏰ ربع ساعة", callback_data=f"rem:snz:{rem_id}:15"),
        InlineKeyboardButton("⏰ ساعة", callback_data=f"rem:snz:{rem_id}:60"),
    ]])


async def _fire(context: ContextTypes.DEFAULT_TYPE) -> None:
    rem_id = context.job.data
    r = memory.get_reminder(rem_id)
    if not r or not r["active"]:
        return
    due = _parse_utc(r["due_utc"])
    text = f"⏰ تذكير يا أدهم:\n{r['text']}"
    if datetime.now(timezone.utc) - due > timedelta(minutes=2):
        text += f"\n\n(كان موعده {fmt_local(due)}، بس البوت كان طافي)"
    if r["repeat"] == "none":
        memory.deactivate_reminder(rem_id)
    else:
        nxt = _next_future(due, r["repeat"], _days(r["days"]))
        memory.set_reminder_due(rem_id, _utc_str(nxt))
        _schedule(rem_id, nxt)
        text += f"\n\n🔁 الموعد الجاي: {fmt_local(nxt)}"
    await context.bot.send_message(config.OWNER_ID, text, reply_markup=_buttons(rem_id))
    # Let the AI know, so "أجّلها ربع ساعة" right after works.
    memory.add_message("assistant", f"[أرسلت لأدهم التذكير رقم {rem_id}: {r['text']}]")


def _snooze(rem_id: int, minutes: int) -> str:
    r = memory.get_reminder(rem_id)
    if not r:
        return f"ما في تذكير برقم {rem_id}."
    now = datetime.now(timezone.utc)
    current_due = _parse_utc(r["due_utc"])
    if r["repeat"] == "none" and r["active"] and current_due > now:
        # Not sent yet: push its own time back.
        due = current_due + timedelta(minutes=minutes)
        memory.set_reminder_due(rem_id, _utc_str(due))
        _schedule(rem_id, due)
        return f"أخّرته {minutes} دقيقة، صار موعده {fmt_local(due)}."
    # Already sent: remind again N minutes from now.
    due = now + timedelta(minutes=minutes)
    if r["repeat"] == "none":
        memory.set_reminder_due(rem_id, _utc_str(due))
        new_id = rem_id
    else:  # keep the repeating one as is, add a one-off copy
        new_id = memory.add_reminder(r["text"], _utc_str(due))
    _schedule(new_id, due)
    return f"أجّلته {minutes} دقيقة، رح ذكّرك {fmt_local(due)}."


def _delete(rem_id: int) -> bool:
    _unschedule(rem_id)
    return memory.deactivate_reminder(rem_id)


def _list_text() -> str:
    rows = memory.list_active_reminders()
    if not rows:
        return "ما في تذكيرات فعّالة."
    return "\n".join(
        f"#{r['id']} | {r['text']} | {fmt_local(_parse_utc(r['due_utc']))} | {_repeat_text(r['repeat'], r['days'])}"
        for r in rows
    )


# ---------------------------------------------------------------- Telegram handlers

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Buttons under reminder messages and the /reminders list."""
    q = update.callback_query
    if not q or q.from_user.id != config.OWNER_ID:
        return
    await q.answer()
    parts = q.data.split(":")
    action, rem_id = parts[1], int(parts[2])
    if action == "done":
        result = "✅ تمام"
    elif action == "snz":
        result = "😴 " + _snooze(rem_id, int(parts[3]))
    elif action == "del":
        result = f"🗑️ حذفت التذكير #{rem_id}" if _delete(rem_id) else f"التذكير #{rem_id} محذوف أصلاً"
    else:
        return
    await q.edit_message_text(f"{q.message.text}\n\n{result}")


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/reminders — show active reminders with a delete button for each."""
    rows = memory.list_active_reminders()
    if not rows:
        await update.effective_message.reply_text("ما عندك تذكيرات فعّالة يا أدهم 👌")
        return
    buttons = [[InlineKeyboardButton(f"❌ حذف #{r['id']}", callback_data=f"rem:del:{r['id']}")]
               for r in rows[:30]]
    await update.effective_message.reply_text(
        "📋 تذكيراتك:\n\n" + _list_text(), reply_markup=InlineKeyboardMarkup(buttons)
    )


# ---------------------------------------------------------------- AI tools

async def add_reminder(args: dict) -> str:
    text = (args.get("text") or "").strip()
    due_s = (args.get("due") or "").strip().replace(" ", "T")
    repeat = args.get("repeat") or "none"
    if repeat not in REPEAT_AR:
        repeat = "none"
    days = sorted({DAY_CODES.index(d) for d in args.get("weekdays") or [] if d in DAY_CODES})
    if repeat != "weekly":
        days = []
    if not text:
        return "خطأ: نص التذكير فاضي."
    try:
        local = datetime.fromisoformat(due_s)
    except ValueError:
        return "خطأ: صيغة الوقت غلط، لازم تكون YYYY-MM-DD HH:MM."
    local = local.replace(tzinfo=TZ) if local.tzinfo is None else local.astimezone(TZ)

    if days and local.weekday() not in days:
        local = _next_after(local - timedelta(days=1), "weekly", days)
    if local <= datetime.now(TZ):
        if repeat == "none":
            return f"خطأ: الوقت {fmt_local(local)} فات. اسأل أدهم عن الوقت الصح."
        local = _next_future(local, repeat, days).astimezone(TZ)

    days_str = ",".join(map(str, days))
    rem_id = memory.add_reminder(text, _utc_str(local), repeat, days_str)
    _schedule(rem_id, local.astimezone(timezone.utc))
    return f"تم إنشاء التذكير رقم {rem_id}: {text} | {fmt_local(local)} | {_repeat_text(repeat, days_str)}"


async def list_reminders(args: dict) -> str:
    return _list_text()


async def delete_reminder(args: dict) -> str:
    try:
        rem_id = int(args.get("reminder_id"))
    except (TypeError, ValueError):
        return "خطأ: لازم رقم التذكير."
    return f"تم حذف التذكير رقم {rem_id}." if _delete(rem_id) else f"ما في تذكير فعّال برقم {rem_id}."


async def snooze_reminder(args: dict) -> str:
    try:
        rem_id, minutes = int(args.get("reminder_id")), int(args.get("minutes"))
    except (TypeError, ValueError):
        return "خطأ: لازم رقم التذكير وعدد الدقايق."
    if not 1 <= minutes <= 7 * 24 * 60:
        return "خطأ: عدد الدقايق لازم يكون بين 1 وأسبوع."
    return _snooze(rem_id, minutes)


TOOLS = [
    {
        "name": "add_reminder",
        "description": (
            "Create a reminder. Convert Adham's Arabic time expression into an exact local Gaza date-time "
            "using the current time given in the system prompt. For repeating reminders set `repeat` "
            "(and `weekdays` for specific days, e.g. 'كل أحد وأربعاء')."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "What to remind him about, short, in Arabic."},
                "due": {"type": "string", "description": "First time, local Gaza time, format YYYY-MM-DD HH:MM (24h)."},
                "repeat": {"type": "string", "enum": ["none", "daily", "weekly", "monthly"]},
                "weekdays": {
                    "type": "array",
                    "items": {"type": "string", "enum": DAY_CODES},
                    "description": "Only for weekly: which days, e.g. ['sun','wed'].",
                },
            },
            "required": ["text", "due"],
        },
        "handler": add_reminder,
    },
    {
        "name": "list_reminders",
        "description": "List all active reminders with their numbers, times and repeat.",
        "parameters": {"type": "object", "properties": {}},
        "handler": list_reminders,
    },
    {
        "name": "delete_reminder",
        "description": "Cancel a reminder by its number (call list_reminders first if you don't know it).",
        "parameters": {
            "type": "object",
            "properties": {"reminder_id": {"type": "integer"}},
            "required": ["reminder_id"],
        },
        "handler": delete_reminder,
    },
    {
        "name": "snooze_reminder",
        "description": (
            "Postpone a reminder by N minutes (e.g. 'أجّلها ربع ساعة' = 15). If it was not sent yet, "
            "its own time moves later; if it was already sent, it comes again N minutes from now."
        ),
        "parameters": {
            "type": "object",
            "properties": {"reminder_id": {"type": "integer"}, "minutes": {"type": "integer"}},
            "required": ["reminder_id", "minutes"],
        },
        "handler": snooze_reminder,
    },
]
