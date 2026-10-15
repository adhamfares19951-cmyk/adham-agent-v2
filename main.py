"""Telegram bot entry point. Run: python main.py"""
from __future__ import annotations

import io
import logging
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
import memory
from memory import init_db
import brain
import tts
from llm import LLMError
from tg_utils import send_long
from tools import brief, gaza_shops, gmail_tools, jobs, media, outreach, reminders, tech_radar

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("adham-agent")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "**أهلاً يا أدهم 👋 أنا دراعك اليمين — شريكك التقني والتنفيذي الخارق.**\n\n"
        "أنا جاهز لأي شيء تطلبه: كتابة، 🎤 فويس، 📷 صور شاشات وسيرفرات، أو 📄 ملفات PDF وسير ذاتية.\n\n"
        "⚡ **تقنية وشبكات:** توليد سكربتات ميكروتك RouterOS احترافية، حساب عناوين الـ Subnetting، فحص المنافذ والسيرفرات، وحل أعطال الويندوز والشبكات.\n"
        "🏪 **مبيعات غزة وشامل POS:** استكشاف محلات غزة وخانيونس بدون برامج، وتجهيز عروض ميدانية ورسائل تسويقية مقنعة لتطبيق شامل POS الأوفلاين.\n"
        "🎯 **رادار الفريلانس والمشاكل التقنية:** رصد مشاريع طلب البرامج وحل المشاكل على مستقل، خمسات، كفيل، وتويتر، وتجهيز عروض فائزة.\n"
        "🌐 **بحث إنترنت ذكي:** جلب أحدث الأخبار، أسعار العملات والذهب، والحلول التقنية الحديثة.\n"
        f"💼 **صيد الوظائف:** فحص قنوات ومواقع العمل في غزة وعن بعد كل {config.JOB_SCAN_MINUTES} دقيقة، وتجهيز رسائل تقديم.\n"
        "⏰ **تذكيرات ذكية وتقويم:** تذكير بالمواعيد، إدارة الإيميلات والتقويم.\n\n"
        "**الأوامر السريعة:**\n"
        "• `/skills [بحث]` — ترسانة الـ 480 مهارة في البرمجة والذكاء الاصطناعي\n"
        "• `/repo <رابط>` — فحص وتنزيل وقراءة أي مستودع GitHub فوراً\n"
        "• `/code [update/test]` — التحديث التلقائي الشامل لمشاريعك واختباراتها\n"
        "• `/saved [بحث]` — استعراض وبحث عناصرك المحفوظة على فيسبوك (137 عنصراً محفوظاً)\n"
        "• `/voice [نص]` — استوديو التعليق الصوتي العصبي (Neural TTS) بالذكاء الاصطناعي\n"
        "• `/video [عنوان | هوك | نص]` — استوديو إنتاج فيديوهات ريلز وتيك توك وشورتس 9:16 فورياً\n"
        "• `/image <prompt>` — توليد صور وتصاميم وبوسترات واقعية بمحرك FLUX.1 مجاناً\n"
        "• `/leads [نشاط] [مدينة]` — جلب العملاء المستخرجين وروابط المعاينة وعروض الواتساب\n"
        "• `/wa [phone]` — أتمتة الواتساب وتجهيز الفواتير وتقارير Z-Report لـ شامل POS\n"
        "• `/browser <url>` — المتصفح الآلي (Browser Pilot) لتصفح المواقع والتقاط صور شاشة\n"
        "• `/crew [crew_id]` — تشغيل طواقم الوكلاء الذكية (مبيعات، كودينج، فريلانس، ومحتوى)\n"
        "• `/concat <project>` — تجميع وفهرسة كود أي مشروع بالكامل في ملف واحد للـ AI\n"
        "• `/server` — فحص ومراقبة حالة السيرفر والمنافذ وخدمات Coolify السحابية\n"
        "• `/sessions` — حالة حساباتك وجلسات العمل المتصلة (مستقل، خمسات، فيسبوك، لينكد إن)\n"
        "• `/experts` — وكالة الخبراء (270 خبير متخصص في المبيعات، البرمجة، السيكيورتي، والتسويق)\n"
        "• `/gaza` — دليل وفرص محلات غزة وخانيونس وأنظمة شامل POS\n"
        "• `/update` — مزامنة وسحب آخر التعديلات البرمجية من Git وإعادة التشغيل ذاتياً\n"
        "• `/restart` — إعادة تشغيل محرك البوت ذاتياً لتطبيق التعديلات البرمجية فوراً\n"
        "• `/pip <package>` — تثبيت مكتبات وحزم بايثون جديدة بالسيرفر عبر pip فوراً\n"
        "• `/cmd <command>` — تنفيذ أوامر الطرفية وسطر الأوامر على السيرفر مباشرة\n"
        "• `/brief` — الموجز الصباحي الآن\n"
        "• `/jobs` — فحص الوظائف والفرص فوراً\n"
        "• `/reminders` — عرض تذكيراتك النشطة\n"
        "• `/pitch <رقم>` — تجهيز موقع تجريبي ورسالة تسويقية\n"
        "• `/reset` — مسح المحادثة وبدء جلسة جديدة"
    )
    await send_long(update, text)


async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    brain.reset()
    await update.effective_message.reply_text("تمام، مسحت المحادثة 🧹 بلّشنا من جديد.")


async def _synthesize(text: str) -> bytes | None:
    import asyncio
    return await asyncio.to_thread(tts.synthesize_ogg, text)


async def _answer(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, *, voice_reply: bool = False) -> None:
    msg = update.effective_message
    await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
    try:
        answer = await brain.reply(text)
    except LLMError as e:
        answer = e.user_message
    except Exception:
        log.exception("Unexpected error while replying")
        answer = "صار خطأ غير متوقع 😕 جرّب كمان مرة، وإذا تكرر ابعت الخطأ اللي بالشاشة السوداء."

    await send_long(update, answer)

    if voice_reply:
        try:
            ogg = await _synthesize(answer)
            if ogg:
                await msg.reply_voice(voice=io.BytesIO(ogg))
            else:
                log.info("Voice reply skipped (TTS unavailable this time)")
        except Exception:
            log.exception("Voice reply failed", exc_info=True)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or "").strip()
    if not text:
        return

    # Direct JSON interceptor for session/cookie imports (Cookie-Editor format)
    if (text.startswith("[") or text.startswith("{")) and any(k in text for k in ("domain", "expirationDate", "mostaqlweb")):
        from tools import session_manager
        detected_plat = "unknown"
        if "facebook.com" in text:
            detected_plat = "facebook"
        elif "mostaql.com" in text or "mostaqlweb" in text:
            detected_plat = "mostaql"
        elif "khamsat.com" in text:
            detected_plat = "khamsat"
        elif "x.com" in text or "twitter.com" in text:
            detected_plat = "twitter"
        elif "instagram.com" in text:
            detected_plat = "instagram"
        elif "linkedin.com" in text:
            detected_plat = "linkedin"
        elif "upwork.com" in text:
            detected_plat = "upwork"

        ok, msg = session_manager.save_cookies(detected_plat, text)
        if ok and detected_plat != "unknown":
            ver = await session_manager.verify_session(detected_plat)
            await update.effective_message.reply_text(f"{msg}\n\n{ver.get('message', '')}")
        else:
            await update.effective_message.reply_text(msg)
        return

    await _answer(update, context, text)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    audio = msg.voice or msg.audio
    if not audio:
        return

    await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
    try:
        tg_file = await audio.get_file()
        data = bytes(await tg_file.download_as_bytearray())
        file_name = getattr(audio, "file_name", None) or "voice.ogg"
        text = await media.transcribe(data, file_name=file_name)
    except media.MediaError as e:
        await msg.reply_text(e.user_message)
        return
    except Exception:
        log.exception("Voice handling failed")
        await msg.reply_text("ما قدرت أنزّل التسجيل 😕 جرّب كمان مرة.")
        return

    await msg.reply_text(f"🎤 سمعتك: {text}")
    prompt = f"[رسالة صوتية من أدهم، هاد نصها]: {text}"
    await _answer(update, context, prompt, voice_reply=True)


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Photos, videos, video notes, code files, zip archives, and documents."""
    msg = update.effective_message
    file_name = "file"
    is_code = False
    is_zip = False

    if msg.photo:
        tg_file = msg.photo[-1]
        mime = "image/jpeg"
        kind = "صورة"
    elif msg.video:
        tg_file = msg.video
        mime = tg_file.mime_type or "video/mp4"
        kind = "فيديو وتسجيل شاشة"
        file_name = getattr(tg_file, "file_name", "video.mp4") or "video.mp4"
    elif msg.video_note:
        tg_file = msg.video_note
        mime = "video/mp4"
        kind = "مقطع فيديو دائري (Video Note)"
        file_name = "video_note.mp4"
    elif msg.animation:
        tg_file = msg.animation
        mime = tg_file.mime_type or "video/mp4"
        kind = "مقطع متحرك GIF/فيديو"
        file_name = getattr(tg_file, "file_name", "animation.mp4") or "animation.mp4"
    elif msg.document:
        doc = msg.document
        mime = (doc.mime_type or "").lower()
        file_name = doc.file_name or "file.bin"
        ext = Path(file_name).suffix.lower()

        CODE_EXTS = {
            ".py", ".dart", ".php", ".js", ".ts", ".jsx", ".tsx", ".html", ".css",
            ".json", ".sql", ".sh", ".bash", ".ps1", ".bat", ".cmd", ".env", ".yaml",
            ".yml", ".xml", ".md", ".txt", ".c", ".cpp", ".h", ".cs", ".java", ".kt",
            ".rs", ".go", ".mq5", ".mq4", ".r", ".lua", ".ini", ".cfg", ".toml"
        }

        if mime.startswith("image/"):
            kind = f"صورة ({file_name})"
        elif mime == "application/pdf":
            kind = f"ملف PDF ({file_name})"
        elif mime.startswith("video/"):
            kind = f"فيديو ({file_name})"
        elif ext == ".zip":
            kind = f"مشروع مضغوط ZIP ({file_name})"
            is_zip = True
        elif ext in CODE_EXTS or mime.startswith("text/") or "json" in mime or "xml" in mime or "javascript" in mime:
            kind = f"ملف كود مصدري ({file_name})"
            is_code = True
        else:
            is_code = True
            kind = f"ملف ({file_name})"

        tg_file = doc
    else:
        return

    await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
    try:
        file_obj = await tg_file.get_file()
        data = bytes(await file_obj.download_as_bytearray())

        if is_zip:
            import zipfile
            ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = Path(file_name).stem
            dest = config.BASE_DIR / "repos_cache" / f"upload_{safe_name}_{ts_str}"
            dest.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                zf.extractall(dest)
            extracted_files = [str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file()][:40]
            content = (
                f"تم فك الضغط للمشروع بنجاح في مجلد الكاش: `{dest.name}`.\n"
                f"الملفات المستخرجة ({len(extracted_files)}):\n" + "\n".join(f"- `{f}`" for f in extracted_files)
            )
        elif is_code:
            try:
                code_text = data.decode("utf-8")
            except UnicodeDecodeError:
                code_text = data.decode("latin-1", errors="replace")
            content = f"```{Path(file_name).suffix.lstrip('.') or 'text'}\n{code_text[:12000]}\n```"
            if len(code_text) > 12000:
                content += "\n... (تم اقتطاع الكود لأن طوله تجاوز 12,000 حرف)"
        else:
            content = await media.describe(data, mime)
    except media.MediaError as e:
        await msg.reply_text(e.user_message)
        return
    except Exception as e:
        log.exception("File handling failed: %s", e)
        await msg.reply_text("ما قدرت أفتح الملف 😕 إذا أكبر من 20 ميغا ابعت نسخة أصغر.")
        return

    caption = msg.caption or "(ما كتب إشي مع الملف)"
    prompt = f"[أدهم بعت {kind}. هاد محتواها بالتفصيل]:\n{content}\n\n[تعليق وطلب أدهم]: {caption}"
    await _answer(update, context, prompt)


async def handle_other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("بفهم كتابة وفويس وصور وملفات PDF يا أدهم ✍️🎤📷")


async def log_ignored(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    log.info("Ignored message from user id %s (not OWNER_ID)", user.id if user else "unknown")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("Unhandled error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_user and update.effective_user.id == config.OWNER_ID:
        try:
            if update.effective_message:
                await update.effective_message.reply_text("صار خطأ بالبوت 😕 جرّب كمان مرة.")
        except Exception:
            pass


async def post_init(app: Application) -> None:
    reminders.setup(app)
    jobs.setup(app)
    brief.setup(app)
    gmail_tools.setup(app)


async def hunt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/hunt [منصة أو نيتش] — hunt for client requests and programming gigs across social media & freelance sites."""
    args = context.args or []
    platform = args[0] if len(args) > 0 else "all"
    niche = args[1] if len(args) > 1 else ""
    await update.effective_message.reply_text("🎯 الرادار عم بيمسح فيسبوك وتويتر وخمسات ومستقل للفرص الحية، ثواني...")
    try:
        from tools import social_gig_hunter
        report = await social_gig_hunter.hunt_social_gigs(platform=platform, niche=niche, max_results=7)
    except Exception as e:
        log.exception("Social gig hunting failed")
        report = f"صار خطأ أثناء صيد الفرص 😕 ({e})"
    await send_long(update, report)


async def radar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/radar — scan freelance and social platforms for tech problems and software requests."""
    await update.effective_message.reply_text("📡 الرادار عم بيفحص مواقع الفريلانس وشبكات التواصل، ثواني...")
    try:
        leads = await tech_radar.scan_freelance_leads(category="all")
    except Exception as e:
        log.exception("Radar scan failed")
        leads = f"صار خطأ أثناء فحص الرادار 😕 ({e})"
    await send_long(update, leads)


async def gaza_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/gaza [منطقة أو قطاع] — scan commercial sectors and shops in Gaza / Khan Younis."""
    args = context.args or []
    sector = args[0] if len(args) > 0 else "all"
    area = args[1] if len(args) > 1 else "خانيونس"
    await update.effective_message.reply_text(f"🏪 عم بفتح دليل محلات {area} وفرص أنظمة الكاشير...")
    try:
        report = await gaza_shops.scan_gaza_shops(sector=sector, area=area, online_search=False)
    except Exception as e:
        log.exception("Gaza scan failed")
        report = f"صار خطأ أثناء فحص محلات غزة 😕 ({e})"
    await send_long(update, report)


async def experts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/experts [قسم] — browse agency experts catalog (270 specialized agents)."""
    args = context.args or []
    div = args[0] if len(args) > 0 else ""
    from tools import agency_tools
    res = agency_tools.list_agency_experts(division=div)
    await send_long(update, res)


async def yt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/yt [رابط أو بحث] — summarize a YouTube video or search tutorials."""
    args = context.args or []
    if not args:
        await update.effective_message.reply_text(
            "ابعت رابط يوتيوب أو كلمة بحث بعد الأمر، مثال:\n`/yt https://youtu.be/...` أو `/yt شرح ميكروتك`",
            parse_mode="Markdown",
        )
        return
    query_or_url = " ".join(args).strip()
    from tools import youtube_tools
    if "youtube.com" in query_or_url or "youtu.be" in query_or_url:
        await update.effective_message.reply_text("📺 عم بسحب بيانات الفيديو والنص (Transcript) للتلخيص، ثواني...")
        res = await youtube_tools.get_youtube_transcript_and_info(url=query_or_url)
    else:
        await update.effective_message.reply_text(f"🔍 عم ببحث على يوتيوب عن «{query_or_url}»...")
        res = await youtube_tools.search_youtube(query=query_or_url, max_results=5)
    await send_long(update, res)


async def read_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/read [رابط] — read any article or webpage cleanly via Jina Reader."""
    args = context.args or []
    if not args:
        await update.effective_message.reply_text(
            "ابعت رابط المقال أو الصفحة بعد الأمر، مثال:\n`/read https://example.com/article`"
        )
        return
    url = args[0].strip()
    await update.effective_message.reply_text("📄 عم بقرأ محتوى الصفحة عبر Jina Reader...")
    from tools import social_reach
    res = await social_reach.read_with_jina(url=url)
    await send_long(update, res)


async def sessions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/sessions [verify <platform>] — check connected social & freelance accounts sessions."""
    args = context.args or []
    from tools import session_manager
    if len(args) > 0 and args[0] in ("verify", "فحص"):
        plat = args[1] if len(args) > 1 else ""
        await update.effective_message.reply_text(f"🔍 عم بفحص جلسة {plat} مباشرة...")
        res = await session_manager.manage_sessions_handler(action="verify", platform=plat)
    else:
        res = await session_manager.manage_sessions_handler(action="list")
    await send_long(update, res)


async def skills_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/skills [query] — search 480 programming & AI skills."""
    args = context.args or []
    query = " ".join(args).strip() if args else "programming"
    from tools import skills_engine
    res = await skills_engine._tool_search_skills(query=query, limit=10)
    await send_long(update, res)


async def repo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/repo <github_url> — clone, inspect, and analyze GitHub repo."""
    args = context.args or []
    if not args:
        await update.effective_message.reply_text(
            "يرجى إرسال رابط المستودع بعد الأمر، مثال:\n`/repo https://github.com/owner/repo`"
        )
        return
    url = args[0].strip()
    await update.effective_message.reply_text("📦 عم بنزل المستودع وأفكفكه وأقرأ معماريته...")
    from tools import github_engine
    res = await github_engine._tool_inspect_github_repo(repo_url=url)
    await send_long(update, res)


async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/code [update/test/migrate/status] — autonomous project maintenance."""
    args = context.args or []
    action = args[0].strip() if args else "full"
    await update.effective_message.reply_text(f"⚡ عم بنفذ التحديث والاختبارات التلقائية ({action})...")
    from tools import workspace_coder
    res = await workspace_coder._tool_update_project_autonomously(action=action)
    await send_long(update, res)


async def saved_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/saved [query] — view and search Facebook saved items."""
    args = context.args or []
    query = " ".join(args).strip()
    await update.effective_message.reply_text("📂 عم بجلب عناصرك المحفوظة في فيسبوك...")
    from tools import facebook_saved
    res = await facebook_saved.facebook_saved_handler({"query": query, "limit": 15})
    await send_long(update, res)


async def wa_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/wa [phone message] — WhatsApp bridge for invoices, Z-reports, and messaging."""
    args = context.args or []
    from tools import whatsapp_bridge
    if not args:
        await update.effective_message.reply_text(
            "📱 **أتمتة الواتساب (WhatsApp Bridge):**\n\n"
            "• `/wa <رقم> <الرسالة>` — توليد رابط ومحادثة واتساب فورية جاهزة للإرسال\n"
            "• `/wa zreport` — توليد تقرير الإقفال اليومي الشامل (Z-Report) لـ شامل POS\n"
            "• `/wa invoice <اسم_الزبون> <المبلغ>` — تجهيز فاتورة شراء رقمية للعميل"
        )
        return

    first = args[0].lower()
    if first in ["zreport", "z-report", "تقرير"]:
        sales = float(args[1]) if len(args) > 1 and args[1].replace(".", "").isdigit() else 3450.0
        res = await whatsapp_bridge.generate_z_report_handler({"shop_name": "سوبرماركت شامل", "total_sales": sales})
        await send_long(update, res)
        return

    if first in ["invoice", "فاتورة"]:
        cname = args[1] if len(args) > 1 else "الزبون الكريم"
        total = float(args[2]) if len(args) > 2 and args[2].replace(".", "").isdigit() else 150.0
        res = await whatsapp_bridge.generate_invoice_handler({"shop_name": "متجر شامل", "customer_name": cname, "paid": total})
        await send_long(update, res)
        return

    phone = args[0]
    msg = " ".join(args[1:]) if len(args) > 1 else "أهلاً بك، تم تجهيز طلبك بنجاح!"
    res = await whatsapp_bridge.send_whatsapp_link_handler({"phone": phone, "message": msg})
    await send_long(update, res)


async def browser_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/browser <url> [actions] — autonomous browser pilot."""
    args = context.args or []
    if not args:
        await update.effective_message.reply_text("🌐 يرجى إرسال الرابط المطلوب تصفحه، مثال:\n`/browser https://example.com`")
        return
    url = args[0]
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    await update.effective_message.reply_text(f"🌐 جاري إطلاق المتصفح الآلي وتصفح `{url}`...")
    from tools import browser_pilot
    res = await browser_pilot.browse_url(url=url, capture_screenshot=True, wait_seconds=3)

    if res.get("screenshot") and Path(res["screenshot"]).exists():
        try:
            with open(res["screenshot"], "rb") as photo:
                await update.effective_message.reply_photo(
                    photo=photo,
                    caption=f"📸 سكرين شوت لصفحة: {res['title'][:60]}"
                )
        except Exception as e:
            log.warning("Could not send photo: %s", e)

    out = f"📄 **عنوان الصفحة:** `{res['title']}`\n🔗 **الرابط:** {res['url']}\n\n```\n{res['text'][:2000]}\n```"
    await send_long(update, out)


async def crew_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/crew [crew_id task] — run multi-agent crew."""
    args = context.args or []
    from tools import crew_orchestrator
    if not args:
        res = await crew_orchestrator.crew_orchestrator_handler({})
        await send_long(update, res)
        return
    crew_id = args[0].lower()
    task = " ".join(args[1:]) if len(args) > 1 else "تنفيذ مهام الطاقم الافتراضية"
    await update.effective_message.reply_text(f"🚀 جاري تشغيل طاقم `{crew_id}`...")
    res = await crew_orchestrator.crew_orchestrator_handler({"crew_id": crew_id, "task": task})
    await send_long(update, res)


async def concat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/concat <project_name> [extensions] — pack and summarize codebase."""
    args = context.args or []
    from tools import project_concat
    if not args:
        res = await project_concat.project_concat_handler({})
        await send_long(update, res)
        return
    proj = args[0]
    exts = args[1] if len(args) > 1 else ""
    await update.effective_message.reply_text(f"📦 جاري حزم وتجميع ملفات مشروع `{proj}`...")
    res = await project_concat.project_concat_handler({"project_name_or_path": proj, "extensions": exts})
    await send_long(update, res)


async def server_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/server or /vps — view server health, ports, and services."""
    await update.effective_message.reply_text("🖥️ جاري فحص حالة السيرفر والمنافذ...")
    from tools import server_ops
    res = await server_ops.server_status_handler({})
    await send_long(update, res)


async def voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/voice [voice_key] <text> — generate studio-grade neural voiceover."""
    args = context.args or []
    from tools import voice_studio
    if not args:
        await update.effective_message.reply_text(
            "🎙️ **استوديو التعليق الصوتي العصبي (Voice Studio):**\n\n"
            "اكتب الأمر متبوعاً بالنص، مثال:\n"
            "`/voice مرحباً بكم في أسرار الذكاء الاصطناعي!`\n\n"
            "أو حدد نبرة الصوت:\n"
            "• `/voice ar_male_egypt نص الفيديو` (حماسي للشروحات والتيك توك)\n"
            "• `/voice ar_male_gulf نص الفيديو` (فخم ورسمي خليجي)\n"
            "• `/voice en_male_tech English script` (أمريكي نشط لمقاطع التقنية)"
        )
        return

    first = args[0].lower()
    if first in voice_studio.VOICES:
        vkey = first
        txt = " ".join(args[1:])
    else:
        vkey = "ar_male_egypt"
        txt = " ".join(args)

    if not txt:
        await update.effective_message.reply_text("يرجى كتابة النص المراد تحويله لصوت بعد اسم النبرة.")
        return

    await update.effective_message.reply_text(f"🎙️ جاري توليد التعليق الصوتي بالنبرة `{vkey}`...")
    try:
        audio_path = await voice_studio.generate_speech(text=txt, voice_key=vkey)
        if audio_path.exists():
            with open(audio_path, "rb") as audio:
                await update.effective_message.reply_audio(
                    audio=audio,
                    title="AI Voiceover",
                    performer="adham-agent Voice Studio",
                    caption=f"🎙️ **التعليق الصوتي جاهز:**\n`{txt[:120]}...`"
                )
            return
    except Exception as e:
        await update.effective_message.reply_text(f"❌ خطأ أثناء توليد الصوت: {e}")
        return


async def video_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/video <title> | <hook> | <script> — generate complete 9:16 short video."""
    raw = " ".join(context.args or [])
    if not raw:
        await update.effective_message.reply_text(
            "🎬 **استوديو إنتاج الفيديوهات القصيرة (Shorts / Reels / TikTok):**\n\n"
            "طريقة الاستخدام السريعة:\n"
            "`/video العنوان | الهوك الجذاب | نص التعليق الصوتي الكامل`\n\n"
            "مثال:\n"
            "`/video 500+ نموذج مجاني | وقف تدفع على ChatGPT! | وقف تدفع اشتراكات شهرية على الذكاء الاصطناعي، اليوم وفرتلك أكثر من 500 نموذج مجاني وسريع للشركات والمطورين. الرابط بالبايو!`\n\n"
            "أو ببساطة اطلب مني بالرسائل أو بالفويس: *'اعملي ريلز عن أداة كذا'* وسأتكفل بكل شيء!"
        )
        return

    parts = [p.strip() for p in raw.split("|")]
    title = parts[0]
    hook = parts[1] if len(parts) > 1 else title
    script = parts[2] if len(parts) > 2 else f"{hook}. {title}. التفاصيل والرابط بانتظارك بالبايو!"

    await update.effective_message.reply_text("🎬 جاري تحضير وتجميع ورندرة الفيديو (9:16) مع التعليق الصوتي... انتظر ثوانٍ معدودة ⏳")
    from tools import video_assembler
    try:
        res = await video_assembler.assemble_short_video(
            title=title,
            hook=hook,
            points=["أحدث تقنيات 2026", "بدون بطاقات بنكية", "رابط مجاني ومباشر"],
            script_narration=script,
            cta="الرابط مثبت بالبايو!",
            voice_key="ar_male_egypt"
        )
        vpath = Path(res["video_path"])
        if vpath.exists():
            with open(vpath, "rb") as vf:
                await update.effective_message.reply_video(
                    video=vf,
                    caption=res["caption"],
                    supports_streaming=True
                )
            return
    except Exception as e:
        await update.effective_message.reply_text(f"❌ خطأ أثناء إنتاج الفيديو: {e}")


async def restart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/restart — gracefully restarts the bot process via Watchdog."""
    await update.effective_message.reply_text("🔄 جاري إعادة تشغيل البوت ذاتياً... سأعود للعمل خلال ثانيتين بكامل التحديثات!")
    from tools import self_evolution
    self_evolution.trigger_self_restart(delay_seconds=1.0)


async def pip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/pip <pkg> — installs a python package via pip."""
    pkg = " ".join(context.args or []).strip()
    if not pkg:
        await update.effective_message.reply_text("اكتب اسم المكتبة، مثلاً:\n`/pip beautifulsoup4`")
        return
    await update.effective_message.reply_text(f"⏳ جاري تثبيت الحزمة `{pkg}` في بيئة السيرفر...")
    from tools import self_evolution
    res = await self_evolution.install_package(pkg)
    if res["success"]:
        await update.effective_message.reply_text(f"✅ {res['message']}")
    else:
        await update.effective_message.reply_text(f"❌ {res['error']}")


async def cmd_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/cmd <command> — runs a shell command on the host."""
    cmd_str = " ".join(context.args or []).strip()
    if not cmd_str:
        await update.effective_message.reply_text("اكتب الأمر المراد تنفيذه، مثلاً:\n`/cmd git status` أو `/cmd dir`")
        return
    from tools import self_evolution
    res = await self_evolution.execute_server_cmd_handler({"command": cmd_str})
    await update.effective_message.reply_text(res)


async def update_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/update [branch] — pulls latest code from Git and auto-restarts."""
    branch = context.args[0] if context.args else "main"
    await update.effective_message.reply_text(f"🔄 جاري فحص وسحب أحدث التحديثات البرمجية من Git (فرع `{branch}`)...")
    from tools import self_evolution
    res = await self_evolution.git_sync_and_restart(branch=branch)
    if res["success"]:
        await update.effective_message.reply_text(res["message"])
    else:
        await update.effective_message.reply_text(res["error"])


async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/image <prompt> — generate stunning AI image via Flux.1."""
    prompt = " ".join(context.args or []).strip()
    if not prompt:
        await update.effective_message.reply_text("يرجى كتابة وصف الصورة المطلوبة، مثال:\n`/image cyberpunk robot in dark neon room 9:16`")
        return

    aspect = "9:16" if "9:16" in prompt or "ريلز" in prompt else ("16:9" if "16:9" in prompt else "1:1")
    await update.effective_message.reply_text(f"🎨 جاري رسم وتوليد الصورة بمحرك FLUX.1 بأبعاد `{aspect}`...")
    from tools import media_studio
    try:
        res = await media_studio.generate_flux_image(prompt=prompt, aspect_ratio=aspect)
        img_path = Path(res["image_path"])
        if img_path.exists():
            with open(img_path, "rb") as photo:
                await update.effective_message.reply_photo(
                    photo=photo,
                    caption=f"🎨 **الصورة المولدة بالذكاء الاصطناعي (FLUX.1):**\n`{prompt[:120]}`"
                )
            return
    except Exception as e:
        await update.effective_message.reply_text(f"❌ خطأ أثناء توليد الصورة: {e}")


async def leads_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/leads [category] [city] — query extracted business leads and preview links."""
    args = context.args or []
    cat = args[0] if len(args) > 0 else ""
    city = args[1] if len(args) > 1 else ""
    await update.effective_message.reply_text("🎯 جاري جلب العملاء وروابط المعاينة المخصصة من قاعدة البيانات...")
    from tools import lead_pipeline_bridge
    res = await lead_pipeline_bridge.query_leads_handler({"category": cat, "city": city, "limit": 6})
    await send_long(update, res)


def main() -> None:
    init_db()

    app = Application.builder().token(config.TELEGRAM_TOKEN).post_init(post_init).build()

    owner = filters.User(user_id=config.OWNER_ID)

    app.add_handler(CommandHandler("start", start, filters=owner))
    app.add_handler(CommandHandler("reset", reset_cmd, filters=owner))
    app.add_handler(CommandHandler("restart", restart_cmd, filters=owner))
    app.add_handler(CommandHandler("update", update_cmd, filters=owner))
    app.add_handler(CommandHandler("sync", update_cmd, filters=owner))
    app.add_handler(CommandHandler("pip", pip_cmd, filters=owner))
    app.add_handler(CommandHandler("cmd", cmd_cmd, filters=owner))
    app.add_handler(CommandHandler("image", image_command, filters=owner))
    app.add_handler(CommandHandler("leads", leads_command, filters=owner))
    app.add_handler(CommandHandler("skills", skills_command, filters=owner))
    app.add_handler(CommandHandler("repo", repo_command, filters=owner))
    app.add_handler(CommandHandler("code", code_command, filters=owner))
    app.add_handler(CommandHandler("saved", saved_command, filters=owner))
    app.add_handler(CommandHandler("bookmarks", saved_command, filters=owner))
    app.add_handler(CommandHandler("voice", voice_command, filters=owner))
    app.add_handler(CommandHandler("video", video_command, filters=owner))
    app.add_handler(CommandHandler("wa", wa_command, filters=owner))
    app.add_handler(CommandHandler("whatsapp", wa_command, filters=owner))
    app.add_handler(CommandHandler("browser", browser_command, filters=owner))
    app.add_handler(CommandHandler("crew", crew_command, filters=owner))
    app.add_handler(CommandHandler("concat", concat_command, filters=owner))
    app.add_handler(CommandHandler("server", server_command, filters=owner))
    app.add_handler(CommandHandler("vps", server_command, filters=owner))
    app.add_handler(CommandHandler("sessions", sessions_command, filters=owner))
    app.add_handler(CommandHandler("yt", yt_command, filters=owner))
    app.add_handler(CommandHandler("read", read_command, filters=owner))
    app.add_handler(CommandHandler("experts", experts_command, filters=owner))
    app.add_handler(CommandHandler("agency", experts_command, filters=owner))
    app.add_handler(CommandHandler("gaza", gaza_command, filters=owner))
    app.add_handler(CommandHandler("radar", radar_command, filters=owner))
    app.add_handler(CommandHandler("hunt", hunt_command, filters=owner))
    app.add_handler(CommandHandler("gigs", hunt_command, filters=owner))

    app.add_handler(CommandHandler("reminders", reminders.list_command, filters=owner))
    app.add_handler(CommandHandler("jobs", jobs.jobs_command, filters=owner))
    app.add_handler(CommandHandler("brief", brief.brief_command, filters=owner))
    app.add_handler(CommandHandler("pitch", outreach.pitch_command, filters=owner))

    app.add_handler(CallbackQueryHandler(reminders.handle_callback, pattern="^rem:"))
    app.add_handler(CallbackQueryHandler(jobs.handle_callback, pattern="^job:"))
    app.add_handler(CallbackQueryHandler(gmail_tools.handle_callback, pattern="^mail:"))

    app.add_handler(MessageHandler(owner & filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(owner & (filters.VOICE | filters.AUDIO), handle_voice))
    app.add_handler(MessageHandler(owner & (filters.PHOTO | filters.Document.ALL | filters.VIDEO | filters.VIDEO_NOTE | filters.ANIMATION), handle_file))
    app.add_handler(MessageHandler(owner & filters.ALL, handle_other))
    app.add_handler(MessageHandler(~owner, log_ignored))

    app.add_error_handler(error_handler)

    log.info("Bot is running (provider=%s, model=%s). Press Ctrl+C to stop.", config.AI_PROVIDER, config.MODEL)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()