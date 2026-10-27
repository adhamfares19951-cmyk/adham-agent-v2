"""Telegram bot entry point. Run: python main.py"""
from __future__ import annotations

import io
import json
import logging
import os
import re
import time
import traceback
from datetime import datetime
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
from tg_utils import send_long, safe_edit_message_text, safe_reply_text, escape_markdown, clean_for_markdown
from tools import brief, gaza_shops, gmail_tools, jobs, media, outreach, reminders, tech_radar

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).resolve().parent / "bot.log", encoding="utf-8"),
    ],
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
        "• `/panel` — لوحة قيادة نظام التشغيل المؤسسي والأقسام وطابور الموافقات\n"
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
    await update.effective_message.reply_text("🧹 تم تصفير ذاكرة وسياق المحادثة بالكامل بنجاح!\n\nالبوت الآن في حالة نقية وصافية 100% بدون أي تداخل أو هلوسة سابقة. جاهز لأي أمر جديد يا أدهم 🚀")


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
        text = await media.transcribe(data, filename=file_name)
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
    is_apk = False

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
        elif ext == ".apk" or "vnd.android.package-archive" in mime:
            kind = f"تطبيق أندرويد APK ({file_name})"
            is_apk = True
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

        if is_apk:
            from tools import apk_inspector
            ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = config.BASE_DIR / "repos_cache" / f"upload_{ts_str}_{file_name}"
            dest.write_bytes(data)
            content = await apk_inspector._handle_inspect_apk({"apk_path": str(dest)})
        elif is_zip:
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
    err_tb = "".join(traceback.format_exception(None, context.error, context.error.__traceback__)) if context.error else "Unknown error"
    log.error("Unhandled error:\n%s", err_tb)
    if isinstance(update, Update) and update.effective_user and update.effective_user.id == config.OWNER_ID:
        try:
            if update.effective_message:
                short_err = str(context.error) if context.error else "حدث خطأ غير متوقع"
                await update.effective_message.reply_text(
                    f"⚠️ **صار خطأ أثناء تنفيذ الأمر:**\n<code>{short_err[:250]}</code>\n\nجرّب كمان مرة أو تفقد السجلات.",
                    parse_mode="HTML"
                )
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
        report = await social_gig_hunter.hunt_social_gigs({"platform": platform, "niche": niche, "max_results": 7})
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
        report = await gaza_shops.scan_gaza_shops({"sector": sector, "area": area, "online_search": "false"})
    except Exception as e:
        log.exception("Gaza scan failed")
        report = f"صار خطأ أثناء فحص محلات غزة 😕 ({e})"
    await send_long(update, report)


def _build_panel_keyboard() -> InlineKeyboardMarkup:
    """Builds the 6-department Enterprise OS dashboard inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🎯 صيد عملاء وتسويق", callback_data="panel:dept:marketing_sales"),
            InlineKeyboardButton("🎬 استوديو الفيديو والنشر", callback_data="panel:dept:video_studio"),
        ],
        [
            InlineKeyboardButton("💻 مصنع البرمجيات", callback_data="panel:dept:software_factory"),
            InlineKeyboardButton("⚡ هندسة شبكات وطاقة شمسية", callback_data="panel:dept:network_solar_tech"),
        ],
        [
            InlineKeyboardButton("🛒 إدارة الموقع والمتجر", callback_data="panel:dept:store_web"),
            InlineKeyboardButton("🤖 حالة النماذج (Ollama/OpenRouter)", callback_data="panel:models"),
        ],
        [
            InlineKeyboardButton("🌐 البيانات الحية وفحص الـ APIs", callback_data="panel:live_data_hub"),
            InlineKeyboardButton("📋 طابور الموافقات المعلقة", callback_data="panel:approvals"),
        ],
        [
            InlineKeyboardButton("🔄 تحديث اللوحة الرئيسية", callback_data="panel:refresh"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def _get_panel_text() -> str:
    """Formats the Enterprise OS welcome and approval status brief."""
    import memory
    try:
        pending = memory.get_pending_approvals()
        pending_count = len(pending)
    except Exception:
        pending_count = 0

    appr_str = f"⚠️ لديك `{pending_count}` إجراء بانتظار الموافقة!" if pending_count else "✅ لا توجد إجراءات معلقة حالياً."

    return (
        "🏛️ **لوحة قيادة نظام التشغيل المؤسسي (Enterprise Agency OS Dashboard):**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "مرحباً بك يا أدهم في مركز التحكم والمراقبة المؤتمت لوكالتك.\n"
        "اختر أحد الأقسام التشغيلية أو العمليات أدناه لإدارتها فورياً:\n\n"
        f"• **طابور الموافقات (Approval Queue):** {appr_str}\n"
        "• **التوجيه الهجين (Smart Router):** Ollama (محلي) + OpenRouter (أكواد/شبكات) + Gemini\n"
        "• **الحسابات الهندسية:** حتمية 100% (Zero-Hallucination Tools)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


async def panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/panel or /agency — open the interactive Enterprise Agency OS Dashboard."""
    text = _get_panel_text()
    reply_markup = _build_panel_keyboard()
    await safe_reply_text(update.effective_message, text, reply_markup=reply_markup, parse_mode="Markdown")


async def handle_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles interactions with the Agency OS inline panel and approval queue."""
    query = update.callback_query
    await query.answer()

    # Security check: strict OWNER_ID authorization gate
    if not query.from_user or query.from_user.id != config.OWNER_ID:
        log.warning("Unauthorized panel callback attempt from user %s", query.from_user.id if query.from_user else "unknown")
        await query.answer("⛔ غير مصرح لك بتنفيذ هذا الإجراء.", show_alert=True)
        return

    data = query.data or ""
    import agency_orchestrator
    import memory

    # 1. Main Dashboard view / Refresh
    if data in ("panel:main", "panel:refresh"):
        text = _get_panel_text()
        reply_markup = _build_panel_keyboard()
        await safe_edit_message_text(query, text, reply_markup=reply_markup, parse_mode="Markdown")
        return

    # 2. Department Views
    if data.startswith("panel:dept:"):
        dept_id = data.replace("panel:dept:", "")
        res = await agency_orchestrator.execute_department_task(dept_id, "")
        output = res.get("output", "")

        sub_buttons = []
        if dept_id == "network_solar_tech":
            sub_buttons = [
                [
                    InlineKeyboardButton("⚡ تجربة حساب طاقة 1000W", callback_data="panel:quick_solar"),
                    InlineKeyboardButton("🌐 تجربة تقسيم شبكة /24", callback_data="panel:quick_subnet"),
                ]
            ]
        elif dept_id == "marketing_sales":
            sub_buttons = [
                [
                    InlineKeyboardButton("🎯 صيد 3 عملاء موثقين (خانيونس)", callback_data="panel:quick_hunt_leads"),
                    InlineKeyboardButton("📋 العملاء الموثقين", callback_data="panel:quick_list_verified"),
                ],
                [InlineKeyboardButton("🏪 استكشاف محلات غزة", callback_data="panel:quick_gaza")],
            ]
        elif dept_id == "video_studio":
            sub_buttons = [
                [
                    InlineKeyboardButton("📱 سكريبت شامل POS", callback_data="panel:gen_script_pos"),
                    InlineKeyboardButton("📈 سكريبت بوتات التداول", callback_data="panel:gen_script_trading"),
                ],
                [
                    InlineKeyboardButton("⚡ سكريبت ميكروتك وطاقة", callback_data="panel:gen_script_tech"),
                ],
            ]
        elif dept_id == "store_web":
            from core.tunnel_manager import get_tunnel_manager
            tm = get_tunnel_manager()
            pub_url = tm.get_public_url()
            open_btn = (
                InlineKeyboardButton("🔗 فتح المنصة الخارجية", url=pub_url)
                if pub_url
                else InlineKeyboardButton("🔗 المنصة الخارجية (غير متصل)", callback_data="panel:tunnel_refresh")
            )
            sub_buttons = [
                [
                    InlineKeyboardButton("📦 استعراض المنتجات", callback_data="panel:quick_store_prods"),
                    InlineKeyboardButton("📥 الطلبات الجديدة", callback_data="panel:quick_store_orders"),
                ],
                [
                    open_btn,
                    InlineKeyboardButton("🔄 إعادة تشغيل النفق / تحديث", callback_data="panel:tunnel_refresh"),
                ],
            ]

        sub_buttons.append([InlineKeyboardButton("🔙 العودة للوحة الرئيسية", callback_data="panel:main")])
        markup = InlineKeyboardMarkup(sub_buttons)
        await safe_edit_message_text(query, output, reply_markup=markup, parse_mode="Markdown")
        return

    # 3. Model Status View
    if data == "panel:models":
        res = await agency_orchestrator.execute_department_task("model_status", "")
        output = res.get("output", "")
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 إعادة فحص النماذج", callback_data="panel:models")],
            [InlineKeyboardButton("🔙 العودة للوحة الرئيسية", callback_data="panel:main")],
        ])
        await safe_edit_message_text(query, output, reply_markup=markup, parse_mode="Markdown")
        return

    # 4. Approval Queue View
    if data == "panel:approvals":
        pending = memory.get_pending_approvals()
        if not pending:
            text = (
                "📋 **طابور الموافقات الحساسة (Approval Queue):**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "✅ **الطابور نظيف بالكامل!** لا توجد أي إجراءات خارجية معلقة تنتظر موافقتك.\n"
                "أي حملات بريد، نشر فيديوهات، أو تعديلات حساسة ستظهر هنا تلقائياً لتقوم باعتمادها أو رفضها."
            )
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للوحة الرئيسية", callback_data="panel:main")]])
            await safe_edit_message_text(query, text, reply_markup=markup, parse_mode="Markdown")
            return

        lines = [
            f"📋 **طابور الموافقات الحساسة ({len(pending)} إجراء معلق):**",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        buttons = []
        for raw_item in pending[:5]:
            item = dict(raw_item)
            action_type = clean_for_markdown(item.get("action_type", "إجراء"))
            desc = clean_for_markdown(item.get("description", ""))
            created = clean_for_markdown(item.get("created_at", ""))
            lines.append(f"🔹 **إجراء #{item['id']} ({action_type}):**")
            lines.append(f"   📝 {desc}")
            lines.append(f"   ⏰ التاريخ: `{created}`\n")
            buttons.append([
                InlineKeyboardButton(f"✅ اعتماد #{item['id']}", callback_data=f"panel:appr:ok:{item['id']}"),
                InlineKeyboardButton(f"❌ رفض #{item['id']}", callback_data=f"panel:appr:no:{item['id']}"),
            ])

        buttons.append([InlineKeyboardButton("🔙 العودة للوحة الرئيسية", callback_data="panel:main")])
        markup = InlineKeyboardMarkup(buttons)
        await safe_edit_message_text(query, "\n".join(lines), reply_markup=markup, parse_mode="Markdown")
        return

    # 5. Approve Action
    if data.startswith("panel:appr:ok:"):
        item_id = int(data.split(":")[-1])
        memory.update_approval_status(item_id, "approved")
        text = f"✅ **تمت الموافقة بنجاح على الإجراء رقم #{item_id}!**\nسيقوم النظام بتنفيذ المهمة فوراً وفق الصلاحيات الممنوحة."
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 العودة لطابور الموافقات", callback_data="panel:approvals")],
            [InlineKeyboardButton("🔙 اللوحة الرئيسية", callback_data="panel:main")],
        ])
        await safe_edit_message_text(query, text, reply_markup=markup, parse_mode="Markdown")
        return

    # 6. Reject Action
    if data.startswith("panel:appr:no:"):
        item_id = int(data.split(":")[-1])
        memory.update_approval_status(item_id, "rejected")
        text = f"❌ **تم رفض الإجراء رقم #{item_id} وإلغاء تنفيذه.**"
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 العودة لطابور الموافقات", callback_data="panel:approvals")],
            [InlineKeyboardButton("🔙 اللوحة الرئيسية", callback_data="panel:main")],
        ])
        await safe_edit_message_text(query, text, reply_markup=markup, parse_mode="Markdown")
        return

    # 7. Quick Shortcuts for Department Demos
    if data == "panel:quick_solar":
        res = await agency_orchestrator.execute_department_task(
            "network_solar_tech", "حمل 1000 واط وساعات تشغيل 4 ساعات وبطاريات 24 فولت"
        )
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقسم", callback_data="panel:dept:network_solar_tech")]])
        await safe_edit_message_text(query, res["output"], reply_markup=markup, parse_mode="Markdown")
        return

    if data == "panel:quick_subnet":
        res = await agency_orchestrator.execute_department_task(
            "network_solar_tech", "قسم شبكة 192.168.1.0/24 الى 3 vlans"
        )
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقسم", callback_data="panel:dept:network_solar_tech")]])
        await safe_edit_message_text(query, res["output"], reply_markup=markup, parse_mode="Markdown")
        return

    if data == "panel:quick_gaza":
        text = (
            "🏪 **استكشاف محلات غزة وخانيونس:**\n\n"
            "استخدم الأمر مباشرة في الشات:\n"
            "`/leads صيدليات خانيونس`\n"
            "أو `/gaza سوبرماركت دير البلح`\n"
            "وسيقوم البوت باستخراج المحلات وأرقام الجوال وتجهيز روابط المعاينة فوراً."
        )
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقسم", callback_data="panel:dept:marketing_sales")]])
        await safe_edit_message_text(query, text, reply_markup=markup, parse_mode="Markdown")
        return

    if data == "panel:quick_store_prods":
        from tools import website_manager
        prods_text = await website_manager.list_website_products_handler({})
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقسم", callback_data="panel:dept:store_web")]])
        await safe_edit_message_text(query, prods_text, reply_markup=markup, parse_mode="Markdown")
        return

    if data == "panel:quick_store_orders":
        from tools import website_manager
        orders_text = await website_manager.list_client_orders_handler({"status": "new"})
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقسم", callback_data="panel:dept:store_web")]])
        await safe_edit_message_text(query, orders_text, reply_markup=markup, parse_mode="Markdown")
        return

    if data == "panel:tunnel_refresh":
        from core.tunnel_manager import get_tunnel_manager
        await safe_edit_message_text(
            query,
            "🔄 **جاري تشغيل / إعادة تشغيل نفق Cloudflare وتحديث الرابط الخارجي...**\n⏳ الرجاء الانتظار بضع ثوانٍ...",
            parse_mode="Markdown",
        )

        tm = get_tunnel_manager()
        res = await tm.restart_tunnel(port=8080)
        pub_url = res.get("public_url", "")
        if pub_url:
            msg = (
                f"✅ **تم تشغيل نفق Cloudflare وتحديث الرابط بنجاح!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌐 **الرابط الخارجي المباشر:**\n[{pub_url}]({pub_url})\n\n"
                f"📡 **المنفذ المحلي:** `8080`\n"
                f"🛡️ **الحالة:** 🟢 نشط ومحمي بتشفير HTTPS العالمي\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"*(تم حفظ الرابط وتحديثه في المتجر ورسائل التسويق)*"
            )
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 فتح المنصة الآن", url=pub_url)],
                [InlineKeyboardButton("🔙 العودة لقسم المتجر", callback_data="panel:dept:store_web")],
            ])
        else:
            msg = f"⚠️ تعذر التقاط الرابط فورياً: {res.get('message', 'تأكد من عمل خادم المنصة على منفذ 8080')}"
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 المحاولة ثانية", callback_data="panel:tunnel_refresh")],
                [InlineKeyboardButton("🔙 العودة لقسم المتجر", callback_data="panel:dept:store_web")],
            ])
        await safe_edit_message_text(query, msg, reply_markup=markup, parse_mode="Markdown")
        return

    if data == "panel:quick_hunt_leads":
        from tools import lead_hunter
        await safe_edit_message_text(
            query,
            "🔍 **جاري تشغيل محرك صيد العملاء الذكي (Zero-Hallucination)...**\n\n"
            "• البحث الحي عن أنشطة تجارية حقيقية في خانيونس\n"
            "• استخراج والتحقق الصارم من أرقام الجوال الحقيقية\n"
            "• توليد عروض مخصصة وإرسالها فورياً إلى التيليجرام والواتساب\n\n"
            "⏳ جاري الفحص والتحقق...",
            parse_mode="Markdown",
        )

        leads = await lead_hunter.search_and_extract_leads(query="محلات تجارية سوبرماركت", location="خانيونس", max_results=3)
        if not leads:
            leads_rows = memory.list_verified_leads(limit=3)
            leads = [dict(r) for r in leads_rows]
            for l in leads:
                l["whatsapp_url"] = lead_hunter.format_whatsapp_url(l["phone"], l.get("proposed_pitch", ""))

        lines = [
            f"🎯 **نتائج صيد العملاء الموثقين ({len(leads)} عملاء):**",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        for idx, lead in enumerate(leads, 1):
            if not lead.get("id"):
                memory.add_verified_lead(
                    business_name=lead["business_name"],
                    phone=lead["phone"],
                    source_url=lead["source_url"],
                    proposed_pitch=lead["proposed_pitch"],
                )
            await lead_hunter.send_lead_to_telegram(lead)
            b_name_safe = clean_for_markdown(lead.get('business_name', 'عميل'))
            wa_url = lead.get('whatsapp_url') or lead_hunter.format_whatsapp_url(lead['phone'])
            pitch_prev = clean_for_markdown(str(lead.get('proposed_pitch', ''))[:80])
            lines.append(f"*{idx}. {b_name_safe}*")
            lines.append(f"   📞 جوال: `{lead['phone']}`")
            lines.append(f"   💬 [محادثة واتساب مباشرة]({wa_url})")
            lines.append(f"   🔗 [رابط المصدر الموثق]({lead['source_url']})")
            lines.append(f"   💡 العرض: _{pitch_prev}..._\n")

        lines.append("✅ *تم حفظ العملاء وإرسال بطاقات المتابعة مع أزرار واتساب لهاتفك مباشرة.*")
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 استعراض كل العملاء الموثقين", callback_data="panel:quick_list_verified")],
            [InlineKeyboardButton("🔙 العودة لقسم التسويق", callback_data="panel:dept:marketing_sales")],
        ])
        await safe_edit_message_text(query, "\n".join(lines), reply_markup=markup, parse_mode="Markdown")
        return

    if data == "panel:quick_list_verified":
        from tools import lead_hunter
        leads = memory.list_verified_leads(limit=10)
        if not leads:
            text = (
                "📋 **قائمة العملاء الموثقين (Verified Leads):**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "لا توجد سجلات بعد! اضغط على 'صيد 3 عملاء موثقين' لبدء استخراج الأنشطة فوراً."
            )
        else:
            lines = [
                f"📋 **قائمة العملاء الموثقين ({len(leads)} عميل):**",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ]
            for r in leads:
                wa_url = lead_hunter.format_whatsapp_url(r["phone"], r["proposed_pitch"])
                b_name_safe = clean_for_markdown(r["business_name"])
                status_safe = clean_for_markdown(r["status"])
                lines.append(f"🔹 *{b_name_safe}* (`{r['phone']}`)")
                lines.append(f"   الحالة: `{status_safe}` | 💬 [واتساب]({wa_url}) | 🔗 [المصدر]({r['source_url']})")
            lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            text = "\n".join(lines)

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 صيد عملاء جدد الآن", callback_data="panel:quick_hunt_leads")],
            [InlineKeyboardButton("🔙 العودة لقسم التسويق", callback_data="panel:dept:marketing_sales")],
        ])
        await safe_edit_message_text(query, text, reply_markup=markup, parse_mode="Markdown")
        return

    if data in ("panel:gen_script_pos", "panel:gen_script_trading", "panel:gen_script_tech"):
        from tools import social_studio
        topic_map = {
            "panel:gen_script_pos": "pos",
            "panel:gen_script_trading": "trading",
            "panel:gen_script_tech": "network_solar",
        }
        topic_key = topic_map.get(data, "pos")
        script = social_studio.create_social_script(topic_key)
        await social_studio.send_script_approval_preview(script, script["queue_id"])

        s_title = clean_for_markdown(script['title'])
        s_hook = clean_for_markdown(script['hook'])
        text = (
            f"🎬 **تم إنتاج سكريبت ريلز جديد وإرساله للموافقة!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 **العنوان:** *{s_title}*\n"
            f"🎯 **المجال:** `{script['topic']}`\n"
            f"🪝 **الهوك:** _{s_hook}_\n"
            f"🔢 **رقم الطابور:** `#{script['queue_id']}`\n\n"
            f"✅ **تم إرسال بطاقة المعاينة التفاعلية إلى شات التيليجرام الخاص بك** مع أزرار:\n"
            f"• [✅ اعتماد للنشر]\n"
            f"• [🎙️ توليد تعليق صوتي فوري]\n"
            f"• [🔄 إعادة الصياغة]\n\n"
            f"يمكنك أيضاً إدارة الحالة من طابور الموافقات في أي وقت."
        )
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 طابور الموافقات", callback_data="panel:approvals")],
            [InlineKeyboardButton("🔙 العودة لاستوديو الفيديو", callback_data="panel:dept:video_studio")],
        ])
        await safe_edit_message_text(query, text, reply_markup=markup, parse_mode="Markdown")
        return

    if data == "panel:live_data_hub":
        from tools import live_data_hub
        try:
            prices_data = await live_data_hub.get_live_market_prices()
            gw_status = await live_data_hub.get_api_gateway_status_handler({})
            market_report = live_data_hub.format_market_prices_report(prices_data)
            full_report = f"{market_report}\n\n{gw_status}"
        except Exception as e:
            full_report = f"⚠️ حدث خطأ أثناء جلب البيانات الحية: {e}"

        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 تحديث الأسعار اللحظية", callback_data="panel:live_data_hub"),
                InlineKeyboardButton("🌐 فحص شبكات / IP", callback_data="panel:quick_net_inspect"),
            ],
            [InlineKeyboardButton("🔙 العودة للوحة الرئيسية", callback_data="panel:main")],
        ])
        await safe_edit_message_text(query, full_report, reply_markup=markup, parse_mode="Markdown")
        return

    if data == "panel:quick_net_inspect":
        from tools import live_data_hub
        try:
            res = await live_data_hub.inspect_network_target("1.1.1.1")
            report = live_data_hub.format_network_inspection_report(res)
        except Exception as e:
            report = f"⚠️ خطأ أثناء فحص الشبكة: {e}"

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 فحص جديد", callback_data="panel:quick_net_inspect")],
            [InlineKeyboardButton("🔙 العودة لرادار البيانات", callback_data="panel:live_data_hub")],
        ])
        await safe_edit_message_text(query, report, reply_markup=markup, parse_mode="Markdown")
        return


async def handle_social_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles social studio interactive actions: approval, voiceover, and regeneration."""
    query = update.callback_query
    await query.answer()

    # Security check: strict OWNER_ID authorization gate
    if not query.from_user or query.from_user.id != config.OWNER_ID:
        log.warning("Unauthorized social callback attempt from user %s", query.from_user.id if query.from_user else "unknown")
        await query.answer("⛔ غير مصرح لك بتنفيذ هذا الإجراء.", show_alert=True)
        return

    data = query.data or ""
    import memory
    from tools import social_studio

    if data == "noop":
        return

    # Pattern: social:approve:<queue_id>
    if data.startswith("social:approve:"):
        qid = int(data.split(":")[-1])
        memory.update_approval_status(qid, "approved")
        try:
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ تم الاعتماد للنشر", callback_data="noop")],
                    [InlineKeyboardButton("🎙️ توليد تعليق صوتي الآن", callback_data=f"social:voice:{qid}")],
                ])
            )
        except Exception:
            pass
        await safe_reply_text(query.message, f"✅ **تم اعتماد السكريبت #{qid} بنجاح!** جاهز للجدولة والنشر.", parse_mode="Markdown")
        return

    # Pattern: social:voice:<queue_id>
    if data.startswith("social:voice:"):
        qid = int(data.split(":")[-1])
        await safe_reply_text(query.message, "🎙️ جاري توليد التعليق الصوتي العصبي العربي عبر Edge-TTS...")
        item = memory.get_approval_item(qid)
        if not item:
            await safe_reply_text(query.message, "⚠️ لم يتم العثور على السكريبت في طابور الموافقات.")
            return

        payload = item["payload"]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {"script": payload}

        script_text = payload.get("script") or payload.get("hook") or item["description"]
        title = payload.get("title", f"Script_{qid}")
        clean_title = re.sub(r"[^\w\s-]", "", title).strip()[:30]
        out_file = f"audio_output/script_{qid}_{clean_title}.mp3"

        audio_path = await social_studio.generate_arabic_voiceover(script_text, out_file)
        if audio_path and os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                try:
                    await query.message.reply_audio(
                        audio=f,
                        caption=f"🎙️ **التعليق الصوتي المولد لسكريبت #{qid}**\n📌 *{clean_for_markdown(title)}*",
                        title=title,
                        performer="Adham Agency Voice Studio",
                        parse_mode="Markdown",
                    )
                except Exception:
                    f.seek(0)
                    await query.message.reply_audio(
                        audio=f,
                        caption=f"التعليق الصوتي المولد لسكريبت #{qid}\n{title}",
                        title=title,
                        performer="Adham Agency Voice Studio",
                    )
        else:
            await safe_reply_text(query.message, "❌ تعذر توليد التعليق الصوتي. تأكد من اتصال الإنترنت.")
        return

    # Pattern: social:regen:<queue_id>
    if data.startswith("social:regen:"):
        qid = int(data.split(":")[-1])
        item = memory.get_approval_item(qid)
        topic = "pos"
        if item:
            payload = item["payload"]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}
            topic = payload.get("topic", "pos")

        new_script = social_studio.create_social_script(topic)
        title = clean_for_markdown(new_script.get("title", "فيديو جديد"))
        hook = clean_for_markdown(new_script.get("hook", ""))
        full_script = clean_for_markdown(new_script.get("script", ""))
        new_qid = new_script["queue_id"]

        new_msg = (
            "🎬 **استوديو المحتوى الآلي — مسودة جديدة مُعاد صياغتها!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 **العنوان:** *{title}*\n"
            f"🎯 **الموضوع:** `{new_script.get('topic')}`\n"
            f"🪝 **الهوك:** _{hook}_\n\n"
            f"📜 **نص السكريبت الكامل:**\n_{full_script}_\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ اعتماد للنشر", callback_data=f"social:approve:{new_qid}"),
                InlineKeyboardButton("🎙️ توليد تعليق صوتي", callback_data=f"social:voice:{new_qid}"),
            ],
            [
                InlineKeyboardButton("🔄 إعادة صياغة أخرى", callback_data=f"social:regen:{new_qid}"),
            ],
        ])
        await safe_edit_message_text(query, new_msg, reply_markup=markup, parse_mode="Markdown")
        return


async def autoleads_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/autoleads [query] [location] — extract real verified leads and dispatch alerts."""
    args = context.args or []
    query = args[0] if len(args) > 0 else "محلات تجارية"
    location = args[1] if len(args) > 1 else "خانيونس"
    await safe_reply_text(update.effective_message, f"🎯 جاري تشغيل صيد العملاء الموثقين: {query} في {location}...")
    from tools import lead_hunter
    leads = await lead_hunter.search_and_extract_leads(query=query, location=location, max_results=3)
    if not leads:
        await safe_reply_text(update.effective_message, "🔍 لم يتم العثور على أرقام هواتف موثقة جديدة لهذا البحث.")
        return
    for l in leads:
        await lead_hunter.send_lead_to_telegram(l)
    await safe_reply_text(update.effective_message, f"✅ تم استخراج {len(leads)} عملاء موثقين وإرسال بطاقات الواتساب والتواصل فوراً.")


async def script_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/script [pos|trading|tech] — generate viral social script and approval card."""
    args = context.args or []
    topic = args[0] if len(args) > 0 else "pos"
    from tools import social_studio
    res = await social_studio.generate_social_script_handler({"topic": topic})
    await safe_reply_text(update.effective_message, res, parse_mode="Markdown")


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
    res = await social_reach.read_with_jina({"url": url})
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


async def hq_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/hq or /app — Launch Adham's Mobile Command Center."""
    server_ip = "136.244.77.61"
    url = f"http://{server_ip}:8080"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 فتح مقر القيادة | Command Center", url=url)]
    ])
    await update.effective_message.reply_text(
        "📱 **مقر قيادة أدهم المركزي (Mobile Command Center)**\n\n"
        "يمكنك الآن تحريك كل شيء من هاتفك: تشغيل المشاريع، إنتاج الفيديوهات والأصوات، "
        "إدارة العملاء، والطرفية المباشرة:\n"
        f"🔗 `{url}`\n\n"
        "💡 *نصيحة:* افتح الرابط في جوالك واضغط **'Add to Home Screen'** ليعمل كتطبيق دائم!",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def social_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/social or /platforms — view connected social accounts & audience reach."""
    from core.database import db_manager
    try:
        accounts = await db_manager.get_social_accounts()
        summary = await db_manager.get_audience_summary()

        icons = {
            "youtube": "🔴",
            "tiktok": "🎵",
            "facebook": "📘",
            "instagram": "📸",
            "twitter": "🐦",
            "linkedin": "💼",
        }

        lines = [
            "🌐 **شبكة منصات التواصل الاجتماعي وقاعدة الجمهور**",
            "━━━━━━━━━━━━━━━━━━━━━━━",
        ]

        total_followers = summary.get("total_social_followers", 0)
        total_audience = summary.get("total_audience_records", 0)

        for acc in accounts:
            pid = acc.get("id", "")
            icon = icons.get(pid, "🌐")
            name = acc.get("platform_name", pid)
            handle = acc.get("account_handle", "")
            status = "🟢 متصل" if acc.get("auth_status") == "CONNECTED" else "⚪ مفصول"
            followers = f"{acc.get('followers_count', 0):,}"
            posts = acc.get("total_posts", 0)
            lines.append(f"{icon} **{name}** (`{handle}`)")
            lines.append(f"   👥 المتابعون: `{followers}` | 📝 المنشورات: `{posts}` | {status}")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"📊 **إجمالي المتابعين:** `{total_followers:,}` متابع")
        lines.append(f"👥 **سجلات الجمهور والليدات:** `{total_audience}` عميل ومتابع")
        lines.append("\n💡 *للإدارة الكاملة والنشر المتزامن، افتح مقر القيادة عبر /hq*")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 فتح مقر القيادة وإدارة الجمهور", url="http://136.244.77.61:8080")]
        ])
        await safe_reply_text(
            update.effective_message,
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
    except Exception as e:
        await safe_reply_text(update.effective_message, f"❌ حدث خطأ أثناء جلب حسابات التواصل: {e}")


async def audience_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/audience [segment or name] — view audience members and leads."""
    args = context.args or []
    filter_val = " ".join(args).strip() if args else None
    from core.database import db_manager
    try:
        members = await db_manager.get_audience_members(query=filter_val, limit=15)
        if not members:
            await safe_reply_text(
                update.effective_message,
                "📭 لم يتم العثور على سجلات تطابق البحث في قاعدة بيانات الجمهور.\n\n"
                "💡 لإضافة عميل أو متابع جديد:\n"
                "`/addaudience الاسم | المنصة | الهاتف | الفئة`\n"
                "مثال:\n"
                "`/addaudience أبو خالد | twitter | +966501112233 | vip_trader`",
                parse_mode="Markdown"
            )
            return

        lines = [
            f"👥 **قاعدة بيانات الجمهور والعملاء المستهدفين** ({len(members)} سجل)",
            "━━━━━━━━━━━━━━━━━━━━━━━"
        ]

        segment_labels = {
            "vip_trader": "🏆 متداول ذهب/أسواق",
            "pos_buyer": "🛒 مشتري شمل POS",
            "developer": "💻 مطور/برمجة",
            "general": "👤 متابع عام"
        }

        for m in members:
            name = m.get("name", "بدون اسم")
            handle = m.get("username_or_handle") or "-"
            plat = m.get("platform", "عام")
            phone = m.get("contact_phone") or "لا يوجد"
            seg = segment_labels.get(m.get("segment"), m.get("segment"))
            score = m.get("engagement_score", 50)
            notes = clean_for_markdown(m.get("notes") or "")

            lines.append(f"👤 **{name}** (`{handle}`) • *{plat.upper()}*")
            lines.append(f"   🏷️ الفئة: {seg} | ⭐ التفاعل: `{score}%`")
            if phone and phone != "لا يوجد":
                clean_phone = "".join(c for c in phone if c.isdigit())
                lines.append(f"   📞 الهاتف: `{phone}` [واتساب](https://wa.me/{clean_phone})")
            if notes:
                lines.append(f"   📝 ملاحظات: _{notes}_")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("➕ لإضافة عضو جديد: `/addaudience الاسم | المنصة | الهاتف | الفئة`")

        await safe_reply_text(
            update.effective_message,
            "\n".join(lines),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception as e:
        await safe_reply_text(update.effective_message, f"❌ حدث خطأ أثناء جلب الجمهور: {e}")


async def addaudience_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/addaudience <name> | <platform> | <phone> | [segment] — add lead/follower to audience DB."""
    text = " ".join(context.args or []).strip()
    if not text or "|" not in text:
        await safe_reply_text(
            update.effective_message,
            "ℹ️ **طريقة إضافة متابع أو عميل لقاعدة الجمهور:**\n\n"
            "`/addaudience الاسم | المنصة | الهاتف | الفئة`\n\n"
            "📌 **أمثلة:**\n"
            "`/addaudience سامي التميمي | twitter | +966551122334 | vip_trader`\n"
            "`/addaudience هايبر ماركت القدس | facebook | +970599123456 | pos_buyer`\n"
            "`/addaudience كريم السعيد | instagram | +201012345678 | developer`",
            parse_mode="Markdown"
        )
        return

    parts = [p.strip() for p in text.split("|")]
    name = parts[0]
    plat = parts[1].lower() if len(parts) > 1 else "general"
    phone = parts[2] if len(parts) > 2 else ""
    seg = parts[3] if len(parts) > 3 else "general"

    from core.database import db_manager
    try:
        new_id = await db_manager.add_audience_member(
            name=name,
            platform=plat,
            contact_phone=phone,
            segment=seg,
            lifecycle_stage="lead",
            engagement_score=80,
            notes="تمت الإضافة عبر تليجرام"
        )
        await safe_reply_text(
            update.effective_message,
            f"✅ **تمت إضافة العميل لقاعدة الجمهور بنجاح! (ID: {new_id})**\n\n"
            f"👤 **الاسم:** {name}\n"
            f"🌐 **المنصة:** {plat}\n"
            f"📞 **الهاتف:** `{phone}`\n"
            f"🏷️ **الفئة:** {seg}\n\n"
            "💡 يمكنك مراجعته الآن في `/audience` أو في مقر القيادة عبر الجوال `/app`.",
            parse_mode="Markdown"
        )
    except Exception as e:
        await safe_reply_text(update.effective_message, f"❌ فشل حفظ العميل في قاعدة البيانات: {e}")


async def skills_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/skills [query] — search 480 programming & AI skills."""
    args = context.args or []
    query = " ".join(args).strip() if args else "programming"
    from tools import skills_engine
    res = await skills_engine._tool_search_skills({"query": query, "limit": 10})
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
    res = await github_engine._tool_inspect_github_repo({"repo_url": url})
    await send_long(update, res)


async def findrepo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/findrepo <query> — Search all GitHub repos in the world."""
    args = context.args or []
    if not args:
        await update.effective_message.reply_text(
            "يرجى تحديد موضوع البحث، مثال:\n`/findrepo trading bot python`\nأو\n`/findrepo laravel pos`"
        )
        return
    query = " ".join(args).strip()
    await update.effective_message.reply_text(f"🌍 عم ببحث في كل مستودعات GitHub العالمية عن: `{query}`...")
    from tools import github_engine
    res = await github_engine._tool_search_github_worldwide({"query": query})
    await send_long(update, res)


async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/download <url> — Download any file directly to server bypassing 20MB limit."""
    args = context.args or []
    if not args:
        await update.effective_message.reply_text("يرجى إرسال الرابط المباشر للملف، مثال:\n`/download https://example.com/app.apk`")
        return
    url = args[0].strip()
    await update.effective_message.reply_text("⏳ عم بنزل الملف مباشرة للسيرفر بسرعة فائقة وبدون قيود الحجم...")
    downloads_dir = Path("C:/Projects/adham-agent/downloads")
    downloads_dir.mkdir(parents=True, exist_ok=True)
    filename = url.split("/")[-1].split("?")[0] or "downloaded_file.bin"
    file_path = downloads_dir / filename

    try:
        import httpx
        async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
            async with client.stream("GET", url) as resp:
                if resp.status_code != 200:
                    await update.effective_message.reply_text(f"❌ تعذر التنزيل: كود الاستجابة {resp.status_code}")
                    return
                with open(file_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=1024 * 1024):
                        f.write(chunk)

        size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)

        if filename.lower().endswith(".apk"):
            from tools import apk_inspector
            res = apk_inspector.inspect_apk(file_path)
            out = f"✅ **تم تنزيل وفحص التطبيق بنجاح ({size_mb} MB)!**\n\n"
            techs = ", ".join(res.get("tech_stack", [])) or "Native Java/Kotlin"
            out += f"🛠️ **التقنيات المكتشفة:** `{techs}`\n"
            out += f"📦 **عدد حزم الـ DEX:** `{res.get('dex_count', 0)}`\n"
            out += f"📁 **مسار الملف على السيرفر:** `{file_path}`\n\n"
            dangerous = res.get("dangerous_permissions", [])
            if dangerous:
                out += f"🔒 **أهم الصلاحيات الحساسة ({len(dangerous)}):**\n"
                for p in dangerous[:6]:
                    out += f"  • `{p['permission'].split('.')[-1]}`: {p.get('meaning', '')}\n"
            await send_long(update, out)
        else:
            await update.effective_message.reply_text(f"✅ **تم تنزيل وحفظ الملف بنجاح على السيرفر ({size_mb} MB):**\n`{file_path}`")
    except Exception as e:
        await update.effective_message.reply_text(f"❌ حدث خطأ أثناء التنزيل: {e}")


async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/code [update/test/migrate/status] — autonomous project maintenance."""
    args = context.args or []
    action = args[0].strip() if args else "full"
    await update.effective_message.reply_text(f"⚡ عم بنفذ التحديث والاختبارات التلقائية ({action})...")
    from tools import workspace_coder
    res = await workspace_coder._tool_update_project_autonomously({"action": action})
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


async def tunnel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/tunnel [start/stop/status] [port] — manages Cloudflare HTTPS public tunnel."""
    args = context.args or []
    sub = args[0].lower() if args else "start"
    from tools import cloud_tunnel
    if sub in ("stop", "close"):
        res = cloud_tunnel.stop_public_tunnel()
        await update.effective_message.reply_text(f"🛑 {res['message']}")
    elif sub in ("status", "check"):
        st = cloud_tunnel.get_tunnel_status()
        if st["status"] == "active":
            await update.effective_message.reply_text(f"🌐 **النفق السحابي نشط:**\n{st['public_url']}\nالمحلي: http://localhost:{st['local_port']}")
        else:
            await update.effective_message.reply_text("⚪ لا يوجد نفق سحابي نشط حالياً.")
    else:
        port = int(args[1]) if len(args) > 1 and args[1].isdigit() else (int(args[0]) if args and args[0].isdigit() else 8000)
        await update.effective_message.reply_text(f"🌐 جاري فتح نفق سحابي مشفر للبورت `{port}` (Cloudflare Tunnel)... انتظر ثوانٍ معدودة ⏳")
        try:
            res = await cloud_tunnel.start_public_tunnel(port=port)
            await update.effective_message.reply_text(
                f"✅ **تم فتح النفق السحابي بنجاح!**\n\n"
                f"🔗 **الرابط العام المباشر:**\n{res['public_url']}\n\n"
                f"💡 **رابط المعاينة المباشر للزبائن:**\n`{res['public_url']}/p/slug-name`\n\n"
                f"يمكنك إرسال هذا الرابط للزبائن على الواتساب فوراً!"
            )
        except Exception as e:
            await update.effective_message.reply_text(f"❌ خطأ أثناء فتح النفق: {e}")


async def proposal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/proposal <client> | <project> | <price> — generates instant 1-page PDF proposal."""
    raw = " ".join(context.args or []).strip()
    if not raw:
        await update.effective_message.reply_text(
            "📄 **مولد العروض الفنية والمالية (PDF):**\n\n"
            "الاستخدام:\n`/proposal اسم العميل | عنوان المشروع | السعر والمدة`\n\n"
            "مثال:\n`/proposal مطعم التاج | نظام نقاط البيع شامل POS | 500 شيكل - تسليم خلال 48 ساعة`"
        )
        return
    parts = [p.strip() for p in raw.split("|")]
    client = parts[0]
    proj = parts[1] if len(parts) > 1 else "نظام أتمتة وإدارة الأعمال"
    price = parts[2] if len(parts) > 2 else "$450 USD"

    await update.effective_message.reply_text("📄 جاري تصميم ورندرة ملف العرض التنفيذي (PDF)... ⏳")
    from tools import proposal_pdf_builder
    try:
        pdf_path = await proposal_pdf_builder.generate_proposal_pdf(
            client_name=client,
            project_title=proj,
            problem_statement="الاعتماد على الدفاتر الورقية أو أنظمة بطيئة تضيع الوقت والأرباح.",
            proposed_solution="نظام هندسي متكامل سريع يعمل أوفلاين مع فواتير الواتساب وإدارة كاملة للمخزون.",
            deliverables=[
                "برنامج مفعل مدى الحياة ويعمل بدون كهرباء أو إنترنت",
                "قاعدة بيانات سريعة ومحمية مع نسخ احتياطي تلقائي",
                "طباعة الفواتير الحرارية وإرسال تقارير الإقفال للواتساب",
                "تدريب الطاقم وضمان ودعم فني مستمر"
            ],
            pricing=price,
            timeline="3 إلى 5 أيام عمل"
        )
        if pdf_path.exists():
            with open(pdf_path, "rb") as pf:
                await update.effective_message.reply_document(
                    document=pf,
                    filename=f"Proposal_{client}.pdf",
                    caption=f"📄 **عرض فني ومالي تنفيذي جاهز للعميل:** {client}\n📌 جاهز للإرسال على الواتساب أو منصات العمل الحر!"
                )
    except Exception as e:
        await update.effective_message.reply_text(f"❌ خطأ أثناء توليد ملف الـ PDF: {e}")


async def carousel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/carousel <topic> — generates multi-slide square album for Instagram/LinkedIn."""
    topic = " ".join(context.args or []).strip() or "نصائح تقنية في إدارة الأعمال"
    await update.effective_message.reply_text(f"🎨 جاري تصميم ألبوم الكاروسيل (1080x1080) لموضوع: *{topic}*... ⏳")
    from tools import carousel_builder
    from telegram import InputMediaPhoto
    try:
        res = await carousel_builder.generate_carousel(
            title=topic,
            slides_data=[
                {"title": f"دليلك إلى: <span>{topic}</span>", "content": "أهم المبادئ التي يحتاجها كل صاحب عمل ومبرمج في 2026."},
                {"title": "1. <span>الأتمتة والسرعة</span>", "points": ["توفير الوقت المهدور", "تقليل الاعتماد على الورق", "تقارير مالية حية"]},
                {"title": "2. <span>الاستقرار والاستمرارية</span>", "points": ["العمل حتى بدون كهرباء", "قاعدة بيانات محلية آمنة", "دعم فني سريع"]},
                {"title": "الخلاصة <span>والخطوة التالية</span>", "content": "ابدأ اليوم وحول عملك لنظام رقمي ذكي مع شامل POS!"}
            ]
        )
        media_group = []
        for s_path in res["slides"][:6]:
            with open(s_path, "rb") as f:
                media_group.append(InputMediaPhoto(media=f.read()))
        if media_group:
            media_group[0].caption = res["caption"]
            await update.effective_message.reply_media_group(media=media_group)
    except Exception as e:
        await update.effective_message.reply_text(f"❌ خطأ أثناء توليد الكاروسيل: {e}")


async def scrape_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/scrape <query> [city] — live places and business lead scraper."""
    args = context.args or []
    if not args:
        await update.effective_message.reply_text("اكتب النشاط والمدينة، مثلاً:\n`/scrape مطاعم خانيونس` أو `/scrape صيدليات الرياض`")
        return
    q = args[0]
    city = args[1] if len(args) > 1 else "خانيونس"
    await update.effective_message.reply_text(f"🎯 جاري رصد واستخراج محلات *{q}* في مدينة *{city}* فوراً... ⏳")
    from tools import live_lead_scraper
    res = await live_lead_scraper._handle_scrape({"query": q, "city": city, "limit": 6})
    await send_long(update, res)


async def license_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/license <merchant> <device_id> — generates offline cryptographic license for Shamel POS."""
    args = context.args or []
    if len(args) < 2:
        await update.effective_message.reply_text("اكتب اسم المتجر ومعرف الجهاز، مثلاً:\n`/license سوبرماركت_التاج ANDROID-98A72B`")
        return
    merchant = args[0].replace("_", " ")
    device_id = args[1]
    from tools import license_generator
    res = await license_generator._handle_generate_license({"merchant_name": merchant, "device_id": device_id, "is_lifetime": True})
    await send_long(update, res)


async def cash_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/cash [income/expense] [amount] [currency] [desc] — financial tracker & balance."""
    args = context.args or []
    from tools import finance_tracker
    if not args:
        res = await finance_tracker._handle_summary({})
        await update.effective_message.reply_text(res)
        return
    sub = args[0].lower()
    if sub in ("balance", "summary", "تقرير"):
        res = await finance_tracker._handle_summary({})
        await update.effective_message.reply_text(res)
        return
    sign = args[0]
    tx_type = "income" if ("+" in sign or sign in ("income", "إيراد", "قبض")) else "expense"
    clean_amt = "".join(c for c in sign if c.isdigit() or c == ".").strip()
    amt = float(clean_amt) if clean_amt else (float(args[1]) if len(args) > 1 and args[1].replace(".", "").isdigit() else 0.0)
    curr = "ILS"
    for a in args[1:3]:
        if a.upper() in ("USD", "ILS", "JOD", "EUR", "شيكل", "دولار", "دينار"):
            curr = a
            break
    desc = " ".join(args[2:]) if len(args) > 2 else "معاملة مالية"
    res = await finance_tracker._handle_log_tx({"type": tx_type, "amount": amt, "currency": curr, "description": desc})
    await update.effective_message.reply_text(res)


async def mikrotik_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/mikrotik [hardening/failover/backup] — RouterOS engineering commands and configs."""
    args = context.args or []
    act = args[0].lower() if args else "hardening"
    from tools import mikrotik_manager
    res = await mikrotik_manager._handle_mikrotik({"action": act, "host": args[1] if len(args) > 1 else ""})
    await send_long(update, res)


async def audit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/audit [target_path] — static security and secret leak audit."""
    target = " ".join(context.args or []).strip() or "."
    await update.effective_message.reply_text(f"🛡️ جاري الفحص الأمني السريع للمسار `{target}`... ⏳")
    from tools import code_auditor
    res = await code_auditor._handle_audit({"target": target})
    await send_long(update, res)


async def gmaps_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/gmaps <keyword> [city] [country] — Google Maps scraper kit & lead qualification."""
    args = context.args or []
    if not args:
        await update.effective_message.reply_text(
            "🗺️ **Google Maps Scraper Kit (استخراج العملاء المؤهلين):**\n\n"
            "الاستخدام:\n`/gmaps النشاط [المدينة] [الدولة]`\n\n"
            "أمثلة:\n"
            "• `/gmaps مطاعم خانيونس فلسطين`\n"
            "• `/gmaps كافيهات الرياض السعودية`\n"
            "• `/gmaps صيدليات دبي الإمارات`"
        )
        return
    kw = args[0]
    city = args[1] if len(args) > 1 else "خانيونس"
    country = args[2] if len(args) > 2 else "فلسطين"
    await update.effective_message.reply_text(f"🗺️ جاري تشغيل Google Maps Lead Scraper لاستخراج عملاء *{kw}* في *{city}*... انتظر ثوانٍ معدودة ⏳")
    from tools import gmaps_lead_kit
    res = await gmaps_lead_kit.extract_gmaps_leads_kit(keyword=kw, city=city, country=country, limit=6)
    csv_path = Path(res["csv_path"])
    if csv_path.exists():
        with open(csv_path, "rb") as cf:
            await update.effective_message.reply_document(
                document=cf,
                filename=csv_path.name,
                caption=f"📄 **ملف CSV المستخرج ({res['total_extracted']} عميل):**\nتم تسجيلهم تلقائياً في نظام المعاينات!"
            )
    out_text = await gmaps_lead_kit._handle_gmaps_kit({"keyword": kw, "city": city, "country": country, "limit": 6})
    await send_long(update, out_text)


async def caption_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/caption [video_path] — burns karaoke animated subtitles onto video."""
    msg = update.effective_message
    reply = msg.reply_to_message
    video_to_process = None

    if reply and (reply.video or reply.video_note or reply.document):
        tg_doc = reply.video or reply.video_note or reply.document
        await msg.reply_text("⏳ جاري تنزيل الفيديو المردود عليه لإضافة كابشن الكاراوكي...")
        f_obj = await tg_doc.get_file()
        ts = int(time.time())
        local_video = config.BASE_DIR / "repos_cache" / f"reply_video_{ts}.mp4"
        await f_obj.download_to_drive(str(local_video))
        video_to_process = local_video
    elif context.args:
        video_to_process = Path(" ".join(context.args).strip())

    if not video_to_process or not video_to_process.exists():
        await msg.reply_text(
            "🎬 **توليد كابشن الكاراوكي المتحرك (AutoCaption Pro):**\n\n"
            "• رد على أي فيديو بكلمة `/caption` ليقوم بتفريغه وحرق الكابشن كلمة بكلمة عليه فوراً!\n"
            "• أو اكتب: `/caption videos/video_1792057299.mp4`"
        )
        return

    await msg.reply_text("🎬 جاري تفريغ الكلمات بدقة الميلي ثانية وحرق كابشن الكاراوكي الأصفر المشع على الفيديو... ⏳")
    from tools import video_autocaption
    try:
        res = await video_autocaption.burn_karaoke_subtitles(video_to_process)
        out_v = Path(res["video_path"])
        if out_v.exists():
            with open(out_v, "rb") as vf:
                await msg.reply_video(
                    video=vf,
                    caption=f"✨ **فيديو الكابشن المتحرك (AutoCaption Pro):**\n• الكلمات المتزامنة: {res['total_words']} كلمة\n• تأثير الكاراوكي: إضاءة الكلمة الحالية باللون الأصفر!"
                )
    except Exception as e:
        await msg.reply_text(f"❌ خطأ أثناء توليد الكابشن: {e}")


async def yt_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/yt_stats — displays YouTube channel stats (subscribers, views, videos)."""
    msg = update.effective_message
    from tools import youtube_publisher
    if not youtube_publisher.is_authenticated():
        await msg.reply_text(
            "⚠️ **قناة يوتيوب غير مربوطة بعد!**\n\n"
            "1. ضع ملف `client_secret.json` داخل مجلد `sessions/`.\n"
            "2. شغل ملف `setup_youtube.bat` من جهازك لتأكيد الصلاحية في ثانيتين!"
        )
        return

    await msg.reply_text("📊 جاري جلب إحصائيات قناتك على يوتيوب مباشرة من Google API...")
    try:
        info = await youtube_publisher.get_channel_info()
        if "error" in info:
            await msg.reply_text(f"⚠️ {info['error']}")
            return

        text = (
            f"📺 **إحصائيات القناة الحية (YouTube Studio):**\n\n"
            f"• **اسم القناة**: `{info['title']}`\n"
            f"• **المشتركون**: `{info['subscribers']}` 👥\n"
            f"• **إجمالي المشاهدات**: `{info['views']}` 👁️\n"
            f"• **عدد الفيديوهات**: `{info['videos']}` 🎥\n"
            f"• **المعرّف**: `{info.get('custom_url', '—')}`\n"
            f"• **معرف القناة**: `{info.get('channel_id')}`\n\n"
            f"🟢 **حالة الاتصال**: نشط ومتصل بالكامل ويمكن للبوت النشر فوراً!"
        )
        await msg.reply_text(text)
    except Exception as e:
        await msg.reply_text(f"❌ حدث خطأ أثناء الاتصال باليوتيوب: {e}")


async def yt_upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/yt_upload [title] | [description] | [privacy] — upload replied video to YouTube."""
    msg = update.effective_message
    reply = msg.reply_to_message
    from tools import youtube_publisher

    if not youtube_publisher.is_authenticated():
        await msg.reply_text(
            "⚠️ **قناة يوتيوب غير موثقة بعد!**\n"
            "يرجى تشغيل `setup_youtube.bat` لربط القناة أولاً."
        )
        return

    video_path = None
    if reply and (reply.video or reply.video_note or reply.document):
        tg_doc = reply.video or reply.video_note or reply.document
        await msg.reply_text("⏳ جاري تنزيل الفيديو المردود عليه للرفع إلى يوتيوب...")
        f_obj = await tg_doc.get_file()
        ts = int(time.time())
        local_video = config.BASE_DIR / "repos_cache" / f"yt_upload_{ts}.mp4"
        await f_obj.download_to_drive(str(local_video))
        video_path = local_video

    raw_args = " ".join(context.args).strip()
    parts = [p.strip() for p in raw_args.split("|")]

    title = parts[0] if len(parts) >= 1 and parts[0] else "فيديو جديد عبر أدهم بوت #Shorts"
    description = parts[1] if len(parts) >= 2 else "تم النشر تلقائياً بواسطة المساعد الذكي أدهم."
    privacy = parts[2] if len(parts) >= 3 else "public"

    if not video_path:
        # Check if user specified a file path as first argument
        if parts[0] and Path(parts[0]).exists():
            video_path = Path(parts[0])
            title = parts[1] if len(parts) >= 2 else video_path.stem
            description = parts[2] if len(parts) >= 3 else ""
        else:
            await msg.reply_text(
                "🎬 **طريقة رفع الفيديوهات إلى يوتيوب:**\n\n"
                "• **الطريقة 1 (الأسهل)**: رد على أي فيديو في المحادثة بالأمر:\n"
                "`/yt_upload العنوان | الوصف | public`\n\n"
                "• **الطريقة 2**: حدد مسار الفيديو:\n"
                "`/yt_upload videos/video_1792057299.mp4 | عنوان الفيديو | وصف الفيديو`"
            )
            return

    await msg.reply_text(f"🚀 جاري رفع الفيديو إلى يوتيوب ({privacy})...\n🎬 العنوان: `{title}`")
    try:
        res = await youtube_publisher.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            privacy_status=privacy
        )
        await msg.reply_text(
            f"🎉 **تم نشر الفيديو بنجاح على يوتيوب!**\n\n"
            f"🎬 **العنوان**: {res['title']}\n"
            f"🔗 **رابط المشاهدة**: {res['url']}\n"
            f"🔒 **الخصوصية**: {res['privacy']}\n"
            f"📱 **النوع**: {'YouTube Short ⚡' if res['is_short'] else 'فيديو عادي 🎥'}"
        )
    except Exception as e:
        await msg.reply_text(f"❌ فشل رفع الفيديو: {e}")


async def publish_short_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/publish_short [topic or title | hook | script] — autonomous end-to-end shorts studio."""
    msg = update.effective_message
    from tools import youtube_publisher, video_assembler

    try:
        if not youtube_publisher.is_authenticated():
            await msg.reply_text(
                "⚠️ **قناة يوتيوب غير موثقة بعد!**\n"
                "يرجى وضع ملف `client_secret.json` ثم تشغيل `setup_youtube.bat` لربط قناتك أولاً."
            )
            return

        raw_args = " ".join(context.args).strip()
        parts = [p.strip() for p in raw_args.split("|")]

        topic = ""
        title, hook, script = "", "", ""
        if len(parts) >= 3:
            title, hook, script = parts[0], parts[1], parts[2]
        else:
            topic = raw_args

        await msg.reply_text(
            "🎬 **استوديو الشورتس الآلي بدأ العمل!**\n"
            "⚡ جاري توليد الفكرة والشارت المؤسسي والصوت العصبي وحرق الكابشن والرفع المباشر إلى قناتك..."
        )

        res = await video_assembler.autonomous_publish_short(
            topic=topic,
            title=title,
            hook=hook,
            script=script,
            language="en" if not re.search(r"[\u0600-\u06FF]", raw_args) else "ar",
        )

        final_video = Path(res["video_path"])
        yt_url = res.get("youtube_url") or (res.get("youtube") or {}).get("url") or "قيد المعالجة"
        tt_status = res.get("tiktok_status") or ((res.get("tiktok") or {}).get("message") if (res.get("tiktok") or {}).get("published") else "جاهز")
        with open(final_video, "rb") as vf:
            await msg.reply_video(
                video=vf,
                caption=(
                    f"🎉 **تم إنتاج ونشر الفيديو على المنصات بنجاح!**\n\n"
                    f"🎬 **العنوان**: {res['title']}\n"
                    f"🔗 **يوتيوب شورتس**: {yt_url}\n"
                    f"📱 **تيك توك**: {tt_status}\n\n"
                    f"⚡ 4 مشاهد ديناميكية + كابشن كاريوكي + موسيقى لو فاي متزامنة!"
                )
            )
    except Exception as e:
        log.error("Error in publish_short_command:\n%s", traceback.format_exc())
        await msg.reply_text(f"❌ حدث خطأ أثناء خط الإنتاج والنشر:\n<code>{e}</code>", parse_mode="HTML")


async def publish_long_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/publish_long [topic] — builds and publishes a complete 16:9 multi-chapter masterclass to YouTube."""
    msg = update.effective_message
    from tools import long_video_studio, youtube_publisher

    topic = " ".join(context.args).strip() or "Smart Money Concepts Complete Masterclass"
    await msg.reply_text(
        f"🎬 **جاري إنتاج الماستر كلاس الكامل (16:9 Landscape) لقناتك Core Trade AI!**\n"
        f"📌 الموضوع: {topic}\n"
        f"⚡ جاري توليد الفصول، الرندرة الجرافيكية، الصوت العصبي لكل فصل، ودمج الفيديو الكامل..."
    )

    try:
        chapters = [
            {
                "title": "The Hidden Wall Street Architecture",
                "subtitle": "Why 95% of retail technical indicators are engineered to fail.",
                "points": [
                    "Retail liquidity pools act as fuel for market makers",
                    "High-frequency algorithms execute stop runs before true expansion",
                    "Why RSI and MACD give false signals in trending markets",
                    "The shift from retail trading to institutional order tracking",
                ],
                "script": "Welcome to Core Trade AI. If you've been trading financial markets, you've likely felt that the market is watching your stop loss. The truth is: it is. In this masterclass, we uncover how hedge funds and central banks actually engineer liquidity.",
                "theme_color": "#ef4444",
            },
            {
                "title": "Smart Money Concepts: Order Blocks & Imbalances",
                "subtitle": "Tracking institutional accumulation zones with mathematical precision.",
                "points": [
                    "Identifying the true Order Block before displacement",
                    "Fair Value Gaps (FVG) and algorithmic rebalancing",
                    "The difference between high-volume accumulation and noise",
                    "How to mark pristine institutional entry zones",
                ],
                "script": "Institutional players cannot enter positions with a single click. Their orders are so massive they create structural footprints known as Order Blocks and Fair Value Gaps. When displacement occurs, algorithms leave imbalances that act like magnets pulling price back.",
                "theme_color": "#06b6d4",
            },
            {
                "title": "Liquidity Sweeps & Stop Run Mechanics",
                "subtitle": "How smart money triggers liquidations above equal highs and lows.",
                "points": [
                    "Buy-side vs Sell-side liquidity pools",
                    "The psychology of double tops and false breakout traps",
                    "Recognizing the turtle soup and false wick reversal",
                    "Entering on the re-test of the sweep",
                ],
                "script": "Every time retail traders see a clean double top, they place stop losses right above it. To an institutional algorithm, that cluster of stops is free liquidity. The market spikes above the highs, fills massive institutional short orders, and immediately reverses.",
                "theme_color": "#eab308",
            },
            {
                "title": "Algorithmic Risk Management & Quantitative Edge",
                "subtitle": "The mathematical formula that separates profitable traders from gamblers.",
                "points": [
                    "Asymmetric risk to reward: Minimum 1 to 3 ratio",
                    "Dynamic position sizing based on true market volatility",
                    "Eliminating emotional bias through systematic rule sets",
                    "The compounding power of disciplined execution",
                ],
                "script": "Even with a 45% win rate, a quantitative trader with a 1 to 3 risk-to-reward ratio will outperform 99% of discretionary traders. Wealth is built through asymmetric payoff and disciplined position sizing, not by predicting every candle.",
                "theme_color": "#10b981",
            },
            {
                "title": "The Core Trade AI Advantage",
                "subtitle": "Automating your edge with algorithmic precision.",
                "points": [
                    "Real-time liquidity detection algorithms",
                    "Automated alerts on high-probability institutional setups",
                    "Continuous backtesting across multi-asset portfolios",
                    "Join the future of quantitative smart money trading",
                ],
                "script": "At Core Trade AI, our mission is simple: level the playing field by providing retail traders with the same algorithmic intelligence used by proprietary trading desks. Subscribe to our channel, join our community, and start trading with the algorithm.",
                "theme_color": "#38bdf8",
            },
        ]

        res = await long_video_studio.assemble_long_form_video(
            title=f"{topic} (Full Masterclass)",
            chapters=chapters,
        )

        yt_msg = ""
        if youtube_publisher.is_authenticated():
            yt_res = await youtube_publisher.upload_video(
                video_path=Path(res["video_path"]),
                title=f"{res['title']} | Core Trade AI",
                description=res["description"],
                privacy_status="public",
                is_short=False,
                tags=["trading", "smc", "forex", "gold", "crypto", "smartmoney", "algo"],
            )
            yt_msg = f"\n🚀 **تم نشر الفيديو الطويل مباشرة على يوتيوب!**\n🔗 **الرابط:** {yt_res['url']}"

        await msg.reply_text(
            f"🎉 **تم الانتهاء من إنتاج الماستر كلاس الطويل!**\n\n"
            f"📺 **العنوان:** {res['title']}\n"
            f"⚖️ **الحجم:** {res['file_size_mb']} MB (1080p Widescreen)\n"
            f"📑 **الفصول (Timestamps):**\n" + "\n".join(res["timestamps"]) +
            yt_msg
        )
    except Exception as e:
        log.error("Error in publish_long_command:\n%s", traceback.format_exc())
        await msg.reply_text(f"❌ حدث خطأ أثناء إنتاج الفيديو الطويل:\n<code>{e}</code>", parse_mode="HTML")


async def tiktok_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/tiktok [publish [topic] | upload [video_path] | status] — manages TikTok publishing & creation."""
    msg = update.effective_message
    reply = msg.reply_to_message
    from tools import tiktok_publisher, video_assembler

    args = context.args or []
    sub = (args[0].lower() if args else "").strip()

    # Case 1: Replied to a video -> upload to TikTok directly
    if reply and (reply.video or reply.video_note or reply.document):
        tg_doc = reply.video or reply.video_note or reply.document
        await msg.reply_text("⏳ جاري تنزيل الفيديو المردود عليه لرفعه إلى تيك توك...")
        f_obj = await tg_doc.get_file()
        ts = int(time.time())
        local_video = config.BASE_DIR / "repos_cache" / f"tiktok_upload_{ts}.mp4"
        await f_obj.download_to_drive(str(local_video))
        caption = " ".join(args).strip() or "Smart Money Concepts & Algorithmic Trading #trading #forex #smc #crypto #fyp"
        await msg.reply_text("🚀 جاري رفع الفيديو تلقائياً إلى تيك توك عبر المتصفح الآلي...")
        try:
            res = await tiktok_publisher.upload_video(video_path=local_video, caption=caption)
            await msg.reply_text(f"✅ {res['message']}\n📝 الكابشن: {res['caption']}")
        except Exception as e:
            await msg.reply_text(f"❌ فشل رفع الفيديو إلى تيك توك: {e}")
        return

    # Case 2: Produce & publish a new short video to TikTok & YouTube
    if sub in ("publish", "نزل", "انشر", "create", "make") or (len(args) > 0 and sub != "upload" and sub != "status" and not Path(args[0]).exists()):
        topic = " ".join(args[1:] if sub in ("publish", "نزل", "انشر", "create", "make") else args).strip()
        await msg.reply_text(
            f"🎬 **جاري إنتاج فيديو احترافي متعدد المشاهد ونشره فوراً على تيك توك ويوتيوب!**\n"
            f"📌 الموضوع: {topic or 'استراتيجيات التداول الذكي (SMC)'}\n"
            f"⚡ جاري رندرة 4 شارتات منفصلة + صوت عصبي + موسيقى لو فاي + كابشن كاريوكي..."
        )
        try:
            res = await video_assembler.autonomous_publish_short(
                topic=topic,
                language="ar" if re.search(r"[\u0600-\u06FF]", topic) else "en",
                publish_to_tiktok=True,
                publish_to_youtube=True,
            )
            final_video = Path(res["video_path"])
            yt_url = res.get("youtube_url") or (res.get("youtube") or {}).get("url") or "قيد المعالجة"
            tt_status = res.get("tiktok_status") or ((res.get("tiktok") or {}).get("message") if (res.get("tiktok") or {}).get("published") else "جاهز")
            with open(final_video, "rb") as vf:
                await msg.reply_video(
                    video=vf,
                    caption=(
                        f"🎉 **تم إنتاج ونشر الفيديو بنجاح على تيك توك ويوتيوب!**\n\n"
                        f"🎬 **العنوان**: {res['title']}\n"
                        f"📱 **تيك توك**: {tt_status}\n"
                        f"🔗 **يوتيوب**: {yt_url}\n\n"
                        f"⚡ 4 مشاهد حركية + كابشن نيون كلمة بكلمة!"
                    )
                )
        except Exception as e:
            log.error("Error in tiktok publish:\n%s", traceback.format_exc())
            await msg.reply_text(f"❌ حدث خطأ أثناء الإنتاج والنشر على تيك توك:\n<code>{e}</code>", parse_mode="HTML")
        return

    # Case 3: Explicit upload by file path
    if sub == "upload":
        if len(args) < 2:
            await msg.reply_text(
                "🎬 **طرق النشر على تيك توك:**\n\n"
                "1. **إنتاج ونشر فيديو فوري جديد:**\n`/tiktok publish موضوع الفيديو` أو `/publish_short`\n\n"
                "2. **رفع فيديو محدد موجود بالسيرفر:**\n`/tiktok upload videos/my_video.mp4 [الكابشن]`\n\n"
                "3. **رفع أي فيديو موجود بالمحادثة:**\nرد على الفيديو واكتب: `/tiktok [الكابشن]`"
            )
            return
        v_path = args[1]
        caption = " ".join(args[2:]).strip() or "Smart Money Concepts with Core Trade AI #trading #forex #smc"
        await msg.reply_text("🚀 جاري رفع الفيديو تلقائياً إلى حساب تيك توك عبر المتصفح الآلي...")
        try:
            res = await tiktok_publisher.upload_video(video_path=v_path, caption=caption)
            await msg.reply_text(f"✅ {res['message']}\n📝 الكابشن: {res['caption']}")
        except Exception as e:
            await msg.reply_text(f"❌ فشل رفع الفيديو إلى تيك توك: {e}")
        return

    # Case 4: Status check
    auth = tiktok_publisher.is_authenticated()
    if auth:
        await msg.reply_text(
            "✅ **حساب تيك توك موثق وجاهز 100% للنشر التلقائي!**\n\n"
            "الأوامر المتاحة للنشر الفوري:\n"
            "• `/tiktok publish [الموضوع]` — ينتج فيديو كامل بـ 4 مشاهد وينشره على تيك توك ويوتيوب فوراً\n"
            "• `/publish_short [الموضوع]` — استوديو الشورتس الشامل (يوتيوب وتيك توك معاً)\n"
            "• رد على أي فيديو في الشات واكتب: `/tiktok` لرفعه فوراً لحسابك\n"
            "• أو اطلب مني بالرسائل العادية أو الفويس: *'نزل فيديو على تيك توك عن الذهب'*"
        )
    else:
        await msg.reply_text(
            "⚠️ **حساب تيك توك غير مسجل بعد!**\n\n"
            "لتفعيله بسهولة:\n"
            "1. افتح مجلد البوت على جهازك.\n"
            "2. شغّل الملف `setup_tiktok.bat` لمرة واحدة.\n"
            "3. سجّل دخولك إلى تيك توك ثم أغلق المتصفح لحفظ الجلسة للأبد."
        )


async def publish_long_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/publish_long or /masterclass [topic] — generates high-end 60FPS motion graphics masterclass (16:9 1080p)."""
    msg = update.effective_message
    from tools import motion_studio

    topic = " ".join(context.args).strip() if context.args else "استراتيجية صيد السيولة والأوردر بلوك للذهب"

    await msg.reply_text(
        f"🎬 **جاري تشغيل استوديو الموشن جرافيك العالمي (Motion Video Studio)!**\n\n"
        f"📌 **الموضوع:** {topic}\n"
        f"⚡ **التقنية:** Remotion 60FPS + فيزياء النوابض (Spring Physics)\n"
        f"📈 **العناصر:** شموع متحركة لايف + كروت منبثقة بتطلع وتنزل + فصول متعددة + تعليق صوتي عصبي استوديو\n\n"
        f"⏳ جاري كتابة السيناريو ورسم الشارتات وتصيير الفيديو..."
    )

    try:
        res = await motion_studio.generate_motion_masterclass(topic=topic, ratio="16:9")
        final_video = Path(res["video_path"])

        with open(final_video, "rb") as vf:
            await msg.reply_video(
                video=vf,
                caption=(
                    f"🏆 **تم إنتاج الماستركلاس الاحترافي بنجاح!**\n\n"
                    f"🎬 **العنوان:** {res['topic']}\n"
                    f"📐 **الأبعاد:** 1920x1080 (16:9 YouTube Masterclass)\n"
                    f"⚡ **موشن جرافيك حقيقي 60FPS:** شموع مرسومة لايف، كروت تطفو وتنزلق، تقسيم فصول، وصوت استوديو!\n"
                    f"📁 **الحجم:** {res['size_mb']} MB"
                )
            )
    except Exception as e:
        log.error("Error in publish_long_command:\n%s", traceback.format_exc())
        await msg.reply_text(f"❌ حدث خطأ أثناء إنتاج الماستركلاس:\n<code>{e}</code>", parse_mode="HTML")


async def fruit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/fruit [character] [topic] — generates viral 9:16 talking fruit / object comedy shorts with Remotion 60FPS."""
    msg = update.effective_message
    from tools import motion_studio

    args = context.args or []
    valid_chars = ["orange", "apple", "avocado", "banana", "lemon", "bitcoin", "coffee"]
    character = "orange"
    topic = "مستر برتقال في خطر والخلاط"

    if args:
        if args[0].lower() in valid_chars:
            character = args[0].lower()
            if len(args) > 1:
                topic = " ".join(args[1:])
        else:
            topic = " ".join(args)

    await msg.reply_text(
        f"🍊 **جاري تشغيل استوديو الفواكه المتكلمة (Talking Character Studio)!**\n\n"
        f"🎭 **الشخصية:** {character}\n"
        f"📌 **الموضوع:** {topic}\n"
        f"✨ **التقنية:** Remotion 60FPS + عيون ترمش وتتحرك + فم يتزامن مع مخارج الحروف + صوت كرتوني مرح\n\n"
        f"⏳ جاري كتابة السيناريو الكوميدي وتوليد الصوت وتصيير الفيديو..."
    )

    try:
        res = await motion_studio.generate_talking_fruit_short(topic=topic, character=character)
        final_video = Path(res["video_path"])

        with open(final_video, "rb") as vf:
            await msg.reply_video(
                video=vf,
                caption=(
                    f"🍊 **تم إنتاج فيديو الفاكهة المتكلمة بنجاح!**\n\n"
                    f"🎭 **الشخصية:** {res['character']}\n"
                    f"🎬 **القصة:** {res['topic']}\n"
                    f"📐 **الأبعاد:** 1080x1920 (9:16 TikTok / Reels / Shorts)\n"
                    f"✨ **عيون ترمش وتتبع + فم يتكلم مع مخارج الصوت + نظارة شمسية وكروت قافزة!**\n"
                    f"📁 **الحجم:** {res['size_mb']} MB"
                )
            )
    except Exception as e:
        log.error("Error in fruit_command:\n%s", traceback.format_exc())
        await msg.reply_text(f"❌ حدث خطأ أثناء إنتاج فيديو الفاكهة المتكلمة:\n<code>{e}</code>", parse_mode="HTML")


async def dub_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/dub [url or topic or reply to video] — Auto-dubs viral Arabic animation/drama shorts into Hollywood English + High-CPM SEO."""
    msg = update.effective_message
    args = context.args or []
    target = " ".join(args).strip() if args else ""

    # Check if user replied to a video or document
    video_file_path = None
    if msg.reply_to_message and (msg.reply_to_message.video or msg.reply_to_message.document):
        rep = msg.reply_to_message
        media_obj = rep.video or rep.document
        if media_obj and getattr(media_obj, "file_name", "").endswith((".mp4", ".mov", ".mkv", ".webm")) or rep.video:
            await msg.reply_text("📥 جاري تنزيل ملف الفيديو المرسل مباشرة من تليجرام للبدء في دبلجته...")
            downloads_dir = Path("C:/Projects/adham-agent/downloads")
            downloads_dir.mkdir(parents=True, exist_ok=True)
            tf = await media_obj.get_file()
            video_file_path = str(downloads_dir / f"telegram_dub_{int(time.time())}.mp4")
            await tf.download_to_drive(video_file_path)
            target = video_file_path

    if not target:
        target = "https://www.youtube.com/shorts/OKt7UbQ8cUE"

    target_display = "ملف فيديو مرفوع 📹" if video_file_path else target

    await msg.reply_text(
        f"🎙️ **تشغيل محرك الدبلجة السينمائية العالمية (Auto Dubbing Engine)!**\n\n"
        f"🎯 **الهدف:** {target_display}\n"
        f"🇺🇸 **اللغة:** دبلجة إنجليزية بهوليوود ستايل (تمثيل صوتي متعدد الشخصيات)\n"
        f"🛡️ **الحماية:** فلاتر ذكية مضادة للحظر (Anti-Ban & Zero Reused Content)\n"
        f"📈 **السيو:** استخراج حزمة SEO كاملة لاستهداف الدول الأعلى ربحاً (US/UK/Canada High RPM).\n\n"
        f"⏳ جاري التحميل والتحليل الصوتي وتجهيز الدبلجة... سأرسل لك الفيديو هنا فور اكتماله!"
    )

    import sys
    sys.path.insert(0, r"C:\Projects\motion-video-studio")
    from auto_dubbing_engine import AutoDubbingEngine
    engine = AutoDubbingEngine()

    try:
        if target.startswith("http") or (video_file_path and os.path.exists(video_file_path)):
            res = await engine.process_video_url(target)
        else:
            found = engine.search_viral_arabic_shorts(target, max_results=1)
            if not found:
                await msg.reply_text("❌ لم يتم العثور على فيديوهات شورتس عربية مطابقة للبحث.")
                return
            best_url = found[0]["url"]
            await msg.reply_text(f"🔍 تم رصد أنسب فيديو تريند:\n**{found[0]['title']}**\n🔗 {best_url}\n⏳ جاري الدبلجة والإنتاج...")
            res = await engine.process_video_url(best_url)
    except Exception as e:
        import traceback
        log.error("Error in dub_command:\n%s", traceback.format_exc())
        await msg.reply_text(f"⚠️ حدث خطأ أثناء الدبلجة: {str(e)}")


async def fruitdrama_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/fruitdrama [topic] — generates viral Pixar Fruit Drama storytelling shorts (Strawberry, Banana, Apple) with Remotion 60FPS."""
    msg = update.effective_message
    from tools import motion_studio

    args = context.args or []
    topic = " ".join(args).strip() if args else "الموزة خانت الفراولة بطريقة صادمة 💔"

    await msg.reply_text(
        f"🎬 **جاري تشغيل استوديو دراما الفواكه بيكسار 3D (Pixar Fruit Drama Engine)!**\n\n"
        f"📖 **القصة:** {topic}\n"
        f"🍓 **الشخصيات:** الفراولة الحزينة + الموزة الخائنة + التفاحة المتواطئة\n"
        f"📐 **الأبعاد:** 1080x1920 (9:16 Shorts / Reels / TikTok)\n"
        f"✨ **المميزات:** محاكاة 3D سينمائية + عيون بيكسار معبرة + فم متزامن + اهتزاز كاميرا للصدمة + ترجمة عربية Cairo-Bold + أصوات ذكاء اصطناعي متعددة\n\n"
        f"⏳ جاري تأليف المشاهد وتوليد الأصوات وتصيير الفيديو..."
    )

    try:
        res = await motion_studio.generate_fruit_drama_short(topic=topic)
        final_video = Path(res["video_path"])

        with open(final_video, "rb") as vf:
            await msg.reply_video(
                video=vf,
                caption=(
                    f"🎬 **تم إنتاج حلقة دراما الفواكه بيكسار 3D بنجاح!**\n\n"
                    f"💔 **القصة:** {res['topic']}\n"
                    f"🍓 **أبطال الحلقة:** الفراولة والموزة والتفاحة\n"
                    f"📐 **الأبعاد:** 1080x1920 (9:16 Shorts / Reels / TikTok)\n"
                    f"✨ **إخراج كامل:** زوايا كاميرا درامية، مؤثرات صدمة وزووم، وترجمة عربية متحركة\n"
                    f"📁 **الحجم:** {res['size_mb']} MB"
                )
            )
    except Exception as e:
        log.error("Error in fruitdrama_command:\n%s", traceback.format_exc())
        await msg.reply_text(f"❌ حدث خطأ أثناء إنتاج دراما الفواكه:\n<code>{e}</code>", parse_mode="HTML")


async def fight_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/fight — generates the 3-round epic boxing match between Avocado and Apple."""
    msg = update.effective_message
    from tools import motion_studio

    await msg.reply_text(
        "🥊 **جاري إطلاق نزال المصارعة الملحمي بين الأفوكادو والتفاحة!**\n\n"
        "🏟️ **الحلبة:** حلبة مصارعة كاملة + حبال ديناميكية + كشافات ستاديوم + جمهور يهتف\n"
        "⚡ **النزال:** 3 جولات كاملة (Round 1 + Round 2 + Final K.O.)\n"
        "🍋 **الحكم:** ليمونة بقميص الحكام وصفارة يحسم النزال\n"
        "🎙️ **التعليق:** صوت معلق رياضي حماسي بنبرة WWE\n\n"
        "⏳ جاري تجهيز الحلبة وتصيير الفيديو بدقة 1080x1920..."
    )

    try:
        res = await motion_studio.generate_fruit_fight_match()
        final_video = Path(res["video_path"])

        with open(final_video, "rb") as vf:
            await msg.reply_video(
                video=vf,
                caption=(
                    "🥊 **تم إنتاج فيديو نزال المصارعة بنجاح!**\n\n"
                    "🥑 **الأفوكادو ضد التفاحة 🍎 (3 جولات)**\n"
                    "🏆 **الفائز بالضربة القاضية:** مستر أفوكادو!\n"
                    "📐 **الأبعاد:** 1080x1920 (9:16 TikTok / Reels)\n"
                    f"📁 **الحجم:** {res['size_mb']} MB"
                )
            )
    except Exception as e:
        log.error("Error in fight_command:\n%s", traceback.format_exc())
        await msg.reply_text(f"❌ حدث خطأ أثناء إنتاج فيديو النزال:\n<code>{e}</code>", parse_mode="HTML")


async def nano_banana_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/banana or /nano [topic] — Runs the autonomous studio: Seedane 2.5 30s + Gemini Pro (Belal Hatb) + Concat/VideoStitcher."""
    msg = update.effective_message
    topic = " ".join(context.args).strip() if context.args else "انكسار البرتقالة والعودة القوية بعد الخيانة"

    await msg.reply_text(
        f"🍌 **استوديو Nano Banana السينمائي المستقل (Veo Pro & Concat):**\n\n"
        f"🎬 **القصة:** {topic}\n"
        f"✨ **المحركات النشطة:**\n"
        f"  • هندسة السيناريو: نمط Seedane 2.5 30s\n"
        f"  • محرك الفيديو: Google Veo (حساب Belal Hatb Pro ⭐)\n"
        f"  • المونتاج ودمج الصوت: محرك Concat / VideoStitcher\n\n"
        f"⏳ جاري تشغيل خط الإنتاج وتوليد المشاهد وإرسال الفيديو النهائي لك فوراً..."
    )

    try:
        from tools.autonomous_studio_pipeline import autonomous_studio
        async def _notify(text: str):
            try:
                await msg.reply_text(text)
            except Exception:
                pass

        ts = int(time.time())
        out_clip = config.BASE_DIR.parent / "workspace_data" / "youtube_ready" / f"banana_studio_{ts}.mp4"

        prompt = (
            f"3D Pixar style animated video, vertical 9:16 format. Character continuity: "
            f"Cute anthropomorphic orange character with blue baseball cap. Scene: {topic}. "
            f"Cinematic lighting, expressive facial micro-expressions, 24fps motion, 8k render."
        )

        video_path = await autonomous_studio.generate_gemini_video_clip(
            prompt=prompt,
            output_mp4_path=out_clip,
            notify_cb=_notify
        )

        if video_path and video_path.exists() and video_path.stat().st_size > 1024:
            with open(video_path, "rb") as vf:
                await msg.reply_video(
                    video=vf,
                    caption=(
                        f"🍌 **تم إنتاج فيديو Nano Banana بنجاح!**\n\n"
                        f"🎬 **القصة:** {topic}\n"
                        f"📐 **الأبعاد:** 9:16 (Shorts / Reels)\n"
                        f"⭐️ **المحرك:** Google Veo (Belal Hatb Pro)\n"
                        f"✂️ **المونتاج:** Concat / VideoStitcher Engine\n"
                        f"📁 **الحجم:** {round(video_path.stat().st_size / (1024*1024), 2)} MB"
                    )
                )
        else:
            await msg.reply_text("⚠️ لم يتم استخراج ملف الفيديو، جاري فحص سجل التنزيلات...")
    except Exception as e:
        log.error("Error in nano_banana_command:\n%s", traceback.format_exc())
        await msg.reply_text(f"❌ حدث خطأ أثناء تشغيل استوديو بنانا:\n<code>{e}</code>", parse_mode="HTML")


async def cinema_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/cinema [drama|fight] — generates hyper-realistic cinematic storyboard and treatment."""
    msg = update.effective_message
    from tools import motion_studio

    template = "drama"
    if context.args:
        arg = context.args[0].lower()
        if "fight" in arg or "kombat" in arg or "قتال" in arg or "ملاكمة" in arg:
            template = "fight"
        elif "drama" in arg or "apple" in arg or "تفاحة" in arg or "دراما" in arg:
            template = "drama"

    genre_label = "دراما التفاحة والأمومة الصامدة (Sad Apple Mother Drama)" if template == "drama" else "قتال مورتال كومبات الفواكه (Mortal Kombat Fruit Brawl)"
    await msg.reply_text(
        f"🎬 **جاري تشغيل استوديو الإخراج السينمائي فائق الواقعية (AI Cinematic Studio)!**\n\n"
        f"🎭 **القالب المختار:** {genre_label}\n"
        f"✨ **المعايير:** ARRI Alexa 65 + Unreal Engine 5.4 + Sub-surface scattering + فيزياء الكاميرا الواقعية\n\n"
        f"⏳ جاري هندسة البرومبتات الـ 8K، وتوزيع اللقطات، وتوليد ملف المعالجة الإخراجية..."
    )

    try:
        res = await motion_studio.generate_cinematic_storyboard(template=template)
        md_path = Path(res["md_path"])

        preview_text = res.get("treatment_preview", "")
        if len(preview_text) > 3500:
            preview_text = preview_text[:3500] + "\n\n... (المعالجة كاملة في الملف المرفق أدناه)"

        await msg.reply_text(
            f"🎬 **تم إنتاج الستوريبورد والمعالجة السينمائية بنجاح!**\n\n"
            f"{preview_text}"
        )

        if md_path.exists():
            with open(md_path, "rb") as mf:
                await msg.reply_document(
                    document=mf,
                    filename=md_path.name,
                    caption=f"📄 ملف المعالجة السينمائية الكامل ({genre_label})"
                )
    except Exception as e:
        log.error("Error in cinema_command:\n%s", traceback.format_exc())
        await msg.reply_text(f"❌ حدث خطأ أثناء إنتاج الستوريبورد السينمائي:\n<code>{e}</code>", parse_mode="HTML")


async def autocut_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/autocut [video_path] — trims dead air and silence using video-use heuristics."""
    msg = update.effective_message
    reply = msg.reply_to_message
    from tools import video_director

    video_to_process = None
    if reply and (reply.video or reply.video_note or reply.document):
        tg_doc = reply.video or reply.video_note or reply.document
        await msg.reply_text("⏳ جاري تنزيل الفيديو المردود عليه لقص فترات الصمت...")
        f_obj = await tg_doc.get_file()
        ts = int(time.time())
        local_video = config.BASE_DIR / "repos_cache" / f"autocut_src_{ts}.mp4"
        await f_obj.download_to_drive(str(local_video))
        video_to_process = local_video
    elif context.args:
        video_to_process = Path(" ".join(context.args).strip())

    if not video_to_process or not video_to_process.exists():
        await msg.reply_text(
            "✂️ **محرك القص الذكي وحذف الصمت (video-use Engine):**\n\n"
            "• رد على أي فيديو بكلمة `/autocut` ليقوم باكتشاف الصمت وحذفه تلقائياً مع تنعيم الصوت 30ms لمنع الفرقعة!\n"
            "• أو اكتب: `/autocut videos/my_video.mp4`"
        )
        return

    await msg.reply_text("✂️ جاري تحليل الصمت والتردد وقص الفراغات بأمان... ⏳")
    try:
        res = await video_director.auto_cut_silence(video_to_process)
        out_v = Path(res["output_path"])
        if out_v.exists():
            with open(out_v, "rb") as vf:
                await msg.reply_video(
                    video=vf,
                    caption=(
                        f"✨ **تم القص والتنعيم الصوتي بنجاح (video-use):**\n"
                        f"• عدد القصات: {res['cuts_count']}\n"
                        f"• الوقت المقتطع: {res['trimmed_seconds']}s\n"
                        f"• المدة: {res['new_duration']}s (بدلاً من {res['original_duration']}s)"
                    )
                )
    except Exception as e:
        await msg.reply_text(f"❌ خطأ أثناء القص: {e}")


async def grade_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/grade [preset] — applies cinematic color grading (neutral_punch, warm_cinematic, cool_tech, subtle)."""
    msg = update.effective_message
    reply = msg.reply_to_message
    from tools import video_director

    video_to_process = None
    if reply and (reply.video or reply.video_note or reply.document):
        tg_doc = reply.video or reply.video_note or reply.document
        await msg.reply_text("⏳ جاري تنزيل الفيديو لتطبيق التلوين السينمائي...")
        f_obj = await tg_doc.get_file()
        ts = int(time.time())
        local_video = config.BASE_DIR / "repos_cache" / f"grade_src_{ts}.mp4"
        await f_obj.download_to_drive(str(local_video))
        video_to_process = local_video
    elif context.args and Path(context.args[0]).exists():
        video_to_process = Path(context.args[0])

    preset = "neutral_punch"
    if context.args:
        for arg in context.args:
            if arg.lower() in video_director.GRADE_PRESETS:
                preset = arg.lower()
                break

    if not video_to_process or not video_to_process.exists():
        await msg.reply_text(
            "🎨 **محرك التلوين السينمائي (Color Grading Engine):**\n\n"
            "• رد على أي فيديو بالأمر: `/grade [preset]`\n"
            "• الفلاتر المتاحة:\n"
            "  - `neutral_punch`: تباين ونقاء حاد طبيعي (الأفضل والأكثر توازناً)\n"
            "  - `warm_cinematic`: دفء هوليوودي وتباين سينمائي عميق\n"
            "  - `cool_tech`: أزرق تقني بارد ونظيف\n"
            "  - `subtle`: تنظيف خفيف جداً بدون تغيير الألوان\n\n"
            "مثال: رد بـ `/grade warm_cinematic`"
        )
        return

    await msg.reply_text(f"🎨 جاري تطبيق التلوين السينمائي `{preset}` عبر FFmpeg... ⏳")
    try:
        out_v = await video_director.apply_color_grade(video_to_process, preset=preset)
        if out_v.exists():
            with open(out_v, "rb") as vf:
                await msg.reply_video(
                    video=vf,
                    caption=f"🎬 **تم التلوين السينمائي بنجاح:**\n• الفلتر: `{preset}`"
                )
    except Exception as e:
        await msg.reply_text(f"❌ خطأ أثناء التلوين: {e}")


async def concat_app_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/concat_app — provides download link and features for Concat (free CapCut replacement)."""
    msg = update.effective_message
    from tools import video_director
    info = await video_director.get_concat_app_info()
    features = "\n".join(f"• {f}" for f in info["features"])
    text = (
        f"🎬 **{info['app_name']} ({info['version']})**\n"
        f" البديل الحقيقي والمجاني 100% لبرنامج CapCut بدون أي اشتراكات أو علامات مائية!\n\n"
        f"📥 **رابط التنزيل المباشر لويندوز:**\n"
        f"{info['installer_url']}\n\n"
        f"✨ **أبرز المميزات:**\n{features}\n\n"
        f"🔗 **المستودع الرسمي:** {info['official_repo']}"
    )
    await msg.reply_text(text)


def main() -> None:
    init_db()

    app = Application.builder().token(config.TELEGRAM_TOKEN).post_init(post_init).build()

    owner = filters.User(user_id=config.OWNER_ID)

    app.add_handler(CommandHandler("start", start, filters=owner))
    app.add_handler(CommandHandler(["reset", "clear", "wipe", "clean"], reset_cmd, filters=owner))
    app.add_handler(CommandHandler("restart", restart_cmd, filters=owner))
    app.add_handler(CommandHandler("update", update_cmd, filters=owner))
    app.add_handler(CommandHandler("sync", update_cmd, filters=owner))
    app.add_handler(CommandHandler("pip", pip_cmd, filters=owner))
    app.add_handler(CommandHandler("cmd", cmd_cmd, filters=owner))
    app.add_handler(CommandHandler("image", image_command, filters=owner))
    app.add_handler(CommandHandler("leads", leads_command, filters=owner))
    app.add_handler(CommandHandler("hq", hq_command, filters=owner))
    app.add_handler(CommandHandler("app", hq_command, filters=owner))
    app.add_handler(CommandHandler("social", social_command, filters=owner))
    app.add_handler(CommandHandler("socials", social_command, filters=owner))
    app.add_handler(CommandHandler("platforms", social_command, filters=owner))
    app.add_handler(CommandHandler("audience", audience_command, filters=owner))
    app.add_handler(CommandHandler("addaudience", addaudience_command, filters=owner))
    app.add_handler(CommandHandler("crm", audience_command, filters=owner))
    app.add_handler(CommandHandler("skills", skills_command, filters=owner))
    app.add_handler(CommandHandler("repo", repo_command, filters=owner))
    app.add_handler(CommandHandler("findrepo", findrepo_command, filters=owner))
    app.add_handler(CommandHandler("download", download_command, filters=owner))
    app.add_handler(CommandHandler("searchrepo", findrepo_command, filters=owner))
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
    app.add_handler(CommandHandler(["panel", "agency"], panel_command, filters=owner))
    app.add_handler(CommandHandler("gaza", gaza_command, filters=owner))
    app.add_handler(CommandHandler("radar", radar_command, filters=owner))
    app.add_handler(CommandHandler("hunt", hunt_command, filters=owner))
    app.add_handler(CommandHandler("gigs", hunt_command, filters=owner))
    app.add_handler(CommandHandler("tunnel", tunnel_command, filters=owner))
    app.add_handler(CommandHandler("proposal", proposal_command, filters=owner))
    app.add_handler(CommandHandler("carousel", carousel_command, filters=owner))
    app.add_handler(CommandHandler("scrape", scrape_command, filters=owner))
    app.add_handler(CommandHandler("license", license_command, filters=owner))
    app.add_handler(CommandHandler("cash", cash_command, filters=owner))
    app.add_handler(CommandHandler("balance", cash_command, filters=owner))
    app.add_handler(CommandHandler("mikrotik", mikrotik_command, filters=owner))
    app.add_handler(CommandHandler("audit", audit_command, filters=owner))
    app.add_handler(CommandHandler("gmaps", gmaps_command, filters=owner))
    app.add_handler(CommandHandler("caption", caption_command, filters=owner))
    app.add_handler(CommandHandler("yt_stats", yt_stats_command, filters=owner))
    app.add_handler(CommandHandler("yt_upload", yt_upload_command, filters=owner))
    app.add_handler(CommandHandler("publish_short", publish_short_command, filters=owner))
    app.add_handler(CommandHandler("publish_long", publish_long_command, filters=owner))
    app.add_handler(CommandHandler("masterclass", publish_long_command, filters=owner))
    app.add_handler(CommandHandler("fruit", fruit_command, filters=owner))
    app.add_handler(CommandHandler("fruitdrama", fruitdrama_command, filters=owner))
    app.add_handler(CommandHandler("dub", dub_command, filters=owner))
    app.add_handler(CommandHandler("autodub", dub_command, filters=owner))
    app.add_handler(CommandHandler("pixar", fruitdrama_command, filters=owner))
    app.add_handler(CommandHandler("banana", nano_banana_command, filters=owner))
    app.add_handler(CommandHandler("nano", nano_banana_command, filters=owner))
    app.add_handler(CommandHandler("talking_object", fruit_command, filters=owner))
    app.add_handler(CommandHandler("fight", fight_command, filters=owner))
    app.add_handler(CommandHandler("wrestling", fight_command, filters=owner))
    app.add_handler(CommandHandler("cinema", cinema_command, filters=owner))
    app.add_handler(CommandHandler("drama", cinema_command, filters=owner))
    app.add_handler(CommandHandler("storyboard", cinema_command, filters=owner))
    app.add_handler(CommandHandler("tiktok", tiktok_command, filters=owner))
    app.add_handler(CommandHandler("autocut", autocut_command, filters=owner))
    app.add_handler(CommandHandler("grade", grade_command, filters=owner))
    app.add_handler(CommandHandler("concat_app", concat_app_command, filters=owner))

    app.add_handler(CommandHandler("reminders", reminders.list_command, filters=owner))
    app.add_handler(CommandHandler("jobs", jobs.jobs_command, filters=owner))
    app.add_handler(CommandHandler("brief", brief.brief_command, filters=owner))
    app.add_handler(CommandHandler("pitch", outreach.pitch_command, filters=owner))
    app.add_handler(CommandHandler("script", script_command, filters=owner))
    app.add_handler(CommandHandler("autoleads", autoleads_command, filters=owner))

    app.add_handler(CallbackQueryHandler(reminders.handle_callback, pattern="^rem:"))
    app.add_handler(CallbackQueryHandler(jobs.handle_callback, pattern="^job:"))
    app.add_handler(CallbackQueryHandler(gmail_tools.handle_callback, pattern="^mail:"))
    app.add_handler(CallbackQueryHandler(handle_panel_callback, pattern="^panel:"))
    app.add_handler(CallbackQueryHandler(handle_social_callback, pattern="^social:"))

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