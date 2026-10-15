"""Project Packer & Concat Engine for adham-agent.
Inspired by jub0t/concat and repopack.
Packages any local project, folder, or repository files into a clean, unified Markdown document
optimized for LLMs, counting tokens, and allowing Adham to audit entire codebases from Telegram.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger("project_concat")

WORKSPACE_ROOT = Path("e:/Users/adham/Desktop/new")
PACKED_DIR = Path(__file__).resolve().parent.parent / "packed_projects"
PACKED_DIR.mkdir(parents=True, exist_ok=True)

IGNORE_DIRS = {
    "node_modules", "vendor", ".git", "build", ".dart_tool", "__pycache__",
    ".idea", ".vscode", "dist", "coverage", "storage", ".gradle", "wheels",
    "python_runtime", "tmp", "logs", "crash_dumps",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".pdf", ".exe", ".dll",
    ".so", ".dylib", ".zip", ".tar", ".gz", ".7z", ".mp4", ".mp3", ".wav",
    ".db", ".sqlite", ".sqlite3", ".pyc", ".whl", ".bin",
}


def concat_project_files(
    target_path: Path,
    extensions: list[str] | None = None,
    max_file_size_kb: int = 250
) -> dict[str, Any]:
    """Recursively scans and packs text files into a single unified Markdown text."""
    if not target_path.exists():
        raise FileNotFoundError(f"المسار '{target_path}' غير موجود.")

    packed_content: list[str] = []
    file_count = 0
    total_lines = 0
    total_bytes = 0

    clean_exts = [e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions] if extensions else None

    # Walk directory
    for root, dirs, files in os.walk(target_path):
        # In-place modify dirs to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

        for f in files:
            fpath = Path(root) / f
            suffix = fpath.suffix.lower()

            if suffix in BINARY_EXTENSIONS:
                continue

            if clean_exts and suffix not in clean_exts:
                continue

            try:
                size_kb = fpath.stat().st_size / 1024
                if size_kb > max_file_size_kb:
                    continue

                with open(fpath, "r", encoding="utf-8", errors="replace") as infile:
                    code = infile.read()

                rel_path = fpath.relative_to(target_path)
                lines = code.splitlines()
                line_count = len(lines)

                file_count += 1
                total_lines += line_count
                total_bytes += len(code.encode("utf-8"))

                packed_content.append(f"## 📄 File: `{rel_path}` ({line_count} lines, {size_kb:.1f} KB)\n")
                lang = suffix[1:] if suffix.startswith(".") else ""
                packed_content.append(f"```{lang}\n{code}\n```\n\n---\n")
            except Exception as e:
                log.warning("Could not read file %s: %s", fpath, e)

    # Estimate token count (~4 characters per token for code)
    estimated_tokens = total_bytes // 4
    project_name = target_path.name
    output_filename = f"{project_name}_packed.md"
    output_file = PACKED_DIR / output_filename

    header = (
        f"# 📦 Consolidated Project Codebase: `{project_name}`\n\n"
        f"- **Path:** `{target_path}`\n"
        f"- **Total Files Packed:** {file_count}\n"
        f"- **Total Lines of Code:** {total_lines:,}\n"
        f"- **Estimated Tokens:** ~{estimated_tokens:,} tokens\n"
        f"- **File Size:** {total_bytes / 1024:.1f} KB\n\n"
        f"---\n\n"
    )

    full_text = header + "".join(packed_content)

    with open(output_file, "w", encoding="utf-8") as out:
        out.write(full_text)

    return {
        "project_name": project_name,
        "output_file": str(output_file),
        "file_count": file_count,
        "total_lines": total_lines,
        "estimated_tokens": estimated_tokens,
        "size_kb": total_bytes / 1024,
    }


async def project_concat_handler(args: dict) -> str:
    """Tool handler for packaging and concating projects."""
    name_or_path = (args.get("project_name_or_path") or "").strip()
    exts = args.get("extensions")

    if not name_or_path:
        # List known workspace projects
        known = [
            "lead-preview-bot", "shamel_pos_app", "local_services_app",
            "adham-agent", "ai-engineering-from-scratch"
        ]
        return (
            "يرجى تحديد المشروع أو المسار المراد تجميعه. المشاريع الرئيسية في بيئة عملك:\n"
            + "\n".join(f"• `{p}`" for p in known)
            + "\n\n💡 مثال: `/concat lead-preview-bot php,blade.php`"
        )

    # Resolve target path
    target = Path(name_or_path)
    if not target.is_absolute():
        target = WORKSPACE_ROOT / name_or_path

    if not target.exists():
        return f"المسار '{target}' غير موجود. تأكد من صحة اسم المشروع."

    ext_list = None
    if isinstance(exts, str) and exts:
        ext_list = [e.strip() for e in exts.split(",") if e.strip()]
    elif isinstance(exts, list):
        ext_list = exts

    try:
        res = concat_project_files(target, extensions=ext_list)
        return (
            f"📦 **تم تجميع وفهرسة كود مشروع `{res['project_name']}` بنجاح (Concat Engine)!**\n\n"
            f"📊 **إحصائيات التجميع:**\n"
            f"• 📄 عدد الملفات المجمعة: **{res['file_count']} ملف**\n"
            f"• 📝 إجمالي أسطر الكود: **{res['total_lines']:,} سطر**\n"
            f"• 🪙 التوكنز المقدرة للذكاء الاصطناعي: **~{res['estimated_tokens']:,} Tokens**\n"
            f"• 💾 حجم الملف النهائي: **{res['size_kb']:.1f} KB**\n\n"
            f"📁 **مسار الملف المحفوظ:**\n`{res['output_file']}`\n\n"
            f"💡 *أصبح الملف جاهزاً بالكامل لتغذية أي نموذج ذكاء اصطناعي أو مراجعته من الجوال!*"
        )
    except Exception as e:
        return f"❌ خطأ أثناء تجميع المشروع: {e}"


TOOLS = [
    {
        "name": "pack_and_concat_project",
        "description": (
            "تجميع وضغط ملفات أي مشروع أو مجلد كود كامل في ملف واحد منسق (Concat / Repopack) "
            "مع احتساب التوكنز والأسطر وتجاهل مجلدات الكاش والمكتبات (vendor/node_modules) لتسهيل قراءته وفحصه عبر الـ AI."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "project_name_or_path": {
                    "type": "string",
                    "description": "اسم المشروع (مثل lead-preview-bot, shamel_pos_app) أو مساره",
                },
                "extensions": {
                    "type": "string",
                    "description": "امتدادات الملفات المطلوبة مفصولة بفواصل (مثل: dart أو php,blade.php أو py)",
                },
            },
            "required": ["project_name_or_path"],
        },
        "handler": project_concat_handler,
    }
]
