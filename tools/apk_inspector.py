"""Android APK Inspector & Security Auditor for adham-agent.
Analyzes Android APK packages (such as Shamel POS or client applications) to extract:
- Tech stack detection (Flutter, React Native, Native Kotlin/Java, Unity, Cordova)
- Target architecture ABIs (arm64-v8a, armeabi-v7a, x86_64)
- DEX count and approximate method/class footprint
- Declared permissions and security triage (dangerous vs normal permissions)
- App icon extraction and asset size breakdown.
"""
from __future__ import annotations

import logging
import os
import re
import zipfile
from pathlib import Path
from typing import Any

log = logging.getLogger("apk_inspector")

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "apk_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


DANGEROUS_PERMISSIONS = {
    "android.permission.READ_EXTERNAL_STORAGE": "قراءة ملفات الذاكرة الخارجية (حساس)",
    "android.permission.WRITE_EXTERNAL_STORAGE": "تعديل وكتابة ملفات الذاكرة الخارجية (حساس)",
    "android.permission.ACCESS_FINE_LOCATION": "تحديد الموقع الجغرافي الدقيق GPS",
    "android.permission.ACCESS_COARSE_LOCATION": "تحديد الموقع الجغرافي التقريبي",
    "android.permission.CAMERA": "الوصول للكاميرا (مطلوب للباركود)",
    "android.permission.RECORD_AUDIO": "تسجيل الصوت والميكروفون",
    "android.permission.READ_PHONE_STATE": "قراءة حالة الهاتف وهوية الشريحة",
    "android.permission.READ_CONTACTS": "قراءة جهات الاتصال (شديد الحساسية)",
    "android.permission.SYSTEM_ALERT_WINDOW": "الظهور فوق التطبيقات الأخرى (Overlay)",
    "android.permission.BLUETOOTH_CONNECT": "الاتصال بطابعات البلوتوث الحرارية (شامل POS)",
    "android.permission.BLUETOOTH_SCAN": "البحث عن أجهزة وبلوتوث مجاورة",
    "android.permission.INTERNET": "الاتصال بالإنترنت",
}


def inspect_apk(apk_path: str | Path) -> dict[str, Any]:
    """Analyzes an APK file and extracts technical metadata."""
    apk_file = Path(apk_path)
    if not apk_file.exists():
        raise FileNotFoundError(f"ملف APK غير موجود في المسار: {apk_file}")

    file_size_mb = apk_file.stat().st_size / (1024 * 1024)

    tech_stack = "Native (Java / Kotlin)"
    architectures = set()
    dex_files = []
    permissions = set()
    has_flutter = False
    has_react_native = False
    has_unity = False
    extracted_icon_path = None

    with zipfile.ZipFile(apk_file, "r") as zf:
        namelist = zf.namelist()

        # Check tech stack
        for name in namelist:
            if "libflutter.so" in name or "flutter_assets/" in name:
                has_flutter = True
            elif "libhermes.so" in name or "index.android.bundle" in name:
                has_react_native = True
            elif "libunity.so" in name:
                has_unity = True

            if name.startswith("lib/"):
                parts = name.split("/")
                if len(parts) >= 2 and parts[1]:
                    architectures.add(parts[1])

            if name.endswith(".dex"):
                dex_files.append(name)

        if has_flutter:
            tech_stack = "Flutter (Google UI Toolkit)"
        elif has_react_native:
            tech_stack = "React Native"
        elif has_unity:
            tech_stack = "Unity Game Engine"

        # Try to extract icon
        icon_candidates = [n for n in namelist if "ic_launcher" in n or "app_icon" in n or "icon.png" in n]
        if icon_candidates:
            # Prefer largest png
            best_icon = sorted(icon_candidates, key=lambda x: ("xxxhdpi" in x, "xxhdpi" in x, x.endswith(".png")), reverse=True)[0]
            icon_data = zf.read(best_icon)
            out_icon = OUTPUT_DIR / f"icon_{apk_file.stem}.png"
            out_icon.write_bytes(icon_data)
            extracted_icon_path = str(out_icon.resolve())

        # Inspect AndroidManifest.xml binary strings for permissions
        if "AndroidManifest.xml" in namelist:
            manifest_data = zf.read("AndroidManifest.xml")
            # Extract plain ASCII strings from binary XML
            matches = re.findall(b"android\\.permission\\.[A-Za-z0-9_]+", manifest_data)
            for m in matches:
                try:
                    permissions.add(m.decode("ascii"))
                except Exception:
                    pass

    dangerous_detected = []
    normal_detected = []
    for p in sorted(permissions):
        desc = DANGEROUS_PERMISSIONS.get(p, "")
        if desc and "حساس" in desc or "GPS" in desc or "كاميرا" in desc:
            dangerous_detected.append(f"{p} ({desc})")
        else:
            normal_detected.append(f"{p} ({desc})" if desc else p)

    return {
        "file_name": apk_file.name,
        "size_mb": round(file_size_mb, 2),
        "tech_stack": tech_stack,
        "architectures": list(architectures) or ["Universal / No native libs"],
        "dex_count": len(dex_files),
        "permissions_count": len(permissions),
        "dangerous_permissions": dangerous_detected,
        "normal_permissions": normal_detected,
        "icon_path": extracted_icon_path
    }


async def _handle_inspect_apk(args: dict) -> str:
    path = args.get("apk_path", "")
    if not path:
        return "يرجى تحديد مسار ملف الـ APK المراد فحصه."

    try:
        info = inspect_apk(path)
        arch_str = ", ".join(info["architectures"])
        dang_str = "\n".join(f"  ⚠️ {p}" for p in info["dangerous_permissions"]) or "  لا توجد صلاحيات خطيرة."
        norm_str = "\n".join(f"  ▫️ {p}" for p in info["normal_permissions"][:8]) or "  لا توجد صلاحيات عادية."
        if len(info["normal_permissions"]) > 8:
            norm_str += f"\n  ... و {len(info['normal_permissions']) - 8} صلاحيات أخرى."

        icon_msg = f"\n🖼️ **تم استخراج أيقونة التطبيق:** `{info['icon_path']}`" if info["icon_path"] else ""

        return (
            f"📱 **تقرير الفحص الشامل لملف الأندرويد ({info['file_name']}):**\n\n"
            f"• **الحجم:** {info['size_mb']} MB\n"
            f"• **التقنية البرمجية (Tech Stack):** 🚀 **{info['tech_stack']}**\n"
            f"• **المعماريات المدعومة (ABIs):** `{arch_str}`\n"
            f"• **ملفات الـ DEX:** {info['dex_count']} ملفات (Class bytecode)\n"
            f"• **إجمالي الصلاحيات:** {info['permissions_count']} صلاحية\n{icon_msg}\n\n"
            f"🔐 **الصلاحيات الحساسة والمهمة:**\n{dang_str}\n\n"
            f"📋 **أبرز الصلاحيات العادية:**\n{norm_str}"
        )
    except Exception as e:
        return f"❌ خطأ أثناء فحص ملف الـ APK: {e}"


TOOLS = [
    {
        "name": "inspect_apk_package",
        "description": "فحص وتفكيك ملفات تطبيقات الأندرويد (APK) واستخراج التقنية (Flutter أو React Native)، وحجم الملف، والمعماريات، والصلاحيات الحساسة، وأيقونة التطبيق.",
        "parameters": {
            "type": "object",
            "properties": {
                "apk_path": {"type": "string", "description": "المسار الكامل لملف الـ APK على الجهاز أو السيرفر"}
            },
            "required": ["apk_path"]
        },
        "handler": _handle_inspect_apk,
    }
]
