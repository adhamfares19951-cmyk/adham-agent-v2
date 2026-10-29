"""Read-only audit of every registered tool. Writes tool_audit_report.md (no secrets).

What it does:
1. STATIC: every tool has name/description/parameters/handler; schemas are valid; lists stale or
   unclassified names in SAFE_TOOLS / DANGEROUS_TOOLS; per-group counts; intent-selection check.
2. LIVE (read-only whitelist only): calls a few harmless tools through tools.run() and records
   OK / needs-args / error. Nothing is sent, published, deleted or written.
Run from the project folder:  venv\\Scripts\\python.exe tool_audit.py
"""
from __future__ import annotations

import asyncio
import re
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import tools  # noqa: E402

SECRET_RE = re.compile(r"(AIza[0-9A-Za-z_\-]{20,}|ghp_[0-9A-Za-z]{20,}|\b\d{8,10}:[A-Za-z0-9_\-]{30,}|sk-[A-Za-z0-9]{20,})")

# Strictly read-only. Args are minimal; a schema error just means "needs arguments".
LIVE_CALLS: list[tuple[str, dict]] = [
    ("list_reminders", {}),
    ("list_leads", {}),
    ("list_verified_leads", {}),
    ("recent_opportunities", {}),
    ("get_financial_report", {}),
    ("list_agency_experts", {}),
    ("search_skills", {"query": "python"}),
    ("get_live_rates", {}),
    ("check_server_infrastructure", {}),
    ("tiktok_check_status", {}),
    ("tiktok_get_analytics", {}),
    ("youtube_get_channel_stats", {}),
    ("get_tunnel_status", {}),
    ("list_website_products", {}),
    ("list_client_orders", {}),
    ("get_api_gateway_status", {}),
    ("web_search", {"query": "test"}),
]


def clip(s: str, n: int = 160) -> str:
    s = SECRET_RE.sub("[REDACTED]", str(s)).replace("\n", " ")
    return s[:n]


def static_checks(out: list[str]) -> None:
    all_tools = tools._TOOLS
    out.append(f"## Static checks\n\nRegistered tools: **{len(all_tools)}**\n")
    if tools.DUPLICATE_TOOLS:
        out.append(f"- DUPLICATE names ignored: {sorted(set(tools.DUPLICATE_TOOLS))}")
    bad = []
    for name, t in all_tools.items():
        problems = []
        if not t.get("description"):
            problems.append("no description")
        if not callable(t.get("handler")):
            problems.append("handler not callable")
        params = t.get("parameters")
        if not isinstance(params, dict) or params.get("type") != "object":
            problems.append("parameters not an object schema")
        else:
            try:
                import jsonschema
                jsonschema.Draft7Validator.check_schema(params)
            except Exception as e:  # noqa: BLE001
                problems.append(f"invalid schema: {clip(e, 80)}")
        if problems:
            bad.append((name, problems))
    out.append(f"- Tools with structural problems: **{len(bad)}**")
    for n, p in bad:
        out.append(f"  - `{n}`: {', '.join(p)}")

    names = set(all_tools)
    stale_safe = sorted(tools.SAFE_TOOLS - names)
    stale_danger = sorted(tools.DANGEROUS_TOOLS - names)
    unclassified = sorted(n for n in names if n not in tools.SAFE_TOOLS and n not in tools.DANGEROUS_TOOLS)
    out.append(f"- Names in SAFE_TOOLS that do not exist (stale): {len(stale_safe)} {stale_safe}")
    out.append(f"- Names in DANGEROUS_TOOLS that do not exist (stale): {len(stale_danger)} {stale_danger}")
    out.append(f"- Registered but unclassified (gated by default, need approval every time): {len(unclassified)} {unclassified}")
    disabled = sorted(n for n in names if tools.is_tool_disabled(n))
    out.append(f"- Hard-disabled: {disabled}")

    out.append("\n### Per-group counts\n")
    groups: dict[str, int] = {}
    for n, g in tools._TOOL_TO_GROUP.items():
        groups[g] = groups.get(g, 0) + 1
    for g, c in sorted(groups.items()):
        out.append(f"- {g}: {c}")

    out.append("\n### Intent selection (which tools reach the model)\n")
    probes = {
        "leads": "بدي عملاء جدد من غزة",
        "video": "اعمللي فيديو عن التداول",
        "publish": "انشر الفيديو على تيك توك",
        "generic": "مرحبا",
        "reminder": "ذكرني بكرة الساعة 9",
        "files": "شو الملفات بمجلد المشروع",
    }
    for label, q in probes.items():
        sel = tools.select_tools(q, [])
        grp_counts: dict[str, int] = {}
        for s in sel:
            g = tools._TOOL_TO_GROUP.get(s["name"], "?")
            grp_counts[g] = grp_counts.get(g, 0) + 1
        out.append(f"- {label}: {len(sel)} tools -> {grp_counts}")


async def live_checks(out: list[str]) -> None:
    out.append("\n## Live read-only calls\n")
    out.append("| tool | status | note |\n|---|---|---|")
    for name, args in LIVE_CALLS:
        if name not in tools._TOOLS:
            out.append(f"| {name} | MISSING | not registered |")
            continue
        t0 = time.time()
        try:
            res = await tools.run(name, args)
            dt = time.time() - t0
            r = str(res)
            if r.startswith("خطأ في معطيات"):
                status = "NEEDS-ARGS"
            elif r.startswith("⛔") or "طابور الموافقات" in r:
                status = "GATED"
            elif r.startswith("خطأ"):
                status = "ERROR"
            else:
                status = "OK"
            out.append(f"| {name} | {status} ({dt:.1f}s) | {clip(r, 110)} |")
        except Exception as e:  # noqa: BLE001
            out.append(f"| {name} | CRASH | {clip(e, 110)} |")


def main() -> None:
    out = ["# Tool audit report\n", f"Generated: {time.strftime('%Y-%m-%d %H:%M')}\n"]
    static_checks(out)
    asyncio.run(live_checks(out))
    text = SECRET_RE.sub("[REDACTED]", "\n".join(out))
    (ROOT / "tool_audit_report.md").write_text(text, encoding="utf-8")
    print(text)
    print("\nSaved: tool_audit_report.md")


if __name__ == "__main__":
    main()
