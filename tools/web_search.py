"""Web search & research tools:
1. web_search: fast search with Groq/Gemini/DuckDuckGo fallback.
2. deep_web_research: multi-angle deep research that searches multiple queries, reads top pages, and synthesizes a structured report.
3. get_live_rates: live prices of currencies (USD/ILS, JOD/ILS, EUR), gold, and crypto (BTC, ETH).
"""
import asyncio
import logging
import re
from urllib.parse import urlparse

import httpx

import config

log = logging.getLogger("web_search")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
SEARCH_PROMPT = (
    "Search the web and answer this request with a factual, well-structured summary. "
    "Include exact dates, numbers, facts, and names from the sources. "
    "If the results are unclear or outdated, say so. Answer in Arabic (with technical terms in English).\n\n"
    "Request: {query}"
)
_client = httpx.AsyncClient(timeout=120)


def _clean(text: str) -> str:
    text = re.sub(r"【[^】]*】", "", text)  # Groq citation marks
    return text.replace("**", "").strip()


async def _groq_search(query: str) -> str:
    key, model = config.BACKUP_KEYS.get("Groq", ("", ""))
    if not key or not model.startswith("openai/gpt-oss"):
        raise RuntimeError("Groq search not configured")
    for attempt in range(2):
        resp = await _client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": SEARCH_PROMPT.format(query=query)}],
                "tools": [{"type": "browser_search"}],
            },
        )
        if resp.status_code == 429 and attempt == 0:
            try:
                wait = min(20.0, float(resp.headers.get("retry-after", "10")))
            except ValueError:
                wait = 10.0
            log.info("Groq search rate-limited, waiting %.0fs", wait)
            await asyncio.sleep(wait)
            continue
        break
    resp.raise_for_status()
    msg = resp.json()["choices"][0]["message"]
    sources = []
    for tool in msg.get("executed_tools") or []:
        for url in re.findall(r"URL:\s*(https?://\S+)", tool.get("output") or ""):
            if "exa.ai/search" not in url and url not in sources:
                sources.append(url)
    return _with_sources(_clean(msg.get("content") or ""), sources)


async def _gemini_search(query: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    resp = await client.aio.models.generate_content(
        model=config.MODEL,
        contents=SEARCH_PROMPT.format(query=query),
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    sources = []
    try:
        for ch in resp.candidates[0].grounding_metadata.grounding_chunks or []:
            if ch.web and ch.web.uri:
                sources.append(ch.web.uri)
    except (AttributeError, IndexError, TypeError):
        pass
    return _with_sources(_clean(resp.text or ""), sources)


async def _ddgs_search(query: str, max_results: int = 5) -> str:
    """Plain DuckDuckGo text search."""
    from ddgs import DDGS

    def _run() -> list[dict]:
        return list(DDGS().text(query, max_results=max_results))

    results = await asyncio.to_thread(_run)
    if not results:
        raise RuntimeError("no ddgs results")
    lines = []
    sources = []
    for r in results:
        t, h, b = r.get("title", ""), r.get("href", ""), r.get("body", "")
        if h and h not in sources:
            sources.append(h)
        lines.append(f"• **{t}**\n  {b}\n  الرابط: {h}")
    return _with_sources("\n\n".join(lines), sources)


def _with_sources(text: str, sources: list[str]) -> str:
    if not text:
        raise RuntimeError("empty search result")
    if sources:
        text += "\n\n🔗 **المصادر الرئيسية:**\n" + "\n".join(f"- {u}" for u in sources[:4])
    return text


async def web_search(args: dict) -> str:
    query = (args.get("query") or "").strip()
    if not query:
        return "خطأ: نص البحث فاضي."
    engines = [("Groq", _groq_search)]
    if config.GEMINI_API_KEY:
        engines.append(("Gemini", _gemini_search))
    engines.append(("DuckDuckGo", _ddgs_search))
    for name, engine in engines:
        try:
            return await engine(query)
        except Exception as e:
            log.warning("%s search failed: %s", name, str(e)[:200])
    return ("البحث بالإنترنت مش متاح هلّق (كل محركات البحث مضغوطة أو خلص حدها). "
            "احكي لأدهم بصراحة إنك ما قدرت تجيب المعلومة، وممنوع تخمّن أي رقم أو سعر أو نتيجة.")


async def deep_web_research(args: dict) -> str:
    """Multi-query deep research: searches topic from multiple angles and combines findings."""
    topic = (args.get("topic") or "").strip()
    if not topic:
        return "خطأ: يرجى تزويد موضوع البحث."

    from ddgs import DDGS
    from tools.web_reader import page_text

    queries = [
        topic,
        f"{topic} 2026",
        f"{topic} news updates",
    ]

    all_hits = []
    seen_urls = set()

    def _search_all():
        hits = []
        dd = DDGS()
        for q in queries[:2]:
            try:
                for r in dd.text(q, max_results=3):
                    u = r.get("href", "")
                    if u and u not in seen_urls:
                        seen_urls.add(u)
                        hits.append(r)
            except Exception:
                pass
        return hits

    all_hits = await asyncio.to_thread(_search_all)
    if not all_hits:
        # Fallback to single web_search
        return await web_search({"query": topic})

    # Read top 2 distinct web pages for deeper insights
    page_snippets = []
    for hit in all_hits[:2]:
        url = hit.get("href", "")
        try:
            txt = await page_text(url, max_chars=1800)
            if txt and len(txt) > 100:
                host = urlparse(url).hostname or url
                page_snippets.append(f"📄 **مقتطف من {host}:**\n{txt[:1200]}...\n({url})")
        except Exception:
            pass

    # Build comprehensive research summary
    results_summary = [f"**نتائج البحث والتحري المتعمق عن: `{topic}`**\n"]
    results_summary.append("🔍 **أبرز النتائج والمصادر:**")
    for h in all_hits[:5]:
        results_summary.append(f"• **{h.get('title')}**\n  {h.get('body')}\n  🔗 {h.get('href')}")

    if page_snippets:
        results_summary.append("\n📚 **تفاصيل مستخلصة من الصفحات مباشرة:**")
        results_summary.extend(page_snippets)

    return "\n\n".join(results_summary)


async def get_live_rates(args: dict) -> str:
    """Fetch live currency, gold, and crypto exchange rates."""
    target = (args.get("target") or "all").lower().strip()
    lines = ["**📊 أسعار العملات والذهب والكريبتو الحية:**\n"]

    async with httpx.AsyncClient(timeout=8) as client:
        # 1. FX Rates (USD/ILS, JOD/ILS, EUR/USD)
        try:
            r = await client.get("https://open.er-api.com/v6/latest/USD")
            rates = r.json().get("rates", {})
            ils = rates.get("ILS")
            jod = rates.get("JOD")
            eur = rates.get("EUR")
            if ils:
                lines.append(f"💵 **الدولار مقابل الشيكل (USD/ILS):** `{ils:.3f} ₪`")
            if ils and jod:
                dinar_ils = ils / jod
                lines.append(f"🇯🇴 **الدينار الأردني مقابل الشيكل (JOD/ILS):** `{dinar_ils:.3f} ₪`")
            if eur:
                lines.append(f"💶 **اليورو مقابل الدولار (EUR/USD):** `{1.0/eur:.3f} $`")
        except Exception as e:
            log.warning("FX fetch failed: %s", e)

        # 2. Crypto (BTC, ETH, SOL)
        try:
            r = await client.get("https://api.binance.com/api/v3/ticker/price?symbols=[\"BTCUSDT\",\"ETHUSDT\",\"SOLUSDT\"]")
            data = {item["symbol"]: float(item["price"]) for item in r.json()}
            lines.append("\n🪙 **العملات الرقمية (Crypto):**")
            lines.append(f"• **البيتكوين (BTC):** `${data.get('BTCUSDT', 0):,.1f}`")
            lines.append(f"• **الإيثيريوم (ETH):** `${data.get('ETHUSDT', 0):,.1f}`")
            lines.append(f"• **سولانا (SOL):** `${data.get('SOLUSDT', 0):,.1f}`")
        except Exception as e:
            log.warning("Crypto fetch failed: %s", e)

    return "\n".join(lines)


TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Fast internet search for current facts, dates, news, sport matches, weather, "
            "or fast answers. Returns a summary with source links."
        ),
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What to search for."}},
            "required": ["query"],
        },
        "handler": web_search,
    },
    {
        "name": "deep_web_research",
        "description": (
            "In-depth web research: runs multi-angle searches, fetches page text from top sources, "
            "and synthesizes detailed factual reports with full links. "
            "Use when Adham asks for thorough research, market scans, complex comparisons, or detailed background."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The detailed topic or question to investigate deeply."}
            },
            "required": ["topic"],
        },
        "handler": deep_web_research,
    },
    {
        "name": "get_live_rates",
        "description": (
            "Get live exchange rates for USD/ILS (Dollar to Shekel), JOD/ILS (Jordanian Dinar to Shekel), "
            "EUR/USD, and crypto prices (Bitcoin, Ethereum, Solana). "
            "Use whenever Adham asks about today's currency or crypto prices."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Optional target ('fx', 'crypto', or 'all'). Default 'all'."}
            },
        },
        "handler": get_live_rates,
    },
]
