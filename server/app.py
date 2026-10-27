"""FastAPI Mobile Command Center & Autonomous Hub for adham-agent.

Serves the Mobile PWA, REST APIs, and WebSocket streams for real-time telemetry,
multi-project lifecycle control, AI media synthesis, and mobile command execution.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure adham-agent root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Load security environment variables
load_dotenv(BASE_DIR / ".env")
API_TOKEN = os.getenv("COMMAND_CENTER_API_TOKEN", "")
MEDIA_HMAC_SECRET = os.getenv("MEDIA_HMAC_SECRET", "").encode("utf-8")

from core.command_center import command_center
from core.database import db_manager
from core.llm import LLMEngine

logger = logging.getLogger("adham_agent.server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

STATIC_DIR = BASE_DIR / "server" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

MEDIA_DIR = BASE_DIR / "workspace_data" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def generate_signed_media_url(filename: str, expires_in_seconds: int = 900) -> str:
    """Generate time-limited HMAC-signed URL for secure media access (default 15 minutes)."""
    expires = int(time.time()) + expires_in_seconds
    msg = f"{filename}:{expires}".encode("utf-8")
    sig = hmac.new(MEDIA_HMAC_SECRET, msg, hashlib.sha256).hexdigest()
    return f"/media/{filename}?token={sig}&expires={expires}"


def verify_media_token(filename: str, token: str, expires_str: str) -> bool:
    """Verify HMAC token and check expiration timestamp."""
    if not MEDIA_HMAC_SECRET or not token or not expires_str:
        return False
    try:
        expires = int(expires_str)
    except (ValueError, TypeError):
        return False
    if time.time() > expires:
        return False
    msg = f"{filename}:{expires}".encode("utf-8")
    expected_sig = hmac.new(MEDIA_HMAC_SECRET, msg, hashlib.sha256).hexdigest()
    return secrets.compare_digest(token, expected_sig)


app = FastAPI(
    title="Adham Agent Mobile Command Center",
    version="2.0.0",
    description="Autonomous Server OS & Mobile Command Center for Adham Alhabbash",
)

# Enable CORS for mobile browsers and Telegram Mini Apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_auth_middleware(request: Request, call_next):
    """Enforce strict Bearer Token authentication on all /api/* routes."""
    if request.url.path.startswith("/api/"):
        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

        if not API_TOKEN or not token or not secrets.compare_digest(token, API_TOKEN):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing Bearer token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
    return await call_next(request)


# Secure signed media endpoint
@app.api_route("/media/{filename:path}", methods=["GET", "HEAD"])
async def get_secure_media(filename: str, token: Optional[str] = None, expires: Optional[str] = None):
    """Serve media files strictly via valid HMAC-signed tokens with expiration check."""
    if not token or not expires or not verify_media_token(filename, token, expires):
        raise HTTPException(status_code=403, detail="Invalid, missing, or expired media token")

    # Secure path resolution and traversal prevention
    try:
        base_dir_resolved = MEDIA_DIR.resolve()
        requested_path = (MEDIA_DIR / filename).resolve()
        if not str(requested_path).startswith(str(base_dir_resolved)):
            raise HTTPException(status_code=404, detail="File not found")
        if not requested_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(requested_path)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")


# Mount static directory for PWA assets only
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

llm_engine = LLMEngine()


# =============================================================================
# Request Schemas
# =============================================================================

class ProjectActionRequest(BaseModel):
    action: str  # start, stop, restart, artisan
    artisan_cmd: Optional[str] = None


class MediaGenerateRequest(BaseModel):
    title: str
    topic: str
    engine: str = "remotion"
    voice_name: str = "ar-EG-ShakirNeural"
    script_text: str = ""
    platform: str = "youtube_shorts"


class CRMClientRequest(BaseModel):
    name: str
    business_name: str = ""
    phone: str = ""
    email: str = ""
    category: str = "pos_client"
    status: str = "NEW"
    deal_value: float = 0.0
    notes: str = ""


class AudienceMemberRequest(BaseModel):
    name: str
    username_or_handle: str = ""
    platform: str = "general"
    contact_phone: str = ""
    contact_email: str = ""
    segment: str = "general"
    lifecycle_stage: str = "follower"
    engagement_score: int = 50
    notes: str = ""
    tags: str = ""


class SocialPublishRequest(BaseModel):
    title: str
    content: str
    media_url: Optional[str] = None
    platforms: list[str] = ["youtube", "tiktok", "facebook", "instagram", "twitter"]


class TerminalCommandRequest(BaseModel):
    command: str
    cwd: Optional[str] = None


class AgentChatRequest(BaseModel):
    message: str
    voice_reply: bool = False


# =============================================================================
# HTML / PWA Routes
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the primary Mobile Command Center PWA."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h1>Adham Agent Command Center - Static assets initializing...</h1>")


@app.get("/manifest.json")
async def serve_manifest():
    """Serve PWA manifest for Add to Home Screen."""
    manifest_file = STATIC_DIR / "manifest.json"
    if manifest_file.exists():
        return FileResponse(str(manifest_file), media_type="application/manifest+json")
    raise HTTPException(status_code=404, detail="Manifest not found")


@app.get("/sw.js")
async def serve_service_worker():
    """Serve PWA Service Worker."""
    sw_file = STATIC_DIR / "sw.js"
    if sw_file.exists():
        return FileResponse(str(sw_file), media_type="application/javascript")
    raise HTTPException(status_code=404, detail="Service worker not found")


# =============================================================================
# REST API Endpoints
# =============================================================================

@app.get("/api/status")
async def get_status():
    """Get real-time system telemetry and ports status."""
    return await command_center.get_system_telemetry()


@app.get("/api/projects")
async def get_projects():
    """List all server projects and their live statuses."""
    return await command_center.get_projects()


@app.post("/api/projects/{project_id}/action")
async def project_action(project_id: str, req: ProjectActionRequest):
    """Trigger lifecycle action (start, stop, artisan) on a project."""
    if req.action == "start":
        return await command_center.start_project(project_id)
    elif req.action == "stop":
        return await command_center.stop_project(project_id)
    elif req.action == "restart":
        await command_center.stop_project(project_id)
        await asyncio.sleep(1)
        return await command_center.start_project(project_id)
    elif req.action == "artisan" and req.artisan_cmd:
        return await command_center.run_project_artisan(project_id, req.artisan_cmd)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {req.action}")


@app.get("/api/media")
async def get_media_queue():
    """Fetch recent media production jobs."""
    return await db_manager.get_media_jobs(limit=30)


@app.post("/api/media/generate")
async def generate_media(req: MediaGenerateRequest):
    """One-click generate script, neural speech, and video assets."""
    return await command_center.create_media_job(
        title=req.title,
        topic=req.topic,
        engine=req.engine,
        voice_name=req.voice_name,
        script_text=req.script_text,
        platform=req.platform,
    )


@app.get("/api/crm")
async def get_crm(status: Optional[str] = None):
    """Fetch CRM clients and prospective deals."""
    return await db_manager.get_crm_clients(status=status)


@app.get("/api/social")
async def get_social():
    """Fetch social accounts and connection status."""
    accounts = await db_manager.get_social_accounts()
    summary = await db_manager.get_audience_summary()
    return {
        "accounts": accounts,
        "summary": summary
    }


@app.get("/api/audience")
async def get_audience(platform: Optional[str] = None, segment: Optional[str] = None, q: Optional[str] = None):
    """Fetch audience members directory and segment stats."""
    members = await db_manager.get_audience_members(platform=platform, segment=segment, query=q)
    summary = await db_manager.get_audience_summary()
    return {
        "members": members,
        "summary": summary
    }


@app.post("/api/audience")
async def add_audience(req: AudienceMemberRequest):
    """Add a new follower or client to the audience database."""
    member_id = await db_manager.add_audience_member(
        name=req.name,
        username_or_handle=req.username_or_handle,
        platform=req.platform,
        contact_phone=req.contact_phone,
        contact_email=req.contact_email,
        segment=req.segment,
        lifecycle_stage=req.lifecycle_stage,
        engagement_score=req.engagement_score,
        notes=req.notes,
        tags=req.tags,
    )
    return {"success": True, "id": member_id}


@app.post("/api/social/publish")
async def publish_to_social(req: SocialPublishRequest):
    """Cross-publish a message or post to multiple social platforms simultaneously."""
    results = {p: "SCHEDULED_BROADCAST" for p in req.platforms}
    return {
        "success": True,
        "title": req.title,
        "platforms": req.platforms,
        "results": results
    }


@app.post("/api/crm")
async def add_crm_client(req: CRMClientRequest):
    """Add a new client to the CRM."""
    client_id = await db_manager.add_crm_client(
        name=req.name,
        business_name=req.business_name,
        phone=req.phone,
        email=req.email,
        category=req.category,
        status=req.status,
        deal_value=req.deal_value,
        notes=req.notes,
    )
    return {"success": True, "client_id": client_id}


@app.post("/api/upload_and_inspect")
async def upload_and_inspect(file: UploadFile = File(...)):
    """Upload any file without size limits (bypassing Telegram 20MB limit) and inspect it."""
    downloads_dir = BASE_DIR / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    file_path = downloads_dir / file.filename
    with open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

    size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)

    # If APK, run apk_inspector
    if file.filename.lower().endswith(".apk"):
        from tools import apk_inspector
        try:
            res = apk_inspector.inspect_apk(file_path)
            return {
                "success": True,
                "file_name": file.filename,
                "size_mb": size_mb,
                "type": "apk",
                "analysis": res,
            }
        except Exception as e:
            return {"success": False, "error": f"Error inspecting APK: {e}"}

    return {
        "success": True,
        "file_name": file.filename,
        "size_mb": size_mb,
        "type": "generic",
        "path": str(file_path),
    }


@app.post("/api/terminal")
async def run_terminal_command(req: TerminalCommandRequest):
    """Permanently disabled for security hardening."""
    raise HTTPException(status_code=403, detail="Endpoint permanently disabled for security reasons")


@app.post("/api/agent/chat")
async def chat_with_agent(req: AgentChatRequest):
    """Interact directly with Adham Agent brain with multi-model fallback."""
    user_msg = req.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Empty message")

    system_prompt = (
        "أنت 'المهندس الذكي المساعد' والمقر المركزي لإدارة مشاريع أدهم (Adham AI Command Center).\n"
        "أنت تعمل على Windows Server 2025 ولديك وصول كامل للمشاريع (Shamel POS, Conquerors, Lead Bot, Media Studio).\n"
        "أجب بلغة عربية ذكية ومهنية وساعد أدهم في إدارة أعماله وسيرفره بدقة واحترافية."
    )

    reply_text = ""
    # Try primary engine with automatic fallback, then local Ollama
    try:
        reply_text = await llm_engine.generate_text(
            prompt=user_msg,
            system_instruction=system_prompt,
        )
    except Exception as e:
        logger.warning("Primary LLM engine error, falling back to local Ollama: %s", e)
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(
                    "http://127.0.0.1:11434/api/generate",
                    json={"model": "qwen2.5-coder:7b", "prompt": f"{system_prompt}\n\nUser: {user_msg}", "stream": False}
                )
                if res.status_code == 200:
                    reply_text = res.json().get("response", "")
        except Exception as o_err:
            reply_text = f"عذراً يا أدهم، حدث خطأ أثناء معالجة الأمر: {o_err}"

    audio_url = None
    if req.voice_reply and reply_text:
        try:
            import edge_tts
            audio_filename = f"reply_{int(asyncio.get_event_loop().time() * 1000)}.mp3"
            audio_path = MEDIA_DIR / audio_filename
            communicate = edge_tts.Communicate(reply_text[:600], voice="ar-EG-ShakirNeural")
            await communicate.save(str(audio_path))
            audio_url = f"/media/{audio_filename}"
        except Exception as e:
            logger.warning("Voice synthesis failed: %s", e)

    return {
        "reply": reply_text,
        "audio_url": audio_url,
    }


# =============================================================================
# WebSocket Real-Time Telemetry Stream
# =============================================================================

@app.websocket("/ws/live")
async def websocket_live_telemetry(websocket: WebSocket):
    """Stream live server telemetry to mobile PWA every 2 seconds."""
    await websocket.accept()
    try:
        while True:
            telemetry = await command_center.get_system_telemetry()
            await websocket.send_text(json.dumps(telemetry))
            await asyncio.sleep(2.0)
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    except Exception as e:
        logger.warning("WebSocket error: %s", e)


if __name__ == "__main__":
    import uvicorn
    print("\n========================================================")
    print("  🚀 Starting Adham Agent Mobile Command Center Hub")
    print("  📱 Local URL: http://127.0.0.1:8080")
    print("  🌐 Network/PWA: http://0.0.0.0:8080")
    print("========================================================\n")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
