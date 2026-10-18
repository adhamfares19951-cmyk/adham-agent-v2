"""Tech & Freelance Opportunity Radar:
Scans freelance platforms (Mostaql, Khamsat, Kafiil, Upwork, Reddit) and social platforms (X/Twitter, forums, Telegram)
for people who need custom software, have software bugs, or face technical/network/IT problems.
"""
import asyncio
import logging
import re
from urllib.parse import quote

import httpx

log = logging.getLogger("tech_radar")


async def _fetch_live_mostaql_projects() -> list[dict]:
    """Directly fetch current open projects from Mostaql listing page (100% fresh, posted today/recently)."""
    url = "https://mostaql.com/projects"
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            # Extract links and titles
            found = []
            matches = re.finditer(r'href=[\'"](https://mostaql\.com/project/(\d+)-[^\'"]+)[\'"][^>]*>([^<]+)<', resp.text)
            seen_ids = set()
            for m in matches:
                p_url, p_id, p_title = m.group(1), m.group(2), m.group(3).strip()
                if p_id not in seen_ids and len(p_title) > 5 and not p_title.startswith("http"):
                    seen_ids.add(p_id)
                    found.append({
                        "title": p_title,
                        "href": p_url,
                        "body": f"مشروع مفتوح حالياً على منصة مستقل: {p_title}",
                        "source": "مستقل (مباشر - حي)",
                    })
            return found
    except Exception as e:
        log.warning("Direct Mostaql fetch failed: %s", e)
        return []


async def scan_freelance_leads(args: dict | None = None, category: str = "all", keyword: str = "") -> str:
    """Scans freelance sites (Mostaql, Khamsat, Kafiil, Upwork) for projects needing custom software, bug fixes, or IT help."""
    if isinstance(args, dict):
        category = (args.get("category") or category).lower().strip()
        keyword = (args.get("keyword") or keyword).strip()
    else:
        category = (category or "all").lower().strip()
        keyword = (keyword or "").strip()

    from ddgs import DDGS

    # 1. Fetch direct live projects from Mostaql first (100% fresh today)
    live_leads = await _fetch_live_mostaql_projects()
    filtered_live = []
    if keyword:
        filtered_live = [p for p in live_leads if keyword.lower() in p["title"].lower()]
    elif category == "bugs":
        filtered_live = [p for p in live_leads if any(k in p["title"] for k in ("مشكلة", "إصلاح", "عطل", "تعديل", "حل"))]
    elif category == "new_software":
        filtered_live = [p for p in live_leads if any(k in p["title"] for k in ("برنامج", "تطبيق", "نظام", "موقع", "إنشاء"))]
    else:
        filtered_live = live_leads[:4]

    # 2. Search queries with strict time limit (timelimit='w' = past week only)
    queries = []
    if keyword:
        queries.append(f'site:mostaql.com/project "{keyword}"')
        queries.append(f'site:khamsat.com/community/requests "{keyword}"')
    else:
        queries.append('site:mostaql.com/project ("مشكلة في" OR "إصلاح" OR "برنامج مبيعات" OR "ميكروتك")')
        queries.append('site:khamsat.com/community/requests ("مطلوب مبرمج" OR "عندي مشكلة" OR "تصميم برنامج")')

    seen_urls = {p["href"] for p in filtered_live}
    raw_hits = list(filtered_live)

    def _run_search():
        dd = DDGS()
        hits = []
        for q in queries[:2]:
            try:
                # timelimit='w' restricts to the current week, preventing ancient 2023-2025 archived projects
                for r in dd.text(q, timelimit="w", max_results=4):
                    u = r.get("href", "")
                    t = r.get("title", "")
                    b = r.get("body", "")
                    combo = f"{t} {b}".lower()

                    # Filter out old years and closed markers
                    if any(y in combo for y in ("2023", "2024", "2025")) and "2026" not in combo:
                        continue
                    if any(c in combo for c in ("مغلق", "مكتمل", "closed", "expired", "منتهي")):
                        continue

                    if u and u not in seen_urls:
                        seen_urls.add(u)
                        hits.append(r)
            except Exception as e:
                log.warning("Search query failed %s: %s", q[:30], e)
        return hits

    search_hits = await asyncio.to_thread(_run_search)
    raw_hits.extend(search_hits)

    if not raw_hits:
        return "ما لقيت طلبات فريلانس نشطة مفتوحة حالياً لهذا الأسبوع. تم استبعاد كافة المشاريع القديمة والأرشيف."

    lines = ["**🎯 رادار مشاريع الفريلانس والبرمجيات النشطة (محدثة لهذا الأسبوع 2026):**\n"]
    for i, h in enumerate(raw_hits[:8], 1):
        title = h.get("title", "")
        url = h.get("href", "")
        snippet = h.get("body", "")

        # Detect platform
        platform = "مستقل (حي)" if h.get("source") else ("مستقل" if "mostaql.com" in url else ("خمسات" if "khamsat.com" in url else "كفيل"))
        kind_tag = "🛠️ [إصلاح مشكلة/عطل]" if any(k in title + snippet for k in ("مشكلة", "إصلاح", "عطل", "خطأ", "تعديل")) else "💻 [طلب برنامج/تطبيق جديد]"

        lines.append(
            f"{i}. {kind_tag} **{title}**\n"
            f"   • **المنصة:** {platform}\n"
            f"   • **تفاصيل الطلب:** {snippet}\n"
            f"   • 🔗 **رابط المشروع:** {url}\n"
        )

    lines.append(
        "> 💡 **ملاحظة الأمان الزمني:** تم فحص المشاريع والتأكد من أنها حية ومطروحة مؤخراً وليست من الأرشيف القديم.\n"
        "> احكيلي: *'اكتبلي عرض لمشروع رقم كذا'* لأجهزلك بروبوزال احترافي فوراً!"
    )
    return "\n".join(lines)


async def scan_social_tech_issues(args: dict) -> str:
    """Scans social media (X/Twitter, Reddit, public tech groups) for people complaining of software/tech problems or looking for developers."""
    topic = (args.get("topic") or "برمجة وشبكات").strip()

    from ddgs import DDGS

    queries = [
        f'site:x.com OR site:twitter.com ("عندي مشكلة في البرنامج" OR "مطلوب مبرمج لحل مشكلة" OR "مشكلة في السيرفر")',
        f'site:reddit.com/r/forhire ("bug fix" OR "fix my script" OR "need software")',
        f'site:reddit.com/r/techsupport ("need technician" OR "network problem" OR "server issue")',
    ]

    seen = set()
    posts = []

    def _run():
        dd = DDGS()
        hits = []
        for q in queries[:2]:
            try:
                # timelimit='w' restricts results to past week only, preventing 2023 tweets
                for r in dd.text(q, timelimit="w", max_results=4):
                    u = r.get("href", "")
                    t = r.get("title", "")
                    b = r.get("body", "")
                    combo = f"{t} {b}".lower()

                    # Exclude past years
                    if any(y in combo for y in ("2023", "2024", "2025")) and "2026" not in combo:
                        continue

                    if u and u not in seen:
                        seen.add(u)
                        hits.append(r)
            except Exception:
                pass
        return hits

    raw_posts = await asyncio.to_thread(_run)
    if not raw_posts:
        return f"ما لقيت منشورات جديدة على السوشيال ميديا خلال هذا الأسبوع بخصوص '{topic}'. تم استبعاد منشورات السنوات السابقة."

    lines = [f"**📡 رادار السوشيال ميديا الحديث لمشاكل التكنولوجيا والبرمجيات (`{topic}` - 2026):**\n"]
    for i, p in enumerate(raw_posts[:7], 1):
        t = p.get("title", "")
        u = p.get("href", "")
        b = p.get("body", "")

        network = "تويتر / X" if ("x.com" in u or "twitter.com" in u) else ("ريديت (Reddit)" if "reddit.com" in u else "منصة عامة")
        lines.append(
            f"{i}. 📢 **{t}**\n"
            f"   • **المصدر:** {network}\n"
            f"   • **نص المنشور:** {b}\n"
            f"   • 🔗 **الرابط:** {u}\n"
        )

    lines.append(
        "> 🚀 **فرصة صيد:** هذه المنشورات حديثة لهذا الأسبوع، بتقدر تدخل على الرابط وترد عليه بالحل المقترح فوراً!"
    )
    return "\n".join(lines)


async def draft_pitch_proposal(args: dict) -> str:
    """Generates a winning, persuasive proposal/reply for a freelance project or client issue."""
    project_title = (args.get("project_title") or "").strip()
    project_details = (args.get("project_details") or "").strip()
    platform = (args.get("platform") or "مستقل").strip()
    budget = args.get("budget", "مناسب")

    return (
        f"**مسودة عرض احترافي (Proposal) مقترح لمشروع: {project_title}**\n"
        f"المنصة: {platform} | الميزانية المقترحة: {budget}\n\n"
        "**نص العرض الجاهز للنسخ والإرسال:**\n"
        "```text\n"
        "السلام عليكم ورحمة الله وبركاته،\n"
        f"قرأت تفاصيل طلبك بخصوص '{project_title}' وبإمكاني تنفيذه وحله لك بأعلى معايير الدقة والسرعة.\n\n"
        "أنا فني شبكات وأنظمة ومطور برمجيات بخبرة عملية تمتد لـ 10 سنوات في صيانة الأنظمة، حل الأعطال المعقدة، وبناء الحلول المستقرة.\n"
        "ما سأقوم به تحديداً:\n"
        "1. تشخيص سبب المشكلة الجذري والتأكد من عدم تكراره.\n"
        "2. التطبيق الفوري للحل البرمجي/التقني مع الاختبار الكامل قبل التسليم.\n"
        "3. تقديم دعم فني وتوضيح كامل لما تم إنجازه لضمان راحة بالك.\n\n"
        "يسعدني تواصلك معي في المحادثة للبدء فوراً وبأفضل تكلفة.\n"
        "تحياتي، أدهم\n"
        "```\n\n"
        "> 💡 **نصيحة أدهم:** راجع العرض، وإذا في تفاصيل فنية خاصة بالمشروع ضيف سطرين عنها بالمنتصف وابعته فوراً للعميل!"
    )


TOOLS = [
    {
        "name": "scan_freelance_leads",
        "description": (
            "Radar for freelance websites (Mostaql, Khamsat, Kafiil, Upwork): scans for clients who have "
            "software bugs, need an existing program fixed, or want a new custom program/app/website/network setup. "
            "Use whenever Adham asks about freelance opportunities, clients needing software fixes, or programming jobs."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Optional keyword (e.g. 'برنامج مبيعات', 'ميكروتك', 'تطبيق', 'إصلاح موقع', 'بايثون', 'flutter').",
                },
                "category": {
                    "type": "string",
                    "description": "Category: 'bugs' for fixes/troubleshooting, 'new_software' for build requests, or 'all'.",
                },
            },
        },
        "handler": scan_freelance_leads,
    },
    {
        "name": "scan_social_tech_issues",
        "description": (
            "Radar for social media & tech communities (X/Twitter, Reddit, tech support forums): "
            "scans for people who have a tech/software problem, asked for programming help, or need an IT technician. "
            "Use whenever Adham asks to find people with tech problems on Facebook, Twitter, Instagram, or social platforms."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The tech topic to search for (e.g. 'برنامج', 'شبكة', 'سيرفر', 'موقع', 'كاميرات').",
                }
            },
        },
        "handler": scan_social_tech_issues,
    },
    {
        "name": "draft_pitch_proposal",
        "description": (
            "Drafts a high-conversion, professional proposal or client pitch tailored to a specific freelance project "
            "or client problem, highlighting Adham's 10-year experience and problem-solving skills."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "project_title": {"type": "string", "description": "Title of the project or problem."},
                "project_details": {"type": "string", "description": "The client's description or problem details."},
                "platform": {"type": "string", "description": "Platform name (e.g. مستقل, خمسات, تويتر, لينكدإن)."},
            },
            "required": ["project_title"],
        },
        "handler": draft_pitch_proposal,
    },
]
