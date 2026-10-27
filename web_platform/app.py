"""Adham Agent Web Platform & Official E-Commerce Store.
Built with FastAPI, TailwindCSS, Alpine.js, and Cairo typography.
Directly integrated with agent_memory.db, the Approval Queue, and Telegram Bot API alerts.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

import config
import memory
from tools.engineering_calculators import calculate_solar_system, format_solar_report

log = logging.getLogger("web_platform")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(
    title="Adham Agent Enterprise Web Platform & Store",
    description="Official web platform for Eng. Adham Alhabbash - Shamel POS, AI Agents, MikroTik & Solar Tech",
    version="2.0.0",
)

# Enable CORS for cross-origin API interactions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ==============================================================================
# Pydantic Schemas
# ==============================================================================

class SolarCalcRequest(BaseModel):
    load_watts: float = Field(..., ge=1, description="إجمالي الأحمال المستمرة بالواط")
    backup_hours: float = Field(..., ge=0.5, description="ساعات التشغيل الاحتياطية المطلوبة")
    system_voltage: float = Field(default=24.0, description="جهد بنك البطاريات (12, 24, 48 فولت)")
    panel_wattage: float = Field(default=400.0, description="قدرة اللوح الشمسي بالواط")


class OrderRequest(BaseModel):
    client_name: str = Field(..., min_length=2, description="اسم العميل أو الشركة")
    phone_whatsapp: str = Field(..., min_length=5, description="رقم الواتساب أو الهاتف للتواصل")
    service_or_product: str = Field(..., min_length=2, description="الخدمة أو المنتج المطلوب")
    details: str = Field(default="", description="أي تفاصيل أو متطلبات خاصة إضافية")


# ==============================================================================
# Telegram Real-time Dispatcher
# ==============================================================================

async def send_telegram_order_alert(order_data: dict[str, Any], order_id: int) -> bool:
    """Dispatches instant Telegram notification to OWNER_ID with direct WhatsApp link."""
    token = getattr(config, "TELEGRAM_TOKEN", None)
    owner_id = getattr(config, "OWNER_ID", None)
    if not token or not owner_id:
        log.warning("Telegram notification skipped: TELEGRAM_TOKEN or OWNER_ID is missing.")
        return False

    client_name = str(order_data.get("client_name", "عميل مجهول")).replace("*", "").replace("_", " ")
    phone = str(order_data.get("phone_whatsapp", "")).strip()
    service = str(order_data.get("service_or_product", "خدمة عامة")).replace("*", "").replace("_", " ")
    details = str(order_data.get("details", "")).strip().replace("*", "").replace("_", " ")

    # Format sanitized WhatsApp link
    clean_digits = re.sub(r"\D", "", phone)
    if clean_digits.startswith("059") or clean_digits.startswith("056"):
        clean_digits = "970" + clean_digits[1:]
    wa_link = f"https://wa.me/{clean_digits}" if clean_digits else "غير محدد"

    text = (
        "🛎️ **طلب جديد ورد عبر المنصة الإلكترونية (New Web Order)!**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔢 **رقم الطلب:** `#{order_id}`\n"
        f"👤 **اسم العميل:** {client_name}\n"
        f"📱 **رقم الواتساب:** `{phone}`\n"
        f"🎯 **الخدمة / المنتج:** *{service}*\n"
        f"📝 **التفاصيل:** {details if details else 'لا توجد ملاحظات إضافية'}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 **فتح محادثة واتساب مع العميل مباشرة:**\n"
        f"{wa_link}\n\n"
        "*(تم حفظ الطلب في قاعدة البيانات وإدراجه في طابور الموافقات)*"
    )

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": owner_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                },
            )
            if resp.status_code != 200:
                log.warning("Telegram order alert Markdown failed (status %s). Retrying plain text...", resp.status_code)
                plain_text = text.replace("**", "").replace("*", "").replace("`", "")
                resp2 = await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={
                        "chat_id": owner_id,
                        "text": plain_text,
                        "disable_web_page_preview": True,
                    },
                )
                return resp2.status_code == 200
            return True
    except Exception as e:
        log.exception("Error sending Telegram order alert: %s", e)
        return False


# ==============================================================================
# Web Routes
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """Ensure database and products are initialized on app start."""
    memory.init_db()
    log.info("Adham Agent Web Platform database initialized and verified.")


@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Renders the official enterprise platform homepage."""
    memory.init_db()
    raw_products = memory.list_products(active_only=True)

    products = []
    categories = set()
    for row in raw_products:
        feat = []
        try:
            feat = json.loads(row["features_json"])
        except Exception:
            pass
        p_dict = {
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "price": row["price"],
            "description": row["description"],
            "features": feat,
            "badge": row["badge"],
            "is_active": row["is_active"],
        }
        products.append(p_dict)
        categories.add(row["category"])

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "products": products,
            "categories": sorted(list(categories)),
            "bot_active": True,
        },
    )


@app.get("/api/products")
async def get_products_api():
    """Returns active products list as JSON."""
    raw = memory.list_products(active_only=True)
    out = []
    for r in raw:
        try:
            feat = json.loads(r["features_json"])
        except Exception:
            feat = []
        out.append({
            "id": r["id"],
            "name": r["name"],
            "category": r["category"],
            "price": r["price"],
            "description": r["description"],
            "features": feat,
            "badge": r["badge"],
        })
    return {"status": "success", "count": len(out), "products": out}


@app.post("/api/calc-solar")
async def calc_solar_api(req: SolarCalcRequest):
    """Zero-Hallucination live deterministic solar system calculation."""
    try:
        data = calculate_solar_system(
            load_watts=req.load_watts,
            backup_hours=req.backup_hours,
            system_voltage=req.system_voltage,
            panel_wattage=req.panel_wattage,
        )
        report_text = format_solar_report(data)
        return {
            "status": "success",
            "data": data,
            "report_markdown": report_text,
        }
    except Exception as e:
        log.exception("Solar API calculation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/order")
async def submit_order_api(req: OrderRequest):
    """Submits a new client order, saves to SQLite, enqueues to approval_queue, and alerts Telegram."""
    try:
        # 1. Save to client_orders table
        order_id = memory.create_client_order(
            client_name=req.client_name,
            phone_whatsapp=req.phone_whatsapp,
            service_or_product=req.service_or_product,
            details=req.details,
        )

        order_dict = {
            "order_id": order_id,
            "client_name": req.client_name,
            "phone_whatsapp": req.phone_whatsapp,
            "service_or_product": req.service_or_product,
            "details": req.details,
        }

        # 2. Add to approval_queue for governance
        memory.add_approval_item(
            action_type="client_order",
            description=f"طلب عميل جديد #{order_id}: {req.client_name} - {req.service_or_product}",
            payload=order_dict,
        )

        # 3. Instant Telegram notification to Owner
        telegram_sent = await send_telegram_order_alert(order_dict, order_id)

        return {
            "status": "success",
            "order_id": order_id,
            "message": "تم استلام طلبك بنجاح وسيتواصل معك المهندس أدهم الهباش فوراً عبر الواتساب.",
            "telegram_notified": telegram_sent,
        }
    except Exception as e:
        log.exception("Order submission error: %s", e)
        raise HTTPException(status_code=500, detail=f"تعذر تسجيل الطلب: {e}")


@app.get("/api/stats")
async def get_stats_api():
    """Returns platform and database statistics."""
    try:
        products = memory.list_products(active_only=True)
        orders = memory.list_client_orders()
        pending = memory.get_pending_approvals()
        return {
            "status": "success",
            "active_products": len(products),
            "total_orders": len(orders),
            "pending_approvals": len(pending),
            "server": "Adham Agent Enterprise OS (Online)",
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "web_platform", "engine": "FastAPI"}
