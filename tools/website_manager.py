"""Website & Store Management Tools for Adham Agent.
Allows Telegram Bot & Autonomous Agency OS to:
1. List, add, and update products/services displayed on the web platform.
2. Monitor and review real-time client orders submitted through the website.
3. Manage store pricing, badges, and catalog descriptions directly from Telegram chat.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import memory

log = logging.getLogger("tools.website_manager")


# ==============================================================================
# Handlers & Operations
# ==============================================================================

async def list_website_products_handler(args: dict) -> str:
    """Returns a list of all products and services listed on the website store."""
    try:
        include_inactive = str(args.get("include_inactive", "false")).lower() in ("true", "1", "yes")
        products = memory.list_products(active_only=not include_inactive)

        if not products:
            return "📦 لا توجد أي منتجات أو خدمات معروضة في المتجر حالياً."

        from core.tunnel_manager import get_tunnel_manager
        tm = get_tunnel_manager()
        pub_url = tm.get_public_url()

        lines = [
            f"🛒 **قائمة منتجات وخدمات المتجر الإلكتروني ({len(products)} منتج):**",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        if pub_url:
            lines.append(f"🌐 **الرابط الخارجي المباشر:** {pub_url}\n")

        for p in products:
            feat_list = []
            try:
                feat_list = json.loads(p["features_json"])
            except Exception:
                pass

            status_icon = "🟢 نشط" if p["is_active"] else "⚪ معطل"
            badge_str = f" `{p['badge']}`" if p["badge"] else ""
            price_str = f"${p['price']:.0f}" if p["price"] > 0 else "حسب المتطلبات"

            lines.append(f"🔹 **#{p['id']} — {p['name']}**{badge_str}")
            lines.append(f"   📂 التصنيف: `{p['category']}` | 💵 السعر: **{price_str}** | الحالة: {status_icon}")
            lines.append(f"   📝 {p['description']}")
            if feat_list:
                feat_preview = " • ".join(feat_list[:3])
                lines.append(f"   ✨ المميزات: _{feat_preview}_")
            lines.append("")

        lines.append("💡 *لتعديل أو إضافة منتج، استخدم أداة add_or_update_product أو حدث السعر فورياً.*")
        return "\n".join(lines)
    except Exception as e:
        log.exception("Error listing store products: %s", e)
        return f"❌ خطأ أثناء جلب منتجات الموقع: {e}"


async def add_or_update_product_handler(args: dict) -> str:
    """Adds a new product/service or updates an existing one."""
    try:
        name = str(args.get("name", "")).strip()
        category = str(args.get("category", "خدمات برمجية")).strip()
        price = float(args.get("price", 0.0) or 0.0)
        description = str(args.get("description", "")).strip()
        badge = str(args.get("badge", "")).strip()
        product_id = args.get("product_id")
        if product_id:
            product_id = int(product_id)

        features = args.get("features")
        if isinstance(features, str) and features.startswith("["):
            try:
                features = json.loads(features)
            except Exception:
                features = [f.strip() for f in features.split(",") if f.strip()]
        elif isinstance(features, str) and "," in features:
            features = [f.strip() for f in features.split(",") if f.strip()]

        if not name or not description:
            return "❌ يرجى تقديم اسم المنتج/الخدمة (name) والوصف (description)."

        saved_id = memory.add_or_update_product(
            name=name,
            category=category,
            price=price,
            description=description,
            badge=badge,
            features=features,
            product_id=product_id,
        )

        action_type = "تحديث" if product_id else "إضافة"
        return (
            f"✅ **تم {action_type} المنتج بنجاح في قاعدة بيانات المتجر والموقع!**\n\n"
            f"• **رقم المنتج:** `#{saved_id}`\n"
            f"• **الاسم:** {name}\n"
            f"• **التصنيف:** {category}\n"
            f"• **السعر المعروض:** ${price:.0f}\n"
            f"• **الشارة:** {badge or 'بدون'}\n\n"
            f"🌐 *التعديل يظهر مباشرة على واجهة المنصة للزوار.*"
        )
    except Exception as e:
        log.exception("Error adding/updating product: %s", e)
        return f"❌ خطأ أثناء حفظ المنتج في المتجر: {e}"


async def list_client_orders_handler(args: dict) -> str:
    """Lists client orders received through the web platform."""
    try:
        status_filter = args.get("status")
        if status_filter:
            status_filter = status_filter.strip().lower()
            if status_filter in ("all", "الكل", "any"):
                status_filter = None

        limit = int(args.get("limit", 20) or 20)
        orders = memory.list_client_orders(status=status_filter, limit=limit)

        if not orders:
            msg = "📥 لا توجد أي طلبات واردة من الموقع حالياً"
            if status_filter:
                msg += f" بالحالة `{status_filter}`"
            return msg + "."

        lines = [
            f"📥 **طلبات العملاء الواردة من الموقع ({len(orders)} طلب):**",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]

        status_map = {
            "new": "🟡 جديد",
            "contacted": "🔵 تم التواصل",
            "in_progress": "🟣 قيد التنفيذ",
            "completed": "🟢 مكتمل",
            "cancelled": "🔴 ملغي",
        }

        for o in orders:
            st = status_map.get(o["status"], o["status"])
            lines.append(f"📦 **طلب #{o['id']} — {o['service_or_product']}** ({st})")
            lines.append(f"   👤 العميل: **{o['client_name']}** | 📱 هاتف: `{o['phone_whatsapp']}`")
            if o["details"]:
                lines.append(f"   📝 التفاصيل: {o['details']}")
            lines.append(f"   ⏰ التاريخ: `{o['created_at']}`\n")

        return "\n".join(lines)
    except Exception as e:
        log.exception("Error listing client orders: %s", e)
        return f"❌ خطأ أثناء استعراض طلبات العملاء: {e}"


# ==============================================================================
# Tool Registry Export
# ==============================================================================

TOOLS = [
    {
        "name": "list_website_products",
        "description": "استعراض كافة المنتجات والخدمات المعروضة في المتجر والموقع الإلكتروني الرسمي (الأسعار، الشارات، والحالة).",
        "parameters": {
            "type": "object",
            "properties": {
                "include_inactive": {"type": "boolean", "description": "هل يتم تضمين المنتجات المعطلة أيضاً؟ الافتراضي false."},
            },
        },
        "handler": list_website_products_handler,
    },
    {
        "name": "add_or_update_product",
        "description": "إضافة منتج أو خدمة جديدة للموقع والمتجر الإلكتروني أو تعديل سعره وشاراته ووصفه فورياً من داخل التلجرام.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "اسم المنتج أو الخدمة (مثل: باقة شامل POS السحابية)."},
                "category": {"type": "string", "description": "تصنيف المنتج (مثل: أنظمة محاسبة، ذكاء اصطناعي، شبكات)."},
                "price": {"type": "number", "description": "السعر بالدولار (0 إذا كان حسب المتطلبات)."},
                "description": {"type": "string", "description": "شرح تفصيلي ومقنع للمنتج والفوائد الملموسة للعميل."},
                "badge": {"type": "string", "description": "شارة ترويجية تظهر أعلى البطاقة (مثل: الأكثر طلباً 🔥)."},
                "features": {"type": "string", "description": "قائمة الميزات مفصولة بفواصل أو JSON Array."},
                "product_id": {"type": "integer", "description": "معرف المنتج (إذا كنت تريد تعديل منتج قائم بدلاً من إنشاء جديد)."},
            },
            "required": ["name", "description"],
        },
        "handler": add_or_update_product_handler,
    },
    {
        "name": "list_client_orders",
        "description": "استعراض طلبات العملاء الواردة من الموقع الإلكتروني (الاسم، الواتساب، الخدمة المطلوبة، والحالة).",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "تصفية حسب الحالة: new (جديد), contacted (تم التواصل), completed (مكتمل), all (الكل)."},
                "limit": {"type": "integer", "description": "العدد الأقصى للطلبات المسترجعة (الافتراضي 20)."},
            },
        },
        "handler": list_client_orders_handler,
    },
]
