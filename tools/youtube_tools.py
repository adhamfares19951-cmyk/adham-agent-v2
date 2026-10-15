"""YouTube Intelligence Tool for adham-agent.
Powered by Agent-Reach architecture: Zero API fees, local yt-dlp & transcript API extraction.
"""
import asyncio
import logging
import re
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

log = logging.getLogger("youtube_tools")


def extract_video_id(url_or_id: str) -> str | None:
    """Extract YouTube video ID from various URL formats or raw ID."""
    url_or_id = url_or_id.strip()
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", url_or_id):
        return url_or_id

    parsed = urlparse(url_or_id)
    if parsed.hostname in ("youtu.be", "www.youtu.be"):
        return parsed.path.lstrip("/").split("/")[0][:11]

    if "youtube.com" in (parsed.hostname or ""):
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            return qs.get("v", [None])[0]
        if parsed.path.startswith(("/shorts/", "/embed/", "/v/")):
            parts = parsed.path.split("/")
            if len(parts) >= 3:
                return parts[2][:11]

    # Regex search inside string as fallback
    m = re.search(r"(?:v=|\/|youtu\.be\/)([a-zA-Z0-9_-]{11})", url_or_id)
    return m.group(1) if m else None


def _get_transcript_sync(video_id: str) -> dict:
    """Fetch transcript synchronously with language preferences (Arabic first, then English)."""
    try:
        # Try fetching official Arabic or English, or auto-generated
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            # Preference order: manual ar, auto ar, manual en, auto en, or first available
            try:
                transcript = transcript_list.find_transcript(["ar", "en"])
            except Exception:
                # Get generated or first available
                transcript = next(iter(transcript_list))
            
            raw_entries = transcript.fetch()
        except Exception:
            # Fallback to direct get_transcript
            raw_entries = YouTubeTranscriptApi.get_transcript(video_id, languages=["ar", "en"])

        full_text = " ".join([e.get("text", "") for e in raw_entries])
        # Clean double spaces and linebreaks
        full_text = re.sub(r"\s+", " ", full_text).strip()
        
        # Take key excerpt up to 6000 chars
        return {
            "success": True,
            "text": full_text[:6000],
            "total_chars": len(full_text),
            "entry_count": len(raw_entries),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_video_info_sync(url: str) -> dict:
    """Extract video metadata via yt-dlp without downloading media."""
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "success": True,
                "title": info.get("title", ""),
                "channel": info.get("uploader", "") or info.get("channel", ""),
                "duration": info.get("duration", 0),
                "view_count": info.get("view_count", 0),
                "description": (info.get("description", "") or "")[:1000],
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_youtube_transcript_and_info(args: dict) -> str:
    """Fetch video metadata and transcript for summarizing or understanding."""
    url = (args.get("url") or "").strip()
    if not url:
        return "يرجى تزويدي برابط يوتيوب صحيح."

    video_id = extract_video_id(url)
    if not video_id:
        return "لم أتمكن من استخراج معرف الفيديو من الرابط المدخل."

    canonical_url = f"https://www.youtube.com/watch?v={video_id}"

    # Run yt-dlp and transcript fetch in worker threads
    info_res, trans_res = await asyncio.gather(
        asyncio.to_thread(_get_video_info_sync, canonical_url),
        asyncio.to_thread(_get_transcript_sync, video_id),
    )

    title = info_res.get("title", "فيديو يوتيوب")
    channel = info_res.get("channel", "")
    duration_sec = info_res.get("duration", 0)
    dur_str = f"{duration_sec // 60} دقيقة و {duration_sec % 60} ثانية" if duration_sec else "غير محدد"

    lines = [
        f"📺 **عنوان الفيديو**: {title}",
        f"👤 **القناة**: {channel} | ⏱️ **المدة**: {dur_str}",
        f"🔗 **الرابط**: {canonical_url}",
        "",
    ]

    if trans_res.get("success"):
        text = trans_res.get("text", "")
        lines.append("📝 **النص المكتوب والمستخرج من الفيديو (Transcript)**:")
        lines.append(text)
        if trans_res.get("total_chars", 0) > 6000:
            lines.append("\n(ملاحظة: تم اقتطاع أول 6,000 حرف لتلخيص النقاط الجوهرية).")
    else:
        lines.append("⚠️ **ملاحظة بخصوص الترجمة**:")
        lines.append(f"الفيديو لا يحتوي على ترجمة نصية متاحة ({trans_res.get('error')}).")
        desc = info_res.get("description", "")
        if desc:
            lines.append("\n📄 **وصف الفيديو الرسمي**:")
            lines.append(desc)

    return "\n".join(lines)


def _search_youtube_sync(query: str, max_results: int = 5) -> list[dict]:
    """Search YouTube videos via yt-dlp flat extraction."""
    search_target = f"ytsearch{max_results}:{query}"
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(search_target, download=False)
            entries = res.get("entries", [])
            out = []
            for e in entries:
                if not e:
                    continue
                out.append({
                    "id": e.get("id"),
                    "title": e.get("title"),
                    "channel": e.get("uploader") or e.get("channel"),
                    "duration": e.get("duration"),
                    "url": f"https://www.youtube.com/watch?v={e.get('id')}",
                })
            return out
    except Exception as e:
        log.warning("yt-dlp search failed: %s", e)
        return []


async def search_youtube(args: dict) -> str:
    """Search YouTube for tutorials, technical explanations, or reviews."""
    query = (args.get("query") or "").strip()
    if not query:
        return "يرجى تحديد موضوع البحث."

    max_res = int(args.get("max_results") or 5)
    max_res = min(max(max_res, 1), 10)

    results = await asyncio.to_thread(_search_youtube_sync, query, max_res)
    if not results:
        return f"لم أجد نتائج على يوتيوب لعبارة: {query}"

    lines = [f"🔍 **نتائج البحث على يوتيوب لـ: «{query}»**\n"]
    for i, v in enumerate(results, 1):
        dur = f"({v['duration'] // 60} د)" if v.get("duration") else ""
        lines.append(f"{i}. **{v['title']}** {dur}")
        lines.append(f"   القناة: {v.get('channel', 'غير معروف')}")
        lines.append(f"   الرابط: {v['url']}\n")

    return "\n".join(lines).strip()


TOOLS = [
    {
        "name": "get_youtube_summary",
        "description": (
            "Extract video information, metadata, and full transcripts/subtitles from a YouTube video link. "
            "Essential for summarizing talks, technical tutorials, Forex/trading webinars, and lectures instantly."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "YouTube video link or ID."}
            },
            "required": ["url"],
        },
        "handler": get_youtube_transcript_and_info,
    },
    {
        "name": "search_youtube",
        "description": (
            "Search YouTube for educational videos, technical explanations, reviews, or news. "
            "Returns top video titles, channels, and links."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword or question."},
                "max_results": {"type": "integer", "description": "Number of results (1-10, default 5)."},
            },
            "required": ["query"],
        },
        "handler": search_youtube,
    },
]
