"""Tool registry: every tool module exposes TOOLS = [{name, description, parameters, handler}].
To add a new tool: create a module in this folder and add it to _MODULES below.
"""
import logging

from tools import (
    agency_tools, brief, browser_pilot, calendar_tools, crew_orchestrator, experience_tools, facebook_saved, gaza_shops,
    github_engine, gmail_tools, insights, jobs, memory_tools, network_tools, outreach, project_concat, reminders,
    self_evolution, server_ops, session_manager, skills_engine, social_gig_hunter, social_reach, tech_radar,
    video_assembler, voice_studio, web_reader, web_search, whatsapp_bridge, workspace_coder, youtube_tools,
)

log = logging.getLogger("tools")

_MODULES = [
    agency_tools, skills_engine, github_engine, workspace_coder, web_search, web_reader, network_tools, tech_radar,
    social_gig_hunter, session_manager, facebook_saved, whatsapp_bridge, browser_pilot, crew_orchestrator,
    project_concat, server_ops, self_evolution, video_assembler, voice_studio, gaza_shops, memory_tools, reminders,
    jobs, brief, experience_tools, insights, outreach, gmail_tools, calendar_tools, youtube_tools, social_reach,
]
_TOOLS = {t["name"]: t for m in _MODULES for t in m.TOOLS}


def schemas() -> list[dict]:
    """Tool descriptions for the AI (without the Python handlers)."""
    return [{k: t[k] for k in ("name", "description", "parameters")} for t in _TOOLS.values()]


async def run(name: str, args: dict) -> str:
    """Run a tool and always return text for the AI, even when it fails."""
    tool = _TOOLS.get(name)
    if not tool:
        return f"خطأ: ما في أداة اسمها {name}."
    log.info("Tool call: %s %s", name, args)
    try:
        return await tool["handler"](args)
    except Exception as e:
        log.exception("Tool %s failed", name)
        return f"خطأ أثناء تنفيذ الأداة {name}: {e}"
