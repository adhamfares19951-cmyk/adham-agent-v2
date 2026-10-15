"""Local-business outreach: track leads (shops/companies without a website).
Never sends anything on its own — messages and demo sites are drafts Adham
reviews and sends himself (see /pitch).
"""
import io
import json
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

import config
import memory
from tools.demosite import PITCH_MESSAGE_PROMPT, SITE_PLAN_PROMPT, build_demo_site_html

log = logging.getLogger("outreach")


async def add_lead(args: dict) -> str:
    name = (args.get("business_name") or "").strip()
    sector = (args.get("sector") or "").strip()
    if not name or not sector:
        return "خطأ: لازم اسم المحل ونوع نشاطه."
    lead_id = memory.add_lead(name, sector, (args.get("location") or "").strip(),
                              (args.get("contact_info") or "").strip())
    return f"تم حفظ العميل المحتمل رقم {lead_id}: {name} ({sector}). استخدم /pitch {lead_id} لتجهيز رسالة وموقع تجريبي له."


async def list_leads(args: dict) -> str:
    rows = memory.list_leads(args.get("status") or None)
    if not rows:
        return "ما في عملاء محتملين محفوظين بعد."
    return "\n".join(
        f"#{r['id']} {r['business_name']} ({r['sector']}) — {r['status']}"
        + (f" — {r['location']}" if r["location"] else "")
        for r in rows
    )


async def update_lead_status(args: dict) -> str:
    try:
        lead_id = int(args.get("lead_id"))
    except (TypeError, ValueError):
        return "خطأ: لازم رقم العميل المحتمل."
    status = (args.get("status") or "").strip()
    if status not in ("new", "drafted", "sent", "replied", "won", "lost"):
        return "خطأ: الحالة لازم تكون: new, drafted, sent, replied, won, lost."
    if memory.update_lead_status(lead_id, status, (args.get("notes") or "").strip()):
        return f"تم تحديث حالة العميل رقم {lead_id} إلى {status}."
    return f"ما في عميل محتمل برقم {lead_id}."


def _parse_json_obj(text: str) -> dict:
    text = re.sub(r"```(json)?", "", text or "")
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        return {}
    try:
        data = json.loads(text[start:end + 1])
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


async def pitch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/pitch <lead_id> — draft a demo site + outreach message for a saved lead."""
    from brain import llm  # shared provider chain

    msg = update.effective_message
    args = context.args or []
    if not args or not args[0].isdigit():
        await msg.reply_text("استخدمها هيك: /pitch <رقم العميل المحتمل>\nشوف الأرقام بسؤالي 'وريني العملاء المحتملين'.")
        return

    lead = memory.get_lead(int(args[0]))
    if not lead:
        await msg.reply_text("ما في عميل محتمل بهاد الرقم.")
        return

    status_msg = await msg.reply_text(f"🎨 عم أجهز موقع تجريبي ورسالة لـ {lead['business_name']}...")

    try:
        plan_reply = await llm.generate(
            "You design simple demo websites for local businesses. Reply with JSON only.",
            [{"role": "user", "content": SITE_PLAN_PROMPT.format(
                business_name=lead["business_name"], sector=lead["sector"], location=lead["location"])}],
        )
        memory.add_usage("llm_call")
        plan = _parse_json_obj(plan_reply.text)
        if not plan:
            await status_msg.edit_text("ما قدرت أجهز خطة الموقع، جرب كمان مرة.")
            return

        message_reply = await llm.generate(
            "You write short, warm, non-pushy Arabic outreach messages.",
            [{"role": "user", "content": PITCH_MESSAGE_PROMPT.format(
                business_name=lead["business_name"], sector=lead["sector"], location=lead["location"])}],
        )
        memory.add_usage("llm_call")
        pitch_text = message_reply.text.strip()

        html = build_demo_site_html(lead["business_name"], lead["sector"], lead["location"], plan)
    except Exception:
        log.exception("Failed to build pitch for lead %s", lead["id"])
        await status_msg.edit_text("صار خطأ وأنا بجهز الموقع والرسالة 😕 جرب كمان مرة.")
        return

    memory.update_lead_status(lead["id"], "drafted")

    doc = io.BytesIO(html.encode("utf-8"))
    doc.name = f"{lead['business_name']}_demo.html"
    await status_msg.delete()
    await context.bot.send_document(
        config.OWNER_ID, doc, filename=doc.name,
        caption=f"🌐 موقع تجريبي لـ {lead['business_name']} — افتحه بأي متصفح لتشوف شكله.",
    )
    await msg.reply_text(
        "✍️ مسودة الرسالة (راجعها وابعتها إنت بنفسك، ما حدا رح يبعتها غيرك):\n\n" + pitch_text
    )


TOOLS = [
    {
        "name": "add_lead",
        "description": (
            "Save a local business (shop/company) that looks like a candidate for a website, so "
            "Adham can pitch them one. Use when he mentions a business by name that doesn't seem "
            "to have a real website (only a Facebook page, or nothing online)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "business_name": {"type": "string"},
                "sector": {"type": "string", "description": "e.g. 'مطعم', 'صيدلية', 'محل موبايلات'."},
                "location": {"type": "string"},
                "contact_info": {"type": "string", "description": "Phone/WhatsApp/Facebook page if known."},
            },
            "required": ["business_name", "sector"],
        },
        "handler": add_lead,
    },
    {
        "name": "list_leads",
        "description": "List saved business leads, optionally filtered by status.",
        "parameters": {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["new", "drafted", "sent", "replied", "won", "lost"]}},
        },
        "handler": list_leads,
    },
    {
        "name": "update_lead_status",
        "description": "Update a lead's status after Adham tells you what happened (sent it, they replied, won/lost the deal).",
        "parameters": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "integer"},
                "status": {"type": "string", "enum": ["new", "drafted", "sent", "replied", "won", "lost"]},
                "notes": {"type": "string"},
            },
            "required": ["lead_id", "status"],
        },
        "handler": update_lead_status,
    },
]
