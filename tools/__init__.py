"""Tool registry: modules expose TOOLS = [{name, description, parameters, handler}].
Wave 1.2: Group metadata, dynamic intent selection (cap <= 25), jsonschema validation,
asyncio timeouts, output truncation, security approval gates for dangerous operations.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import logging
import re
from typing import Any

import config
import memory

# Import all tool modules
from tools import (
    agency_tools, apk_inspector, brief, browser_pilot, calendar_tools, carousel_builder, cloud_tunnel,
    code_auditor, codync_manager, crew_orchestrator, document_vision, experience_tools, facebook_saved,
    finance_tracker, gaza_shops, github_engine, gmaps_lead_kit, gmail_tools, insights, jobs,
    lead_pipeline_bridge, license_generator, live_lead_scraper, media_studio, memory_tools,
    mikrotik_manager, network_tools, outreach, project_concat, proposal_pdf_builder, reminders,
    self_evolution, server_ops, session_manager, skills_engine, social_gig_hunter, social_reach,
    tech_radar, video_assembler, video_autocaption, voice_studio, web_reader, web_search,
    whatsapp_bridge, workspace_coder, youtube_tools, youtube_publisher, video_director,
    tiktok_publisher, long_video_studio, motion_studio, engineering_calculators, website_manager,
    lead_hunter, social_studio, live_data_hub, instagram_publisher, social_dispatcher,
)

log = logging.getLogger("tools")

# Module Group Categorization (Wave 1.2)
MODULE_GROUPS: dict[str, list[Any]] = {
    "core": [memory_tools, web_search, web_reader, brief, experience_tools, calendar_tools],
    "reminders_jobs": [reminders, jobs, insights],
    "social_publishing": [social_studio, tiktok_publisher, instagram_publisher, youtube_publisher, youtube_tools, social_dispatcher, social_reach, facebook_saved],
    "network_mikrotik": [network_tools, mikrotik_manager, cloud_tunnel, engineering_calculators],
    "dev_workspace": [workspace_coder, github_engine, self_evolution, code_auditor, codync_manager, apk_inspector, project_concat, server_ops],
    "media": [media_studio, video_assembler, motion_studio, long_video_studio, voice_studio, video_autocaption, video_director, carousel_builder, document_vision],
    "leads_sales": [lead_hunter, live_lead_scraper, gmaps_lead_kit, lead_pipeline_bridge, outreach, gaza_shops, proposal_pdf_builder, whatsapp_bridge, gmail_tools, social_gig_hunter, tech_radar],
    "finance": [finance_tracker, website_manager, license_generator, live_data_hub],
}

# Collect all tools and detect duplicates at import (Wave 1.2)
_TOOLS: dict[str, dict] = {}
_TOOL_TO_GROUP: dict[str, str] = {}

for grp_name, mods in MODULE_GROUPS.items():
    for m in mods:
        for t in getattr(m, "TOOLS", []):
            t_name = t["name"]
            if t_name in _TOOLS:
                # If tool was registered in core, keep it or raise
                pass
            _TOOLS[t_name] = t
            _TOOL_TO_GROUP[t_name] = grp_name

# Add agency / skills engines
for extra_mod, extra_grp in [(agency_tools, "dev_workspace"), (skills_engine, "dev_workspace"), (browser_pilot, "dev_workspace"), (session_manager, "core"), (crew_orchestrator, "dev_workspace")]:
    for t in getattr(extra_mod, "TOOLS", []):
        t_name = t["name"]
        _TOOLS[t_name] = t
        _TOOL_TO_GROUP[t_name] = extra_grp

# Dangerous tools that MUST be gated through approval (Rule 14 & Wave 1.2)
DANGEROUS_TOOLS = {
    "execute_server_command", "workspace_write_file", "self_modify_agent_code",
    "install_python_package", "restart_agent_daemon", "integrate_github_repo_as_tool",
    "tiktok_upload_video", "publish_instagram_reel", "youtube_upload_video",
    "broadcast_social_platforms", "create_and_publish_trading_short",
}

# Shell denylist (Second safety layer)
SHELL_DENYLIST = [
    "format ", "del /s", "rmdir /s", "reg delete", "shutdown",
    "powershell -enc", "curl|iex", "curl | iex", "rm -rf", "mkfs", "dd if=",
]

# Untrusted sources whose output must be wrapped
UNTRUSTED_SOURCES = {
    "web_search", "deep_web_research", "read_webpage", "read_email",
    "search_emails", "workspace_read_file", "browse_website_with_pilot", "read_with_jina"
}


def _match_intent_groups(query: str) -> set[str]:
    """Determines relevant tool groups using token boundary & root matching."""
    t = query.lower()
    latin_tokens = set(re.findall(r'\b[a-z0-9_]+\b', t))
    
    selected = {"core"}  # Core group is always on

    if (latin_tokens & {"remind", "reminder", "job", "jobs", "career", "cv", "resume"}) or \
       any(k in t for k in ["تذكير", "ذكرني", "تنبيه", "وظائف", "وظيفة", "شغل", "فرص", "سيرة"]):
        selected.add("reminders_jobs")

    if (latin_tokens & {"tiktok", "instagram", "reel", "reels", "youtube", "post", "publish", "social", "caption", "facebook"}) or \
       any(k in t for k in ["تيك", "انستا", "انستقرام", "انستغرام", "ريلز", "ريل", "يوتيوب", "نشر", "انشر", "مشاهدات", "كابشن", "فيسبوك", "بوست"]):
        selected.add("social_publishing")

    if (latin_tokens & {"network", "mikrotik", "router", "subnet", "vlan", "ip", "solar"}) or \
       any(k in t for k in ["شبكة", "شبكات", "ميكروتك", "راوتر", "سبنت", "طاقة", "سولار", "انفرتر"]):
        selected.add("network_mikrotik")

    if (latin_tokens & {"code", "python", "script", "git", "github", "repo", "file", "terminal", "cmd", "pip", "debug"}) or \
       any(k in t for k in ["كود", "برمج", "سكربت", "ملف", "مستودع", "تعديل", "تيرمينال", "فحص"]):
        selected.add("dev_workspace")

    if (latin_tokens & {"image", "video", "audio", "voice", "motion", "masterclass", "subtitle"}) or \
       any(k in t for k in ["صورة", "فيديو", "صوت", "تعليق", "موشن", "تصميم", "ترجمة"]):
        selected.add("media")

    if (latin_tokens & {"lead", "leads", "sales", "client", "email", "whatsapp", "gaza", "pitch", "proposal"}) or \
       any(k in t for k in ["عملاء", "عميل", "مبيعات", "زبائن", "ايميل", "واتساب", "غزة", "خانيونس", "عرض", "صفقة"]):
        selected.add("leads_sales")

    if (latin_tokens & {"store", "product", "order", "orders", "price", "finance", "money", "receipt", "balance", "profit", "expenses"}) or \
       any(k in t for k in ["متجر", "منتج", "طلب", "ارباح", "أرباح", "فلوس", "فاتورة", "مالية", "رصيد", "حساب", "مصاريف"]):
        selected.add("finance")

    return selected


def select_tools(query: str, history: list[dict] | None = None) -> list[dict]:
    """Selects at most 25 tool schemas matching the query intent, keeping core tools."""
    active_groups = _match_intent_groups(query)
    
    # Also inspect last user message from history if any
    if history:
        for m in reversed(history):
            if m.get("role") == "user" and isinstance(m.get("content"), str):
                active_groups.update(_match_intent_groups(m["content"]))
                break

    # If only core was selected, add the most common high-value groups
    if len(active_groups) == 1:
        active_groups.update({"reminders_jobs", "leads_sales", "social_publishing"})

    # Collect schemas
    selected_tools: dict[str, dict] = {}

    # 1. Add core tools first
    for t_name, grp in _TOOL_TO_GROUP.items():
        if grp == "core" and t_name in _TOOLS:
            selected_tools[t_name] = _TOOLS[t_name]

    # 2. Add other matched groups until cap <= 25
    for t_name, grp in _TOOL_TO_GROUP.items():
        if len(selected_tools) >= 25:
            break
        if grp in active_groups and t_name not in selected_tools and t_name in _TOOLS:
            selected_tools[t_name] = _TOOLS[t_name]

    return [
        {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}
        for t in selected_tools.values()
    ]


def schemas() -> list[dict]:
    """Returns schemas for all tools (or fallback)."""
    return [
        {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}
        for t in _TOOLS.values()
    ]


async def run(name: str, args: dict | None = None) -> str:
    """Executes a tool with validation, timeouts, truncation, and safety approval gates."""
    tool = _TOOLS.get(name)
    if not tool:
        return f"خطأ: الأداة '{name}' غير مسجلة في النظام."

    if args is None:
        args = {}

    # Wave 1.2: jsonschema validation
    try:
        import jsonschema
        params_schema = tool.get("parameters")
        if params_schema and isinstance(params_schema, dict):
            jsonschema.validate(instance=args, schema=params_schema)
    except Exception as ve:
        log.warning("JSON schema validation failed for %s args=%s: %s", name, args, ve)
        return f"خطأ في معطيات الأداة {name}: {ve}. يرجى تصحيح المعطيات وفق المخطط وإعادة المحاولة."

    # Wave 1.2 & Rule 14: Safety Approval Gate for Dangerous Tools
    if name in DANGEROUS_TOOLS and not args.get("_approved"):
        # Check Shell Denylist first
        if name == "execute_server_command":
            cmd = str(args.get("command", "")).lower()
            if any(deny in cmd for deny in SHELL_DENYLIST):
                log.error("Rejected denied shell command: %s", cmd)
                return f"⛔ تم رفض تنفيذ الأمر لاحتوائه على تعليمة محظورة أمنياً: {cmd}"

        log.warning("Gating dangerous tool %s into approval queue. Args: %s", name, args)
        qid = memory.add_approval_item(
            action_type=name,
            description=f"طلب تنفيذ {name}",
            payload=args,
        )
        return (
            f"⚠️ **تم تحويل هذا الإجراء لطابور الموافقات (#{qid}) بانتظار موافقة أدهم:**\n"
            f"• الأداة: {name}\n"
            f"• المعطيات: {json.dumps(args, ensure_ascii=False)}\n\n"
            "لن يتم التنفيذ إلا بعد الضغط على زر الاعتماد ✅ من أدهم."
        )

    log.info("Tool invocation: %s with args: %s", name, args)
    
    # Wave 1.2: asyncio.wait_for per tool (default 60s, 180s for heavy video studio)
    timeout_seconds = 180.0 if ("video" in name or "motion" in name or "media" in name) else 60.0
    
    try:
        handler = tool["handler"]
        if inspect.iscoroutinefunction(handler):
            raw_res = await asyncio.wait_for(handler(args), timeout=timeout_seconds)
        else:
            raw_res = await asyncio.wait_for(asyncio.to_thread(handler, args), timeout=timeout_seconds)

        res_str = str(raw_res)

        # Truncate results to ~6,000 chars
        if len(res_str) > 6000:
            res_str = res_str[:6000] + "\n\n[... تم قطع باقي المخرجات لتجاوز الحد الأقصى للطول (truncated) ...]"

        # Wrap untrusted external sources
        if name in UNTRUSTED_SOURCES:
            res_str = f"<<<TOOL_OUTPUT (UNTRUSTED_EXTERNAL_DATA)>>>\n{res_str}\n<<<END_TOOL_OUTPUT>>>"

        return res_str

    except asyncio.TimeoutError:
        log.error("Tool %s timed out after %s seconds", name, timeout_seconds)
        return f"خطأ: تجاوزت الأداة {name} الحد الزمني المسموح ({timeout_seconds} ثانية)."
    except Exception as e:
        log.exception("Tool %s execution failed: %s", name, e)
        return f"خطأ أثناء تنفيذ الأداة {name}: {e}"


def validate_tools_schemas() -> dict[str, Any]:
    """Self-check at startup ensuring handlers and schemas align."""
    report = {"total": len(_TOOLS), "valid": 0, "issues": []}
    for name, t in _TOOLS.items():
        if not callable(t.get("handler")):
            report["issues"].append(f"{name}: Handler is not callable")
        else:
            report["valid"] += 1
    return report


# Backward-compatible alias
execute_tool = run
