"""Tool registry: modules expose TOOLS = [{name, description, parameters, handler}].
Wave 1.2: Group metadata, dynamic intent selection (cap <= 25), jsonschema validation,
asyncio timeouts, output truncation, security approval gates for dangerous operations.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
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
    lead_hunter, social_studio, live_data_hub, instagram_publisher, social_dispatcher, clips_pipeline,
)

log = logging.getLogger("tools")

# Module Group Categorization (Wave 1.2)
MODULE_GROUPS: dict[str, list[Any]] = {
    "core": [memory_tools, web_search, web_reader, brief, experience_tools, calendar_tools],
    "reminders_jobs": [reminders, jobs, insights],
    "social_publishing": [social_studio, tiktok_publisher, instagram_publisher, youtube_publisher, youtube_tools, social_dispatcher, social_reach, facebook_saved],
    "network_mikrotik": [network_tools, mikrotik_manager, cloud_tunnel, engineering_calculators],
    "dev_workspace": [workspace_coder, github_engine, self_evolution, code_auditor, codync_manager, apk_inspector, project_concat, server_ops],
    "media": [media_studio, video_assembler, motion_studio, long_video_studio, voice_studio, video_autocaption, video_director, carousel_builder, document_vision, clips_pipeline],
    "leads_sales": [lead_hunter, live_lead_scraper, gmaps_lead_kit, lead_pipeline_bridge, outreach, gaza_shops, proposal_pdf_builder, whatsapp_bridge, gmail_tools, social_gig_hunter, tech_radar],
    "finance": [finance_tracker, website_manager, license_generator, live_data_hub],
}

# Collect all tools; a duplicate name keeps the FIRST registration and is logged loudly
_TOOLS: dict[str, dict] = {}
_TOOL_TO_GROUP: dict[str, str] = {}
DUPLICATE_TOOLS: list[str] = []


def _register(tool: dict, group: str) -> None:
    t_name = tool["name"]
    if t_name in _TOOLS:
        DUPLICATE_TOOLS.append(t_name)
        log.error("Duplicate tool name '%s' (group %s) ignored; kept first registration.", t_name, group)
        return
    _TOOLS[t_name] = tool
    _TOOL_TO_GROUP[t_name] = group


for grp_name, mods in MODULE_GROUPS.items():
    for m in mods:
        for t in getattr(m, "TOOLS", []):
            _register(t, grp_name)

# Add agency / skills engines
for extra_mod, extra_grp in [(agency_tools, "dev_workspace"), (skills_engine, "dev_workspace"), (browser_pilot, "dev_workspace"), (session_manager, "core"), (crew_orchestrator, "dev_workspace")]:
    for t in getattr(extra_mod, "TOOLS", []):
        _register(t, extra_grp)

# ---------------------------------------------------------------------------
# Tool policy (fail-closed): a tool runs WITHOUT approval only if it is listed in SAFE_TOOLS.
# Anything else (including any tool added in the future) goes to the approval queue.
# ---------------------------------------------------------------------------
SAFE_TOOLS = {
    # memory / reminders / calendar / briefs
    "remember_fact", "forget_fact", "log_experience", "add_reminder", "list_reminders",
    "delete_reminder", "snooze_reminder", "set_morning_brief", "list_events", "create_event",
    # read-only research
    "web_search", "deep_web_research", "get_live_rates", "get_live_market_prices", "read_webpage",
    "read_with_jina", "search_reddit", "search_twitter_posts", "search_youtube", "get_youtube_summary",
    "inspect_github_repo", "read_repo_file", "search_repo_code", "search_github_worldwide",
    "search_osm_businesses", "inspect_network_target", "get_api_gateway_status",
    "search_skills", "read_skill_guide", "consult_agency_expert", "list_agency_experts",
    # mail (read + draft only, never send)
    "search_emails", "read_email", "draft_email",
    # jobs / leads (local DB and read-only scans)
    "scan_jobs_now", "recent_opportunities", "deep_job_hunter", "career_insights",
    "add_lead", "list_leads", "update_lead_status", "list_verified_leads", "query_leads_database",
    "scan_gaza_shops", "pitch_shamel_pos", "gaza_field_sales_plan", "scan_freelance_leads",
    "scan_social_tech_issues", "draft_pitch_proposal", "hunt_social_gigs",
    # calculators / drafts / local file generation
    "calculate_solar_system", "calculate_subnet_and_mikrotik", "calculate_subnet", "network_diagnostics",
    "generate_mikrotik_script", "generate_whatsapp_message", "generate_whatsapp_z_report",
    "generate_whatsapp_invoice", "generate_client_proposal_pdf", "analyze_invoice_receipt",
    "generate_social_script", "generate_arabic_voiceover", "generate_social_carousel",
    "log_financial_transaction", "get_financial_report", "audit_code_security", "audit_seo_and_discoverability",
    "inspect_apk_package", "check_server_infrastructure", "get_codync_setup_info",
    # read-only workspace access (path-restricted in workspace_coder)
    "workspace_list_files", "workspace_read_file",
    # read-only status calls of publishers
    "tiktok_get_analytics", "tiktok_check_status", "youtube_get_channel_stats",
    "list_website_products", "list_client_orders", "get_tunnel_status", "get_concat_editor_info",
    # local media generation (no publishing)
    "generate_ai_image", "repurpose_social_video", "generate_ai_voiceover", "burn_karaoke_subtitles_on_video",
    "process_video_clips_inbox", "apply_color_grade", "auto_cut_silence", "create_viral_short_video", "create_long_trading_video",
    "create_motion_masterclass", "create_talking_fruit_short", "create_fruit_drama_short",
    "create_fruit_fight_match", "create_cinematic_storyboard",
}

# Always needs approval (explicit list for documentation; everything not in SAFE_TOOLS is gated anyway).
DANGEROUS_TOOLS = {
    "execute_server_command", "workspace_write_file", "workspace_run_command", "self_modify_agent_code",
    "install_python_package", "restart_agent_daemon", "git_sync_code", "manage_mikrotik_router",
    "generate_shamel_pos_license", "add_or_update_product", "manage_user_sessions", "fetch_with_session",
    "browse_website_with_pilot", "trigger_lead_extraction_job", "scrape_leads_live", "extract_gmaps_leads_kit",
    "hunt_verified_leads", "pack_and_concat_project",
    "tiktok_upload_video", "publish_instagram_reel", "youtube_upload_video",
    "broadcast_social_platforms", "create_and_publish_trading_short",
}

# Hard-blocked: never executed, even with approval. Re-enable by name via env ENABLE_TOOLS.
DISABLED_BY_DEFAULT = {
    "integrate_github_repo_as_tool",   # downloads third-party code and registers it as a tool
    "update_project_autonomously",     # runs git pull / migrate unattended
    "start_public_tunnel", "stop_public_tunnel",  # exposes the machine to the internet
    "download_codync_windows_client",
    "get_facebook_saved_items",        # uses stored browser cookies
    "orchestrate_agent_crew",
}


def _enabled_overrides() -> set[str]:
    raw = os.getenv("ENABLE_TOOLS", "")
    return {n.strip() for n in raw.split(",") if n.strip()}


def is_tool_disabled(name: str) -> bool:
    return name in DISABLED_BY_DEFAULT and name not in _enabled_overrides()


def requires_approval(name: str) -> bool:
    """Fail-closed: gated unless explicitly listed as safe (and not in the dangerous list)."""
    if name in DANGEROUS_TOOLS:
        return True
    return name not in SAFE_TOOLS


# Shell denylist (Second safety layer)
SHELL_DENYLIST = [
    "format ", "del /s", "rmdir /s", "reg delete", "shutdown",
    "powershell -enc", "curl|iex", "curl | iex", "rm -rf", "mkfs", "dd if=",
]

# Untrusted sources whose output must be wrapped
UNTRUSTED_SOURCES = {
    "web_search", "deep_web_research", "read_webpage", "read_email",
    "search_emails", "workspace_read_file", "browse_website_with_pilot", "read_with_jina",
    "read_skill_guide", "search_skills", "read_repo_file", "search_repo_code", "get_youtube_summary",
    "search_reddit", "search_twitter_posts", "deep_job_hunter", "scan_jobs_now"
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

    if (latin_tokens & {"code", "python", "script", "git", "github", "repo", "file", "terminal", "cmd", "pip", "debug", "dir", "ls", "shell", "server", "command", "ping"}) or \
       any(k in t for k in ["كود", "برمج", "سكربت", "ملف", "مستودع", "تعديل", "تيرمينال", "فحص", "سيرفر", "السيرفر", "امر", "أمر", "الامر", "نفذ", "نفّذ"]):
        selected.add("dev_workspace")

    if (latin_tokens & {"image", "video", "audio", "voice", "motion", "masterclass", "subtitle", "clip", "clips", "flow"}) or \
       any(k in t for k in ["صورة", "فيديو", "صوت", "تعليق", "موشن", "تصميم", "ترجمة", "مقطع", "مقاطع", "كليب", "كليبات", "فلو"]):
        selected.add("media")

    if (latin_tokens & {"lead", "leads", "sales", "client", "email", "whatsapp", "gaza", "pitch", "proposal"}) or \
       any(k in t for k in ["عملاء", "عميل", "مبيعات", "زبائن", "ايميل", "واتساب", "غزة", "خانيونس", "عرض", "صفقة"]):
        selected.add("leads_sales")

    if (latin_tokens & {"store", "product", "order", "orders", "price", "finance", "money", "receipt", "balance", "profit", "expenses"}) or \
       any(k in t for k in ["متجر", "منتج", "طلب", "ارباح", "أرباح", "فلوس", "فاتورة", "مالية", "رصيد", "حساب", "مصاريف"]):
        selected.add("finance")

    return selected


SMALLTALK_RE = re.compile(r"^(مرحبا|مرحبتين|اهلا|أهلا|هلا|السلام|صباح|مساء|كيفك|كيف حالك|شكرا|شكراً|يسلمو|تمام|hi|hello|hey|thanks)\\b.{0,25}$", re.I)
MAX_SELECTED_TOOLS = int(os.getenv("MAX_SELECTED_TOOLS", "32") or 32)


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
    if len(active_groups) == 1 and not SMALLTALK_RE.match(query.strip()):
        active_groups.update({"reminders_jobs", "leads_sales", "social_publishing"})

    # Collect schemas
    selected_tools: dict[str, dict] = {}

    # 1. Add core tools first
    for t_name, grp in _TOOL_TO_GROUP.items():
        if grp == "core" and t_name in _TOOLS and not is_tool_disabled(t_name):
            selected_tools[t_name] = _TOOLS[t_name]

    # 2. Add the other matched groups FAIRLY (round-robin), so one big group cannot starve the rest.
    cap = MAX_SELECTED_TOOLS
    pools: list[list[str]] = []
    for grp in MODULE_GROUPS:
        if grp == "core" or grp not in active_groups:
            continue
        names = [n for n, g in _TOOL_TO_GROUP.items()
                 if g == grp and n in _TOOLS and n not in selected_tools and not is_tool_disabled(n)]
        if names:
            pools.append(names)
    # Tools registered via the extra modules (agency/skills/browser/...) keep their own group label.
    idx = 0
    while len(selected_tools) < cap and any(pools):
        pool = pools[idx % len(pools)]
        if pool:
            n = pool.pop(0)
            selected_tools[n] = _TOOLS[n]
        idx += 1

    return [
        {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}
        for t in selected_tools.values()
    ]


def schemas() -> list[dict]:
    """Returns schemas for all tools (or fallback)."""
    return [
        {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}
        for t in _TOOLS.values() if not is_tool_disabled(t["name"])
    ]


async def run(name: str, args: dict | None = None, *, approved: bool = False) -> str:
    """Executes a tool with validation, timeouts, truncation, and safety approval gates."""
    tool = _TOOLS.get(name)
    if not tool:
        return f"خطأ: الأداة '{name}' غير مسجلة في النظام."

    if is_tool_disabled(name):
        log.error("Blocked call to disabled tool %s", name)
        return f"⛔ الأداة '{name}' معطّلة افتراضياً لأسباب أمنية. لتفعيلها أضف اسمها إلى ENABLE_TOOLS في .env."

    if args is None:
        args = {}
    elif isinstance(args, dict):
        # Strip any key starting with '_' from args before schema validation
        args = {k: v for k, v in args.items() if not k.startswith("_")}
    else:
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

    # Shell Denylist ALWAYS runs (even if approved=True)
    if name == "execute_server_command":
        cmd = str(args.get("command", "")).lower()
        if any(deny in cmd for deny in SHELL_DENYLIST):
            log.error("Rejected denied shell command: %s", cmd)
            return f"⛔ تم رفض تنفيذ الأمر لاحتوائه على تعليمة محظورة أمنياً: {cmd}"

    # Dangerous tools approval gate
    if requires_approval(name) and not approved:
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
    for d in DUPLICATE_TOOLS:
        report["issues"].append(f"{d}: duplicate tool name (second registration ignored)")
    for name, t in _TOOLS.items():
        if not callable(t.get("handler")):
            report["issues"].append(f"{name}: Handler is not callable")
        else:
            report["valid"] += 1
    return report


# Backward-compatible alias
async def execute_tool(name: str, args: dict | None = None, *, approved: bool = False) -> str:
    return await run(name, args, approved=approved)
