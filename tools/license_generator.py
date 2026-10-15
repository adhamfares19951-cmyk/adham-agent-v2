"""Offline Cryptographic License Generator for Shamel POS.
Generates mathematically verified, device-locked activation keys for merchants in Gaza and regional markets.
Works 100% offline inside the Flutter APK without requiring an active internet server.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any

log = logging.getLogger("license_generator")

# Secret signing salt for Shamel POS algorithm
_SECRET_KEY = b"shamel-pos-adham-alhabbash-2026-secure-master-seed"


def generate_license(
    merchant_name: str,
    device_id: str,
    duration_days: int = 365,
    is_lifetime: bool = False,
    features: list[str] | None = None,
) -> dict[str, Any]:
    """Generates an offline cryptographic activation license key."""
    if features is None:
        features = ["pos", "offline_db", "thermal_printer", "z_report", "whatsapp_invoicing"]

    now_ts = int(time.time())
    expiry_ts = 0 if is_lifetime else now_ts + (duration_days * 86400)
    expiry_str = "مدى الحياة (Lifetime)" if is_lifetime else time.strftime("%Y-%m-%d", time.localtime(expiry_ts))

    payload = f"{merchant_name.strip()}:{device_id.strip()}:{expiry_ts}:{','.join(sorted(features))}"
    signature = hmac.new(_SECRET_KEY, payload.encode("utf-8"), hashlib.sha256).hexdigest().upper()

    # Create formatted 16-character license string: SHAMEL-XXXX-XXXX-XXXX-XXXX
    key_part = signature[:16]
    formatted_key = f"SHAMEL-{key_part[0:4]}-{key_part[4:8]}-{key_part[8:12]}-{key_part[12:16]}"

    whatsapp_msg = (
        f"أهلاً بك في نظام **شامل POS** 🏪\n\n"
        f"عزيزنا التاجر: **{merchant_name}**\n"
        f"تم تفعيل ترخيصك بنجاح على جهازك رقم `{device_id[:8]}...`\n\n"
        f"🔑 **كود التفعيل الخاص بك:**\n"
        f"`{formatted_key}`\n\n"
        f"📅 **الصلاحية:** {expiry_str}\n"
        f"⚙️ **الميزات المفعلة:**\n" + "\n".join(f"  ✓ {f}" for f in features) + "\n\n"
        f"📌 *طريقة التفعيل:* افتح تطبيق شامل POS -> الإعدادات -> تفعيل الترخيص -> الصق الكود واضغط تفعيل.\n"
        f"📞 للدعم الفني والتدريب: م. أدهم الهباش"
    )

    return {
        "merchant_name": merchant_name,
        "device_id": device_id,
        "license_key": formatted_key,
        "expiry_date": expiry_str,
        "is_lifetime": is_lifetime,
        "features": features,
        "whatsapp_message": whatsapp_msg
    }


async def _handle_generate_license(args: dict) -> str:
    merchant = args.get("merchant_name", "متجر محلي")
    device_id = args.get("device_id", "ANDROID-DEMO-001")
    is_life = bool(args.get("is_lifetime", True))
    duration = int(args.get("duration_days", 365))

    res = generate_license(
        merchant_name=merchant,
        device_id=device_id,
        duration_days=duration,
        is_lifetime=is_life
    )

    return (
        f"🔑 **تم إصدار ترخيص شامل POS بنجاح!**\n\n"
        f"• **المتجر:** {res['merchant_name']}\n"
        f"• **معرف الجهاز:** `{res['device_id']}`\n"
        f"• **كود الترخيص:** `{res['license_key']}`\n"
        f"• **المدة:** {res['expiry_date']}\n\n"
        f"💬 **رسالة الواتساب الجاهزة للإرسال للتاجر:**\n\n"
        f"```text\n{res['whatsapp_message']}\n```"
    )


TOOLS = [
    {
        "name": "generate_shamel_pos_license",
        "description": "توليد كود ترخيص وتفعيل مشفر لتطبيق شامل POS يعمل أوفلاين 100% مرتبط بمعرف هاتف التاجر (Device ID) ومدته (سنة أو مدى الحياة)، مع رسالة واتساب جاهزة للإرسال.",
        "parameters": {
            "type": "object",
            "properties": {
                "merchant_name": {"type": "string", "description": "اسم المتجر أو التاجر"},
                "device_id": {"type": "string", "description": "معرف الجهاز (Android ID أو UUID) الظاهر في التطبيق"},
                "is_lifetime": {"type": "boolean", "description": "هل الترخيص مدى الحياة؟ (الافتراضي true)"},
                "duration_days": {"type": "integer", "description": "المدة بالأيام في حال كان الترخيص سنوياً"}
            },
            "required": ["merchant_name", "device_id"]
        },
        "handler": _handle_generate_license,
    }
]
