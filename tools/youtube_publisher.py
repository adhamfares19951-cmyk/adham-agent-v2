"""YouTube Publisher & Channel Automation for adham-agent.
Handles:
1. Resumable video uploads (Long videos & Shorts)
2. Metadata management (Titles, Descriptions, Tags, Category, Privacy)
3. Channel analytics & subscriber statistics
4. Seamless integration with video_assembler & video_autocaption
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import google.auth.exceptions
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

log = logging.getLogger("youtube_publisher")

BASE_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

CLIENT_SECRET_FILE = SESSIONS_DIR / "client_secret.json"
TOKEN_FILE = SESSIONS_DIR / "youtube_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def is_authenticated() -> bool:
    """Checks if valid YouTube OAuth credentials exist."""
    if not TOKEN_FILE.exists():
        return False
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        return bool(creds and (creds.valid or creds.refresh_token))
    except Exception as e:
        log.warning("Failed to validate YouTube token: %s", e)
        return False


def get_authenticated_service():
    """Builds and returns an authorized YouTube API v3 service."""
    creds = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            log.warning("Corrupt token file: %s", e)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
            except Exception as e:
                log.error("Failed to refresh YouTube token: %s", e)
                creds = None

    if not creds:
        raise RuntimeError(
            "لم يتم توثيق حساب يوتيوب بعد. يرجى تشغيل ملف setup_youtube.bat أو وضع client_secret.json أولاً."
        )

    return build("youtube", "v3", credentials=creds)


def run_oauth_flow_interactive(port: int = 0) -> str:
    """Runs a local browser OAuth flow to authenticate YouTube and save the token."""
    if not CLIENT_SECRET_FILE.exists():
        raise FileNotFoundError(
            f"ملف إعدادات جوجل غير موجود: {CLIENT_SECRET_FILE}.\n"
            "يرجى تحميل ملف الـ OAuth JSON من Google Cloud Console وتسميته client_secret.json في مجلد sessions."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
    # Launches browser on user's machine with dynamic free port
    creds = flow.run_local_server(port=port, prompt="consent", access_type="offline")

    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    return f"تم توثيق قناة يوتيوب بنجاح! تم حفظ التوكن الدائم في: {TOKEN_FILE.name}"


async def get_channel_info() -> dict[str, Any]:
    """Retrieves authenticated channel information, subscriber count, and views."""
    def _fetch():
        youtube = get_authenticated_service()
        response = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            mine=True
        ).execute()

        items = response.get("items", [])
        if not items:
            return {"error": "لم يتم العثور على أي قناة مرتبطة بهذا الحساب."}

        item = items[0]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})

        return {
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "custom_url": snippet.get("customUrl", ""),
            "subscribers": stats.get("subscriberCount", "0"),
            "views": stats.get("viewCount", "0"),
            "videos": stats.get("videoCount", "0"),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "published_at": snippet.get("publishedAt", ""),
            "channel_id": item.get("id", ""),
        }

    return await asyncio.to_thread(_fetch)


async def upload_video(
    video_path: Path | str,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    category_id: str = "28",  # 28 = Science & Technology, 22 = People & Blogs, 27 = Education
    privacy_status: str = "public",  # public, unlisted, private
    is_short: bool | None = None,
    thumbnail_path: Path | str | None = None,
) -> dict[str, Any]:
    """Uploads a video to YouTube with resumable chunked uploading."""
    video_file = Path(video_path)
    if not video_file.exists():
        raise FileNotFoundError(f"ملف الفيديو غير موجود: {video_file}")

    # Determine if it's a Short (vertical and/or < 60s)
    if is_short is None:
        is_short = "#shorts" in title.lower() or "#shorts" in description.lower()

    if is_short and "#Shorts" not in title and "#Shorts" not in description:
        title = f"{title} #Shorts"
        description = f"{description}\n\n#Shorts #YouTubeShorts"

    tags = tags or ["ذكاء_اصطناعي", "تكنولوجيا", "برمجة", "تقنية"]
    if is_short and "Shorts" not in tags:
        tags.append("Shorts")

    def _do_upload():
        youtube = get_authenticated_service()

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            }
        }

        # Resumable media upload in 4MB chunks
        media_body = MediaFileUpload(
            str(video_file),
            chunksize=4 * 1024 * 1024,
            resumable=True
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media_body
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                log.info("Upload progress: %d%%", int(status.progress() * 100))

        video_id = response.get("id")
        video_url = f"https://youtu.be/{video_id}"
        short_url = f"https://youtube.com/shorts/{video_id}"

        # Upload custom thumbnail if provided
        if thumbnail_path and Path(thumbnail_path).exists():
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumbnail_path))
                ).execute()
                log.info("Custom thumbnail uploaded successfully for video %s", video_id)
            except Exception as te:
                log.warning("Failed to upload custom thumbnail: %s", te)

        return {
            "id": video_id,
            "title": title,
            "url": short_url if is_short else video_url,
            "privacy": privacy_status,
            "is_short": is_short,
            "response": response
        }

    return await asyncio.to_thread(_do_upload)


async def _handle_upload_video(args: dict[str, Any]) -> str:
    """Agent tool handler for uploading a video/short to YouTube."""
    vpath = args.get("video_path")
    if not vpath:
        return "خطأ: مسار ملف الفيديو مطلوب (video_path)."
    title = args.get("title", "فيديو جديد عبر أدهم بوت")
    description = args.get("description", "")
    privacy = args.get("privacy", "public")
    tags = args.get("tags")
    is_short = args.get("is_short")

    try:
        res = await upload_video(
            video_path=vpath,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy,
            is_short=is_short
        )
        return (
            f"✅ تم رفع الفيديو ونشره بنجاح على يوتيوب!\n"
            f"🎬 العنوان: {res['title']}\n"
            f"🔗 الرابط: {res['url']}\n"
            f"🔒 الحالة: {res['privacy']}\n"
            f"📱 نوع الفيديو: {'Shorts ⚡' if res['is_short'] else 'فيديو عادي 🎥'}"
        )
    except Exception as e:
        return f"❌ فشل رفع الفيديو إلى يوتيوب: {e}"


async def _handle_get_channel_stats(args: dict[str, Any]) -> str:
    """Agent tool handler for retrieving YouTube channel statistics."""
    try:
        info = await get_channel_info()
        if "error" in info:
            return f"⚠️ {info['error']}"
        return (
            f"📊 إحصائيات قناة يوتيوب الحالية:\n"
            f"📺 اسم القناة: {info['title']}\n"
            f"👥 المشتركون: {info['subscribers']}\n"
            f"👁️ إجمالي المشاهدات: {info['views']}\n"
            f"🎥 عدد الفيديوهات: {info['videos']}\n"
            f"🔗 المعرّف المخصص: {info.get('custom_url', 'غير محدد')}"
        )
    except Exception as e:
        return f"❌ فشل جلب إحصائيات القناة: {e}"


TOOLS = [
    {
        "name": "youtube_upload_video",
        "description": "يرفع فيديو أو شورتس جديد إلى قناة يوتيوب المتصلة مع ضبط العنوان والوصف والهاشتاجات والحالة.",
        "parameters": {
            "type": "object",
            "properties": {
                "video_path": {"type": "string", "description": "المسار الكامل لملف الفيديو MP4 على الجهاز"},
                "title": {"type": "string", "description": "عنوان الفيديو أو الشورتس"},
                "description": {"type": "string", "description": "الوصف والروابط والهاشتاجات"},
                "privacy": {"type": "string", "enum": ["public", "unlisted", "private"], "description": "حالة النشر: عام (public)، غير مدرج (unlisted)، أو خاص (private)"},
                "is_short": {"type": "boolean", "description": "هل الفيديو شورتس عمودي؟"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "قائمة الكلمات الدلالية Tags"}
            },
            "required": ["video_path", "title"]
        },
        "handler": _handle_upload_video
    },
    {
        "name": "youtube_get_channel_stats",
        "description": "يجلب إحصائيات وأداء قناة يوتيوب المتصلة (المشتركين، المشاهدات الكلية، الفيديوهات).",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "handler": _handle_get_channel_stats
    }
]

