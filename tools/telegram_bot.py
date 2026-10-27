"""Autonomous Telegram Remote Control & Real-Time Notification Bot.

Features:
- Long-polling asynchronous Telegram Bot API controller using httpx.
- Secure single-owner access verification (authorized chat ID).
- Dedicated command handlers:
  • /start or /status: Displays live blackboard counters and connected YouTube channel.
  • /video <theme>: Autonomously authors Pixar fruit drama script and uploads the .docx storyboard to chat.
  • /hunt <keywords>: Discovers live leads, crafts tailored proposal, and uploads ATS .docx CV to chat.
  • /publish: Publishes ready .mp4 video in workspace_data/youtube_ready/ and returns live YouTube URL.
  • Natural Language Swarm: Directs any regular text to MasterBrain.execute_goal(text) and returns summary.
- Instant push notifications and document dispatch (send_notification & send_document) for sub-agents.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import httpx

from config.settings import settings
from core.database import db_manager

logger = logging.getLogger("adham_agent.tools.telegram")


class TelegramBotController:
    """Async Telegram Bot controller providing full remote control over the agent swarm."""

    def __init__(
        self,
        token: Optional[str] = None,
        owner_id: Optional[int] = None,
    ) -> None:
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"

        raw_owner = owner_id or int(os.getenv("TELEGRAM_CHAT_ID") or settings.OWNER_ID or 0)
        self.authorized_chat_ids: Set[int] = {raw_owner} if raw_owner > 0 else set()

        self._is_polling = False
        self._last_update_id = 0

    def is_authorized(self, chat_id: int) -> bool:
        """Check if incoming chat ID is authorized. Auto-registers first user if none set."""
        if not self.authorized_chat_ids:
            self.authorized_chat_ids.add(chat_id)
            logger.info("Auto-registered first sender as authorized owner: %s", chat_id)
            return True
        return chat_id in self.authorized_chat_ids

    async def get_me(self) -> Optional[Dict[str, Any]]:
        """Verify token and fetch bot identity via Telegram getMe API."""
        if not self.token:
            return None
        url = f"{self.base_url}/getMe"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("result", {})
                return None
        except Exception as e:
            logger.warning("Telegram getMe error: %s", e)
            return None

    # =========================================================================
    # 1. Low-Level API Methods (Send Message, Document, ChatAction)
    # =========================================================================

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send a text message with HTML formatting and optional inline keyboard."""
        url = f"{self.base_url}/sendMessage"
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200 and parse_mode:
                    # Retry without formatting if entity parsing failed
                    fallback_payload = dict(payload)
                    fallback_payload.pop("parse_mode", None)
                    resp = await client.post(url, json=fallback_payload)
                return resp.status_code == 200
        except Exception as e:
            logger.warning("Failed to send Telegram message to %s: %s", chat_id, e)
            return False

    async def send_chat_action(self, chat_id: int, action: str = "typing") -> None:
        """Broadcast user-friendly typing or uploading status."""
        url = f"{self.base_url}/sendChatAction"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(url, json={"chat_id": chat_id, "action": action})
        except Exception:
            pass

    async def send_document(
        self,
        file_path: Union[str, Path],
        caption: str = "",
        chat_id: Optional[int] = None,
    ) -> bool:
        """Upload a file (.docx, .md, .png, etc.) directly to Telegram chat."""
        target_path = Path(file_path)
        if not target_path.is_file():
            logger.warning("Cannot send non-existent document: %s", file_path)
            return False

        target_chat = chat_id or (list(self.authorized_chat_ids)[0] if self.authorized_chat_ids else None)
        if not target_chat:
            logger.warning("No authorized chat ID available to send document.")
            return False

        url = f"{self.base_url}/sendDocument"
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                with open(target_path, "rb") as f:
                    files = {"document": (target_path.name, f)}
                    data = {"chat_id": str(target_chat), "caption": caption, "parse_mode": "HTML"}
                    resp = await client.post(url, data=data, files=files)
                    return resp.status_code == 200
        except Exception as e:
            logger.warning("Failed to upload document %s to Telegram: %s", target_path.name, e)
            return False

    async def send_photo(
        self,
        file_path: Union[str, Path],
        caption: str = "",
        chat_id: Optional[int] = None,
    ) -> bool:
        """Upload a photo (.jpg, .png, etc.) directly as an inline image to Telegram."""
        target_path = Path(file_path)
        if not target_path.is_file():
            logger.warning("Cannot send non-existent photo: %s", file_path)
            return False

        target_chat = chat_id or (list(self.authorized_chat_ids)[0] if self.authorized_chat_ids else None)
        if not target_chat:
            logger.warning("No authorized chat ID available to send photo.")
            return False

        url = f"{self.base_url}/sendPhoto"
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                with open(target_path, "rb") as f:
                    files = {"photo": (target_path.name, f)}
                    data = {"chat_id": str(target_chat), "caption": caption, "parse_mode": "HTML"}
                    resp = await client.post(url, data=data, files=files)
                    return resp.status_code == 200
        except Exception as e:
            logger.warning("Failed to upload photo %s to Telegram: %s", target_path.name, e)
            return False

    async def send_notification(self, text: str, parse_mode: str = "HTML") -> None:
        """Push instant notification message to all authorized devices."""
        for cid in list(self.authorized_chat_ids):
            await self.send_message(chat_id=cid, text=text, parse_mode=parse_mode)

    # =========================================================================
    # 2. Command Handlers
    # =========================================================================

    def _get_keyboard_markup(self) -> Dict[str, Any]:
        """Generate interactive command buttons keyboard."""
        return {
            "keyboard": [
                [{"text": "🍌 Nano Banana Studio"}, {"text": "📊 Live Status"}],
                [{"text": "🎥 Cinematic 3D Short"}, {"text": "🎬 New Viral Short"}],
                [{"text": "🚀 Publish Video"}, {"text": "🥊 Fruit Fight"}],
                [{"text": "💼 Hunt Job Leads"}],
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
        }

    async def handle_start(self, chat_id: int) -> None:
        """Handle /start command with interactive dashboard keyboard."""
        welcome_msg = (
            "⚡ <b>ADHAM-AGENT Autonomous Digital Twin Online</b> ⚡\n\n"
            "Welcome Adham! Your autonomous multi-agent swarm is ready for remote dispatch:\n\n"
            "• <code>/banana &lt;theme&gt;</code> - 🍌 Autonomous Nano Banana Studio (Dola + Gemini Pro Veo + Concat)\n"
            "• <code>/cinema &lt;theme&gt;</code> - 🎥 Full 3D Pixar Cinematic Short (Multi-Cloud Auto-Failover)\n"
            "• <code>/video &lt;theme&gt;</code> - Generate viral 3D drama script + storyboard sheet\n"
            "• <code>/publish</code> - Auto-publish ready video to YouTube Shorts\n"
            "• <code>/status</code> - Live blackboard metrics & connected YouTube channel\n"
            "• <code>/hunt &lt;keywords&gt;</code> - Discover jobs & send tailored ATS .docx CV\n"
            "• <b>Any text in Arabic/English</b> - Dispatched to MasterBrain AI Swarm"
        )
        await self.send_message(chat_id=chat_id, text=welcome_msg, reply_markup=self._get_keyboard_markup())

    async def handle_status(self, chat_id: int) -> None:
        """Handle /status command displaying live database counters."""
        counts = await db_manager.get_dashboard_counts()
        yt_status = youtube_uploader.get_auth_status()

        ch_name = "Not Connected"
        if yt_status.get("channel_info"):
            ch_name = yt_status["channel_info"].get("title", "Connected")
        elif yt_status.get("mode") == "DRY_RUN":
            ch_name = "Simulation (Dry-Run)"

        status_msg = (
            "📊 <b>ADHAM-AGENT System Status</b>\n"
            "──────────────────────────\n"
            f"🎬 <b>Total Video Scripts:</b> {counts['total_videos']}\n"
            f"🚀 <b>Published Videos:</b> {counts['published_videos']}\n"
            f"💼 <b>Discovered Leads:</b> {counts['total_leads']}\n"
            f"📄 <b>ATS CVs Generated:</b> {counts['generated_cvs']}\n"
            f"⚡ <b>Pending Tasks:</b> {counts['pending_tasks']}\n"
            "──────────────────────────\n"
            f"📺 <b>YouTube Channel:</b> <code>{ch_name}</code>\n"
            f"🔐 <b>Uploader Mode:</b> <code>{yt_status['mode']}</code>\n"
            f"🤖 <b>Dual Engine:</b> <code>Gemini ({settings.GEMINI_MODEL}) + DeepSeek</code>\n"
            f"⏱️ <b>Server Time:</b> <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
        )
        await self.send_message(chat_id=chat_id, text=status_msg)

    async def handle_video(self, chat_id: int, theme: str) -> None:
        """Handle /video command: authors script and sends .docx storyboard to chat."""
        if not theme:
            theme = "Mr. Orange Betrayal and Ultimate Revenge"

        await self.send_chat_action(chat_id, action="typing")
        await self.send_message(chat_id, f"🎬 <b>Authoring Pixar 3D drama script for:</b> <i>'{theme}'</i>...")

        try:
            from agents.youtube_agent import youtube_agent
            result = await youtube_agent.generate_viral_package(theme=theme, target_scene_count=6)
            summary_msg = (
                "✅ <b>Viral Short Script Created!</b>\n"
                f"📌 <b>Title:</b> {result['title']}\n"
                f"🎯 <b>Theme:</b> {result['theme']}\n"
                f"🎥 <b>Scenes:</b> {len(result['scenes'])} beats\n"
                f"🪝 <b>Hook:</b> {result['hook_description'][:150]}..."
            )
            await self.send_message(chat_id, summary_msg)

            # Upload the generated DOCX storyboard to Telegram
            if result.get("storyboard_docx") and Path(result["storyboard_docx"]).is_file():
                await self.send_chat_action(chat_id, action="upload_document")
                await self.send_document(
                    file_path=result["storyboard_docx"],
                    caption=f"📑 Storyboard Production Sheet: #{result['video_id']} - {result['title'][:50]}",
                    chat_id=chat_id,
                )

            # Autonomous Remotion 60FPS Video Rendering Pipeline
            await self.send_chat_action(chat_id, action="upload_video")
            await self.send_message(
                chat_id,
                "⚙️ <b>جاري الآن تصيير الفيديو بالكامل بدقة 60FPS ومؤثرات الصوت...</b>\n"
                "⏱️ يستغرق تجهيز الفيديو قرابة 60-90 ثانية. سأرسله لك هنا فور جهوزه!"
            )
            try:
                from tools.motion_studio import generate_talking_fruit_short
                render_res = await generate_talking_fruit_short(topic=theme, character="orange", copy_to_ready=True)
                v_path = render_res.get("video_path")
                if v_path and Path(v_path).is_file():
                    await self.send_chat_action(chat_id, action="upload_document")
                    await self.send_document(
                        file_path=v_path,
                        caption=(
                            f"🎬 <b>فيديو الشورتس جاهز بين يديك!</b>\n"
                            f"📌 العنوان: {result['title'][:60]}\n"
                            f"📁 تم حفظه تلقائياً في مجلد <code>workspace_data/youtube_ready/</code>\n"
                            f"💾 الحجم: {render_res.get('size_mb')} MB | الجودة: 60FPS 9:16\n\n"
                            f"🚀 <b>لنشره فوراً على قناتك Fruity Toons 3D أرسل:</b> <code>/publish</code>"
                        ),
                        chat_id=chat_id,
                    )
            except Exception as r_err:
                logger.warning("Auto render video error: %s", r_err)
                await self.send_message(chat_id, f"⚠️ تنبيه تصيير الفيديو: {r_err}")

        except Exception as e:
            logger.error("Failed to generate video script via Telegram: %s", e)
            await self.send_message(chat_id, f"❌ <b>Error:</b> {e}")

    async def handle_cinema(self, chat_id: int, theme: str) -> None:
        """Handle /cinema command: autonomous multi-cloud 3D cinematic shorts production with auto-failover."""
        if not theme:
            theme = "مسكينة الفراولة: كفاح العمل والمفاجأة الملكية السعيدة"

        await self.send_chat_action(chat_id, action="typing")
        await self.send_message(
            chat_id,
            f"🎬 <b>بدء الإنتاج السينمائي فائق الدقة (3D Pixar / Multi-Cloud Pool)...</b>\n"
            f"📌 <b>الفكرة:</b> <i>'{theme}'</i>\n"
            f"⚡ يعمل النظام آلياً عبر مصفوفة السحابات مع ميزة التبديل التلقائي بدون توقف!"
        )

        try:
            from agents.youtube_agent import youtube_agent

            async def _progress(msg: str):
                await self.send_message(chat_id, msg)

            result = await youtube_agent.produce_and_render_full_short(
                theme=theme,
                target_scene_count=4,
                progress_callback=_progress,
            )

            v_path = result.get("video_path")
            if v_path and Path(v_path).is_file():
                await self.send_chat_action(chat_id, action="upload_video")
                file_mb = round(Path(v_path).stat().st_size / (1024 * 1024), 2)
                caption = (
                    f"🎬 <b>شورتس 3D سينمائي فائق الجودة جاهز بين يديك!</b>\n\n"
                    f"📌 <b>العنوان:</b> {result['title']}\n"
                    f"🎞️ <b>المشاهد:</b> {result.get('scenes_count', 4)} لقطات متحركة\n"
                    f"💾 <b>الحجم:</b> {file_mb} MB | 9:16 Vertical HD\n"
                    f"📁 تم حفظه تلقائياً في <code>workspace_data/youtube_ready/</code>\n\n"
                    f"🚀 <b>لنشره فوراً على قناتك Fruity Toons 3D أرسل:</b> <code>/publish</code>"
                )
                await self.send_document(
                    file_path=v_path,
                    caption=caption,
                    chat_id=chat_id,
                )
            else:
                await self.send_message(chat_id, f"⚠️ لم يتم العثور على ملف الفيديو الناتج: {result}")

        except Exception as e:
            logger.error("Failed to generate cinematic short: %s", e)
            await self.send_message(chat_id, f"❌ خطأ أثناء الإنتاج السينمائي: {e}")

    async def handle_banana_studio(self, chat_id: int, theme: str = "") -> None:
        """Handle /banana or /nano: triggers autonomous Dola + Gemini Pro Veo + Concat pipeline."""
        if not theme:
            theme = "البرتقالة المصدومة تكتشف خيانة الموزة مع التفاحة في المطعم الفاخر"

        await self.send_chat_action(chat_id, action="typing")
        await self.send_message(
            chat_id,
            f"🍌🎬 <b>استوديو Nano Banana الثلاثي قيد التشغيل!</b>\n\n"
            f"📌 <b>السيناريو:</b> <i>'{theme}'</i>\n"
            f"⚡ <b>الخطوات المنفذة آلياً:</b>\n"
            f"1️⃣ صياغة المشهد بنمط Seedane 2.5 30s\n"
            f"2️⃣ توليد الكي فريم الألترا 9:16 عبر Dola Web\n"
            f"3️⃣ تحريك المشهد عبر Google Veo بحساب Gemini Pro (Belal Hatb ⭐)\n"
            f"4️⃣ دمج ومونتاج المشاهد بمؤثرات Foley عبر FFmpeg Concat\n\n"
            f"⏱️ <i>انتظر قليلاً وجاري تحضير ورندرة الفيديو بالكامل...</i>"
        )

        try:
            from tools.autonomous_studio_pipeline import autonomous_studio

            async def _progress(step_msg: str):
                await self.send_message(chat_id, step_msg)

            v_path = await autonomous_studio.produce_full_banana_short(
                theme=theme,
                notify_cb=_progress,
            )

            if v_path and Path(v_path).is_file():
                await self.send_chat_action(chat_id, action="upload_video")
                file_mb = round(Path(v_path).stat().st_size / (1024 * 1024), 2)
                caption = (
                    f"🍌🎬 <b>فيديو Pixar 3D جاهز بين يديك بجودة استوديو Veo!</b>\n\n"
                    f"📌 <b>القصة:</b> {theme}\n"
                    f"💾 <b>الحجم:</b> {file_mb} MB | 9:16 Vertical HD (24fps)\n"
                    f"📁 تم حفظه تلقائياً في <code>workspace_data/youtube_ready/</code>\n\n"
                    f"🚀 <b>لنشره فوراً على قناتك أرسل:</b> <code>/publish</code>"
                )
                await self.send_document(
                    file_path=v_path,
                    caption=caption,
                    chat_id=chat_id,
                )
            else:
                await self.send_message(chat_id, f"⚠️ لم يتم العثور على ملف الفيديو الناتج: {v_path}")

        except Exception as e:
            logger.error("Failed to run banana studio via Telegram: %s", e)
            await self.send_message(chat_id, f"❌ خطأ أثناء تشغيل استوديو الموز والبرتقال: {e}")

    async def handle_fight(self, chat_id: int) -> None:
        """Handle /fight command: render an epic 3-round fruit wrestling battle."""
        await self.send_chat_action(chat_id, action="typing")
        await self.send_message(
            chat_id,
            "🥊 <b>جاري تصيير نزال مصارعة الفواكه الملحمي (3 جولات) بالكامل بدقة 60FPS...</b>\n"
            "⏱️ انتظر حوالي دقيقة وسأرسل لك الفيديو النهائي هنا!"
        )
        try:
            from tools.motion_studio import generate_fruit_fight_match
            res = await generate_fruit_fight_match(copy_to_ready=True)
            v_path = res.get("video_path")
            if v_path and Path(v_path).is_file():
                await self.send_chat_action(chat_id, action="upload_document")
                await self.send_document(
                    file_path=v_path,
                    caption=(
                        f"🏆 <b>نزال الفواكه الأسطوري جاهز!</b>\n"
                        f"📌 {res.get('title')}\n"
                        f"📁 تم حفظه في <code>workspace_data/youtube_ready/</code>\n"
                        f"💾 الحجم: {res.get('size_mb')} MB\n\n"
                        f"🚀 لنشره على قناتك Fruity Toons 3D أرسل: <code>/publish</code>"
                    ),
                    chat_id=chat_id,
                )
        except Exception as e:
            logger.error("Failed to render fight: %s", e)
            await self.send_message(chat_id, f"❌ خطأ في تصيير النزال: {e}")

    async def handle_hunt(self, chat_id: int, keywords_str: str) -> None:
        """Handle /hunt command: discovers leads, saves to DB, and sends tailored .docx CV."""
        keywords = [k.strip() for k in keywords_str.split(",") if k.strip()] if keywords_str else None

        await self.send_chat_action(chat_id, action="typing")
        await self.send_message(chat_id, "💼 <b>Searching live job feeds (Jobicy, Remotive, ReliefWeb)...</b>")

        try:
            from agents.hunter_agent import hunter_agent
            leads = await hunter_agent.discover_and_hunt(keywords=keywords, auto_propose_top=True)
            if not leads:
                await self.send_message(chat_id, "No matching leads found at this time.")
                return

            lead_msg = (
                f"✅ <b>Found {len(leads)} matching opportunities!</b>\n"
                f"Top Lead: <b>{leads[0]['title']}</b> ({leads[0].get('organization', 'Client')})\n"
                f"Platform: <code>{leads[0].get('platform', 'Feed')}</code>"
            )
            await self.send_message(chat_id, lead_msg)

            # If top lead auto-generated a CV, upload the docx file
            if "proposal_result" in leads[0]:
                p_res = leads[0]["proposal_result"]
                cv_file = p_res.get("cv_docx_path")
                if cv_file and Path(cv_file).is_file():
                    await self.send_chat_action(chat_id, action="upload_document")
                    await self.send_document(
                        file_path=cv_file,
                        caption=f"📄 Tailored ATS CV: {p_res['job_title']} (Match: {p_res['relevance_score']}%)",
                        chat_id=chat_id,
                    )
        except Exception as e:
            logger.error("Failed to hunt leads via Telegram: %s", e)
            await self.send_message(chat_id, f"❌ <b>Error:</b> {e}")

    async def handle_publish(self, chat_id: int) -> None:
        """Handle /publish command: publish ready video in youtube_ready."""
        await self.send_chat_action(chat_id, action="typing")
        from agents.youtube_agent import youtube_agent
        from tools.youtube_uploader import youtube_uploader
        ready_videos = await youtube_agent.check_ready_videos()
        if not ready_videos:
            await self.send_message(
                chat_id,
                "⚠️ <b>No .mp4 video found in <code>workspace_data/youtube_ready/</code>.</b>\n"
                "Render or drop a video file there first."
            )
            return

        target_video = ready_videos[0]
        await self.send_message(chat_id, f"🚀 <b>Publishing:</b> <code>{target_video['file_name']}</code>...")

        try:
            res = await youtube_uploader.upload_video(
                video_id_in_db=1,
                file_path=target_video["file_path"],
                title=f"Dramatic Fruit Animation {datetime.now().strftime('%d/%m')}",
                description="Viral Pixar 3D animated shorts drama. #Shorts #FruitDrama",
                tags=["Shorts", "Animation", "FruitDrama"],
            )

            msg = (
                f"🎉 <b>Video Published!</b>\n"
                f"<b>Status:</b> <code>{res['status']}</code> (Mode: {res['mode']})\n"
                f"<b>Video ID:</b> <code>{res['youtube_video_id']}</code>\n"
                f"🔗 <a href=\"{res['video_url']}\">Watch on YouTube</a>"
            )
            await self.send_message(chat_id, msg)
        except Exception as e:
            logger.error("Failed to publish video via Telegram: %s", e)
            await self.send_message(chat_id, f"❌ <b>Publishing Error:</b> {e}")

    async def handle_natural_language(self, chat_id: int, text: str) -> None:
        """Pass any natural language message directly to MasterBrain swarm."""
        await self.send_chat_action(chat_id, action="typing")
        await self.send_message(chat_id, f"🧠 <b>MasterBrain analyzing goal:</b>\n<i>'{text}'</i>...")

        try:
            from core.brain import master_brain
            results = await master_brain.execute_goal(text)
            task_list = results.get("results", [])

            lines = ["⚡ <b>Swarm Execution Complete:</b>"]
            docx_to_send: List[str] = []

            for item in task_list:
                status = "✓ SUCCESS" if item.get("status") == "COMPLETED" else "✗ FAILED"
                t_id = item.get("task_id", "")[:8]
                res_data = item.get("result", {})

                # Check for output artifacts to send
                if isinstance(res_data, dict):
                    if res_data.get("cv_docx_path"):
                        docx_to_send.append(res_data["cv_docx_path"])
                    if res_data.get("storyboard_docx"):
                        docx_to_send.append(res_data["storyboard_docx"])

                lines.append(f"• [<code>{t_id}</code>] {status}")

            await self.send_message(chat_id, "\n".join(lines))

            # Send any generated documents directly
            for docx_path in docx_to_send:
                if Path(docx_path).is_file():
                    await self.send_document(file_path=docx_path, chat_id=chat_id)

        except Exception as e:
            logger.error("Error executing goal via Telegram: %s", e)
            await self.send_message(chat_id, f"❌ <b>Execution Error:</b> {e}")

    # =========================================================================
    # 3. Message Routing & Polling Loop
    # =========================================================================

    async def _process_update(self, update: Dict[str, Any]) -> None:
        """Route incoming message or button callback."""
        msg = update.get("message")
        if not msg:
            return

        chat_id = msg.get("chat", {}).get("id")
        text = (msg.get("text") or "").strip()

        if not chat_id or not text:
            return

        # Security verification
        if not self.is_authorized(chat_id):
            logger.warning("Unauthorized access attempt by chat ID: %s", chat_id)
            await self.send_message(chat_id, "⛔ <b>Access Denied:</b> This bot is configured for private owner access.")
            return

        # Route commands
        if text.startswith("/start"):
            await self.handle_start(chat_id)
        elif text.startswith("/banana") or text.startswith("/nano") or text == "🍌 Nano Banana Studio":
            theme = text.replace("/banana", "").replace("/nano", "").replace("🍌 Nano Banana Studio", "").strip()
            await self.handle_banana_studio(chat_id, theme)
        elif text.startswith("/status") or text == "📊 Live Status":
            await self.handle_status(chat_id)
        elif text.startswith("/cinema") or text == "🎥 Cinematic 3D Short":
            theme = text.replace("/cinema", "").replace("🎥 Cinematic 3D Short", "").strip()
            await self.handle_cinema(chat_id, theme)
        elif text.startswith("/video") or text == "🎬 New Viral Short":
            theme = text.replace("/video", "").replace("🎬 New Viral Short", "").strip()
            await self.handle_video(chat_id, theme)
        elif text.startswith("/fight") or text == "🥊 Fruit Fight":
            await self.handle_fight(chat_id)
        elif text.startswith("/hunt") or text == "💼 Hunt Job Leads":
            kws = text.replace("/hunt", "").replace("💼 Hunt Job Leads", "").strip()
            await self.handle_hunt(chat_id, kws)
        elif text.startswith("/publish") or text == "🚀 Publish Video":
            await self.handle_publish(chat_id)
        else:
            await self.handle_natural_language(chat_id, text)

    async def start_polling(self) -> None:
        """Start long-polling loop fetching updates from Telegram."""
        if not self.token:
            logger.warning("No TELEGRAM_BOT_TOKEN found. Telegram bot controller disabled.")
            return

        self._is_polling = True
        logger.info("Telegram Bot controller polling started for bot token...")

        # Delete old webhook if present so getUpdates works reliably
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(f"{self.base_url}/deleteWebhook")
        except Exception:
            pass

        async with httpx.AsyncClient(timeout=35.0) as client:
            while self._is_polling:
                try:
                    url = f"{self.base_url}/getUpdates"
                    params = {
                        "offset": self._last_update_id + 1,
                        "timeout": 25,
                        "allowed_updates": ["message"],
                    }
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        updates = data.get("result", [])
                        for u in updates:
                            self._last_update_id = u["update_id"]
                            # Dispatch task asynchronously
                            asyncio.create_task(self._process_update(u))
                    elif resp.status_code in (401, 404):
                        logger.error("Telegram API token invalid (status %d). Stopping polling.", resp.status_code)
                        self._is_polling = False
                        break
                except httpx.TimeoutException:
                    pass
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.warning("Telegram polling error: %s. Reconnecting in 3s...", e)
                    await asyncio.sleep(3)

    def stop_polling(self) -> None:
        """Stop background polling loop."""
        self._is_polling = False
        logger.info("Telegram Bot polling stopped.")


# Singleton instance
telegram_bot = TelegramBotController()
