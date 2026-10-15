"""MikroTik RouterOS Live Manager & Automation Engine for adham-agent.
Provides remote administration, configuration backups, health checks, and emergency script execution
for MikroTik RouterOS v6 and v7 devices (CCR, RB, hEX, Cloud Hosted Routers).
"""
from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("mikrotik_manager")

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUPS_DIR = BASE_DIR / "backups"
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)


def generate_ros_hardening_script() -> str:
    """Generates production-grade RouterOS v6/v7 security hardening commands."""
    return """# === MIKROTIK ROUTEROS HARDENING & FIREWALL (Adham Alhabbash Standard) ===
/ip firewall filter
add chain=input action=accept connection-state=established,related comment="Accept established/related"
add chain=input action=drop connection-state=invalid comment="Drop invalid connections"
add chain=input action=accept protocol=icmp comment="Allow ICMP (Ping)"
add chain=input action=accept protocol=tcp dst-port=8291,22 src-address-list=Safe_Admin comment="Allow WinBox/SSH to Admin"
add chain=input action=drop comment="Drop all other input traffic"

/ip firewall service-port
set telnet disabled=yes
set ftp disabled=yes
set www disabled=yes
set api disabled=yes
set api-ssl disabled=yes

/tool bandwidth-server set enabled=no
/ip dns set allow-remote-requests=no
"""


def generate_failover_script(isp1_gw: str = "192.168.1.1", isp2_gw: str = "192.168.2.1") -> str:
    """Generates dual-WAN recursive routing failover configuration."""
    return f"""# === DUAL WAN RECURSIVE FAILOVER (RouterOS v7) ===
/ip route
add dst-address=8.8.8.8/32 gateway={isp1_gw} scope=10 comment="ISP1 Check Link"
add dst-address=8.8.4.4/32 gateway={isp2_gw} scope=10 comment="ISP2 Check Link"
add dst-address=0.0.0.0/0 gateway=8.8.8.8 check-gateway=ping distance=1 target-scope=11 comment="Primary Default Route"
add dst-address=0.0.0.0/0 gateway=8.8.4.4 check-gateway=ping distance=2 target-scope=11 comment="Secondary Default Route"
"""


async def backup_mikrotik_config(
    host: str,
    user: str = "admin",
    password: str = "",
    port: int = 22,
) -> dict[str, Any]:
    """Connects to a remote MikroTik device via SSH and exports full configuration."""
    ts = int(time.time())
    backup_file = BACKUPS_DIR / f"mikrotik_backup_{host.replace('.', '_')}_{ts}.rsc"

    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        def _run_ssh():
            client.connect(hostname=host, port=port, username=user, password=password, timeout=8)
            stdin, stdout, stderr = client.exec_command("/export compact")
            output = stdout.read().decode("utf-8", errors="replace")
            client.close()
            return output

        export_data = await asyncio.to_thread(_run_ssh)
        backup_file.write_text(export_data, encoding="utf-8")

        return {
            "status": "success",
            "host": host,
            "backup_path": str(backup_file.resolve()),
            "file_size": backup_file.stat().st_size,
            "lines_count": len(export_data.splitlines()),
            "message": f"تم سحب وتصدير إعدادات ميكروتك بنجاح ({len(export_data.splitlines())} سطر)!"
        }
    except ImportError:
        # Fallback if paramiko is not installed: generate safe export command instructions
        return {
            "status": "instructions_only",
            "host": host,
            "command": "/export compact file=backup_adham",
            "message": "مكتبة SSH المباشرة غير مثبتة، يمكنك تنفيذ الأمر المباشر على الراوتر:\n`/export compact file=backup_adham`"
        }
    except Exception as e:
        log.warning("MikroTik SSH backup failed: %s", e)
        return {
            "status": "error",
            "host": host,
            "error": str(e),
            "message": f"فشل الاتصال بالراوتر `{host}`: {e}"
        }


async def _handle_mikrotik(args: dict) -> str:
    action = args.get("action", "hardening")
    host = args.get("host", "")

    if action == "backup" and host:
        res = await backup_mikrotik_config(
            host=host,
            user=args.get("user", "admin"),
            password=args.get("password", ""),
            port=int(args.get("port", 22))
        )
        if res["status"] == "success":
            return f"✅ **تم سحب النسخة الاحتياطية لميكروتك بنجاح!**\n• الراوتر: `{res['host']}`\n• المسار: `{res['backup_path']}`\n• الأسطر: {res['lines_count']} سطر"
        return f"⚠️ {res['message']}"

    elif action == "failover":
        script = generate_failover_script(
            isp1_gw=args.get("isp1_gw", "192.168.1.1"),
            isp2_gw=args.get("isp2_gw", "192.168.2.1")
        )
        return f"🌐 **سكربت ميكروتك للتحويل التلقائي بين خطين إنترنت (Dual WAN Failover):**\n\n```routeros\n{script}\n```\nقم بنسخه ولصقه في New Terminal مباشرة!"

    else:
        script = generate_ros_hardening_script()
        return f"🛡️ **سكربت تأمين وحماية راوتر ميكروتك (Firewall & Hardening):**\n\n```routeros\n{script}\n```\nيحمي المنفذ 8291 ويغلق المنافذ غير الضرورية ويمنع هجمات الـ Brute Force!"


TOOLS = [
    {
        "name": "manage_mikrotik_router",
        "description": "إدارة وحماية وأخذ نسخ احتياطية لسيرفرات وراوترات ميكروتك (RouterOS v6 & v7)، وتوليد سكربتات الطوارئ والـ Failover والـ Hardening.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["hardening", "failover", "backup"],
                    "description": "نوع العملية المطلوبة"
                },
                "host": {"type": "string", "description": "عنوان IP الراوتر للنسخ الاحتياطي"},
                "user": {"type": "string", "description": "اسم المستخدم (الافتراضي admin)"},
                "password": {"type": "string", "description": "كلمة المرور"},
                "port": {"type": "integer", "description": "منفذ SSH (الافتراضي 22)"},
                "isp1_gw": {"type": "string", "description": "جيت واي الخط الأول للـ Failover"},
                "isp2_gw": {"type": "string", "description": "جيت واي الخط الثاني للـ Failover"}
            },
            "required": ["action"]
        },
        "handler": _handle_mikrotik,
    }
]
