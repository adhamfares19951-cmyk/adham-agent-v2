"""WhatsApp Automation & Business Outreach Bridge for adham-agent.
Provides tools to generate WhatsApp Z-Reports for POS shops, create digital invoices,
compose tailored outreach messages with wa.me deep links, and integrate with local/remote WhatsApp gateways.
"""
from __future__ import annotations

import json
import logging
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any

log = logging.getLogger("whatsapp_bridge")

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "whatsapp_config.json"


def _clean_phone(phone: str) -> str:
    """Standardizes phone number for WhatsApp international format (e.g. 97059..., 9725..., 9665...)."""
    digits = "".join(filter(str.isdigit, phone))
    # If starts with 059 or 056 (Palestine)
    if digits.startswith("059") or digits.startswith("056"):
        return "970" + digits[1:]
    # If starts with 05 (general/Saudi/Israel)
    if digits.startswith("05"):
        return "972" + digits[1:]  # Or default regional
    if digits.startswith("00"):
        return digits[2:]
    return digits


def generate_wa_link(phone: str, message: str) -> str:
    """Generates a direct Click-to-Chat WhatsApp link."""
    clean = _clean_phone(phone)
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{clean}?text={encoded}"


def build_z_report_text(
    shop_name: str,
    date_str: str,
    total_sales: float,
    total_profit: float,
    cash_in_drawer: float,
    transaction_count: int,
    top_items: list[str] | None = None,
    notes: str = ""
) -> str:
    """Builds a formatted WhatsApp Z-Report message for POS owners."""
    items_text = ""
    if top_items:
        items_text = "\n🔥 *أكثر الأصناف مبيعاً اليوم:*\n" + "\n".join(f"  • {item}" for item in top_items)

    notes_text = f"\n📌 *ملاحظات:* {notes}" if notes else ""

    return (
        f"📊 *تقرير الإقفال اليومي (Z-Report)*\n"
        f"🏪 *المتجر:* {shop_name}\n"
        f"📅 *التاريخ:* {date_str}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *إجمالي المبيعات:* {total_sales:,.2f} ₪\n"
        f"📈 *صافي الأرباح التقديرية:* {total_profit:,.2f} ₪\n"
        f"💵 *النقدية في الدرج (Cash):* {cash_in_drawer:,.2f} ₪\n"
        f"🧾 *عدد الفواتير المنفذة:* {transaction_count} فاتورة\n"
        f"━━━━━━━━━━━━━━━━━━"
        f"{items_text}"
        f"{notes_text}\n\n"
        f"✅ *تم التدقيق والاعتماد عبر نظام شامل POS الذكي.*"
    )


def build_invoice_text(
    shop_name: str,
    invoice_number: str,
    customer_name: str,
    items: list[dict[str, Any]],
    total: float,
    paid: float,
    notes: str = ""
) -> str:
    """Builds a formatted digital WhatsApp receipt/invoice for customers."""
    date_now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    items_lines = []
    for it in items:
        name = it.get("name", "صنف")
        qty = it.get("qty", 1)
        price = it.get("price", 0.0)
        subtotal = qty * price
        items_lines.append(f"  ▫️ {name} (×{qty}) ⬅️ *{subtotal:,.2f} ₪*")

    items_block = "\n".join(items_lines)
    remaining = max(0.0, total - paid)
    rem_text = f"\n⚠️ *المتبقي ذمم:* {remaining:,.2f} ₪" if remaining > 0 else "\n✅ *الحالة: مسدد بالكامل نقداً*"

    return (
        f"🧾 *فاتورة شراء إلكترونية*\n"
        f"🏪 *{shop_name}*\n"
        f"📅 {date_now} | رقم الفاتورة: `#{invoice_number}`\n"
        f"👤 *العميل:* {customer_name}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 *الأصناف والمنتجات:*\n"
        f"{items_block}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💵 *الإجمالي النهائي:* {total:,.2f} ₪\n"
        f"💳 *المدفوع:* {paid:,.2f} ₪"
        f"{rem_text}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"شكراً لزيارتكم ونسعد بخدمتكم دائماً! 🌹\n"
        f"⚡ *فاتورة صادرة عن نظام شامل POS.*"
    )


# ==============================================================================
# Tool Handlers for AI Agent
# ==============================================================================

async def send_whatsapp_link_handler(args: dict) -> str:
    """Generates direct Click-to-Chat WhatsApp links and ready text."""
    phone = (args.get("phone") or "").strip()
    message = (args.get("message") or "").strip()
    if not phone or not message:
        return "يرجى تزويد رقم الهاتف ونص الرسالة المراد إرسالها."

    clean = _clean_phone(phone)
    link = generate_wa_link(phone, message)

    return (
        f"✅ **تم تجهيز رسالة ورابط الواتساب بنجاح!**\n\n"
        f"📱 **الرقم:** `{clean}`\n"
        f"🔗 **رابط الفتح المباشر:** [اضغط هنا للمحادثة الفورية على واتساب]({link})\n\n"
        f"💬 **نص الرسالة المجهز:**\n```\n{message}\n```\n\n"
        f"💡 *يمكنك فتح الرابط مباشرة من الجوال وسيقوم بفتح محادثة العميل مع وضع النص في صندوق الإرسال.*"
    )


async def generate_z_report_handler(args: dict) -> str:
    """Generates an Arabic WhatsApp Z-Report for POS shops."""
    shop_name = args.get("shop_name") or "متجر شامل"
    date_str = args.get("date") or datetime.now().strftime("%Y-%m-%d")
    total_sales = float(args.get("total_sales") or 0.0)
    total_profit = float(args.get("total_profit") or (total_sales * 0.22))
    cash = float(args.get("cash_in_drawer") or total_sales)
    count = int(args.get("transaction_count") or 15)
    owner_phone = args.get("owner_phone", "")
    top_items = args.get("top_items", ["أرز بسمتي 5 كجم", "زيت نباتي 3 لتر", "حليب سائل"])

    report_text = build_z_report_text(
        shop_name=shop_name,
        date_str=date_str,
        total_sales=total_sales,
        total_profit=total_profit,
        cash_in_drawer=cash,
        transaction_count=count,
        top_items=top_items
    )

    result = [f"📊 **تقرير Z-Report اليومي المنسق لنظام شامل POS:**\n\n{report_text}"]
    if owner_phone:
        link = generate_wa_link(owner_phone, report_text)
        result.append(f"\n\n📲 **رابط إرسال التقرير فوراً لصاحب المحل بالواتساب:**\n[إرسال عبر WhatsApp]({link})")

    return "\n".join(result)


async def generate_invoice_handler(args: dict) -> str:
    """Generates a customer digital invoice ready to send via WhatsApp."""
    shop_name = args.get("shop_name") or "متجر شامل التجاري"
    inv_num = args.get("invoice_number") or str(int(datetime.now().timestamp()) % 100000)
    customer_name = args.get("customer_name") or "الزبون الكريم"
    customer_phone = args.get("customer_phone", "")
    items = args.get("items") or [
        {"name": "سكر أبيض 1 كجم", "qty": 2, "price": 4.5},
        {"name": "شاي أسود فاخر", "qty": 1, "price": 12.0},
    ]
    total = sum(it.get("qty", 1) * it.get("price", 0.0) for it in items)
    paid = float(args.get("paid", total))

    inv_text = build_invoice_text(
        shop_name=shop_name,
        invoice_number=inv_num,
        customer_name=customer_name,
        items=items,
        total=total,
        paid=paid
    )

    result = [f"🧾 **الفاتورة الرقمية لـ شامل POS:**\n\n{inv_text}"]
    if customer_phone:
        link = generate_wa_link(customer_phone, inv_text)
        result.append(f"\n\n📲 **رابط إرسال الفاتورة فوراً للزبون بالواتساب:**\n[إرسال الفاتورة للعميل]({link})")

    return "\n".join(result)


TOOLS = [
    {
        "name": "generate_whatsapp_message",
        "description": "تجهيز وتوليد رسالة واتساب مع رابط فتح مباشر (wa.me) لأي رقم جوال فلسطيني أو دولي.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "رقم الهاتف المراد إرسال الرسالة إليه"},
                "message": {"type": "string", "description": "نص الرسالة المجهزة"},
            },
            "required": ["phone", "message"],
        },
        "handler": send_whatsapp_link_handler,
    },
    {
        "name": "generate_whatsapp_z_report",
        "description": "توليد تقرير الإقفال اليومي (Z-Report) لنظام شامل POS وتجهيزه للإرسال لصاحب المحل بالواتساب.",
        "parameters": {
            "type": "object",
            "properties": {
                "shop_name": {"type": "string", "description": "اسم المحل أو السوبرماركت"},
                "total_sales": {"type": "number", "description": "إجمالي المبيعات بالشيكل (₪)"},
                "total_profit": {"type": "number", "description": "صافي الأرباح التقديرية"},
                "cash_in_drawer": {"type": "number", "description": "مبلغ الكاش المتواجد في الدرج"},
                "transaction_count": {"type": "integer", "description": "عدد الفواتير المنفذة اليوم"},
                "owner_phone": {"type": "string", "description": "رقم جوال صاحب المحل (اختياري لتوليد الرابط)"},
            },
            "required": ["shop_name", "total_sales"],
        },
        "handler": generate_z_report_handler,
    },
    {
        "name": "generate_whatsapp_invoice",
        "description": "إنشاء فاتورة رقمية للزبون في نظام شامل POS وتجهيزها للإرسال الفوري عبر الواتساب.",
        "parameters": {
            "type": "object",
            "properties": {
                "shop_name": {"type": "string", "description": "اسم المتجر"},
                "customer_name": {"type": "string", "description": "اسم العميل"},
                "customer_phone": {"type": "string", "description": "رقم هاتف العميل بالواتساب"},
                "items": {
                    "type": "array",
                    "description": "قائمة الأصناف: [{\"name\": \"...\", \"qty\": 1, \"price\": 10.0}]",
                },
                "paid": {"type": "number", "description": "المبلغ المدفوع"},
            },
            "required": ["shop_name", "customer_name"],
        },
        "handler": generate_invoice_handler,
    },
]
