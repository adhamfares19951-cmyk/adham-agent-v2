"""Automated YouTube Data API v3 Publisher & Channel Analytics Tool.

Features:
- Handles YouTube Data API v3 OAuth2 credentials flow and persistent token storage.
- Resumable chunked upload with COPPA compliance (selfDeclaredMadeForKids=False).
- Automated #Shorts tagging for vertical short-form video reach.
- Safe Dry-Run Simulation mode when client_secrets.json is not yet configured.
- Channel analytics synchronization with SQLite database.
"""

from __future__ import annotations

import http.server
import json
import logging
import os
import shutil
import socket
import time
import urllib.parse
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaFileUpload

from config.settings import settings
from core.database import db_manager, DatabaseManager

logger = logging.getLogger("adham_agent.tools.youtube")

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly",
]


class YouTubeUploader:
    """YouTube Data API v3 integration with automated upload, token persistence, and dry-run safety."""

    def __init__(
        self,
        db: Optional[DatabaseManager] = None,
        client_secrets_file: Optional[str] = None,
        token_file: Optional[Path] = None,
    ) -> None:
        self.db = db or db_manager
        self.client_secrets_file = client_secrets_file or settings.YOUTUBE_CLIENT_SECRETS_FILE
        self.token_file = token_file or (settings.WORKSPACE_DATA_DIR / "youtube_token.json")
        self._service: Optional[Resource] = None

    def _get_client_secrets_path(self) -> Optional[Path]:
        """Resolve actual location of client_secrets.json on disk across all workspace locations."""
        candidates = [
            Path(self.client_secrets_file),
            settings.WORKSPACE_DATA_DIR / "client_secret.json",
            settings.WORKSPACE_DATA_DIR / "client_secrets.json",
            settings.WORKSPACE_DATA_DIR.parent / self.client_secrets_file,
            settings.WORKSPACE_DATA_DIR.parent / "client_secret.json",
            settings.WORKSPACE_DATA_DIR.parent / "client_secrets.json",
            settings.WORKSPACE_DATA_DIR.parent / "adham-agent" / "sessions" / "client_secret.json",
            settings.WORKSPACE_DATA_DIR.parent / "adham-agent" / "sessions" / "client_secrets.json",
            settings.WORKSPACE_DATA_DIR.parent / "adham-agent" / "client_secret.json",
            settings.WORKSPACE_DATA_DIR.parent / "adham-agent" / "client_secrets.json",
            Path.cwd() / "client_secret.json",
            Path.cwd() / "client_secrets.json",
            Path.cwd() / "adham-agent" / "sessions" / "client_secret.json",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        return None

    def _get_token_path(self) -> Path:
        """Resolve actual location of cached youtube_token.json on disk."""
        candidates = [
            self.token_file,
            settings.WORKSPACE_DATA_DIR / "youtube_token.json",
            settings.WORKSPACE_DATA_DIR.parent / "youtube_token.json",
            settings.WORKSPACE_DATA_DIR.parent / "adham-agent" / "sessions" / "youtube_token.json",
            settings.WORKSPACE_DATA_DIR.parent / "adham-agent" / "youtube_token.json",
            Path.cwd() / "adham-agent" / "sessions" / "youtube_token.json",
            Path.cwd() / "workspace_data" / "youtube_token.json",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        return self.token_file.resolve()

    def get_auth_status(self) -> Dict[str, Any]:
        """Inspect and report the exact authentication status and channel connectivity."""
        secrets_path = self._get_client_secrets_path()
        token_path = self._get_token_path()

        creds: Optional[Credentials] = None
        token_found = token_path.is_file()
        is_authenticated = False
        is_expired = False
        has_refresh_token = False
        channel_info: Optional[Dict[str, Any]] = None

        if token_found:
            try:
                creds = Credentials.from_authorized_user_file(str(token_path), YOUTUBE_SCOPES)
                has_refresh_token = bool(creds.refresh_token)
                is_expired = bool(creds.expired)

                if is_expired and has_refresh_token:
                    logger.info("Credentials expired. Auto-refreshing with Google OAuth2...")
                    creds.refresh(Request())
                    # Write updated token to both paths
                    token_path.write_text(creds.to_json(), encoding="utf-8")
                    dest_data_token = settings.WORKSPACE_DATA_DIR / "youtube_token.json"
                    dest_data_token.parent.mkdir(parents=True, exist_ok=True)
                    dest_data_token.write_text(creds.to_json(), encoding="utf-8")
                    is_expired = False

                is_authenticated = bool(creds.valid)
            except Exception as e:
                logger.warning("Error evaluating token: %s", e)
                creds = None

        mode = "DRY_RUN"
        if is_authenticated and creds:
            mode = "LIVE_PRODUCTION"
            try:
                service = build("youtube", "v3", credentials=creds)
                resp = service.channels().list(mine=True, part="snippet,statistics").execute()
                items = resp.get("items", [])
                if items:
                    snip = items[0].get("snippet", {})
                    stats = items[0].get("statistics", {})
                    channel_info = {
                        "title": snip.get("title"),
                        "channel_id": items[0].get("id"),
                        "subscriber_count": stats.get("subscriberCount"),
                        "video_count": stats.get("videoCount"),
                    }
            except Exception as ch_err:
                logger.warning("Could not query channel info: %s", ch_err)
        elif secrets_path:
            mode = "READY_TO_AUTHENTICATE"

        return {
            "mode": mode,
            "secrets_found": bool(secrets_path),
            "secrets_path": str(secrets_path) if secrets_path else None,
            "token_found": token_found,
            "token_path": str(token_path) if token_found else None,
            "is_authenticated": is_authenticated,
            "is_expired": is_expired,
            "has_refresh_token": has_refresh_token,
            "channel_info": channel_info,
        }

    def get_authenticated_service(self) -> Optional[Resource]:
        """Authenticate and return the YouTube API service object, or None if in dry-run mode."""
        if self._service is not None:
            return self._service

        token_path = self._get_token_path()
        creds: Optional[Credentials] = None

        # 1. Load cached token if available
        if token_path.is_file():
            try:
                creds = Credentials.from_authorized_user_file(str(token_path), YOUTUBE_SCOPES)
            except Exception as e:
                logger.warning("Could not load cached YouTube credentials from %s: %s", token_path, e)
                creds = None

        # 2. Refresh or trigger OAuth flow if needed
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired YouTube access token via refresh_token...")
                creds.refresh(Request())
                token_path.write_text(creds.to_json(), encoding="utf-8")
                dest_data_token = settings.WORKSPACE_DATA_DIR / "youtube_token.json"
                dest_data_token.parent.mkdir(parents=True, exist_ok=True)
                dest_data_token.write_text(creds.to_json(), encoding="utf-8")
            except Exception as e:
                logger.warning("Failed to refresh YouTube token: %s", e)
                creds = None

        if not creds or not creds.valid:
            secrets_path = self._get_client_secrets_path()
            if not secrets_path:
                logger.info("YouTube client secrets file not found. Operating in SAFE_DRY_RUN mode.")
                return None

            try:
                flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), YOUTUBE_SCOPES)
                creds = flow.run_local_server(port=0)
                token_path.parent.mkdir(parents=True, exist_ok=True)
                token_path.write_text(creds.to_json(), encoding="utf-8")
                dest_data_token = settings.WORKSPACE_DATA_DIR / "youtube_token.json"
                dest_data_token.parent.mkdir(parents=True, exist_ok=True)
                dest_data_token.write_text(creds.to_json(), encoding="utf-8")
            except Exception as e:
                logger.error("OAuth flow failed: %s. Reverting to SAFE_DRY_RUN mode.", e)
                return None

        self._service = build("youtube", "v3", credentials=creds)
        return self._service

    def switch_or_authenticate_channel(self, open_browser: bool = True) -> Dict[str, Any]:
        """Trigger an interactive browser OAuth2 flow to connect or switch to a new YouTube channel."""
        secrets_path = self._get_client_secrets_path()
        if not secrets_path or not secrets_path.is_file():
            raise FileNotFoundError(f"Client secrets file not found at {secrets_path}. Place client_secret.json first.")

        # Backup existing token if present
        token_path = self._get_token_path()
        if token_path.is_file():
            backup_file = token_path.parent / "youtube_token_previous_backup.json"
            shutil.copy2(token_path, backup_file)
            logger.info("Backed up prior token to %s", backup_file)

        logger.info("Launching OAuth2 flow with prompt='select_account' for YouTube channel switch...")

        class _OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress terminal clutter

            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)

                if "code" in params:
                    self.server.auth_response_path = self.path
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>YouTube Channel Connected</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 40px; text-align: center; max-width: 500px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5); }
        h1 { color: #22c55e; margin: 0 0 16px; font-size: 26px; }
        p { color: #94a3b8; font-size: 16px; line-height: 1.6; margin: 0 0 24px; }
        .badge { background: #0ea5e9; color: white; padding: 6px 16px; border-radius: 9999px; font-weight: 600; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>✓ YouTube Channel Connected!</h1>
        <p>Authentication token was successfully captured by <b>adham-agent</b>.<br>You can safely close this browser tab and return to the terminal.</p>
        <span class="badge">Fruit Drama Active 🍊🍓</span>
    </div>
</body>
</html>"""
                    self.wfile.write(html.encode("utf-8"))
                else:
                    # Ignore favicon.ico or stray browser exploratory requests
                    self.send_response(204)
                    self.end_headers()

        def find_free_port(start_port: int = 8080) -> int:
            for p in range(start_port, start_port + 20):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    if s.connect_ex(("127.0.0.1", p)) != 0:
                        return p
            return 8080

        port = find_free_port(8080)
        redirect_uri = f"http://localhost:{port}/"
        flow = InstalledAppFlow.from_client_secrets_file(
            str(secrets_path),
            YOUTUBE_SCOPES,
            redirect_uri=redirect_uri,
        )
        auth_url, _ = flow.authorization_url(prompt="select_account", access_type="offline")

        server = http.server.HTTPServer(("127.0.0.1", port), _OAuthCallbackHandler)
        server.auth_response_path = None
        server.timeout = 2.0

        if open_browser:
            webbrowser.open(auth_url, new=1, autoraise=True)

        logger.info("Listening on %s for OAuth2 callback...", redirect_uri)
        print(f"\n👉 If the browser does not open automatically, visit this URL:\n   {auth_url}\n")
        print(f"⏳ Waiting for account selection in browser (listening on {redirect_uri})...")

        start_time = time.time()
        timeout_seconds = 300  # 5 minutes
        while server.auth_response_path is None:
            server.handle_request()
            if time.time() - start_time > timeout_seconds:
                server.server_close()
                raise TimeoutError("Authentication timed out after 5 minutes.")

        auth_path = server.auth_response_path
        server.server_close()

        # oauthlib requires https in authorization_response
        full_auth_response = f"https://localhost:{port}{auth_path}"
        flow.fetch_token(authorization_response=full_auth_response)
        creds = flow.credentials

        # Save to both workspace locations
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

        dest_data_token = settings.WORKSPACE_DATA_DIR / "youtube_token.json"
        dest_data_token.parent.mkdir(parents=True, exist_ok=True)
        dest_data_token.write_text(creds.to_json(), encoding="utf-8")

        # Reset service instance and build fresh with new credentials
        self._service = build("youtube", "v3", credentials=creds)

        # Query newly connected channel info
        ch_resp = self._service.channels().list(mine=True, part="snippet,statistics").execute()
        items = ch_resp.get("items", [])
        ch_info = {}
        if items:
            snip = items[0].get("snippet", {})
            stats = items[0].get("statistics", {})
            ch_info = {
                "channel_id": items[0].get("id"),
                "title": snip.get("title"),
                "description": snip.get("description"),
                "subscriber_count": stats.get("subscriberCount"),
                "video_count": stats.get("videoCount"),
            }

        logger.info("Successfully connected to YouTube channel: %s (ID: %s)", ch_info.get("title"), ch_info.get("channel_id"))
        return {
            "status": "SUCCESS",
            "message": "Connected to new YouTube channel successfully",
            "channel": ch_info,
            "token_path": str(dest_data_token),
        }

    def update_channel_branding(
        self,
        description: str,
        keywords: str,
        default_language: str = "en",
    ) -> Dict[str, Any]:
        """Update channel description and SEO keywords via YouTube Data API v3 channels.update."""
        service = self.get_authenticated_service()
        if not service:
            logger.warning("Operating in DRY_RUN mode. Cannot update live channel branding.")
            return {
                "status": "SIMULATED_SUCCESS",
                "mode": "DRY_RUN",
                "description": description,
                "keywords": keywords,
                "notice": "Simulated branding update. Authenticate channel to apply live changes.",
            }

        # 1. Fetch channel ID and current branding
        resp = service.channels().list(mine=True, part="brandingSettings,id,snippet").execute()
        items = resp.get("items", [])
        if not items:
            raise RuntimeError("No authenticated YouTube channel found for this token.")

        channel_id = items[0]["id"]
        branding = items[0].get("brandingSettings", {})
        channel_settings = branding.get("channel", {})

        # 2. Apply new branding metadata
        channel_settings["description"] = description
        channel_settings["keywords"] = keywords
        channel_settings["defaultLanguage"] = default_language
        branding["channel"] = channel_settings

        body = {
            "id": channel_id,
            "brandingSettings": branding,
        }

        logger.info("Updating branding for channel ID %s...", channel_id)
        update_resp = service.channels().update(part="brandingSettings", body=body).execute()
        updated_branding = update_resp.get("brandingSettings", {}).get("channel", {})

        return {
            "status": "SUCCESS",
            "channel_id": channel_id,
            "title": items[0].get("snippet", {}).get("title"),
            "description": updated_branding.get("description"),
            "keywords": updated_branding.get("keywords"),
        }

    async def upload_video(
        self,
        video_id_in_db: int,
        file_path: str,
        title: str,
        description: str,
        tags: List[str],
        privacy_status: str = "public",
        publish_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a video to YouTube with resumable chunks and update database record."""
        path_obj = Path(file_path)
        if not path_obj.is_file():
            raise FileNotFoundError(f"Video file does not exist on disk: {file_path}")

        # Ensure #Shorts is in title and tags for vertical video reach
        formatted_title = title.strip()
        if "#Shorts" not in formatted_title and "#shorts" not in formatted_title:
            formatted_title = f"{formatted_title} #Shorts"

        formatted_tags = list(tags)
        for tag in ["Shorts", "Animation", "FruitDrama"]:
            if tag not in formatted_tags:
                formatted_tags.append(tag)

        # YouTube metadata payload
        body = {
            "snippet": {
                "title": formatted_title[:100],
                "description": description,
                "tags": formatted_tags,
                "categoryId": "24",  # Entertainment
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,  # Required for dramatic fruit channel
            },
        }

        if publish_at:
            body["status"]["publishAt"] = publish_at
            body["status"]["privacyStatus"] = "private"

        service = self.get_authenticated_service()

        # ---------------------------------------------------------------------
        # Dry-Run Simulation Mode (When client_secrets.json is not configured)
        # ---------------------------------------------------------------------
        if service is None:
            simulated_id = f"yt_sim_{uuid.uuid4().hex[:10]}"
            logger.info(
                "[DRY_RUN] YouTube Video #%d simulated upload: '%s' -> ID: %s",
                video_id_in_db,
                formatted_title,
                simulated_id,
            )
            await self.db.update_youtube_video_status(
                video_id=video_id_in_db,
                status="PUBLISHED_SIMULATED",
                video_path=str(path_obj.resolve()),
                youtube_video_id=simulated_id,
            )
            return {
                "status": "SIMULATED_SUCCESS",
                "mode": "DRY_RUN",
                "youtube_video_id": simulated_id,
                "video_url": f"https://youtube.com/shorts/{simulated_id}",
                "title": formatted_title,
                "file_path": str(path_obj),
                "notice": "Video validated and logged. Place client_secret.json to enable live uploads.",
            }

        # ---------------------------------------------------------------------
        # Real Production Upload Mode
        # ---------------------------------------------------------------------
        logger.info("Starting live resumable upload for video #%d: '%s'...", video_id_in_db, formatted_title)
        media = MediaFileUpload(
            str(path_obj),
            chunksize=1024 * 1024,
            resumable=True,
            mimetype="video/mp4",
        )

        request = service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info("Upload progress: %d%%", int(status.progress() * 100))

        actual_yt_id = response.get("id")
        logger.info("Video successfully published to YouTube! ID: %s", actual_yt_id)

        await self.db.update_youtube_video_status(
            video_id=video_id_in_db,
            status="PUBLISHED",
            video_path=str(path_obj.resolve()),
            youtube_video_id=actual_yt_id,
        )

        return {
            "status": "PUBLISHED",
            "mode": "LIVE",
            "youtube_video_id": actual_yt_id,
            "video_url": f"https://youtube.com/shorts/{actual_yt_id}",
            "title": formatted_title,
            "file_path": str(path_obj),
        }

    async def sync_channel_analytics(self) -> List[Dict[str, Any]]:
        """Query statistics for published videos and update the database."""
        videos = await self.db.get_youtube_videos(status="PUBLISHED", limit=50)
        if not videos:
            return []

        service = self.get_authenticated_service()
        if not service:
            logger.info("Analytics sync skipped (Safe Dry-Run mode active).")
            return [{"id": v["id"], "views": v.get("views", 0), "likes": v.get("likes", 0)} for v in videos]

        video_ids = [v["youtube_video_id"] for v in videos if v.get("youtube_video_id")]
        if not video_ids:
            return []

        response = service.videos().list(
            part="statistics",
            id=",".join(video_ids[:50]),
        ).execute()

        synced_results = []
        for item in response.get("items", []):
            yt_id = item["id"]
            stats = item.get("statistics", {})
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))

            # Match DB video record
            matched = next((v for v in videos if v["youtube_video_id"] == yt_id), None)
            if matched:
                await self.db.update_youtube_video_status(
                    video_id=matched["id"],
                    status="PUBLISHED",
                    views=views,
                    likes=likes,
                )
                synced_results.append({
                    "video_id": matched["id"],
                    "youtube_id": yt_id,
                    "views": views,
                    "likes": likes,
                })

        return synced_results


# Singleton instance
youtube_uploader = YouTubeUploader()
