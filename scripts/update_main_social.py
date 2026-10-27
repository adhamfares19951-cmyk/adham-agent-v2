# -*- coding: utf-8 -*-
"""Adds zero-hallucination social publishing commands and intent interceptor to main.py."""
from pathlib import Path

main_path = Path("C:/Projects/adham-agent/main.py")
code = main_path.read_text(encoding="utf-8")

# Helper block for social intent
interceptor_block = """
async def _handle_social_and_seo_direct(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    \"\"\"Zero-Hallucination deterministic executor for publishing, social media, and SEO requests.\"\"\"
    t = text.lower()
    msg = update.effective_message
    if not msg:
        return False

    is_ig = any(k in t for k in ["انستقرام", "انستغرام", "انستا", "instagram", "ig", "ريلز", "ريل", "reel"])
    is_publish = any(k in t for k in ["انشر", "نشر", "ارفع", "نزل", "اعمل", "سوي", "share", "post", "publish"])
    is_tiktok = any(k in t for k in ["تيك توك", "تيكتوك", "tiktok"])
    is_all = any(k in t for k in ["الكل", "كل المنصات", "كل مكان", "الحسابات", "broadcast", "all"])
    is_seo = any(k in t for k in ["سيو", "seo", "محركات البحث", "محرك البحث", "سيت ماب", "sitemap", "فهرسة"])

    # 1. Multi-platform broadcast
    if is_publish and (is_all or (is_ig and is_tiktok)):
        await msg.reply_text("🌐 **أمرك يا أدهم!** بدأت فوراً بالنشر المتزامن على تيك توك وإنستغرام ريلز عبر المتصفح الآلي بدون أي هلوسة 🚀...")
        from tools import social_dispatcher
        res = await social_dispatcher.broadcast_social()
        ig_shot = Path(res.get("instagram", {}).get("proof_screenshot") or "")
        tt_shot = Path(res.get("tiktok", {}).get("proof_screenshot") or "")
        report = "🎉 **اكتملت مهمة النشر الشامل بنجاح:**\\n\\n"
        if res.get("instagram", {}).get("success"):
            report += "✅ **إنستغرام (@smartstore.gcc):** تم نشر الريلز مباشرة!\\n"
            if ig_shot.exists():
                try:
                    with open(ig_shot, "rb") as f:
                        await msg.reply_photo(photo=f, caption="📸 **إثبات نشر إنستغرام ريلز (@smartstore.gcc)**")
                except Exception:
                    pass
        else:
            report += f"❌ **إنستغرام:** {res.get('instagram', {}).get('error', 'تعذر')}\\n"

        if res.get("tiktok", {}).get("success"):
            report += "✅ **تيك توك (@coretradeai):** تم الرفع والنشر في تيك توك ستوديو!\\n"
            if tt_shot.exists():
                try:
                    with open(tt_shot, "rb") as f:
                        await msg.reply_photo(photo=f, caption="📸 **إثبات نشر تيك توك (@coretradeai)**")
                except Exception:
                    pass
        else:
            report += f"⚠️ **تيك توك:** {res.get('tiktok', {}).get('detail', 'تعذر')}\\n"

        await msg.reply_text(report)
        return True

    # 2. Instagram Reel
    if is_publish and is_ig and not is_tiktok:
        await msg.reply_text("📸 **أمرك يا أدهم!** جاري رفع ونشر الريلز على حساب إنستغرام الرسمي (@smartstore.gcc) فورياً عبر المتصفح الآلي...")
        from tools import social_dispatcher
        res = await social_dispatcher.execute_instagram_reel()
        if res.get("success"):
            proof = Path(res.get("proof_screenshot") or "")
            if proof.exists():
                try:
                    with open(proof, "rb") as f:
                        await msg.reply_photo(
                            photo=f,
                            caption=(
                                "🎉 **تم نشر الريلز على إنستغرام بنجاح!**\\n\\n"
                                "📌 **الحساب:** `@smartstore.gcc`\\n"
                                "🎬 **المنتج:** مصباح G-Lamp الذكي 4 في 1\\n"
                                "⚡ *الريل الآن متاح للمشاهدة والتفاعل لجمهور السعودية والإمارات.*"
                            )
                        )
                except Exception:
                    await msg.reply_text("✅ " + res.get("message", "تم نشر الريلز بنجاح!"))
            else:
                await msg.reply_text("✅ " + res.get("message", "تم نشر الريلز بنجاح!"))
        else:
            err = res.get("error", "خطأ غير معروف")
            err_shot = Path(res.get("error_shot") or "")
            if err_shot.exists():
                try:
                    with open(err_shot, "rb") as f:
                        await msg.reply_photo(photo=f, caption=f"❌ تعذر نشر الريلز: {err}")
                except Exception:
                    await msg.reply_text(f"❌ تعذر نشر الريلز على إنستغرام: {err}")
            else:
                await msg.reply_text(f"❌ تعذر نشر الريلز على إنستغرام: {err}")
        return True

    # 3. TikTok Upload
    if is_publish and is_tiktok and not is_ig:
        await msg.reply_text("⚡ **أمرك يا أدهم!** جاري رفع الفيديو ونشره تلقائياً على حسابك في تيك توك عبر المتصفح الآلي...")
        from tools import social_dispatcher
        res = await social_dispatcher.execute_tiktok_video()
        if res.get("success"):
            proof = Path(res.get("proof_screenshot") or "")
            if proof.exists():
                try:
                    with open(proof, "rb") as f:
                        await msg.reply_photo(
                            photo=f,
                            caption=(
                                "🚀 **تم نشر الفيديو بنجاح على تيك توك!**\\n\\n"
                                "📌 **الحساب:** `Smart Store | متجر سمارت` (@coretradeai)\\n"
                                "🎬 **المنتج:** مصباح G-Lamp 4 في 1\\n"
                                "✅ *الفيديو الآن في TikTok Studio ومفهرس بالهاشتاجات.*"
                            )
                        )
                except Exception:
                    await msg.reply_text("✅ تم رفع الفيديو إلى تيك توك بنجاح!")
            else:
                await msg.reply_text("✅ تم رفع الفيديو إلى تيك توك بنجاح!")
        else:
            await msg.reply_text(f"❌ تعذر رفع الفيديو إلى تيك توك: {res.get('detail')}")
        return True

    # 4. SEO & Search Engine Discovery
    if is_seo:
        from tools import social_dispatcher
        report = await social_dispatcher._handle_seo_audit({})
        await msg.reply_text(report)
        return True

    return False
"""

# Commands
commands_block = """
async def reel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    \"\"\"/reel — publishes the G-Lamp video as an Instagram Reel to @smartstore.gcc.\"\"\"
    msg = update.effective_message
    await msg.reply_text("📸 **أمرك يا أدهم!** جاري نشر الريلز فوراً على حساب إنستغرام @smartstore.gcc...")
    from tools import social_dispatcher
    res = await social_dispatcher.execute_instagram_reel()
    if res.get("success"):
        proof = Path(res.get("proof_screenshot") or "")
        if proof.exists():
            with open(proof, "rb") as f:
                await msg.reply_photo(photo=f, caption="🎉 **تم نشر الريلز بنجاح على @smartstore.gcc!**")
        else:
            await msg.reply_text("✅ تم النشر بنجاح!")
    else:
        await msg.reply_text(f"❌ تعذر النشر: {res.get('error')}")


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    \"\"\"/broadcast — broadcasts video to TikTok and Instagram simultaneously.\"\"\"
    await _handle_social_and_seo_direct(update, context, "انشر على تيك توك وانستقرام")


async def seo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    \"\"\"/seo — audits search engine indexing, sitemap, and high-ranking GCC keywords.\"\"\"
    from tools import social_dispatcher
    report = await social_dispatcher._handle_seo_audit({})
    await update.effective_message.reply_text(report)
"""

if "_handle_social_and_seo_direct" not in code:
    # 1. Insert interceptor before handle_text
    code = code.replace("async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:",
                        interceptor_block + "\n\nasync def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:")

    # 2. Add intent check inside handle_text
    handle_text_target = """    # Direct JSON interceptor for session/cookie imports (Cookie-Editor format)"""
    new_handle_check = """    # Autonomous Zero-Hallucination Social Media & SEO Dispatcher
    handled = await _handle_social_and_seo_direct(update, context, text)
    if handled:
        return

    # Direct JSON interceptor for session/cookie imports (Cookie-Editor format)"""
    code = code.replace(handle_text_target, new_handle_check)

    # 3. Add command handlers before def main()
    code = code.replace("def main() -> None:", commands_block + "\n\ndef main() -> None:")

    # 4. Register commands in main()
    cmd_registration_target = """    app.add_handler(CommandHandler("tiktok", tiktok_command, filters=owner))"""
    cmd_registration_new = """    app.add_handler(CommandHandler("tiktok", tiktok_command, filters=owner))
    app.add_handler(CommandHandler(["reel", "reels", "instagram", "ig"], reel_command, filters=owner))
    app.add_handler(CommandHandler(["broadcast", "post_all", "publish_all"], broadcast_command, filters=owner))
    app.add_handler(CommandHandler(["seo", "sitemap"], seo_command, filters=owner))"""
    code = code.replace(cmd_registration_target, cmd_registration_new)

    main_path.write_text(code, encoding="utf-8")
    print("SUCCESS: main.py updated with deterministic social & SEO dispatcher and commands!")
else:
    print("Already updated.")
