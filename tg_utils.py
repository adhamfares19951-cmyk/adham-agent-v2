"""Small Telegram helpers shared by main.py and the tools.
Features:
- markdown_to_telegram_html: converts Markdown to rich Telegram HTML (bold, italic, code blocks, blockquotes, links).
- send_long: splits long messages safely and sends with HTML formatting, falling back to plain text if needed.
- escape_markdown: escapes Telegram legacy Markdown characters.
- clean_for_markdown: strips/sanitizes problematic formatting characters from dynamic text.
- safe_edit_message_text: robust callback query message editor with automatic parse_mode=None fallback.
- safe_reply_text: robust message replier with automatic parse_mode=None fallback.
"""
import html
import logging
import re
from typing import Any
from telegram import Update

log = logging.getLogger("tg_utils")
TG_LIMIT = 3900  # Telegram max is 4096, keep a safety margin for HTML tags


def escape_markdown(text: str) -> str:
    """Safely escapes Telegram legacy Markdown special characters (_ * ` [)."""
    if not text:
        return ""
    return re.sub(r"([_*`\[])", r"\\\1", str(text))


def clean_for_markdown(text: str) -> str:
    """Removes or replaces problematic formatting characters from raw text.
    Replaces underscores with spaces, removes asterisks and backticks.
    Ideal for fields like action_type, business names, or descriptions.
    """
    if not text:
        return ""
    return str(text).replace("_", " ").replace("*", "").replace("`", "")


async def safe_edit_message_text(
    query: Any,
    text: str,
    reply_markup: Any = None,
    parse_mode: str | None = "Markdown",
    **kwargs: Any,
) -> Any:
    """Safely edits a Telegram callback query message.
    If Telegram raises BadRequest due to entity parsing errors,
    it automatically falls back to plain text (parse_mode=None).
    """
    try:
        return await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            **kwargs,
        )
    except Exception as e:
        err_str = str(e).lower()
        if "message is not modified" in err_str:
            return None
        if parse_mode is not None and ("can't parse" in err_str or "entity" in err_str or "bad request" in err_str):
            log.warning(
                "Telegram edit_message_text failed with parse_mode=%s (%s). Retrying with parse_mode=None...",
                parse_mode, e
            )
            try:
                plain_text = text.replace("**", "").replace("*", "").replace("`", "")
                return await query.edit_message_text(
                    text=plain_text,
                    reply_markup=reply_markup,
                    parse_mode=None,
                    **kwargs,
                )
            except Exception as e2:
                if "message is not modified" in str(e2).lower():
                    return None
                log.warning("safe_edit_message_text fallback edit failed: %s. Attempting new reply...", e2)
        # Fallback to replying if edit is completely rejected
        try:
            plain_text = text.replace("**", "").replace("*", "").replace("`", "")
            return await query.message.reply_text(
                text=plain_text,
                reply_markup=reply_markup,
                parse_mode=None,
                **kwargs,
            )
        except Exception as e3:
            log.error("All safe_edit_message_text attempts failed: %s", e3)
            return None


async def safe_reply_text(
    message: Any,
    text: str,
    reply_markup: Any = None,
    parse_mode: str | None = "Markdown",
    **kwargs: Any,
) -> Any:
    """Safely sends a message reply. If entity parsing fails, retries with parse_mode=None."""
    try:
        return await message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            **kwargs,
        )
    except Exception as e:
        err_str = str(e).lower()
        if parse_mode is not None and ("can't parse" in err_str or "entity" in err_str or "bad request" in err_str):
            log.warning(
                "Telegram reply_text failed with parse_mode=%s (%s). Retrying with parse_mode=None...",
                parse_mode, e
            )
            try:
                plain_text = text.replace("**", "").replace("*", "").replace("`", "")
                return await message.reply_text(
                    text=plain_text,
                    reply_markup=reply_markup,
                    parse_mode=None,
                    **kwargs,
                )
            except Exception as e2:
                log.error("safe_reply_text fallback failed: %s", e2)
                return None
        log.error("safe_reply_text failed: %s", e)
        return None


def markdown_to_telegram_html(text: str) -> str:
    """Safely converts common Markdown into valid Telegram HTML.
    Tags supported by Telegram: <b>, <i>, <s>, <u>, <code>, <pre>, <blockquote>, <a href="...">.
    """
    if not text:
        return ""

    placeholders = {}
    counter = 0

    def make_token(prefix: str) -> str:
        nonlocal counter
        tok = f"\x02{prefix}_{counter}\x03"
        counter += 1
        return tok

    # 1. Multi-line code blocks: ```lang\ncode\n```
    def replace_code_block(m):
        lang = (m.group(1) or "").strip()
        code = m.group(2)
        escaped = html.escape(code.strip("\r\n"))
        if lang:
            tag = f'<pre><code class="language-{html.escape(lang)}">{escaped}</code></pre>'
        else:
            tag = f'<pre><code>{escaped}</code></pre>'
        tok = make_token("CBLOCK")
        placeholders[tok] = tag
        return tok

    text = re.sub(r"```([a-zA-Z0-9_\-\+]*)\r?\n?(.*?)\r?\n?```", replace_code_block, text, flags=re.DOTALL)

    # 2. Inline code: `code`
    def replace_inline_code(m):
        code = m.group(1)
        tag = f'<code>{html.escape(code)}</code>'
        tok = make_token("INLINE")
        placeholders[tok] = tag
        return tok

    text = re.sub(r"`([^`\r\n]+)`", replace_inline_code, text)

    # 3. Escape HTML characters in remaining regular text
    text = html.escape(text)

    # 4. Headers: # Header or # **Header** -> <b>Header</b>
    text = re.sub(r"^(?:#{1,6})\s*\*{0,2}(.+?)\*{0,2}$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # 5. Bold: **bold** or __bold__
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text, flags=re.DOTALL)
    text = re.sub(r"(?<![a-zA-Z0-9])__(.+?)__(?![a-zA-Z0-9])", r"<b>\1</b>", text, flags=re.DOTALL)
    text = re.sub(r"<b>\s*<b>", "<b>", text)
    text = re.sub(r"</b>\s*</b>", "</b>", text)

    # 6. Italic: *italic* or _italic_
    text = re.sub(r"(?<![a-zA-Z0-9\*])\*([^\*\r\n]+?)\*(?![a-zA-Z0-9\*])", r"<i>\1</i>", text)
    text = re.sub(r"(?<![a-zA-Z0-9_])_([^_\r\n]+?)_(?![a-zA-Z0-9_])", r"<i>\1</i>", text)

    # 7. Strikethrough: ~~del~~
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text, flags=re.DOTALL)

    # 8. Blockquotes: > quote
    lines = text.split("\n")
    processed_lines = []
    quote_acc = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("&gt;"):
            q_text = line.replace("&gt;", "", 1).strip()
            quote_acc.append(q_text)
        else:
            if quote_acc:
                processed_lines.append(f"<blockquote>{chr(10).join(quote_acc)}</blockquote>")
                quote_acc = []
            processed_lines.append(line)
    if quote_acc:
        processed_lines.append(f"<blockquote>{chr(10).join(quote_acc)}</blockquote>")
    text = "\n".join(processed_lines)

    # 9. Links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\s\)]+)\)", r'<a href="\2">\1</a>', text)

    # 10. Restore placeholders
    for tok, val in placeholders.items():
        text = text.replace(tok, val)

    return text


def split_text(text: str, limit: int = TG_LIMIT) -> list[str]:
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n\n", 0, limit)
        if cut < limit // 3:
            cut = text.rfind("\n", 0, limit)
        if cut < limit // 3:
            cut = text.rfind(" ", 0, limit)
        if cut < limit // 3:
            cut = limit
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        chunks.append(text)
    return chunks or ["..."]


async def send_long(update: Update, text: str) -> None:
    msg = update.effective_message
    for chunk in split_text(text):
        if not chunk.strip():
            continue
        html_chunk = markdown_to_telegram_html(chunk)
        try:
            await msg.reply_html(html_chunk, disable_web_page_preview=True)
        except Exception as e:
            log.warning("Telegram HTML formatting failed (%s), falling back to plain text", e)
            try:
                await msg.reply_text(chunk, disable_web_page_preview=True)
            except Exception as e2:
                log.error("Failed to send message: %s", e2)
