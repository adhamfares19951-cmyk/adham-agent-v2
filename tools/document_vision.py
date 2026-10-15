"""Document Vision & Invoice Intelligence for adham-agent.
1. Parses receipts, handwritten store lists, and invoices into structured JSON for Shamel POS.
2. Extracts text, tables, and sections from PDF files and documents.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from tools import media

log = logging.getLogger("document_vision")

BASE_DIR = Path(__file__).resolve().parent.parent


def parse_receipt_text_to_json(raw_text: str) -> dict[str, Any]:
    """Parses raw text or OCR output of a store invoice into structured data."""
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    total = 0.0
    items = []
    store_name = "متجر محلي"
    date_str = ""

    # Heuristic parsing for prices and items
    price_pattern = re.compile(r"(\d+(?:\.\d{1,2})?)\s*(?:شيكل|دولار|ILS|USD|SAR|ر\.س|JD)?$", re.IGNORECASE)

    for i, line in enumerate(lines):
        if i == 0 and len(line) < 40 and not any(char.isdigit() for char in line):
            store_name = line
            continue

        # Look for dates
        date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", line)
        if date_match and not date_str:
            date_str = date_match.group(1)

        # Look for Total line
        if any(keyword in line.lower() for keyword in ["المجموع", "الإجمالي", "total", "صافي", "المبلغ"]):
            m = re.search(r"(\d+(?:\.\d{1,2})?)", line)
            if m:
                try:
                    total = float(m.group(1))
                except ValueError:
                    pass
            continue

        # Check for item + price
        m_price = price_pattern.search(line)
        if m_price:
            price_val = float(m_price.group(1))
            item_name = line[:m_price.start()].strip(" -:•")
            if item_name:
                items.append({"name": item_name, "price": price_val, "qty": 1})

    if not total and items:
        total = sum(it["price"] for it in items)

    return {
        "store_name": store_name,
        "date": date_str,
        "total_amount": round(total, 2),
        "items_count": len(items),
        "items": items,
        "raw_snippet": raw_text[:300]
    }


async def analyze_receipt_file(file_path: str) -> dict[str, Any]:
    """Reads a receipt file (Image or PDF) and extracts structured invoice data."""
    target = Path(file_path)
    if not target.is_absolute():
        target = BASE_DIR / target

    if not target.exists():
        raise FileNotFoundError(f"الملف غير موجود: {file_path}")

    data = target.read_bytes()
    suffix = target.suffix.lower()
    mime = "application/pdf" if suffix == ".pdf" else "image/jpeg"

    prompt = (
        "هذه صورة فاتورة / إيصال مبيعات أو كشف حساب يدوي. "
        "استخرج بدقة تامة: اسم المتجر، التاريخ، قائمة الأصناف مع أسعارها وكمياتها، والإجمالي النهائي. "
        "أجب بصيغة منظمة وواضحة جداً."
    )
    extracted_text = await media._gemini(data, mime, prompt)
    structured = parse_receipt_text_to_json(extracted_text)
    structured["llm_summary"] = extracted_text
    return structured


# ==============================================================================
# AI Agent Tool Handlers
# ==============================================================================

async def analyze_invoice_handler(args: dict) -> str:
    """Tool handler for analyzing receipts and invoices."""
    file_path = args.get("file_path", "").strip()
    raw_text = args.get("raw_text", "").strip()

    if file_path:
        try:
            res = await analyze_receipt_file(file_path)
            return (
                f"🧾 **تحليل الفاتورة والإيصال:**\n"
                f"🏪 **المتجر:** {res['store_name']}\n"
                f"📅 **التاريخ:** {res['date'] or 'غير محدد'}\n"
                f"💰 **الإجمالي المحسوب:** {res['total_amount']}\n"
                f"📦 **عدد الأصناف:** {res['items_count']}\n\n"
                f"**التفاصيل المستخرجة:**\n{res['llm_summary']}"
            )
        except Exception as e:
            return f"❌ خطأ أثناء تحليل ملف الفاتورة: {e}"

    if raw_text:
        res = parse_receipt_text_to_json(raw_text)
        return (
            f"🧾 **تحليل نص الفاتورة:**\n"
            f"🏪 **المتجر:** {res['store_name']}\n"
            f"💰 **الإجمالي:** {res['total_amount']}\n"
            f"📦 **الأصناف ({res['items_count']}):**\n" +
            "\n".join(f"- {it['name']}: {it['price']}" for it in res["items"])
        )

    return "يرجى تزويدي بمسار ملف الفاتورة أو نصها."


TOOLS = [
    {
        "name": "analyze_invoice_receipt",
        "description": "تحليل صور وكشوف الفواتير والإيصالات وقوائم الطلبات المكتوبة باليد أو المطبوعة وتحويلها لبيانات مهيكلة لنظام شامل POS.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "مسار ملف صورة الفاتورة أو ملف PDF"},
                "raw_text": {"type": "string", "description": "النص المكتوب للفاتورة إن وُجد"},
            },
        },
        "handler": analyze_invoice_handler,
    },
]
