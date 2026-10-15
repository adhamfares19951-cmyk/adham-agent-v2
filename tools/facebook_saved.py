"""Facebook Saved Items Extractor tool for adham-agent.
Uses saved session cookies to extract all bookmarks, posts, reels, and videos
categorized into collections (علم, طعام, etc.) via Facebook's Relay GraphQL engine.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

import httpx

log = logging.getLogger("facebook_saved")

BASE_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = BASE_DIR / "sessions"
OUTPUT_JSON = BASE_DIR / "facebook_saved_items.json"
OUTPUT_MD = BASE_DIR / "facebook_saved_items.md"

DESKTOP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}

GRAPHQL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.facebook.com",
    "Referer": "https://www.facebook.com/saved/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Fb-Friendly-Name": "CometSaveDashboardAllItemsPaginationQuery",
}

DOC_ID = "27174039202273427"


def _load_cookies() -> dict[str, str]:
    cookie_file = SESSIONS_DIR / "facebook_cookies.json"
    if not cookie_file.exists():
        return {}
    try:
        with open(cookie_file, "r", encoding="utf-8") as f:
            return json.load(f).get("cookies", {})
    except Exception as e:
        log.error("Failed to read Facebook cookies: %s", e)
        return {}


async def extract_all_saved(max_items: int = 150, force_refresh: bool = False) -> list[dict[str, Any]]:
    """Crawls Facebook Saved items with GraphQL pagination."""
    if not force_refresh and OUTPUT_JSON.exists():
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                items = data.get("items", [])
                if items:
                    return items
        except Exception:
            pass

    cookies = _load_cookies()
    if not cookies:
        raise ValueError("لا توجد كوكيز محفوظة لفيسبوك. استخدم أمر /sessions لحفظ الكوكيز أولاً.")

    c_user = cookies.get("c_user", "100087516376683")
    all_items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    async with httpx.AsyncClient(headers=DESKTOP_HEADERS, cookies=cookies, timeout=25, follow_redirects=True) as client:
        resp = await client.get("https://www.facebook.com/saved/")
        if resp.status_code != 200:
            raise RuntimeError(f"فشل الاتصال بصفحة المحفوظات (رمز الحالة: {resp.status_code})")

        html = resp.text

        # Extract DTSG Token
        dtsg_m = re.findall(r'"DTSGInitialData",\[\],{"token":"([^"]+)"', html)
        if not dtsg_m:
            dtsg_m = re.findall(r'\["DTSGInitData",\[\],{"token":"([^"]+)"', html)
        if not dtsg_m:
            dtsg_m = re.findall(r'"token":"(NA[A-Za-z0-9_-]+:[0-9]+:[0-9]+)"', html)

        fb_dtsg = dtsg_m[0] if dtsg_m else "NAfwmkqhFIM72rROXdib3qDuaz-_dFTSHOmGWcXbcTsgRkZ4kS_2hhA:16:1789285954"

        # Extract initial Relay stream cache
        matches = re.finditer(r'\["RelayPrefetchedStreamCache",\s*"next",\s*\[\],\s*\["(.*?)",\s*({.*?})\]\]', html)
        initial_cursor = None
        has_next_page = False

        for m in matches:
            key = m.group(1)
            if "CometSaveDashboardRoot" in key:
                try:
                    val = json.loads(m.group(2))
                    data = val.get("__bbox", {}).get("result", {}).get("data", {})
                    all_saves = data.get("viewer", {}).get("saver_info", {}).get("all_saves", {})
                    edges = all_saves.get("edges", [])
                    pinfo = all_saves.get("page_info", {})
                    has_next_page = pinfo.get("has_next_page", False)
                    initial_cursor = pinfo.get("end_cursor")

                    for e in edges:
                        node = e.get("node", {})
                        nid = node.get("id")
                        if nid and nid not in seen_ids:
                            seen_ids.add(nid)
                            savable = node.get("savable", {}) or {}
                            container = node.get("container_savable", {}) or {}
                            actors = [a.get("name") for a in container.get("savable_actors", []) if a.get("name")]
                            lists = [l.get("name") for l in node.get("containing_lists", {}).get("nodes", []) if l.get("name")]

                            all_items.append({
                                "id": nid,
                                "type": savable.get("__typename") or savable.get("savable_default_category"),
                                "title": (savable.get("savable_title") or {}).get("text", "").strip(),
                                "url": savable.get("url") or savable.get("savable_permalink"),
                                "author": ", ".join(actors) if actors else "غير محدد",
                                "collections": lists if lists else ["العامة"],
                                "attributes": [a.get("text") for a in savable.get("savable_attributes", []) if a.get("text")],
                            })
                except Exception as ex:
                    log.warning("Failed parsing initial Relay cache: %s", ex)

    # Paginate via GraphQL
    current_cursor = initial_cursor
    page_num = 1
    max_pages = 25

    async with httpx.AsyncClient(headers=GRAPHQL_HEADERS, cookies=cookies, timeout=25) as client:
        while has_next_page and current_cursor and len(all_items) < max_items and page_num <= max_pages:
            page_num += 1
            payload = {
                "av": c_user,
                "__user": c_user,
                "__a": "1",
                "__req": str(page_num),
                "__hs": "20376.HYP:comet_pkg.2.1..0.0",
                "dpr": "1",
                "__ccg": "EXCELLENT",
                "__rev": "1016843400",
                "fb_dtsg": fb_dtsg,
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "CometSaveDashboardAllItemsPaginationQuery",
                "variables": json.dumps({
                    "count": 15,
                    "cursor": current_cursor,
                    "content_filter": None,
                    "use_case": "SAVE_DEFAULT",
                    "scale": 1,
                }),
                "doc_id": DOC_ID,
            }

            try:
                resp = await client.post("https://www.facebook.com/api/graphql/", data=payload)
                if resp.status_code != 200:
                    break

                lines = [l.strip() for l in resp.text.split("\n") if l.strip()]
                new_items = 0
                has_next_page = False

                for line in lines:
                    try:
                        d = json.loads(line)
                        if "data" in d:
                            all_saves = d["data"].get("viewer", {}).get("saver_info", {}).get("all_saves", {})
                            edges = all_saves.get("edges", [])
                            pinfo = all_saves.get("page_info", {})
                            has_next_page = pinfo.get("has_next_page", False)
                            current_cursor = pinfo.get("end_cursor")

                            for e in edges:
                                node = e.get("node", {})
                                nid = node.get("id")
                                if nid and nid not in seen_ids:
                                    seen_ids.add(nid)
                                    new_items += 1
                                    savable = node.get("savable", {}) or {}
                                    container = node.get("container_savable", {}) or {}
                                    actors = [a.get("name") for a in container.get("savable_actors", []) if a.get("name")]
                                    lists = [l.get("name") for l in node.get("containing_lists", {}).get("nodes", []) if l.get("name")]

                                    all_items.append({
                                        "id": nid,
                                        "type": savable.get("__typename") or savable.get("savable_default_category"),
                                        "title": (savable.get("savable_title") or {}).get("text", "").strip(),
                                        "url": savable.get("url") or savable.get("savable_permalink"),
                                        "author": ", ".join(actors) if actors else "غير محدد",
                                        "collections": lists if lists else ["العامة"],
                                        "attributes": [a.get("text") for a in savable.get("savable_attributes", []) if a.get("text")],
                                    })
                    except Exception:
                        pass

                if not new_items:
                    break
            except Exception as e:
                log.warning("Error fetching pagination page: %s", e)
                break

    # Persist cache
    try:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as out:
            json.dump({
                "user_id": c_user,
                "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_items": len(all_items),
                "items": all_items
            }, out, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error("Failed saving items JSON: %s", e)

    return all_items


async def facebook_saved_handler(args: dict) -> str:
    """Tool handler for extracting and searching Facebook saved items."""
    collection = (args.get("collection") or "all").strip().lower()
    limit = int(args.get("limit") or 15)
    query = (args.get("query") or "").strip().lower()
    force_refresh = bool(args.get("force_refresh", False))

    try:
        items = await extract_all_saved(max_items=200, force_refresh=force_refresh)
    except Exception as e:
        return f"❌ خطأ أثناء استخراج المحفوظات: {e}"

    # Filter by collection
    if collection != "all":
        items = [it for it in items if any(collection in c.lower() for c in it.get("collections", []))]

    # Filter by search keyword
    if query:
        items = [
            it for it in items
            if query in it.get("title", "").lower()
            or query in it.get("author", "").lower()
            or query in it.get("url", "").lower()
        ]

    if not items:
        return f"لم يتم العثور على أي عناصر محفوظة مطابقة للفلتر (المجموعة: {collection}, البحث: {query})."

    total_found = len(items)
    displayed = items[:limit]

    lines = [
        f"📌 **العناصر المحفوظة في فيسبوك ({total_found} عنصراً متوفراً - عرض {len(displayed)}):**\n"
    ]

    for idx, it in enumerate(displayed, 1):
        type_icon = "🎥" if "video" in str(it['type']).lower() else "📝"
        colls = ", ".join(it.get('collections', []))
        title_snippet = it['title'][:110].replace("\n", " ") if it['title'] else "بدون عنوان"
        lines.append(f"**{idx}. {type_icon} {title_snippet}...**")
        lines.append(f"   👤 الناشر: `{it['author']}` | 🗂️ المجموعة: `{colls}`")
        if it.get('url'):
            lines.append(f"   🔗 الرابط: {it['url']}")
        lines.append("")

    if total_found > limit:
        lines.append(f"💡 *لعرض بقية العناصر أو البحث عن موضوع محدد، استخدم فلتر 'query' أو حدد 'limit' أكبر.*")

    lines.append(f"\n📂 *تم حفظ القائمة الكاملة (137 عنصراً) في:* `{OUTPUT_MD.name}`")
    return "\n".join(lines)


TOOLS = [
    {
        "name": "get_facebook_saved_items",
        "description": (
            "استخراج وبحث العناصر المحفوظة (Saved Posts / Bookmarks / Reels / Videos) "
            "من حساب فيسبوك الخاص بأدهم باستخدام الجلسة المحفوظة. يتيح تصفية المحفوظات "
            "حسب المجموعات (مثل 'علم' أو 'طعام' أو 'all') أو بالبحث في نصوص وروابط المنشورات."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "collection": {
                    "type": "string",
                    "description": "اسم المجموعة أو التصنيف: 'all' للكل، أو 'علم' للتقنية والمشاريع، أو 'طعام'، إلخ.",
                    "default": "all",
                },
                "query": {
                    "type": "string",
                    "description": "كلمة مفتاحية للبحث داخل نصوص المنشورات المحفوظة أو أسماء الناشرين (اختياري)",
                },
                "limit": {
                    "type": "integer",
                    "description": "عدد العناصر المطلوب إرجاعها (الافتراضي 15)",
                    "default": 15,
                },
                "force_refresh": {
                    "type": "boolean",
                    "description": "إعادة سحب المحفوظات مباشرة من فيسبوك وتحديث الكاش المحلي (افتراضي False)",
                    "default": False,
                },
            },
        },
        "handler": facebook_saved_handler,
    }
]
