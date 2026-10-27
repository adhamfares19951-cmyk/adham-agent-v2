"""FastAPI Mobile Command Center & Autonomous Hub for adham-agent.

Serves the Mobile PWA, REST APIs, and WebSocket streams for real-time telemetry,
multi-project lifecycle control, AI media synthesis, and mobile command execution.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure adham-agent root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.command_center import command_center
from core.database import db_manager
from core.llm import LLMClient

logger = logging.getLogger("adham_agent.server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

STATIC_DIR = BASE_DIR / "dashboard" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

MEDIA_DIR = BASE_DIR / "workspace_data" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

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

# Mount media directory
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

llm_client = LLMClient()


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


@app.post("/api/terminal")
async def run_terminal_command(req: TerminalCommandRequest):
    """Execute PowerShell command directly from mobile Command Center."""
    return await command_center.execute_shell_command(req.command, cwd=req.cwd)


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
    # Try cloud models, fallback to Ollama
    try:
        if llm_client.has_deepseek:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ]
            reply_text = await llm_client.chat_deepseek(messages, max_tokens=1000)
        elif llm_client.has_gemini:
            full_prompt = f"{system_prompt}\n\nUser: {user_msg}"
            reply_text = await llm_client.generate_gemini(full_prompt)
        else:
            # Local Ollama fallback
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(
                    "http://127.0.0.1:11434/api/generate",
                    json={"model": "qwen2.5-coder:7b", "prompt": f"{system_prompt}\n\nUser: {user_msg}", "stream": False}
                )
                if res.status_code == 200:
                    reply_text = res.json().get("response", "")
    except Exception as e:
        logger.error("Error in AI chat: %s", e)
        reply_text = f"عذراً يا أدهم، حدث خطأ أثناء معالجة الأمر عبر الذكاء الاصطناعي: {e}"

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
