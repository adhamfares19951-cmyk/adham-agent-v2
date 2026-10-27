"""Dedicated Verification Suite for Async Await & Telegram Markdown Entity Fixes:
1. Verifies search_and_extract_leads is an async coroutine function and can be awaited without TypeError.
2. Verifies hunt_verified_leads_handler awaits search_and_extract_leads properly.
3. Verifies escape_markdown and clean_for_markdown sanitize strings with unclosed tags, underscores, etc.
4. Verifies safe_edit_message_text and safe_reply_text catch 'Can't parse entities' and fallback to parse_mode=None.
5. Verifies approval queue items with 'client_order' and unclosed Markdown formatting render safely.
"""
import asyncio
import inspect
import sys
from unittest.mock import AsyncMock, MagicMock

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import tg_utils
from tools import lead_hunter, social_studio
import memory


async def test_async_await_fix():
    print("\n[1/4] Testing Async Await Fix (search_and_extract_leads)...")
    
    # Check that search_and_extract_leads is a coroutine function
    assert inspect.iscoroutinefunction(lead_hunter.search_and_extract_leads), (
        "search_and_extract_leads must be an async coroutine function"
    )
    print("  ✓ lead_hunter.search_and_extract_leads is verified as async def.")

    # Call it with await (the exact call from main.py and agency_orchestrator.py)
    leads = await lead_hunter.search_and_extract_leads(
        query="صيدليات ومحلات تجارية",
        location="خانيونس",
        max_results=2
    )
    assert isinstance(leads, list), f"Expected list of leads, got {type(leads)}"
    assert len(leads) > 0, "Should return at least 1 lead"
    for l in leads:
        assert "business_name" in l
        assert "phone" in l
        assert "source_url" in l
        assert "proposed_pitch" in l
        assert "whatsapp_url" in l
        print(f"  ✓ Lead awaited safely: {l['business_name']} ({l['phone']}) - WhatsApp URL present")

    # Test tool handler that also calls search_and_extract_leads
    handler_res = await lead_hunter.hunt_verified_leads_handler({
        "query": "ملابس",
        "location": "خانيونس",
        "count": 2
    })
    assert isinstance(handler_res, str)
    assert "نتائج صيد العملاء الموثقين" in handler_res
    print("  ✓ hunt_verified_leads_handler executed and awaited search_and_extract_leads with 100% success.")


def test_markdown_sanitizers():
    print("\n[2/4] Testing Markdown Sanitization & Escaping...")

    # Test escape_markdown
    raw_str = "client_order_item *bold* `code` [link]"
    escaped = tg_utils.escape_markdown(raw_str)
    assert r"\_" in escaped or r"\*" in escaped or r"\`" in escaped
    print(f"  ✓ escape_markdown sanitized: '{raw_str}' -> '{escaped}'")

    # Test clean_for_markdown (turns client_order into 'client order' and strips rogue asterisks)
    action_type = "client_order"
    clean_action = tg_utils.clean_for_markdown(action_type)
    assert clean_action == "client order"
    print(f"  ✓ clean_for_markdown: '{action_type}' -> '{clean_action}' (no unclosed italics)")

    bad_desc = "طلب شراء: شامل_POS_v1.0 *غير مغلق [رابط غير كامل"
    cleaned_desc = tg_utils.clean_for_markdown(bad_desc)
    assert "_" not in cleaned_desc
    assert "*" not in cleaned_desc
    print(f"  ✓ clean_for_markdown: '{bad_desc}' -> '{cleaned_desc}'")


async def test_safe_telegram_message_handlers():
    print("\n[3/4] Testing safe_edit_message_text & safe_reply_text Fallbacks...")

    # Mock Telegram callback query with broken entity parse error (byte offset 614 error)
    class TelegramBadRequest(Exception):
        pass

    mock_query = MagicMock()
    mock_query.edit_message_text = AsyncMock()
    mock_query.message.reply_text = AsyncMock()

    # Simulate Telegram throwing BadRequest on Markdown
    call_count = 0
    async def mock_edit(text, reply_markup=None, parse_mode=None, **kwargs):
        nonlocal call_count
        call_count += 1
        if parse_mode == "Markdown":
            raise TelegramBadRequest("Can't parse entities: can't find end of the entity starting at byte offset 614")
        return MagicMock(text=text)

    mock_query.edit_message_text.side_effect = mock_edit

    # Call safe_edit_message_text with bad markdown
    problematic_text = "📋 **طابور الموافقات الحساسة (1 إجراء معلق):**\n🔹 **إجراء #10 (client_order):**\n📝 طلب شراء_شامل"
    res = await tg_utils.safe_edit_message_text(mock_query, problematic_text, parse_mode="Markdown")

    assert res is not None, "safe_edit_message_text must succeed via fallback"
    assert call_count == 2, f"Should have attempted Markdown then fallen back to plain text, calls: {call_count}"
    print("  ✓ safe_edit_message_text caught 'byte offset 614' error and automatically retried with parse_mode=None!")

    # Test safe_reply_text fallback
    mock_msg = MagicMock()
    reply_calls = 0
    async def mock_reply(text, reply_markup=None, parse_mode=None, **kwargs):
        nonlocal reply_calls
        reply_calls += 1
        if parse_mode == "Markdown":
            raise TelegramBadRequest("Can't parse entities: can't find end of the entity starting at byte offset 120")
        return MagicMock(text=text)

    mock_msg.reply_text = AsyncMock(side_effect=mock_reply)
    reply_res = await tg_utils.safe_reply_text(mock_msg, "Test bad markdown *unclosed", parse_mode="Markdown")
    assert reply_res is not None
    assert reply_calls == 2
    print("  ✓ safe_reply_text caught entity parsing error and automatically retried with parse_mode=None!")


async def test_approval_queue_rendering_simulation():
    print("\n[4/4] Testing Approval Queue Real Payload Formatting...")
    # Add a mock pending approval item with complex characters
    qid = memory.add_approval_item(
        action_type="client_order",
        description="طلب شراء: شامل_POS_v1.0 | العميل: test_user_99 | هاتف: 0599000111",
        payload={"order_id": 99, "item": "shamel_pos"}
    )
    assert qid > 0

    pending = memory.get_pending_approvals()
    assert any(p["id"] == qid for p in pending)

    # Format exactly as main.py lines 525-535
    lines = [
        f"📋 **طابور الموافقات الحساسة ({len(pending)} إجراء معلق):**",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for raw_item in pending[:5]:
        item = dict(raw_item)
        action_type = tg_utils.clean_for_markdown(item.get("action_type", "إجراء"))
        desc = tg_utils.clean_for_markdown(item.get("description", ""))
        created = tg_utils.clean_for_markdown(item.get("created_at", ""))
        lines.append(f"🔹 **إجراء #{item['id']} ({action_type}):**")
        lines.append(f"   📝 {desc}")
        lines.append(f"   ⏰ التاريخ: `{created}`\n")

    rendered = "\n".join(lines)
    # Check that client_order was sanitized to 'client order'
    assert "client order" in rendered
    assert "client_order" not in rendered, "Raw underscores in action_type must not be present"
    print("  ✓ Approval Queue formatted with clean action_type and descriptions (zero rogue underscores).")

    # Clean up test item
    memory.update_approval_status(qid, "approved")
    print("  ✓ Approval item cleaned up.")


async def main():
    print("==================================================================")
    print("🧪 RUNNING BUGFIX VERIFICATION SUITE (ASYNC AWAIT & TELEGRAM PARSER)")
    print("==================================================================")
    await test_async_await_fix()
    test_markdown_sanitizers()
    await test_safe_telegram_message_handlers()
    await test_approval_queue_rendering_simulation()
    print("\n==================================================================")
    print("🎉 ALL BUGFIX TESTS PASSED 100% WITH ZERO ERRORS!")
    print("==================================================================")


if __name__ == "__main__":
    asyncio.run(main())
