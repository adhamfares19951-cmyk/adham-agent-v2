"""Social Reach & Deep Web Reader for adham-agent.
Inspired by Agent-Reach: Reads web pages via Jina Reader, searches Reddit & Twitter/X without paid API keys.
"""
import asyncio
import html
import logging
import re
from urllib.parse import quote, urlparse

import httpx

log = logging.getLogger("social_reach")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ar,en-US,en;q=0.9",
}


async def read_with_jina(args: dict) -> str:
    """Read any article or web page using Jina Reader (https://r.jina.ai/) returning clean LLM-friendly Markdown."""
    url = (args.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        return "يرجى تزويدي برابط ويب صحيح يبدأ بـ http:// أو https://"

    jina_url = f"https://r.jina.ai/{url}"
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=HEADERS) as client:
            resp = await client.get(jina_url)
            if resp.status_code == 200 and resp.text.strip():
                content = resp.text.strip()
                if len(content) > 6000:
                    content = content[:6000] + "\n\n...(تم اقتطاع باقي المقال للتركيز على الجوهر)."
                return f"📄 **محتوى المقال (المستخرج عبر Jina Reader)**:\n\n{content}"
    except Exception as e:
        log.warning("Jina Reader failed: %s, falling back to direct fetch", e)

    # Fallback to direct fetch
    try:
        from tools.web_reader import page_text
        text = await page_text(url)
        return f"📄 **محتوى الصفحة**:\n\n{text}"
    except Exception as e:
        return f"تعذر قراءة محتوى الرابط: {e}"


async def search_reddit(args: dict) -> str:
    """Search Reddit threads, questions, and discussions using public Reddit search."""
    query = (args.get("query") or "").strip()
    subreddit = (args.get("subreddit") or "").strip()
    if not query:
        return "يرجى تحديد موضوع البحث على ريديت."

    limit = min(max(int(args.get("limit") or 5), 1), 10)

    # If specific subreddit requested
    if subreddit:
        url = f"https://www.reddit.com/r/{subreddit}/search.json?q={quote(query)}&restrict_sr=1&sort=relevance&limit={limit}"
    else:
        url = f"https://www.reddit.com/search.json?q={quote(query)}&sort=relevance&limit={limit}"

    client_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    }

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers=client_headers) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                children = data.get("data", {}).get("children", [])
                if children:
                    lines = [f"💬 **أبرز نقاشات Reddit حول: «{query}»**\n"]
                    for idx, item in enumerate(children[:limit], 1):
                        p = item.get("data", {})
                        title = p.get("title", "")
                        sub = p.get("subreddit_name_prefixed", "")
                        score = p.get("score", 0)
                        num_comments = p.get("num_comments", 0)
                        permalink = f"https://reddit.com{p.get('permalink', '')}"
                        selftext = (p.get("selftext", "") or "").strip()
                        snippet = f" - «{selftext[:180]}...»" if selftext else ""

                        lines.append(f"{idx}. **{title}** ({sub} | ⬆️ {score} | 💬 {num_comments})")
                        if snippet:
                            lines.append(f"   {snippet}")
                        lines.append(f"   🔗 {permalink}\n")
                    return "\n".join(lines).strip()
    except Exception as e:
        log.warning("Direct Reddit search error: %s", e)

    # Fallback via DuckDuckGo site:reddit.com search
    try:
        from ddgs import DDGS
        ddgs = DDGS()
        ddg_query = f"site:reddit.com {query}"
        results = await asyncio.to_thread(lambda: list(ddgs.text(ddg_query, max_results=limit)))
        if results:
            lines = [f"💬 **نقاشات Reddit (عبر الرادار السريع): «{query}»**\n"]
            for idx, r in enumerate(results, 1):
                lines.append(f"{idx}. **{r.get('title', '')}**")
                lines.append(f"   {r.get('body', '')}")
                lines.append(f"   🔗 {r.get('href', '')}\n")
            return "\n".join(lines).strip()
    except Exception as e:
        log.warning("Reddit fallback search error: %s", e)

    return f"لم أتمكن من العثور على نقاشات كافية في Reddit حول «{query}»."


async def search_twitter_posts(args: dict) -> str:
    """Search public Twitter/X discussions, user opinions, and news via public search."""
    query = (args.get("query") or "").strip()
    if not query:
        return "يرجى إدخال موضوع البحث على تويتر/X."

    limit = min(max(int(args.get("limit") or 5), 1), 10)

    try:
        from ddgs import DDGS
        ddgs = DDGS()
        ddg_query = f"(site:x.com OR site:twitter.com) {query}"
        results = await asyncio.to_thread(lambda: list(ddgs.text(ddg_query, max_results=limit)))
        if results:
            lines = [f"🐦 **أبرز ما كُتب على منصة X / Twitter حول: «{query}»**\n"]
            for idx, r in enumerate(results, 1):
                lines.append(f"{idx}. **{r.get('title', '')}**")
                lines.append(f"   {r.get('body', '')}")
                lines.append(f"   🔗 {r.get('href', '')}\n")
            return "\n".join(lines).strip()
    except Exception as e:
        log.warning("Twitter search failed: %s", e)

    return f"لم أجد منشورات كافية على منصة X حول «{query}»."


TOOLS = [
    {
        "name": "read_with_jina",
        "description": (
            "Read any web page, blog post, tech article, or documentation using Jina Reader. "
            "Returns clean, ad-free Markdown formatted specifically for LLM analysis."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full webpage URL (e.g. https://...)"}
            },
            "required": ["url"],
        },
        "handler": read_with_jina,
    },
    {
        "name": "search_reddit",
        "description": (
            "Search Reddit communities for real troubleshooting experiences, hardware/software issues (MikroTik, Flutter, EA, servers), and reviews."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Topic, error message, or keyword."},
                "subreddit": {"type": "string", "description": "Optional specific subreddit (e.g. mikrotik, flutterdev, sysadmin)."},
                "limit": {"type": "integer", "description": "Number of results (1-10, default 5)."},
            },
            "required": ["query"],
        },
        "handler": search_reddit,
    },
    {
        "name": "search_twitter_posts",
        "description": (
            "Search public Twitter / X posts, discussions, and sentiment about tech, market news, or products."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keyword or topic to search."},
                "limit": {"type": "integer", "description": "Number of results (1-10, default 5)."},
            },
            "required": ["query"],
        },
        "handler": search_twitter_posts,
    },
]
