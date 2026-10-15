"""Google Calendar: list events, create events. A personal event (no
attendees) is just his own calendar and is created directly; an event with
outside attendees is an invitation sent in his name, so it needs his explicit
confirmation first (non-negotiable rule).
"""
import asyncio
import logging
from datetime import datetime, timezone

import google_auth
from google_auth import GoogleAuthError

log = logging.getLogger("calendar_tools")


async def _service():
    return await asyncio.to_thread(google_auth.calendar_service)


async def list_events(args: dict) -> str:
    max_results = min(int(args.get("max_results") or 10), 20)
    try:
        service = await _service()
        now = datetime.now(timezone.utc).isoformat()
        resp = await asyncio.to_thread(
            lambda: service.events().list(
                calendarId="primary", timeMin=now, maxResults=max_results,
                singleEvents=True, orderBy="startTime").execute()
        )
        events = resp.get("items", [])
        if not events:
            return "ما في مواعيد جاية."
        lines = []
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date"))
            lines.append(f"id={e['id']} {e.get('summary', '(بدون عنوان)')} — {start}")
        return "\n".join(lines)
    except GoogleAuthError as e:
        return e.user_message
    except Exception as e:
        log.exception("list_events failed")
        return f"خطأ بجلب المواعيد: {e}"


async def create_event(args: dict) -> str:
    summary = (args.get("summary") or "").strip()
    start_iso = args.get("start_iso")
    end_iso = args.get("end_iso")
    attendees = args.get("attendees") or []
    confirmed = bool(args.get("confirmed"))

    if not summary or not start_iso or not end_iso:
        return "خطأ: لازم عنوان الموعد ووقت البداية والنهاية (ISO 8601 بتوقيت غزة)."

    if attendees and not confirmed:
        return (
            "هاد الموعد فيه دعوة لناس تانيين (" + ", ".join(attendees) + "). "
            "إرسال دعوة لحدا غيرك لازم موافقتك الصريحة الأول — اسأل أدهم إذا موافق يبعت "
            "الدعوة، وإذا وافق نادي نفس الأداة بـ confirmed=true. إذا بدك موعد شخصي بس، "
            "اعمله بدون attendees."
        )

    try:
        service = await _service()
        event = {
            "summary": summary,
            "start": {"dateTime": start_iso, "timeZone": "Asia/Gaza"},
            "end": {"dateTime": end_iso, "timeZone": "Asia/Gaza"},
        }
        if attendees:
            event["attendees"] = [{"email": a} for a in attendees]
        created = await asyncio.to_thread(
            lambda: service.events().insert(calendarId="primary", body=event, sendUpdates="all").execute()
        )
        return f"تم إنشاء الموعد: {summary} ({start_iso}). id={created.get('id')}"
    except GoogleAuthError as e:
        return e.user_message
    except Exception as e:
        log.exception("create_event failed")
        return f"خطأ بإنشاء الموعد: {e}"


TOOLS = [
    {
        "name": "list_events",
        "description": "List Adham's upcoming Google Calendar events.",
        "parameters": {
            "type": "object",
            "properties": {"max_results": {"type": "integer", "description": "Default 10, max 20."}},
        },
        "handler": list_events,
    },
    {
        "name": "create_event",
        "description": (
            "Create a Google Calendar event for Adham. If it has attendees (an invitation sent "
            "to other people in his name), you MUST get his explicit yes/no confirmation in chat "
            "before calling this with confirmed=true — never invite people without asking first."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "start_iso": {"type": "string", "description": "ISO 8601 datetime, Asia/Gaza time."},
                "end_iso": {"type": "string", "description": "ISO 8601 datetime, Asia/Gaza time."},
                "attendees": {"type": "array", "items": {"type": "string"}, "description": "Email addresses to invite, if any."},
                "confirmed": {"type": "boolean", "description": "True only after Adham explicitly agreed to invite the attendees."},
            },
            "required": ["summary", "start_iso", "end_iso"],
        },
        "handler": create_event,
    },
]
