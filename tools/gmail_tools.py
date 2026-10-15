"""Gmail: read-only search/read tools, plus a draft-then-approve flow for
sending — nothing is ever sent without Adham tapping ✅ first (non-negotiable).
"""
import asyncio
import base64
import logging
import uuid
from email.mime.text import MIMEText

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, ContextTypes

import config
import google_auth
from google_auth import GoogleAuthError

log = logging.getLogger("gmail_tools")

_app: Application | None = None
_pending: dict[str, dict] = {}  # token -> {"to", "subject", "body"}


def setup(app: Application) -> None:
    global _app
    _app = app


async def _service():
    return await asyncio.to_thread(google_auth.gmail_service)


def _extract_body(payload: dict) -> str:
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    for part in payload.get("parts", []) or []:
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
    for part in payload.get("parts", []) or []:
        text = _extract_body(part)
        if text:
            return text
    return "(ما قدرت أطلع نص الرسالة، ممكن تكون HTML بس)"


async def search_emails(args: dict) -> str:
    query = (args.get("query") or "is:unread").strip()
    max_results = min(int(args.get("max_results") or 10), 20)
    try:
        service = await _service()
        resp = await asyncio.to_thread(
            lambda: service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        )
        msgs = resp.get("messages", [])
        if not msgs:
            return "ما في رسائل مطابقة."
        lines = []
        for m in msgs:
            full = await asyncio.to_thread(
                lambda mid=m["id"]: service.users().messages().get(
                    userId="me", id=mid, format="metadata",
                    metadataHeaders=["From", "Subject", "Date"]).execute()
            )
            headers = {h["name"]: h["value"] for h in full.get("payload", {}).get("headers", [])}
            lines.append(
                f"id={m['id']} من: {headers.get('From', '')} | "
                f"{headers.get('Subject', '(بدون عنوان)')} | {headers.get('Date', '')}"
            )
        return "\n".join(lines)
    except GoogleAuthError as e:
        return e.user_message
    except Exception as e:
        log.exception("search_emails failed")
        return f"خطأ بجلب الإيميلات: {e}"


async def read_email(args: dict) -> str:
    message_id = args.get("message_id")
    if not message_id:
        return "خطأ: لازم رقم الرسالة (id) يلي طلع من search_emails."
    try:
        service = await _service()
        full = await asyncio.to_thread(
            lambda: service.users().messages().get(userId="me", id=message_id, format="full").execute()
        )
        headers = {h["name"]: h["value"] for h in full.get("payload", {}).get("headers", [])}
        body = _extract_body(full.get("payload", {}))
        return (f"من: {headers.get('From', '')}\nالموضوع: {headers.get('Subject', '')}\n"
                f"التاريخ: {headers.get('Date', '')}\n\n{body[:3000]}")
    except GoogleAuthError as e:
        return e.user_message
    except Exception as e:
        log.exception("read_email failed")
        return f"خطأ بقراءة الرسالة: {e}"


async def draft_email(args: dict) -> str:
    to = (args.get("to") or "").strip()
    subject = (args.get("subject") or "").strip()
    body = (args.get("body") or "").strip()
    if not to or not subject or not body:
        return "خطأ: لازم المرسل إليه والموضوع والنص الثلاثة."

    token = uuid.uuid4().hex[:8]
    _pending[token] = {"to": to, "subject": subject, "body": body}

    preview = f"📧 مسودة إيميل جاهزة:\n\nإلى: {to}\nالموضوع: {subject}\n\n{body}"
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ إرسال", callback_data=f"mail:send:{token}"),
        InlineKeyboardButton("❌ إلغاء", callback_data=f"mail:cancel:{token}"),
    ]])
    await _app.bot.send_message(config.OWNER_ID, preview, reply_markup=markup)
    return ("جهزت المسودة وعرضتها عليك بزرين (إرسال/إلغاء) — ما رح تنبعت إلا لما توافق. "
            "إذا بدك تعديل، احكيلي شو تبدل وبجهزلك مسودة جديدة.")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if not q or q.from_user.id != config.OWNER_ID:
        return
    _, action, token = q.data.split(":")
    draft = _pending.pop(token, None)
    if not draft:
        await q.answer("المسودة خلصت صلاحيتها أو انبعتت قبل هيك.")
        return

    if action == "cancel":
        await q.answer("تم الإلغاء.")
        await q.edit_message_text("❌ ألغيت الرسالة.")
        return

    await q.answer("📤 عم أبعتها...")
    try:
        service = await _service()
        message = MIMEText(draft["body"])
        message["to"] = draft["to"]
        message["subject"] = draft["subject"]
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        await asyncio.to_thread(
            lambda: service.users().messages().send(userId="me", body={"raw": raw}).execute()
        )
        await q.edit_message_text(f"✅ انبعتت الرسالة لـ {draft['to']}.")
    except GoogleAuthError as e:
        await q.edit_message_text(e.user_message)
    except Exception as e:
        log.exception("send email failed")
        await q.edit_message_text(f"❌ صار خطأ وأنا ببعتها: {e}")


TOOLS = [
    {
        "name": "search_emails",
        "description": "Search Adham's Gmail (Gmail search syntax, e.g. 'is:unread', 'from:someone@ngo.org'). Read-only.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Gmail search query. Default 'is:unread'."},
                "max_results": {"type": "integer", "description": "Default 10, max 20."},
            },
        },
        "handler": search_emails,
    },
    {
        "name": "read_email",
        "description": "Read one email's full text by its id (from search_emails).",
        "parameters": {
            "type": "object",
            "properties": {"message_id": {"type": "string"}},
            "required": ["message_id"],
        },
        "handler": read_email,
    },
    {
        "name": "draft_email",
        "description": (
            "Prepare an email to send and show it to Adham with Send/Cancel buttons. "
            "NEVER sends by itself — only Adham tapping the button actually sends it. "
            "Use this whenever he asks you to reply to or write an email."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
        "handler": draft_email,
    },
]
