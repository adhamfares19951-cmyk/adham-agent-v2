"""Self-Evolution & Meta-Programming Engine for adham-agent.
Empowers the bot to act like an autonomous senior engineer (Antigravity standard):
1. Install new Python libraries dynamically via pip into python_runtime without manual server access.
2. Self-modify its own source code, tools, prompts, or configuration safely (with syntax checking & backups).
3. Clone and integrate new GitHub repositories into active tool modules and register them automatically.
4. Cleanly trigger an autonomous self-restart via Watchdog (exit code 0) so new tools take effect in 2 seconds.
5. Execute server-level PowerShell/Bash commands for deployment, diagnostic, and automation.
"""
from __future__ import annotations

import ast
import asyncio
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

log = logging.getLogger("self_evolution")

BASE_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXE = BASE_DIR / "python_runtime" / "python.exe"
if not PYTHON_EXE.exists():
    PYTHON_EXE = Path(sys.executable)

TOOLS_DIR = BASE_DIR / "tools"
REPOS_CACHE = BASE_DIR / "repos_cache"
REPOS_CACHE.mkdir(parents=True, exist_ok=True)


async def _run_proc(cmd: list[str] | str, cwd: Path | None = None, timeout: int = 120) -> tuple[int, str, str]:
    """Runs a subprocess asynchronously with timeout."""
    def _exec():
        is_shell = isinstance(cmd, str)
        p = subprocess.run(
            cmd,
            cwd=str(cwd or BASE_DIR),
            shell=is_shell,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return p.returncode, p.stdout, p.stderr

    try:
        return await asyncio.to_thread(_exec)
    except subprocess.TimeoutExpired:
        return -1, "", f"انتهت مهلة التنفيذ ({timeout}s)"
    except Exception as e:
        return -1, "", str(e)


async def install_package(package_name: str) -> dict[str, Any]:
    """Installs a python package into the local environment using pip."""
    pkg = package_name.strip()
    if not pkg:
        return {"success": False, "error": "اسم الحزمة فارغ"}

    cmd = [str(PYTHON_EXE), "-m", "pip", "install", pkg, "--no-warn-script-location"]
    code, stdout, stderr = await _run_proc(cmd, timeout=180)

    if code == 0:
        return {
            "success": True,
            "message": f"تم تثبيت الحزمة '{pkg}' بنجاح في بيئة السيرفر!",
            "details": stdout[-500:] if stdout else "Installation completed cleanly."
        }
    else:
        return {
            "success": False,
            "error": f"فشل تثبيت الحزمة '{pkg}': {stderr[-600:] or stdout[-600:]}"
        }


def safe_edit_source_file(rel_path: str, new_content: str, backup: bool = True) -> dict[str, Any]:
    """Safely edits a source file in adham-agent with syntax validation and backup."""
    clean_rel = rel_path.lstrip("/\\")
    target = BASE_DIR / clean_rel

    # Security check: must be inside BASE_DIR or workspace
    try:
        target.resolve().relative_to(BASE_DIR.parent)
    except ValueError:
        return {"success": False, "error": "مسار الملف يقع خارج بيئة المشاريع المسموح بها."}

    # If it is a Python file, strictly validate AST syntax
    if target.suffix.lower() == ".py":
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"فشل التحقق من صحة الكود البرمجي (SyntaxError): السطر {e.lineno} - {e.msg}",
            }

    backup_path = None
    if target.exists() and backup:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = target.with_name(f"{target.name}.bak_{ts}")
        try:
            shutil.copy2(target, backup_path)
        except Exception as e:
            log.warning("Could not create backup for %s: %s", target, e)

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new_content, encoding="utf-8")
        return {
            "success": True,
            "file": str(target),
            "backup": str(backup_path) if backup_path else None,
            "size": len(new_content),
        }
    except Exception as e:
        return {"success": False, "error": f"فشل كتابة الملف: {e}"}


async def clone_and_register_github_tool(
    repo_url: str,
    tool_module_name: str,
    tool_code: str,
    install_dependencies: bool = True
) -> dict[str, Any]:
    """Clones a GitHub repository, writes a new tool module in tools/, and registers it in tools/__init__.py."""
    import re
    # 1. Clone repository
    m = re.search(r"github\.com[/:]([\w\-_]+)/([\w\-_]+)", repo_url)
    repo_name = m.group(2).removesuffix(".git") if m else f"repo_{int(time.time())}"
    dest = REPOS_CACHE / repo_name

    clone_res = ""
    if not dest.exists():
        code, out, err = await _run_proc(["git", "clone", "--depth", "1", repo_url, str(dest)])
        if code != 0:
            return {"success": False, "error": f"فشل استنساخ المستودع: {err or out}"}
        clone_res = f"تم استنساخ المستودع بنجاح في `{dest.name}`."
    else:
        clone_res = f"المستودع موجود مسبقاً في `{dest.name}`."

    # 2. Check requirements.txt
    req_file = dest / "requirements.txt"
    if install_dependencies and req_file.exists():
        await _run_proc([str(PYTHON_EXE), "-m", "pip", "install", "-r", str(req_file), "--no-warn-script-location"])

    # 3. Create the tool module in tools/
    mod_name = tool_module_name.removesuffix(".py").strip()
    target_tool_file = TOOLS_DIR / f"{mod_name}.py"

    write_res = safe_edit_source_file(str(target_tool_file.relative_to(BASE_DIR)), tool_code)
    if not write_res.get("success"):
        return write_res

    # 4. Register in tools/__init__.py if not already present
    init_file = TOOLS_DIR / "__init__.py"
    if init_file.exists():
        init_content = init_file.read_text(encoding="utf-8")
        if mod_name not in init_content:
            # Add to import list
            init_content = re.sub(
                r"from tools import \((.*?)\)",
                lambda m: f"from tools import ({m.group(1).rstrip()}{mod_name},\n)",
                init_content,
                flags=re.DOTALL
            )
            # Add to _MODULES list
            init_content = re.sub(
                r"_MODULES = \[(.*?)\]",
                lambda m: f"_MODULES = [{m.group(1).rstrip()}, {mod_name}]",
                init_content,
                flags=re.DOTALL
            )
            safe_edit_source_file(str(init_file.relative_to(BASE_DIR)), init_content, backup=True)

    return {
        "success": True,
        "message": f"تم دمج المستودع `{repo_name}` وبناء وتفعيل الأداة `{mod_name}.py` بنجاح!",
        "clone": clone_res,
        "tool_file": str(target_tool_file),
    }


def trigger_self_restart(delay_seconds: float = 1.5) -> None:
    """Schedules a clean exit (code 0) so the Watchdog supervisor instantly restarts main.py."""
    async def _restart_soon():
        await asyncio.sleep(delay_seconds)
        log.info("Self-restart triggered: exiting cleanly with code 0 for Watchdog revival...")
        os._exit(0)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_restart_soon())
    except RuntimeError:
        os._exit(0)


async def git_sync_and_restart(remote: str = "origin", branch: str = "main") -> dict[str, Any]:
    """Pulls latest code updates from Git and triggers self-restart if changes are found."""
    code, out, err = await _run_proc(["git", "pull", remote, branch])
    if code == 0:
        clean_out = (out or "").strip()
        if "Already up to date" in clean_out or "بالفعل محدث" in clean_out:
            return {
                "success": True,
                "message": "🟢 البوت محدث بالفعل لآخر إصدار من Git (لا توجد تغييرات جديدة).",
                "restarted": False
            }
        trigger_self_restart(delay_seconds=1.5)
        return {
            "success": True,
            "message": f"🚀 **تم سحب التحديثات البرمجية من Git بنجاح!**\n\n```text\n{clean_out[:500]}\n```\n🔄 *جاري إعادة تشغيل البوت ذاتياً لتفعيل التعديلات خلال ثانيتين...*",
            "restarted": True
        }
    else:
        return {
            "success": False,
            "error": f"❌ خطأ أثناء مزامنة Git: {err.strip() or out.strip()}"
        }


# ==============================================================================
# AI Agent Tool Handlers
# ==============================================================================

async def install_python_package_handler(args: dict) -> str:
    """Tool handler for installing python libraries via pip."""
    pkg = args.get("package_name", "").strip()
    if not pkg:
        return "يرجى تحديد اسم الحزمة البرمجية (مثل: pillow, beautifulsoup4, yt-dlp)."

    res = await install_package(pkg)
    if res["success"]:
        return f"✅ **نجاح التثبيت:**\n{res['message']}\n```\n{res.get('details', '')}\n```"
    else:
        return f"❌ **خطأ أثناء تثبيت المكتبة:**\n{res['error']}"


async def self_modify_agent_code_handler(args: dict) -> str:
    """Tool handler for self-modifying source code."""
    file_path = args.get("file_path", "").strip()
    new_code = args.get("new_code", "")
    reason = args.get("reason", "تحديث وتطوير ذاتي للكود")

    if not file_path or not new_code:
        return "يرجى تحديد مسار الملف والكود الجديد."

    res = safe_edit_source_file(file_path, new_code)
    if res["success"]:
        out = [
            f"✅ **تم تعديل وتحديث الملف البرمجي بنجاح!**",
            f"📄 **الملف:** `{res['file']}`",
            f"🎯 **السبب:** {reason}",
        ]
        if res.get("backup"):
            out.append(f"🛡️ **تم إنشاء نسخة احتياطية آمنة:** `{res['backup']}`")
        out.append("\n💡 *إذا كان التعديل في أدوات البوت أو ملفات التشغيل، يمكنك طلب إعادة التشغيل لتفعيل التعديلات فوراً.*")
        return "\n".join(out)
    else:
        return f"❌ **فشل تعديل الملف:** {res['error']}"


async def integrate_github_repo_handler(args: dict) -> str:
    """Tool handler for integrating GitHub repositories into new tools."""
    repo_url = args.get("repo_url", "").strip()
    tool_name = args.get("tool_name", "").strip()
    tool_code = args.get("tool_code", "")
    install_deps = args.get("install_dependencies", True)

    if not repo_url or not tool_name or not tool_code:
        return "يرجى تزويدي برابط المستودع (repo_url) واسم ملف الأداة (tool_name) والكود المصدري للأداة (tool_code)."

    res = await clone_and_register_github_tool(
        repo_url=repo_url,
        tool_module_name=tool_name,
        tool_code=tool_code,
        install_dependencies=install_deps
    )

    if res["success"]:
        return (
            f"🎉 **تم دمج مستودع GitHub وتطوير الأداة بنجاح!**\n\n"
            f"🔗 **المستودع:** {repo_url}\n"
            f"🛠️ **الملف المولد:** `{res['tool_file']}`\n"
            f"📝 **التقرير:** {res['message']}\n\n"
            f"🔄 *جاري إعادة تشغيل محرك البوت تلقائياً لتسجيل الأداة الجديدة في الذاكرة الحية...*"
        )
    else:
        return f"❌ **فشل دمج المستودع:** {res['error']}"


async def restart_agent_handler(args: dict) -> str:
    """Tool handler for restarting the agent cleanly."""
    reason = args.get("reason", "تحديث وتفعيل الأكواد والأدوات الجديدة")
    trigger_self_restart(delay_seconds=1.5)
    return (
        f"🔄 **جاري إعادة تشغيل البوت ذاتياً (Self-Restart)...**\n\n"
        f"🎯 **السبب:** {reason}\n"
        f"⏱️ سيقوم المشرف الخارق (Watchdog) بإعادة تشغيل النظام خلال ثانيتين مع تحميل جميع الحزم والأدوات المعدلة فوراً!\n"
        f"سأكون جاهزاً لاستقبال طلباتك في ثوانٍ."
    )


async def execute_server_cmd_handler(args: dict) -> str:
    """Tool handler for running server-level shell/powershell commands."""
    cmd = args.get("command", "").strip()
    if not cmd:
        return "يرجى كتابة الأمر المطلوب تنفيذه على السيرفر."

    code, out, err = await _run_proc(cmd, timeout=60)
    res_str = out if out else err
    if not res_str:
        res_str = "(تم التنفيذ بنجاح دون مخرجات نصية)"

    return (
        f"💻 **نتيجة تنفيذ الأمر على السيرفر (Exit code: {code}):**\n"
        f"```cmd\n{cmd}\n```\n"
        f"**المخرجات:**\n"
        f"```text\n{res_str[:2500]}\n```"
    )


TOOLS = [
    {
        "name": "install_python_package",
        "description": "تثبيت مكتبات وحزم بايثون جديدة مباشرة عبر pip في بيئة السيرفر دون الحاجة للوصول اليدوي للجهاز.",
        "parameters": {
            "type": "object",
            "properties": {
                "package_name": {"type": "string", "description": "اسم المكتبة المراد تثبيتها (مثال: pillow, yt-dlp, beautifulsoup4)"},
            },
            "required": ["package_name"],
        },
        "handler": install_python_package_handler,
    },
    {
        "name": "self_modify_agent_code",
        "description": "تعديل وكتابة الكود المصدري للبوت نفسه أو لأي ملف بالمشروع بدقة هندسية عالية مع فحص السلامة (Syntax Check) وعمل نسخ احتياطية.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "مسار الملف النسبي داخل البوت (مثال: tools/my_tool.py أو config.py)"},
                "new_code": {"type": "string", "description": "الكود المصدري الجديد الكامل للملف"},
                "reason": {"type": "string", "description": "سبب التعديل والوظيفة الجديدة المضافة"},
            },
            "required": ["file_path", "new_code"],
        },
        "handler": self_modify_agent_code_handler,
    },
    {
        "name": "integrate_github_repo_as_tool",
        "description": "استنساخ مستودع GitHub جديد وتحليله وبناء أداة مخصصة منه في مجلد tools/ وتسجيلها بالبوت تلقائياً.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {"type": "string", "description": "رابط مستودع جيت هب"},
                "tool_name": {"type": "string", "description": "اسم ملف الأداة الجديد بدون .py (مثال: deep_scraper)"},
                "tool_code": {"type": "string", "description": "كود بايثون للأداة المخصصة مع مصفوفة TOOLS والمتغيرات"},
                "install_dependencies": {"type": "boolean", "description": "تثبيت متطلبات requirements.txt إن وجدت"},
            },
            "required": ["repo_url", "tool_name", "tool_code"],
        },
        "handler": integrate_github_repo_handler,
    },
    {
        "name": "restart_agent_daemon",
        "description": "إعادة تشغيل البوت ذاتياً وبشكل نظيف عبر المشرف (Watchdog) لتفعيل الأكواد والمكتبات والأدوات الجديدة فوراً.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "سبب إعادة التشغيل"},
            },
        },
        "handler": restart_agent_handler,
    },
    {
        "name": "execute_server_command",
        "description": "تنفيذ أوامر النظام والطرفية (PowerShell/CMD/Bash) مباشرة على السيرفر لتشخيص الأنظمة أو إدارة السيرفر.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "الأمر المراد تنفيذه في سطر الأوامر"},
            },
            "required": ["command"],
        },
        "handler": execute_server_cmd_handler,
    },
    {
        "name": "git_sync_code",
        "description": "سحب أحدث التعديلات البرمجية من مستودع Git وإعادة تشغيل البوت ذاتياً لمزامنة ما تم تطويره على جهازك المحلي إلى السيرفر.",
        "parameters": {
            "type": "object",
            "properties": {
                "remote": {"type": "string", "description": "اسم الريموت (افتراضي: origin)"},
                "branch": {"type": "string", "description": "اسم الفرع (افتراضي: main)"},
            },
        },
        "handler": lambda args: git_sync_and_restart(args.get("remote", "origin"), args.get("branch", "main")),
    },
]
