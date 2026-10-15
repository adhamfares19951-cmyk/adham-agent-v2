"""Multi-Currency Financial Tracker & Revenue Ledger for adham-agent.
Tracks Shamel POS sales, freelance revenue, and server infrastructure costs across USD, ILS, and JOD.
Persists records in SQLite and generates real-time balance sheets and net profit statements.
"""
from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("finance_tracker")

BASE_DIR = Path(__file__).resolve().parent.parent
FINANCE_DB = BASE_DIR / "agent_finance.db"


def _init_db() -> None:
    conn = sqlite3.connect(str(FINANCE_DB))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,         -- 'income' or 'expense'
            amount REAL NOT NULL,
            currency TEXT NOT NULL,     -- 'USD', 'ILS', 'JOD', 'EUR'
            category TEXT NOT NULL,     -- 'shamel_pos', 'freelance', 'server', 'personal'
            description TEXT,
            timestamp INTEGER NOT NULL,
            date_str TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def log_transaction(
    tx_type: str,
    amount: float,
    currency: str = "ILS",
    category: str = "shamel_pos",
    description: str = "",
) -> dict[str, Any]:
    """Logs an income or expense transaction."""
    _init_db()
    ts = int(time.time())
    date_str = time.strftime("%Y-%m-%d %H:%M")
    curr = currency.upper().strip()
    if curr in ("شيكل", "NIS"):
        curr = "ILS"
    elif curr in ("دولار", "$"):
        curr = "USD"
    elif curr in ("دينار", "JD"):
        curr = "JOD"

    conn = sqlite3.connect(str(FINANCE_DB))
    c = conn.cursor()
    c.execute("""
        INSERT INTO transactions (type, amount, currency, category, description, timestamp, date_str)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tx_type.lower(), amount, curr, category, description, ts, date_str))
    tx_id = c.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": tx_id,
        "type": tx_type,
        "amount": amount,
        "currency": curr,
        "category": category,
        "description": description,
        "date": date_str
    }


def get_financial_summary() -> dict[str, Any]:
    """Calculates balances and net cashflow broken down by currency."""
    _init_db()
    conn = sqlite3.connect(str(FINANCE_DB))
    c = conn.cursor()

    c.execute("SELECT type, currency, SUM(amount) FROM transactions GROUP BY type, currency")
    rows = c.fetchall()

    c.execute("SELECT type, amount, currency, category, description, date_str FROM transactions ORDER BY id DESC LIMIT 5")
    recent = c.fetchall()
    conn.close()

    totals: dict[str, dict[str, float]] = {}
    for tx_type, curr, total in rows:
        if curr not in totals:
            totals[curr] = {"income": 0.0, "expense": 0.0, "net": 0.0}
        totals[curr][tx_type] = total or 0.0

    for curr, data in totals.items():
        data["net"] = data["income"] - data["expense"]

    return {
        "currencies": totals,
        "recent_transactions": recent
    }


async def _handle_log_tx(args: dict) -> str:
    tx_type = args.get("type", "income")
    amount = float(args.get("amount", 0.0))
    currency = args.get("currency", "ILS")
    cat = args.get("category", "shamel_pos")
    desc = args.get("description", "")

    res = log_transaction(tx_type=tx_type, amount=amount, currency=currency, category=cat, description=desc)
    icon = "🟢 إيراد جديد" if tx_type == "income" else "🔴 مصروف مسجل"
    return (
        f"{icon} **تم التسجيل في السجل المالي:**\n"
        f"• **المبلغ:** {res['amount']} {res['currency']}\n"
        f"• **القسم:** {res['category']}\n"
        f"• **التفاصيل:** {res['description'] or 'بدون تفاصيل'}\n"
        f"• **التاريخ:** {res['date']}"
    )


async def _handle_summary(args: dict) -> str:
    summary = get_financial_summary()
    lines = ["📊 **التقرير المالي وصافي الأرباح:**\n"]

    if not summary["currencies"]:
        return "⚪ السجل المالي فارغ حتى الآن. يمكنك تسجيل أول عملية مثل: `سجل بيع نسخة شامل 450 شيكل`"

    for curr, bal in summary["currencies"].items():
        lines.append(
            f"**عملة {curr}:**\n"
            f"  • الإيرادات: +{bal['income']:,.2f} {curr}\n"
            f"  • المصاريف: -{bal['expense']:,.2f} {curr}\n"
            f"  • 💎 **الصافي:** **{bal['net']:,.2f} {curr}**\n"
        )

    if summary["recent_transactions"]:
        lines.append("🕒 **آخر 5 حركات مسجلة:**")
        for t_type, amt, curr, cat, desc, dt in summary["recent_transactions"]:
            arrow = "➕" if t_type == "income" else "➖"
            lines.append(f"  {arrow} {amt} {curr} ({cat}) - {desc[:30]} [{dt}]")

    return "\n".join(lines)


TOOLS = [
    {
        "name": "log_financial_transaction",
        "description": "تسجيل إيراد أو مصروف مالي جديد (بيع نسخة شامل POS، أرباح فريلانس، تكاليف سيرفرات ومصاريف) بالشيكل أو الدولار أو الدينار.",
        "parameters": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["income", "expense"], "description": "إيراد (income) أو مصروف (expense)"},
                "amount": {"type": "number", "description": "المبلغ الرقمي"},
                "currency": {"type": "string", "description": "العملة (ILS أو USD أو JOD)"},
                "category": {"type": "string", "description": "القسم: shamel_pos, freelance, server, personal"},
                "description": {"type": "string", "description": "تفاصيل الحركة واسم العميل أو الخدمة"}
            },
            "required": ["type", "amount"]
        },
        "handler": _handle_log_tx,
    },
    {
        "name": "get_financial_report",
        "description": "عرض التقرير المالي وكشف الحساب وصافي الأرباح الحالي مفصلاً لكل عملة (شيكل، دولار، دينار) وآخر الحركات.",
        "parameters": {"type": "object", "properties": {}},
        "handler": _handle_summary,
    }
]
