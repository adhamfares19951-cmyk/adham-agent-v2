"""Adham Agent Web Platform & Official E-Commerce Store.
Built with FastAPI, TailwindCSS, Alpine.js, and Cairo typography.
Directly integrated with agent_memory.db, the Approval Queue, and Telegram Bot API alerts.
"""
from __future__ import annotations
import sqlite3

import json
import logging
import re
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse, Response
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

@app.middleware("http")
async def track_visitors_middleware(request: Request, call_next):
    path = request.url.path
    # Only track web pages, not static assets
    if not any(path.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".ico", ".svg", ".css", ".js", ".map"]):
        try:
            ip = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for") or (request.client.host if request.client else "")
            country = request.headers.get("cf-ipcountry", "Unknown")
            referer = request.headers.get("referer", "Direct")
            ua = request.headers.get("user-agent", "")[:200]
            
            with sqlite3.connect(memory.DB_PATH) as conn:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO site_visits (path, ip, country, referer, user_agent) VALUES (?, ?, ?, ?, ?)",
                    (path, ip, country, referer, ua)
                )
                conn.commit()
        except Exception:
            pass

    return await call_next(request)


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


@app.get("/glamp", response_class=HTMLResponse)
async def glamp_landing_page(request: Request):
    """Renders high-converting COD dropshipping landing page for G-Lamp 4-in-1."""
    base = _get_base_url()
    return templates.TemplateResponse(
        request=request,
        name="glamp_landing.html",
        context={"base_url": base},
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


@app.get("/logo")
async def get_logo_ai():
    """Returns the luxury 3D AI logo."""
    logo_path = BASE_DIR / "logo_ai.jpg"
    if logo_path.exists():
        return FileResponse(str(logo_path), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Logo not found")


@app.get("/logo-vector")
async def get_logo_vector():
    """Returns the clean vector badge logo."""
    logo_path = BASE_DIR / "logo_vector.png"
    if logo_path.exists():
        return FileResponse(str(logo_path), media_type="image/png")
    raise HTTPException(status_code=404, detail="Vector logo not found")


@app.get("/video")
async def get_ad_video():
    """Returns the latest ready-to-post 9:16 TikTok / Reels / Snap ad video."""
    vid_path = Path("C:/Projects/adham-agent/workspace_data/media/glamp_tiktok_angle2.mp4")
    if not vid_path.exists():
        vid_path = Path("C:/Projects/adham-agent/workspace_data/media/glamp_tiktok_final.mp4")
    if vid_path.exists():
        return FileResponse(str(vid_path), media_type="video/mp4", filename="glamp_ad_angle2.mp4")
    raise HTTPException(status_code=404, detail="Video not found")


@app.get("/media/{filename:path}")
async def get_media_file(filename: str):
    """Serves media files dynamically from workspace_data/media directory."""
    media_dir = Path("C:/Projects/adham-agent/workspace_data/media").resolve()
    file_path = (media_dir / filename).resolve()
    if not str(file_path).startswith(str(media_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    if file_path.exists() and file_path.is_file():
        media_type = "video/mp4" if file_path.suffix == ".mp4" else ("audio/mpeg" if file_path.suffix == ".mp3" else "application/octet-stream")
        return FileResponse(str(file_path), media_type=media_type, filename=file_path.name)
    raise HTTPException(status_code=404, detail="File not found")




def _get_base_url() -> str:
    return (memory.get_setting("public_web_url") or "http://127.0.0.1:8080").rstrip("/")



@app.get("/a8f3b2e7c9d14682b5e0f7193245cba8.txt", response_class=PlainTextResponse)
async def get_indexnow_key():
    """IndexNow search engine verification key file."""
    return PlainTextResponse("a8f3b2e7c9d14682b5e0f7193245cba8", media_type="text/plain")

@app.get("/robots.txt", response_class=PlainTextResponse)
async def get_robots_txt():
    """Search Engine crawling permissions & dynamic sitemap declaration."""
    base = _get_base_url()
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Allow: /glamp\n"
        "Allow: /logo\n"
        "Allow: /logo-vector\n"
        "Allow: /video\n"
        f"Sitemap: {base}/sitemap.xml\n"
    )
    return PlainTextResponse(content, media_type="text/plain")


@app.get("/sitemap.xml")
async def get_sitemap_xml():
    """Dynamic XML Sitemap for Google, Bing, and Search Engine indexers."""
    base = _get_base_url()
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>{base}/</loc>
    <lastmod>2026-10-27</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{base}/glamp</loc>
    <lastmod>2026-10-27</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
    <image:image>
      <image:loc>{base}/logo</image:loc>
      <image:title>مصباح G-Lamp الذكي 4 في 1</image:title>
    </image:image>
  </url>
</urlset>"""
    return Response(content=xml_content, media_type="application/xml")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "web_platform", "engine": "FastAPI"}


@app.get("/api/traffic")
async def get_site_traffic():
    """Returns live analytics on website visitors, pageviews, and visitor countries."""
    with sqlite3.connect(memory.DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM site_visits")
        total_views = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM site_visits WHERE path = '/glamp'")
        glamp_views = c.fetchone()[0]

        c.execute("SELECT COUNT(DISTINCT ip) FROM site_visits WHERE ip IS NOT NULL AND ip != '' AND ip != '127.0.0.1'")
        unique_ips = c.fetchone()[0]

        c.execute("SELECT path, ip, country, referer, created_at FROM site_visits ORDER BY id DESC LIMIT 10")
        recent = [
            {"path": r[0], "ip": r[1], "country": r[2], "referer": r[3], "time": r[4]}
            for r in c.fetchall()
        ]

        c.execute("SELECT COUNT(*) FROM client_orders")
        total_orders = c.fetchone()[0]

    return {
        "status": "success",
        "total_pageviews": total_views,
        "glamp_landing_views": glamp_views,
        "unique_external_visitors": unique_ips,
        "total_orders": total_orders,
        "recent_visitors": recent,
    }
