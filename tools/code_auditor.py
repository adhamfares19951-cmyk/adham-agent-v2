"""Code Security & Secret Leak Auditor for adham-agent.
Performs static security analysis on code files, repositories, and snippets before deployment:
- Scans for exposed API keys, private tokens, passwords, and database credentials
- Detects SQL injection risks, dangerous eval/exec calls, and unescaped inputs
- Checks for debug modes left enabled in production (APP_DEBUG=true, DEBUG=True)
- Issues a security grade (A+ to F) with remediation steps.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

log = logging.getLogger("code_auditor")

SECRET_PATTERNS = [
    (r"(?i)telegram[_-]?token\s*[:=]\s*['\"][0-9]{8,11}:[a-zA-Z0-9_-]{35}['\"]", "Telegram Bot Token"),
    (r"sk-[a-zA-Z0-9]{32,64}", "OpenAI API Key"),
    (r"sk-ant-[a-zA-Z0-9_-]{32,100}", "Anthropic Claude API Key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"(?i)password\s*[:=]\s*['\"][^'\"]{6,}['\"]", "Hardcoded Plaintext Password"),
    (r"(?i)(database|db)_url\s*[:=]\s*['\"][a-zA-Z0-9+]+://[^'\"]+['\"]", "Database Connection URL with Credentials"),
    (r"(?i)stripe[_-]?(secret|key)\s*[:=]\s*['\"]sk_(live|test)_[a-zA-Z0-9]{24,}['\"]", "Stripe Secret Key"),
]

VULN_PATTERNS = [
    (r"(?i)eval\s*\(", "Dangerous eval() execution (Code Injection risk)"),
    (r"(?i)exec\s*\(", "Dangerous exec() execution (Remote Code Execution risk)"),
    (r"(?i)select\s+.*\s+from\s+.*\s+where\s+.*(%s|\+)", "Raw SQL Concatenation (SQL Injection risk)"),
    (r"(?i)app_debug\s*=\s*true", "Laravel Debug Mode enabled (Information Disclosure risk)"),
    (r"(?i)debug\s*=\s*true", "Django/Flask Debug Mode enabled in code"),
]


def audit_text_security(code_text: str, filename: str = "snippet") -> dict[str, Any]:
    """Audits code text for security leaks and code smells."""
    findings = []
    
    # Check secrets
    for pat, label in SECRET_PATTERNS:
        matches = re.findall(pat, code_text)
        if matches:
            findings.append({
                "type": "credential_leak",
                "severity": "CRITICAL",
                "label": label,
                "file": filename,
                "count": len(matches)
            })

    # Check vulnerabilities
    for pat, label in VULN_PATTERNS:
        matches = re.findall(pat, code_text)
        if matches:
            findings.append({
                "type": "vulnerability",
                "severity": "HIGH",
                "label": label,
                "file": filename,
                "count": len(matches)
            })

    # Compute score
    critical_count = sum(1 for f in findings if f["severity"] == "CRITICAL")
    high_count = sum(1 for f in findings if f["severity"] == "HIGH")

    if critical_count > 0:
        grade = "F (خطر أمني حرج - مفاتيح مسربة)"
    elif high_count > 2:
        grade = "D (يحتاج مراجعة أمنية عاجلة)"
    elif high_count > 0:
        grade = "B (جيد مع وجود تنبيهات)"
    else:
        grade = "A+ (نظيف وآمن تماماً)"

    return {
        "filename": filename,
        "grade": grade,
        "critical_leaks": critical_count,
        "vulnerabilities": high_count,
        "findings": findings
    }


def audit_directory(path: str | Path, max_files: int = 50) -> dict[str, Any]:
    """Scans all code files in a folder or repository."""
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(f"المسار غير موجود: {root}")

    all_findings = []
    files_checked = 0

    if root.is_file():
        try:
            content = root.read_text(encoding="utf-8", errors="replace")
            res = audit_text_security(content, filename=root.name)
            return {
                "scanned_files": 1,
                "grade": res["grade"],
                "findings": res["findings"]
            }
        except Exception as e:
            return {"error": str(e)}

    # Scan directory recursively
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".py", ".php", ".js", ".ts", ".dart", ".env", ".json", ".sql", ".sh"):
            # skip node_modules, .git, venv
            if any(skip in p.parts for skip in (".git", "node_modules", "vendor", "venv", "__pycache__")):
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                res = audit_text_security(content, filename=str(p.relative_to(root)))
                if res["findings"]:
                    all_findings.extend(res["findings"])
                files_checked += 1
                if files_checked >= max_files:
                    break
            except Exception:
                pass

    critical_count = sum(1 for f in all_findings if f["severity"] == "CRITICAL")
    high_count = sum(1 for f in all_findings if f["severity"] == "HIGH")

    grade = "A+ (نظيف 100%)"
    if critical_count > 0:
        grade = "F (يحتوي تسريبات مفاتيح خطيرة)"
    elif high_count > 2:
        grade = "C (يحتاج سد ثغرات)"
    elif high_count > 0:
        grade = "B+ (آمن عموماً مع تنبيهات)"

    return {
        "scanned_files": files_checked,
        "grade": grade,
        "findings": all_findings
    }


async def _handle_audit(args: dict) -> str:
    target = args.get("target", ".")
    res = audit_directory(target)

    lines = [
        f"🛡️ **تقرير الفحص الأمني للأكواد (Security Audit):**\n",
        f"• **الملفات المفحوصة:** {res.get('scanned_files', 0)} ملفاً",
        f"• **التقييم الأمني العام:** **{res.get('grade', 'A')}**\n"
    ]

    findings = res.get("findings", [])
    if not findings:
        lines.append("🎉 **مبروك! الكود نظيف تماماً ولا يحتوي على أي مفاتيح مسربة أو ثغرات ظاهرة.**")
    else:
        lines.append("⚠️ **الملاحظات والثغرات المكتشفة:**")
        for f in findings[:10]:
            icon = "🚨" if f["severity"] == "CRITICAL" else "⚠️"
            lines.append(f"{icon} [{f['severity']}] `{f['file']}`: {f['label']}")

    return "\n".join(lines)


TOOLS = [
    {
        "name": "audit_code_security",
        "description": "فحص أمني وتحليل ثابت للأكواد والمشاريع والملفات لكشف تسريبات مفاتيح الـ API (OpenAI, AWS, Telegram, Stripe) وثغرات الـ SQL Injection واستدعاءات eval الخطيرة وإصدار بطاقة تقييم أمان (Scorecard).",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "المسار للملف أو المجلد المراد فحصه أمنياً"}
            },
            "required": ["target"]
        },
        "handler": _handle_audit,
    }
]
