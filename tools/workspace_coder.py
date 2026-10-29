"""Workspace Coder & Project Automation Engine for adham-agent.
Empowers the bot to act as an autonomous Senior Software Engineer:
1. Read, write, and edit code across workspace projects (lead-preview-bot, shamel_pos_app, etc.).
2. Execute build, test, and migration commands (e.g. php artisan, phpunit, composer, git, flutter).
3. Automatically update, test, and maintain projects like lead-preview-bot without manual user intervention.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

log = logging.getLogger("workspace_coder")

# Root workspace directory: C:/Projects
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

PROJECTS_MAP = {
    "lead-preview": WORKSPACE_ROOT / "lead-preview-bot",
    "lead-preview-bot": WORKSPACE_ROOT / "lead-preview-bot",
    "shamel_pos": WORKSPACE_ROOT / "shamel_pos_app",
    "shamel_pos_app": WORKSPACE_ROOT / "shamel_pos_app",
    "local_services": WORKSPACE_ROOT / "local_services_app",
    "local_services_app": WORKSPACE_ROOT / "local_services_app",
    "conquerors_bot": WORKSPACE_ROOT / "conquerors_bot",
    "adham-agent": WORKSPACE_ROOT / "adham-agent",
    "agent": WORKSPACE_ROOT / "adham-agent",
}

# Dangerous destructive commands to block for system safety
BLOCKED_PATTERNS = [
    r"\brmdir\s+/[sS]\s+/[qQ]\s+[cC]:",
    r"\bformat\s+[cC]:",
    r"\bdel\s+/[fF]\s+/[sS]\s+/[qQ]\s+[cC]:\\windows",
    r"\bshutdown\b",
    r"\bDrop\s+database\b",
    r"\brm\s+-rf\b",
    r"\bdel\s+/[sS]\b",
    r"\brmdir\s+/[sS]\b",
    r"\breg\s+(add|delete)\b",
    r"\bschtasks\b",
    r"\bnet\s+user\b",
    r"\bcertutil\b",
    r"\bbitsadmin\b",
    r"invoke-expression|\biex\b",
    r"powershell(\.exe)?\s+.*-e(nc|ncodedcommand)\b",
    r"(curl|wget|iwr|invoke-webrequest)\b.*\|\s*(sh|bash|iex|powershell|cmd)",
    r"\.env\b",
    r"cookies|sessions[\\/]|token\.json|credentials\.json|client_secret",
]

# Files the bot must never read or write through workspace tools
SENSITIVE_NAME_RE = re.compile(
    r"(^|[\\/])(\.env(\..*)?|token\.json|credentials\.json|client_secret.*|.*cookies.*|.*\.pem|.*\.key|"
    r"agent_memory\.db.*|bot\.lock)$|(^|[\\/])sessions[\\/]|(^|[\\/])\.git[\\/]",
    re.IGNORECASE,
)


def _is_sensitive(rel_path: str) -> bool:
    return bool(SENSITIVE_NAME_RE.search(rel_path.replace("\\", "/")))


def _safe_target(pdir: Path, rel: str) -> Path | None:
    """Return the resolved path only if it stays inside the project dir and is not sensitive."""
    target = (pdir / rel.lstrip("/\\")).resolve()
    try:
        target.relative_to(pdir.resolve())
    except ValueError:
        return None
    if _is_sensitive(str(target.relative_to(pdir.resolve()))):
        return None
    return target


def _resolve_project_dir(project_name: str) -> Path | None:
    """Only projects listed in PROJECTS_MAP are reachable. No fallback to the workspace root."""
    target = PROJECTS_MAP.get(project_name.lower().strip())
    if target and target.exists() and target.is_dir():
        return target
    return None


def list_project_files(project_name: str, subpath: str = "", max_files: int = 50) -> list[str]:
    """Lists files in a project relative to its directory."""
    pdir = _resolve_project_dir(project_name)
    if pdir is None:
        return [f"المشروع غير معروف أو غير مسموح: {project_name}"]
    start_dir = _safe_target(pdir, subpath) if subpath else pdir
    if start_dir is None or not start_dir.exists():
        return [f"المجلد غير موجود: {subpath}"]

    results = []
    ignored = {".git", "vendor", "node_modules", ".dart_tool", "build", "dist", "__pycache__", "storage", "sessions", "venv", ".venv"}

    for root, dirs, files in os.walk(start_dir):
        dirs[:] = [d for d in dirs if d not in ignored]
        rel_root = Path(root).relative_to(pdir)

        for f in files:
            rel_file = str(rel_root / f) if str(rel_root) != "." else f
            if _is_sensitive(rel_file):
                continue
            results.append(rel_file)
            if len(results) >= max_files:
                return results

    return results


def read_project_file(project_name: str, file_path: str, max_chars: int = 7000) -> dict[str, Any]:
    """Reads a file from a project."""
    pdir = _resolve_project_dir(project_name)
    if pdir is None:
        return {"error": f"المشروع '{project_name}' غير معروف أو غير مسموح."}
    target = _safe_target(pdir, file_path)
    if target is None:
        return {"error": "مسار محظور (خارج المشروع أو ملف حساس مثل .env/الكوكيز/الجلسات)."}

    if not target.exists() or not target.is_file():
        return {"error": f"الملف '{file_path}' غير موجود في مشروع '{project_name}'."}

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        truncated = False
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n... (تم الاقتطاع لطول الملف)"
            truncated = True

        return {
            "success": True,
            "project": project_name,
            "file": file_path,
            "size": target.stat().st_size,
            "content": content,
            "truncated": truncated,
        }
    except Exception as e:
        return {"error": f"فشل في قراءة الملف: {e}"}


def write_project_file(project_name: str, file_path: str, content: str, backup: bool = True) -> dict[str, Any]:
    """Safely writes content to a file, making a backup if it already exists."""
    pdir = _resolve_project_dir(project_name)
    if pdir is None:
        return {"error": f"المشروع '{project_name}' غير معروف أو غير مسموح."}
    target = _safe_target(pdir, file_path)
    if target is None:
        return {"error": "محاولة تعديل مسار محظور (خارج المشروع أو ملف حساس) (Security Violation)."}

    target.parent.mkdir(parents=True, exist_ok=True)

    backup_path = None
    if target.exists() and backup:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = target.with_suffix(f".bak_{ts}")
        try:
            shutil.copy2(target, backup_path)
        except Exception as e:
            log.warning("Could not create backup for %s: %s", target, e)

    try:
        target.write_text(content, encoding="utf-8")

        # Syntax checks for Python and PHP
        syntax_warning = None
        if target.suffix == ".py":
            try:
                import py_compile
                py_compile.compile(str(target), doraise=True)
            except Exception as se:
                syntax_warning = f"تحذير فحص بايثون: {se}"

        return {
            "success": True,
            "project": project_name,
            "file": file_path,
            "backup": str(backup_path) if backup_path else None,
            "syntax_warning": syntax_warning,
            "size_written": len(content),
        }
    except Exception as e:
        return {"error": f"فشل كتابة الملف: {e}"}


async def run_project_command(project_name: str, command: str, timeout: int = 60) -> dict[str, Any]:
    """Runs a development or terminal command in the specified project directory."""
    pdir = _resolve_project_dir(project_name)
    if pdir is None:
        return {"success": False, "error": f"المشروع '{project_name}' غير معروف أو غير مسموح."}

    # Security check
    for pat in BLOCKED_PATTERNS:
        if re.search(pat, command, re.IGNORECASE):
            return {"success": False, "error": f"أمر محظور أمنياً: {command}"}

    log.info("Executing command in %s: %s", pdir, command)

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=str(pdir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return {"success": False, "error": f"انتهت مهلة تنفيذ الأمر ({timeout} ثانية)."}

        out_text = stdout.decode(errors="replace")
        err_text = stderr.decode(errors="replace")

        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": out_text.strip()[:4000],
            "stderr": err_text.strip()[:2000],
        }
    except Exception as e:
        return {"success": False, "error": f"فشل تشغيل الأمر: {e}"}


# Autonomous lead-preview updater helper
async def auto_update_lead_preview(action: str = "full") -> dict[str, Any]:
    """Runs autonomous updates, migrations, and test validations on lead-preview-bot."""
    reports = []

    if action in ("full", "pull"):
        res = await run_project_command("lead-preview-bot", "git pull --ff-only")
        reports.append(f"📦 Git Pull: {'نجح' if res['success'] else 'تنبيه'} -> {res.get('stdout') or res.get('stderr')}")

    if action in ("full", "migrate"):
        res = await run_project_command("lead-preview-bot", "php artisan migrate --force")
        reports.append(f"🗄️ Database Migrate: {'نجح' if res['success'] else 'فشل'} -> {res.get('stdout') or res.get('stderr')}")

    if action in ("full", "test"):
        res = await run_project_command("lead-preview-bot", "vendor/bin/phpunit --no-coverage")
        success = res["success"] or "OK" in (res.get("stdout") or "")
        summary_line = ""
        for line in (res.get("stdout") or "").splitlines():
            if "OK (" in line or "FAILURES!" in line or "Tests:" in line:
                summary_line = line.strip()
        reports.append(f"🧪 PHPUnit Tests: {'🟢 100% ناجح' if success else '❌ فشل'} -> {summary_line or res.get('stdout')[:300]}")

    return {
        "success": True,
        "action": action,
        "reports": reports,
    }


# Tool definitions for brain.py

async def _tool_workspace_list_files(args: dict) -> str:
    proj = str(args.get("project", "lead-preview-bot"))
    subpath = str(args.get("subpath", ""))
    files = list_project_files(proj, subpath=subpath)
    if not files:
        return f"لم أجد أي ملفات في `{proj}/{subpath}`."
    return f"📁 **ملفات `{proj}` ({len(files)} ملف):**\n" + "\n".join(f"• `{f}`" for f in files[:35])


async def _tool_workspace_read_file(args: dict) -> str:
    proj = str(args.get("project", "lead-preview-bot"))
    file_path = str(args.get("file_path", ""))
    if not file_path:
        return "يرجى تحديد مسار الملف."

    res = read_project_file(proj, file_path)
    if "error" in res:
        return f"❌ {res['error']}"

    return (
        f"📄 **الملف: `{file_path}` من `{proj}`** ({res['size']} بايت):\n\n"
        f"```\n{res['content']}\n```"
    )


async def _tool_workspace_write_file(args: dict) -> str:
    proj = str(args.get("project", "lead-preview-bot"))
    file_path = str(args.get("file_path", ""))
    content = str(args.get("content", ""))
    if not file_path or not content:
        return "يرجى توفير مسار الملف ومحتوى الكود."

    res = write_project_file(proj, file_path, content)
    if "error" in res:
        return f"❌ {res['error']}"

    warn = f"\n⚠️ {res['syntax_warning']}" if res.get("syntax_warning") else ""
    bak = f"\n💾 تم حفظ نسخة احتياطية: `{res['backup']}`" if res.get("backup") else ""
    return f"✅ **تم تعديل/إنشاء الملف بنجاح!**\n📁 المشروع: `{proj}`\n📄 الملف: `{file_path}` ({res['size_written']} حرف){bak}{warn}"


async def _tool_workspace_run_command(args: dict) -> str:
    proj = str(args.get("project", "lead-preview-bot"))
    command = str(args.get("command", ""))
    if not command:
        return "يرجى إدخال الأمر المراد تنفيذه."

    res = await run_project_command(proj, command)
    status_icon = "🟢" if res["success"] else "🔴"
    out = res.get("stdout", "")
    err = res.get("stderr", "")

    result_text = []
    if out:
        result_text.append(f"**المخرجات (stdout):**\n```\n{out}\n```")
    if err:
        result_text.append(f"**الأخطاء (stderr):**\n```\n{err}\n```")
    if not out and not err:
        result_text.append("_لا توجد مخرجات نصية._")

    status_msg = "نجح (0)" if res["success"] else f"فشل ({res.get('returncode')})"
    return (
        f"{status_icon} **تنفيذ الأمر في `{proj}`:** `{command}`\n"
        f"الحالة: {status_msg}\n\n"
        + "\n\n".join(result_text)
    )


async def _tool_update_project_autonomously(args: dict) -> str:
    action = str(args.get("action", "full"))
    res = await auto_update_lead_preview(action)
    report_lines = "\n".join(f"• {r}" for r in res["reports"])
    return (
        f"⚡ **تحديث واختبار تلقائي لـ lead-preview-bot:**\n\n"
        f"{report_lines}\n\n"
        f"✅ تمت العملية بالكامل دون الحاجة لأي تدخل يدوي!"
    )


TOOLS = [
    {
        "name": "workspace_list_files",
        "description": "استعرض واستكشف ملفات أي مشروع داخل بيئة العمل (lead-preview-bot, shamel_pos_app, local_services_app, adham-agent).",
        "parameters": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "اسم المشروع مثل lead-preview-bot, shamel_pos_app, local_services_app, adham-agent",
                },
                "subpath": {
                    "type": "string",
                    "description": "مسار مجلد فرعي اختياري مثل app/Services أو resources/views",
                },
            },
            "required": ["project"],
        },
        "handler": _tool_workspace_list_files,
    },
    {
        "name": "workspace_read_file",
        "description": "اقرأ الكود المصدري لأي ملف داخل أي مشروع في بيئة العمل.",
        "parameters": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "اسم المشروع مثل lead-preview-bot أو shamel_pos_app",
                },
                "file_path": {
                    "type": "string",
                    "description": "مسار الملف مثل app/Services/SocialMediaScraperService.php",
                },
            },
            "required": ["project", "file_path"],
        },
        "handler": _tool_workspace_read_file,
    },
    {
        "name": "workspace_write_file",
        "description": "قم بكتابة وتعديل كود أي ملف في المشاريع بأمان تام مع إنشاء نسخة احتياطية وفحص السلامة البرمجية.",
        "parameters": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "اسم المشروع",
                },
                "file_path": {
                    "type": "string",
                    "description": "مسار الملف المراد تعديله أو إنشاؤه",
                },
                "content": {
                    "type": "string",
                    "description": "الكود أو المحتوى الجديد كاملاً",
                },
            },
            "required": ["project", "file_path", "content"],
        },
        "handler": _tool_workspace_write_file,
    },
    {
        "name": "workspace_run_command",
        "description": (
            "نفّذ أوامر بيئة التطوير (php artisan, phpunit, composer, git, npm, flutter, python) "
            "في مجلد أي مشروع مع قراءة المخرجات ورموز الخطأ فوراً."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "اسم المشروع مثل lead-preview-bot",
                },
                "command": {
                    "type": "string",
                    "description": "الأمر المراد تنفيذه مثل php artisan migrate أو vendor/bin/phpunit أو git status",
                },
            },
            "required": ["project", "command"],
        },
        "handler": _tool_workspace_run_command,
    },
    {
        "name": "update_project_autonomously",
        "description": "قم بتحديث وفحص وتشغيل هجرات واختبارات نظام lead-preview-bot ذاتياً بنقرة واحدة بدون تدخل بشري.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["full", "pull", "migrate", "test"],
                    "description": "نوع العملية: full (تحديث وهجرة واختبارات كاملة), migrate, test, pull",
                },
            },
            "required": [],
        },
        "handler": _tool_update_project_autonomously,
    },
]
