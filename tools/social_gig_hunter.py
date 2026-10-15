"""Social Media & Freelance Gig Hunter for adham-agent.
Scans Facebook groups, Twitter/X live posts, Khamsat community requests, Mostaql live projects,
and Instagram for clients and businesses looking for developers, programmers, or custom software solutions.
"""
import asyncio
import logging
import re
from urllib.parse import quote, unquote

import httpx

log = logging.getLogger("social_gig_hunter")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ar,en;q=0.9",
}

DEV_KEYWORDS = [
    "مبرمج", "مطور", "برمجة", "تطبيق", "موقع", "فلاتر", "flutter", "laravel",
    "لارافيل", "ووردبريس", "wordpress", "سكربت", "script", "بوت", "bot",
    "كود", "api", "سيرفر", "قاعدة بيانات", "متجر", "كاشير", "pos", "python", "بايثون"
]


async def _fetch_khamsat_requests(niche: str = "") -> list[dict]:
    """Fetch live community requests directly from Khamsat (100% fresh, updated every hour)."""
    url = "https://khamsat.com/community/requests"
    results = []
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            
            # Extract links with URL-encoded titles
            matches = re.finditer(r'href="(/community/requests/(\d+)-([^"]+))"', resp.text)
            seen_ids = set()
            for m in matches:
                req_path, req_id, raw_slug = m.group(1), m.group(2), m.group(3)
                if req_id in seen_ids:
                    continue
                seen_ids.add(req_id)
                
                title = unquote(raw_slug).replace("-", " ").strip()
                title_lower = title.lower()

                # Filter for development / programming / tech requests
                is_dev = any(k in title_lower for k in DEV_KEYWORDS)
                if niche and niche.lower() not in title_lower and not is_dev:
                    continue
                elif not niche and not is_dev:
                    # Skip graphic design, translation unless asked
                    continue

                results.append({
                    "platform": "خمسات (مجتمع الطلبات 🟢)",
                    "title": title,
                    "url": f"https://khamsat.com{req_path}",
                    "snippet": f"طلب خدمة حي منشور الآن على مجتمع خمسات: {title}",
                    "type": "طلب برمجة / تطوير مباشر",
                })
                if len(results) >= 5:
                    break
    except Exception as e:
        log.warning("Khamsat live fetch error: %s", e)
    return results


async def _fetch_mostaql_projects(niche: str = "") -> list[dict]:
    """Fetch live open projects directly from Mostaql listing page."""
    url = "https://mostaql.com/projects"
    results = []
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            
            matches = re.finditer(r'href=[\'"](https://mostaql\.com/project/(\d+)-[^\'"]+)[\'"][^>]*>([^<]+)<', resp.text)
            seen_ids = set()
            for m in matches:
                p_url, p_id, p_title = m.group(1), m.group(2), m.group(3).strip()
                if p_id in seen_ids or len(p_title) < 5 or p_title.startswith("http"):
                    continue
                seen_ids.add(p_id)
                
                p_lower = p_title.lower()
                is_dev = any(k in p_lower for k in DEV_KEYWORDS)
                if niche and niche.lower() not in p_lower:
                    continue
                elif not niche and not is_dev:
                    continue

                results.append({
                    "platform": "مستقل (مشاريع مفتوحة 💼)",
                    "title": p_title,
                    "url": p_url,
                    "snippet": f"مشروع برمجيات مفتوح يتلقى عروض الآن: {p_title}",
                    "type": "مشروع تعاقدي كامل",
                })
                if len(results) >= 5:
                    break
    except Exception as e:
        log.warning("Mostaql live fetch error: %s", e)
    return results


async def _search_social_via_html(query: str, platform_name: str, max_results: int = 3) -> list[dict]:
    """Search social media posts (Facebook, Twitter, Instagram) via DuckDuckGo HTML parser."""
    url = "https://html.duckduckgo.com/html/"
    results = []
    try:
        async with httpx.AsyncClient(timeout=12, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.post(url, data={"q": query})
            if resp.status_code != 200:
                return []

            blocks = re.findall(r'<div class="result__body">(.*?)</div>\s*</div>', resp.text, re.DOTALL)
            for b in blocks[:max_results]:
                m_link = re.search(r'<a class="result__url"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b)
                m_snip = re.search(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', b, re.DOTALL)
                if m_link:
                    raw_url = m_link.group(1)
                    if "uddg=" in raw_url:
                        m_target = re.search(r'uddg=([^&]+)', raw_url)
                        target_url = unquote(m_target.group(1)) if m_target else raw_url
                    else:
                        target_url = raw_url

                    title = re.sub(r'<[^>]+>', '', m_link.group(2)).strip()
                    snip = re.sub(r'<[^>]+>', '', m_snip.group(1)).strip() if m_snip else ""
                    
                    # Exclude old archive markers if any
                    combo = f"{title} {snip}".lower()
                    if any(c in combo for c in ("مغلق", "closed", "منتهي")):
                        continue

                    results.append({
                        "platform": platform_name,
                        "title": title,
                        "url": target_url,
                        "snippet": snip,
                        "type": "منشور / طلب مباشر على السوشيال ميديا",
                    })
    except Exception as e:
        log.warning("Social search error for %s: %s", platform_name, e)
    return results


async def hunt_social_gigs(args: dict) -> str:
    """Scans Facebook groups, X/Twitter, Khamsat, Mostaql, and Instagram for live programming opportunities and client requests."""
    platform = (args.get("platform") or "all").lower().strip()
    niche = (args.get("niche") or "").strip()
    max_results = min(max(int(args.get("max_results") or 8), 2), 15)

    tasks = []

    # 1. Khamsat Community Requests (Direct instant requests)
    if platform in ("all", "khamsat"):
        tasks.append(_fetch_khamsat_requests(niche))

    # 2. Mostaql Live Open Projects
    if platform in ("all", "mostaql"):
        tasks.append(_fetch_mostaql_projects(niche))

    # 3. Facebook Groups & Developer Requests
    if platform in ("all", "facebook"):
        fb_query = 'site:facebook.com "مطلوب مبرمج" OR "محتاج مطور"'
        if niche:
            fb_query += f' "{niche}"'
        tasks.append(_search_social_via_html(fb_query, "فيسبوك (Facebook 👥)", max_results=3))

    # 4. Twitter / X Live Posts
    if platform in ("all", "twitter", "x"):
        tw_query = 'site:x.com ("مطلوب مبرمج" OR "محتاج مبرمج" OR "مطلوب مطور")'
        if niche:
            tw_query += f' "{niche}"'
        tasks.append(_search_social_via_html(tw_query, "تويتر / إكس (X 🐦)", max_results=3))

    # 5. Instagram Tech & Store Opportunities
    if platform in ("all", "instagram"):
        ig_query = 'site:instagram.com ("مطلوب مبرمج" OR "مطلوب تطبيق")'
        if niche:
            ig_query += f' "{niche}"'
        tasks.append(_search_social_via_html(ig_query, "انستغرام (Instagram 📸)", max_results=2))

    gathered = await asyncio.gather(*tasks, return_exceptions=True)
    all_gigs = []
    for g in gathered:
        if isinstance(g, list):
            all_gigs.extend(g)

    if not all_gigs:
        return (
            "🔍 تم فحص شبكات التواصل ومنصات العمل الحر (فيسبوك، تويتر، خمسات، مستقل)، ولم أجد طلبات برمجية جديدة مطابقة الآن.\n"
            "جرّب البحث بعد قليل أو تغيير الكلمات المفتاحية."
        )

    # Format into professional response with winning pitch
    lines = [
        "🎯 **رادار الفرص البرمجية الحية على السوشيال ميديا ومنصات العمل (Facebook, X, Khamsat, Mostaql)**\n",
        f"📊 **عدد الفرص المرصودة:** {len(all_gigs[:max_results])} فرصة عمل حية\n",
    ]

    for idx, gig in enumerate(all_gigs[:max_results], 1):
        p_name = gig["platform"]
        title = gig["title"]
        url = gig["url"]
        snippet = gig["snippet"]

        lines.append(
            f"**{idx}. 📌 {title}**\n"
            f"   • **المنصة:** {p_name}\n"
            f"   • **التفاصيل:** {snippet}\n"
            f"   • 🔗 **رابط التواصل والتقديم:** {url}\n"
        )

    # Add quick proposal action
    top_gig = all_gigs[0]
    lines.append(
        "---\n"
        "💡 **مسودة عرض مقترح لأول طلب («" + top_gig["title"][:40] + "...»):**\n"
        "```text\n"
        "السلام عليكم، قرأت تفاصيل طلبكم وبإمكاني تنفيذه لكم باحترافية وسرعة عالية.\n"
        "أنا مهندس برمجيات ومطور تطبيقات (Flutter / Laravel / Full-Stack) بخبرة عملية 10 سنوات في بناء وتطوير الأنظمة وحل المشكلات المعقدة.\n"
        "جاهز للبدء فوراً وتسليمكم كوداً نظيفاً مع الاختبار والدعم الفني الكامل.\n"
        "تحياتي، أدهم\n"
        "```\n"
        "> 🚀 *احكيلي: 'اكتبلي عرض مخصص للفرصة رقم X' لأجهزلك بروبوزال تقني مفصل لها فوراً!*"
    )

    return "\n".join(lines)


TOOLS = [
    {
        "name": "hunt_social_gigs",
        "description": (
            "Scan social media platforms (Facebook groups, Twitter/X, Instagram) and freelance communities "
            "(Khamsat community requests, Mostaql open projects) for people looking for programmers, software developers, "
            "mobile app builders, or website solutions. Returns direct contact links and draft pitch proposals."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "description": "Platform to focus on: 'all', 'facebook', 'twitter', 'khamsat', 'mostaql', 'instagram'. Default is 'all'.",
                },
                "niche": {
                    "type": "string",
                    "description": "Specific tech specialty or keyword (e.g. 'flutter', 'laravel', 'wordpress', 'bot', 'pos').",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of opportunities to retrieve (default: 8).",
                },
            },
        },
        "handler": hunt_social_gigs,
    },
]
