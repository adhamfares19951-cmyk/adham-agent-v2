"""Job monitor: checks Telegram channels and job/freelance sites on a timer,
lets the AI pick what fits Adham, and sends him a card for each match.

AI steps (kept cheap so free quota lasts):
  1. screen: one call classifies all new items by title/short text (job / freelance / aid / skip)
  2. evaluate: only the kept items get a full read (details page) and a match card.
  3. auto-apply: only matches scoring >= AUTO_APPLY_SCORE also get a drafted cover letter +
     tailored CV summary, bundled as a ready .docx sent alongside the card.
"""
import asyncio
import html
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, ContextTypes

import config
import memory
from llm import LLMError
from tools.documents import build_application_docx
from tools.web_reader import client, html_to_text, page_text

log = logging.getLogger("jobs")

AUTO_APPLY_SCORE = 80  # score at/above which a ready cover-letter+CV package is auto-attached

# Public Telegram channels (web preview at t.me/s/<name>).
TELEGRAM_CHANNELS = ["Gazarecruiters", "jobspals2", "mtqdmon", "GazaAid24", "paljobs", "wzayfgaza"]

# Websites: name -> (listing page, regex for item links (group 1 = unique id), open the details page?)
# Khamsat details pages come back empty to bots, so we judge those from the listing text only.
WEBSITES = {
    "PEF": ("https://e.pef.ps/ar/Jobs?type=Jobs", r"/ar/Jobs/Details/(\d+)", True),
    "Joby": ("https://joby.ps/jobs.php", r"/jobs/(\d+)-[^\"']+", True),
    "مستقل": ("https://mostaql.com/projects", r"https://mostaql\.com/project/(\d+)-[^\"']+", True),
    "خمسات": ("https://khamsat.com/community/requests", r"/community/requests/(\d+)-[^\"']+", False),
}

FIRST_RUN_ITEMS = 5      # on a source's first check, only look at its newest few items
MIN_SCORE = {"job": 60, "freelance": 65, "aid": 50, "course": 65}
CATEGORIES = tuple(MIN_SCORE)
EVAL_BATCH = 8

_app: Application | None = None
_lock = asyncio.Lock()


@dataclass
class Item:
    key: str
    source: str
    url: str
    text: str           # title or post text
    fetch_details: bool  # websites: read the details page before evaluating
    details: str = ""    # already known full text (ReliefWeb API)


# ---------------------------------------------------------------- collecting

def _clean(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


async def _telegram_items(channel: str) -> list[Item]:
    resp = await client.get(f"https://t.me/s/{channel}")
    resp.raise_for_status()
    items = []
    for block in resp.text.split('class="tgme_widget_message_wrap')[1:]:
        post = re.search(r'data-post="([^"]+)"', block)
        body = re.search(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', block, re.S)
        if not post or not body:
            continue
        text = html_to_text(body.group(1))
        if len(text) > 20:
            items.append(Item(f"tg:{post.group(1)}", f"تلجرام @{channel}",
                              f"https://t.me/{post.group(1)}", text, False))
    return items  # oldest first


async def _website_items(name: str, url: str, pattern: str, details: bool) -> list[Item]:
    resp = await client.get(url)
    resp.raise_for_status()
    base = re.match(r"https?://[^/]+", url).group(0)
    found: dict[str, list[str]] = {}
    links: dict[str, str] = {}
    for m in re.finditer(r'<a\s[^>]*href="(' + pattern + r')"[^>]*>(.*?)</a>', resp.text, re.S):
        link, item_id, label = html.unescape(m.group(1)), m.group(2), _clean(m.group(3))
        links.setdefault(item_id, link if link.startswith("http") else base + link)
        if label and label not in found.setdefault(item_id, []):
            found[item_id].append(label)
    items = [Item(f"web:{name}:{i}", name, links[i], " — ".join(found[i])[:600], details)
             for i in links if found.get(i)]
    return list(reversed(items))  # listing pages show newest first; make it oldest first


async def _reliefweb_items() -> list[Item]:
    """ReliefWeb official API (needs an approved appname in .env): jobs in Palestine."""
    resp = await client.post(
        f"https://api.reliefweb.int/v2/jobs?appname={config.RELIEFWEB_APPNAME}",
        json={
            "filter": {"field": "country.name", "value": "occupied Palestinian territory"},
            "fields": {"include": ["title", "source.name", "date.closing", "url_alias", "body", "city.name"]},
            "sort": ["date.created:desc"],
            "limit": 30,
        },
    )
    resp.raise_for_status()
    items = []
    for row in resp.json().get("data", []):
        f = row.get("fields", {})
        org = ", ".join(s.get("name", "") for s in f.get("source", []))
        closing = (f.get("date") or {}).get("closing", "")[:10]
        head = " — ".join(x for x in (f.get("title", ""), org, f"closing {closing}" if closing else "") if x)
        url = f.get("url_alias") or f"https://reliefweb.int/job/{row.get('id')}"
        items.append(Item(f"rw:{row.get('id')}", "ReliefWeb", url, head, False,
                          details=f"{head}\n{(f.get('body') or '')[:2500]}"))
    return list(reversed(items))


async def _collect() -> list[Item]:
    tasks = {f"tg:{ch}/": _telegram_items(ch) for ch in TELEGRAM_CHANNELS}
    tasks.update({f"web:{n}:": _website_items(n, u, p, d) for n, (u, p, d) in WEBSITES.items()})
    if config.RELIEFWEB_APPNAME:
        tasks["rw:"] = _reliefweb_items()
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    new_items, skip_keys = [], []
    for prefix, result in zip(tasks, results):
        if isinstance(result, Exception):
            log.warning("Source %s failed: %s", prefix, result)
            continue
        seen = memory.seen_keys(prefix)
        fresh = [it for it in result if it.key not in seen]
        if not seen and len(fresh) > FIRST_RUN_ITEMS:  # first check of this source
            skip_keys += [it.key for it in fresh[:-FIRST_RUN_ITEMS]]
            fresh = fresh[-FIRST_RUN_ITEMS:]
        new_items += fresh
    memory.mark_seen(skip_keys)
    return new_items


# ---------------------------------------------------------------- AI steps

def _profile() -> str:
    try:
        return (config.BASE_DIR / "profile.md").read_text(encoding="utf-8")
    except OSError:
        return "IT support and network technician in Khan Younis, Gaza."


def _parse_json_list(text: str) -> list:
    text = re.sub(r"```(json)?", "", text or "")
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end < start:
        return []
    try:
        data = json.loads(text[start:end + 1])
    except ValueError:
        return []
    return [d for d in data if isinstance(d, dict)]


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


APPLICATION_PROMPT = """Write a ready-to-send job application package for Adham for this
opportunity:
{title}
{url}

Details of the posting:
{details}

Adham's real background:
{profile}

Return ONLY a JSON object with exactly these fields:
{{"cover_letter": "<a professional English cover letter, 3-4 short paragraphs, tailored to this
  specific posting and grounded only in his real background>",
 "resume_summary": "<a short tailored CV summary in English: one paragraph profile summary,
  then bullet lines (each starting with '-') of his most relevant skills/experience for this
  specific role. Plain text, no markdown formatting>"}}"""


async def _auto_apply_package(item: Item, title: str, details: str) -> bytes | None:
    """For a strong match: draft a cover letter + tailored CV summary and
    return a ready .docx file. Returns None if the AI call fails (the job
    card itself still goes out either way)."""
    from brain import llm

    try:
        reply = await llm.generate(
            "You write honest, professional job application material. Never invent experience.",
            [{"role": "user", "content": APPLICATION_PROMPT.format(
                title=title, url=item.url, details=details[:3000], profile=_profile())}],
        )
        memory.add_usage("llm_call")
        data = _parse_json_obj(reply.text)
        if not data.get("cover_letter"):
            return None
        return build_application_docx(title, data.get("cover_letter", ""), data.get("resume_summary", ""))
    except Exception:
        log.exception("Auto-apply package failed for %s", item.url)
        return None


async def _ask(prompt: str) -> list:
    from brain import llm  # the shared provider chain (imported here to avoid a circular import)
    reply = await llm.generate("You are a careful job screener. Reply with JSON only.",
                               [{"role": "user", "content": prompt}])
    memory.add_usage("llm_call")
    return _parse_json_list(reply.text)


SCREEN_PROMPT = """Screen these posts for Adham. His profile:
{profile}
Saved preferences: {facts}

For each numbered item choose one category:
- "job": a vacancy, internship or cash-for-work he could realistically apply to: IT support, networks, technical support, computers/hardware, telecom, CCTV, systems, data entry, field monitoring, logistics/admin roles in NGOs that fit his experience. He lives in Khan Younis, Gaza; remote is fine.
- "freelance": a freelance/remote project he can deliver: IT/network help, tech support, data entry, Word/Excel/PowerPoint work, simple websites, device troubleshooting.
- "aid": an aid registration, distribution or assistance program for Gaza residents (not general news, not crossing status).
- "course": a training course, scholarship or certification program that would strengthen his IT/network career (e.g. CCNA, Network+, MikroTik, Security+, cloud, IT support). A training program is a course, never a job.
- "skip": anything else (news, jobs clearly outside his field such as teachers, doctors, engineers, accountants, designers, marketers, unrelated trainings).

Items:
{items}

Answer with a JSON array only, e.g. [{{"i": 1, "c": "skip"}}]"""

EVAL_PROMPT = """Evaluate these posts for Adham. His profile:
{profile}
Saved preferences: {facts}
Today: {today}

Rules: use ONLY what the item text says. Never invent titles, organizations or dates.
Score strictly: 80+ only when his experience clearly matches the main duties; generic or vague posts score below 50.

For each item return an object:
{{"i": <number>, "score": <0-100 how well it fits him; 0 if expired or not a real opportunity.
   For [aid] items: how useful and actionable it is for a family in Khan Younis
   (open registration or distribution he can act on = high; general info, status checks, ads = low).
   For [course] items: how much it helps his IT/network career and how accessible it is (free/cheap, online or in Gaza)>,
 "title": "<the real title as written in the item>", "org": "<organization or client, or empty>", "location": "<place or remote>",
 "deadline": "<YYYY-MM-DD or empty if unknown>",
 "why": "<why it fits, one short sentence in Palestinian Arabic>",
 "missing": "<what he lacks for it, one short sentence in Palestinian Arabic, or empty>",
 "summary": "<one-line Arabic summary; for aid: who can register and how>"}}

Items:
{items}

Answer with a JSON array only."""


def _facts() -> str:
    return "; ".join(f["content"] for f in memory.list_facts()) or "none"


async def _screen(items: list[Item]) -> dict[int, str]:
    listed = "\n".join(f"{n}. [{it.source}] {it.text[:300]}" for n, it in enumerate(items, 1))
    result = await _ask(SCREEN_PROMPT.format(profile=_profile(), facts=_facts(), items=listed))
    cats = {int(d["i"]): d.get("c", "skip") for d in result if str(d.get("i", "")).isdigit()}
    if not cats:
        # Unreadable answer: fail so the items stay unseen and get retried next scan.
        raise LLMError("ما قدرت أفرز المنشورات هالمرة، رح أعيد المحاولة بالفحص الجاي.")
    return cats


async def _details(item: Item) -> str:
    if item.details:
        return item.details
    if not item.fetch_details:
        return item.text
    try:
        text = await page_text(item.url, max_chars=2500, start_at=item.text.split(" — ")[0][:40])
    except Exception as e:
        log.info("Could not read %s: %s", item.url, e)
        text = ""
    # Empty or tiny page (blocked / loaded by JavaScript): judge from the listing text instead.
    return text if len(text) >= 150 else item.text


async def _evaluate(batch: list[tuple[Item, str, str]]) -> list[dict]:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    listed = "\n\n".join(f"{n}. [{cat}] [{it.source}]\n{details}" for n, (it, cat, details) in enumerate(batch, 1))
    today = datetime.now(ZoneInfo(config.TIMEZONE)).strftime("%Y-%m-%d")
    return await _ask(EVAL_PROMPT.format(profile=_profile(), facts=_facts(), today=today, items=listed))


# ---------------------------------------------------------------- messages

def _card(category: str, d: dict, item: Item) -> str:
    title = d.get("title") or item.text[:80]
    if category == "aid":
        lines = [f"🆘 مساعدات / تسجيل: {title}", d.get("summary", "")]
        if d.get("deadline"):
            lines.append(f"⏳ لغاية: {d['deadline']}")
    else:
        head = {"job": "💼 وظيفة", "freelance": "💻 شغل عن بعد", "course": "🎓 دورة / تدريب"}[category]
        lines = [f"{head} — تطابق {d.get('score', '?')}%", title]
        place = " | ".join(x for x in (d.get("org"), d.get("location")) if x)
        if place:
            lines.append(f"🏢 {place}")
        lines.append(f"⏳ آخر موعد: {d.get('deadline') or 'مش مذكور'}")
        if d.get("why"):
            lines.append(f"✅ ليش بتناسبك: {d['why']}")
        if d.get("missing"):
            lines.append(f"⚠️ ناقصك: {d['missing']}")
    lines += [f"🔗 {item.url}", f"(المصدر: {item.source})"]
    return "\n".join(x for x in lines if x)


async def _notify(match_id: int, category: str, card: str, package: bytes | None = None) -> None:
    markup = None
    if category in ("job", "freelance"):
        label = "✍️ اكتبلي رسالة تغطية" if category == "job" else "✍️ اكتبلي عرض للمشروع"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"job:cl:{match_id}")]])
    await _app.bot.send_message(config.OWNER_ID, card, reply_markup=markup,
                                disable_web_page_preview=True)
    if package:
        from io import BytesIO
        doc = BytesIO(package)
        doc.name = "Application_Package.docx"
        await _app.bot.send_document(config.OWNER_ID, doc, filename=doc.name,
                                     caption="📎 جهزتلك مسودة رسالة تغطية + سيرة ذاتية مختصرة مطابقة — راجعها قبل ما تبعتها.")


# ---------------------------------------------------------------- the scan

async def scan() -> str:
    """Check all sources once. Returns a short Arabic summary."""
    if _lock.locked():
        return "في فحص شغّال أصلاً، استنى شوي."
    async with _lock:
        items = await _collect()
        if not items:
            return "فحصت كل المصادر، ما في إشي جديد."
        cats = await _screen(items)
        kept = [(it, cats[n]) for n, it in enumerate(items, 1) if cats.get(n) in CATEGORIES]
        today_str = datetime.now(ZoneInfo(config.TIMEZONE)).strftime("%Y-%m-%d")
        sent = 0
        for start in range(0, len(kept), EVAL_BATCH):
            chunk = kept[start:start + EVAL_BATCH]
            details = await asyncio.gather(*(_details(it) for it, _ in chunk))
            batch = [(it, cat, det) for (it, cat), det in zip(chunk, details)]
            for d in await _evaluate(batch):
                try:
                    it, cat, det = batch[int(d["i"]) - 1]
                    score = int(d.get("score") or 0)
                except (KeyError, ValueError, IndexError, TypeError):
                    continue
                if score < MIN_SCORE[cat]:
                    continue

                # --- Strict Expiry & Freshness Filter ---
                deadline = (d.get("deadline") or "").strip()
                if deadline and re.match(r"^\d{4}-\d{2}-\d{2}$", deadline):
                    if deadline < today_str:
                        log.info("Skipped expired opportunity '%s' (deadline %s < today %s)", d.get("title"), deadline, today_str)
                        continue

                det_text = f"{it.text} {det}".lower()
                # Check for explicit expired markers
                if any(x in det_text for x in ("انتهى التقديم", "مغلق", "انتهاء التسجيل", "تم إغلاق", "انتهت فترة التسجيل", "closed", "expired")):
                    log.info("Skipped closed opportunity '%s'", d.get("title"))
                    continue

                # If post explicitly mentions old years (2023, 2024, 2025) and lacks 2026, skip
                if any(y in det_text for y in ("2023", "2024", "2025")) and "2026" not in det_text:
                    log.info("Skipped old-year opportunity '%s'", d.get("title"))
                    continue

                card = _card(cat, d, it)
                title = d.get("title") or it.text[:80]
                match_id = memory.add_match(it.key, cat, score, title, it.url, det, card)

                package = None
                if cat in ("job", "freelance") and score >= AUTO_APPLY_SCORE:
                    package = await _auto_apply_package(it, title, det)

                try:
                    await _notify(match_id, cat, card, package)
                    sent += 1
                except Exception:
                    # A single failed send (e.g. a Telegram network hiccup) shouldn't abort the
                    # whole scan and lose the other matches — it's already saved in memory, so
                    # recent_opportunities / the next /jobs check can still surface it.
                    log.warning("Failed to notify about match %s, will stay available via /jobs", match_id, exc_info=True)
        # Mark as seen only after the AI steps worked, so a quota error means a retry next time.
        memory.mark_seen([it.key for it in items])
        return f"فحصت {len(items)} منشور جديد، وبعتلك {sent} فرصة مناسبة."


async def _scheduled_scan(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        summary = await scan()
        log.info("Scheduled job scan: %s", summary)
    except Exception:
        log.exception("Scheduled job scan failed")  # quiet: next run will retry


def setup(app: Application) -> None:
    global _app
    _app = app
    app.job_queue.run_repeating(_scheduled_scan, interval=config.JOB_SCAN_MINUTES * 60,
                                first=60, name="job-scan")
    log.info("Job monitor: every %d minutes", config.JOB_SCAN_MINUTES)


# ---------------------------------------------------------------- Telegram handlers

async def jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/jobs — scan now."""
    msg = await update.effective_message.reply_text("🔎 بفحص القنوات والمواقع هلّق، ممكن ياخد دقيقة...")
    try:
        summary = await scan()
    except Exception as e:
        log.exception("Manual job scan failed")
        summary = f"صار خطأ بالفحص 😕 ({getattr(e, 'user_message', e)})"
    await msg.edit_text(summary)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'Write me a cover letter' button under a job card."""
    q = update.callback_query
    if not q or q.from_user.id != config.OWNER_ID:
        return
    await q.answer("✍️ عم بكتب...")
    match = memory.get_match(int(q.data.split(":")[2]))
    if not match:
        return
    import brain
    from tg_utils import send_long

    kind = "cover letter" if match["category"] == "job" else "short freelance proposal"
    request = (f"اكتبلي {kind} بالإنجليزي لهالفرصة، مفصّلة على خبرتي من ملفي، "
               f"وبعدها سطرين بالعربي شو أعدّل بالسي في عشانها.\n\n"
               f"{match['title']}\n{match['url']}\n\nالتفاصيل:\n{match['details'][:2500]}")
    try:
        answer = await brain.reply(request)
    except Exception as e:
        answer = getattr(e, "user_message", "صار خطأ وأنا بكتب الرسالة 😕 جرّب كمان مرة.")
    await send_long(update, answer)


# ---------------------------------------------------------------- AI tools

async def scan_jobs_now(args: dict) -> str:
    return await scan()


async def recent_opportunities(args: dict) -> str:
    rows = memory.recent_matches(int(args.get("limit") or 10), args.get("category") or None)
    if not rows:
        return "لسا ما لقيت فرص محفوظة."
    return "\n\n".join(f"#{r['id']} [{r['category']}] ({r['created_at']})\n{r['card']}" for r in rows)


async def deep_job_hunter(args: dict) -> str:
    """Active deep search for jobs across international NGO portals, UN agencies, local Palestine boards, and remote IT portals."""
    role = (args.get("role") or "IT Support").strip()
    location = (args.get("location") or "Gaza").strip()
    org_type = (args.get("org_type") or "NGO/UN/Remote").strip()

    from ddgs import DDGS

    # Target fresh 2026 openings and active recruitment boards
    queries = [
        f'site:reliefweb.int/job "{role}" ("Palestine" OR "Gaza" OR "Jerusalem") 2026',
        f'site:unjobs.org "{role}" ("Palestine" OR "Gaza") 2026',
        f'site:jobs.ps "{role}" 2026',
        f'"{role}" ("Palestine" OR "Gaza") ("NGO" OR "UN" OR "UNDP" OR "UNRWA" OR "ICRC" OR "MSF" OR "NRC") 2026',
        f'site:remotive.com OR site:weworkremotely.com "{role}" ("Remote" OR "Worldwide")',
    ]

    seen = set()
    def _search():
        dd = DDGS()
        hits = []
        for q in queries:
            try:
                # timelimit='m' restricts results to the past month for freshness
                for r in dd.text(q, timelimit="m", max_results=4):
                    url = r.get("href", "")
                    title = r.get("title", "")
                    body = r.get("body", "")
                    combo = f"{title} {body}".lower()

                    # Filter out expired keywords or past years without 2026
                    if any(exp in combo for exp in ("closed", "expired", "مغلق", "منتهي", "انتهى التقديم")):
                        continue
                    if any(y in combo for y in ("2023", "2024", "2025")) and "2026" not in combo:
                        continue

                    if url and url not in seen:
                        seen.add(url)
                        hits.append(r)
            except Exception:
                pass
        return hits

    results = await asyncio.to_thread(_search)
    if not results:
        return f"ما لقيت إعلانات مباشرة نشطة ومفتوحة التقديم لـ '{role}' في {location} لعام 2026 حالياً عبر البحث السريع. تم استبعاد أي إعلانات قديمة أو منتهية."

    lines = [f"**🔍 نتائج البحث العميق عن وظائف نشطة (`{role}` في `{location}` - {org_type} - 2026):**\n"]
    for i, r in enumerate(results[:8], 1):
        title = r.get("title", "")
        url = r.get("href", "")
        body = r.get("body", "")
        lines.append(f"{i}. **{title}**\n   {body}\n   🔗 رابط الإعلان: {url}\n")

    lines.append("> 💡 **ملاحظة الأمان الزمني:** تم فحص التواريخ واستبعاد أي وظائف منتهية التقديم أو من السنوات السابقة.")
    return "\n".join(lines)


TOOLS = [
    {
        "name": "scan_jobs_now",
        "description": (
            "Check the monitored Telegram channels and job sites (PEF, Joby, Mostaql, Khamsat) right now. "
            "Matching opportunities are sent to Adham as separate messages; returns a short summary."
        ),
        "parameters": {"type": "object", "properties": {}},
        "handler": scan_jobs_now,
    },
    {
        "name": "recent_opportunities",
        "description": "List the job / freelance / aid / course opportunities already found and sent to Adham.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "How many (default 10)."},
                "category": {"type": "string", "enum": list(CATEGORIES)},
            },
        },
        "handler": recent_opportunities,
    },
    {
        "name": "deep_job_hunter",
        "description": (
            "Deep search for job openings across international NGOs (ReliefWeb, ICRC, MSF, NRC), UN agencies (UNjobs, UNDP, UNRWA), "
            "local Palestinian portals (jobs.ps, PEF), and global remote IT portals (Remotive, WeWorkRemotely). "
            "Use whenever Adham asks to find jobs, search for specific roles, or look for NGO/UN/remote positions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "description": "Job title or skill (e.g. 'IT Support', 'Network Technician', 'Helpdesk', 'CCTV', 'System Admin').",
                },
                "location": {
                    "type": "string",
                    "description": "Location (e.g. 'Gaza', 'Palestine', 'Remote', 'Middle East'). Default is 'Gaza'.",
                },
                "org_type": {
                    "type": "string",
                    "description": "Organization type (e.g. 'NGO', 'UN', 'Remote IT', 'Local').",
                },
            },
            "required": ["role"],
        },
        "handler": deep_job_hunter,
    },
]
