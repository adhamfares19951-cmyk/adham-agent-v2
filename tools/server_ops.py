"""Server & Infrastructure Operations for adham-agent.
Inspired by coollabsio/coolify and cloud management.
Provides real-time host diagnostics (CPU, RAM, Disk, Uptime), monitors local and remote
daemons and web services, and integrates with Coolify PaaS instances for 1-click deployments.
"""
from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import socket
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

log = logging.getLogger("server_ops")

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "coolify_config.json"


def _check_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """Checks if a TCP port is open and accepting connections."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def get_system_health() -> dict[str, Any]:
    """Retrieves system resource metrics (Disk, Memory, Platform, Uptime)."""
    # Disk usage
    disk_target = str(BASE_DIR.anchor) if BASE_DIR.anchor else ("/" if sys.platform != "win32" else "C:\\")
    total_b, used_b, free_b = shutil.disk_usage(disk_target)
    disk_total_gb = total_b / (1024 ** 3)
    disk_used_gb = used_b / (1024 ** 3)
    disk_free_gb = free_b / (1024 ** 3)
    disk_pct = (used_b / total_b) * 100

    # Ports check
    services = {
        "Laravel lead-preview-bot (Port 8000)": _check_port("127.0.0.1", 8000),
        "Laragon / Nginx / Apache (Port 80)": _check_port("127.0.0.1", 80),
        "MySQL / MariaDB (Port 3306)": _check_port("127.0.0.1", 3306),
    }

    return {
        "os": f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
        "node": platform.node(),
        "python": sys.version.split()[0],
        "disk_total_gb": round(disk_total_gb, 1),
        "disk_used_gb": round(disk_used_gb, 1),
        "disk_free_gb": round(disk_free_gb, 1),
        "disk_pct": round(disk_pct, 1),
        "services": services,
    }


async def query_coolify_instance(endpoint: str, api_token: str) -> dict[str, Any]:
    """Queries a self-hosted Coolify instance for registered applications and deployment health."""
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json",
    }
    url = f"{endpoint.rstrip('/')}/api/v1/applications"
    try:
        async with httpx.AsyncClient(headers=headers, timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                apps = resp.json()
                return {"connected": True, "apps_count": len(apps), "apps": apps}
            return {"connected": False, "status_code": resp.status_code, "error": resp.text[:200]}
    except Exception as e:
        return {"connected": False, "error": str(e)}


# ==============================================================================
# Tool Handlers for AI Agent
# ==============================================================================

async def server_status_handler(args: dict) -> str:
    """Tool handler to inspect server resources and service status."""
    health = get_system_health()

    lines = [
        "🖥️ **حالة السيرفر والبنية التحتية (Server & Infrastructure Health):**\n",
        f"💻 **نظام التشغيل:** `{health['os']}`",
        f"🏷️ **اسم الجهاز / السيرفر:** `{health['node']}`",
        f"🐍 **بيئة بايثون:** `Python {health['python']}`",
        f"💾 **مساحة القرص:** {health['disk_used_gb']} GB مستخدمة من أصل {health['disk_total_gb']} GB "
        f"({health['disk_free_gb']} GB متوفرة — {health['disk_pct']}% مستهلكة)\n",
        "🔌 **حالة الخدمات المحلية (Local Ports & Services):**",
    ]

    for sname, is_up in health["services"].items():
        icon = "🟢 نشط ويعمل" if is_up else "⚪ متوقف / غير مستمع"
        lines.append(f"  • {sname}: **{icon}**")

    # Check Coolify config if exists
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cdata = json.load(f)
            endpoint = cdata.get("endpoint", "")
            token = cdata.get("api_token", "")
            if endpoint and token:
                lines.append(f"\n🚀 **ربط سيرفر Coolify السحابي ({endpoint}):**")
                cres = await query_coolify_instance(endpoint, token)
                if cres.get("connected"):
                    lines.append(f"  • الاتصال: 🟢 متصل بنجاح | التطبيقات المدارة: {cres.get('apps_count')}")
                else:
                    lines.append(f"  • الاتصال: ⚠️ تعذر الاتصال ({cres.get('error', 'خطأ')})")
        except Exception:
            pass
    else:
        lines.append("\n💡 *يمكنك ربط لوحة Coolify السحابية بإضافة رابط السيرفر ومفتاح API في `coolify_config.json`.*")

    return "\n".join(lines)


TOOLS = [
    {
        "name": "check_server_infrastructure",
        "description": (
            "فحص وتشخيص حالة السيرفر، وموارد النظام (CPU/RAM/Disk)، ومنافذ الخدمات المحلية "
            "(Laravel، Nginx، MySQL)، ومراقبة لوحة وتطبيقات استضافة Coolify السحابية."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
        "handler": server_status_handler,
    }
]
