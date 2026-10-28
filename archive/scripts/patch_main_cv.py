with open(r'C:\Projects\adham-agent\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    # 4. SEO & Search Engine Discovery
    if is_seo:
        from tools import social_dispatcher
        report = await social_dispatcher._handle_seo_audit({})
        await msg.reply_text(report)
        return True

    return False"""

replacement = """    # 4. SEO & Search Engine Discovery
    if is_seo:
        from tools import social_dispatcher
        report = await social_dispatcher._handle_seo_audit({})
        await msg.reply_text(report)
        return True

    # 5. Zero-Hallucination CV & PDF Dispatcher
    is_doc_intent = any(k in t for k in ["pdf", "سيرة", "cv", "سي في", "ملف", "السي في", "السيرة", "التقديم", "بي دي اف", "اطباء بلا حدود", "msf", "الطلب", "تنزيل"])
    is_fetch_intent = any(k in t for k in ["هات", "اعمل", "ابعت", "ارسل", "وين", "تنزيل", "تحميل", "بدي", "جهز", "اعطيني"]) or len(t) <= 15
    if is_doc_intent and (is_fetch_intent or "msf" in t or "cv" in t or "سيرة" in t or "pdf" in t):
        await msg.reply_text("📄 **أمرك يا أدهم!** جاري استخراج وإرسال ملف الـ PDF الحقيقي فوراً كمستند مباشر...")
        
        msf_cv = Path(r"C:\\Projects\\adham-agent\\dist_pages\\MSF_Data_Entry_Adham_Alhabbash_CV.pdf")
        if not msf_cv.exists():
            try:
                import subprocess, sys
                subprocess.run([sys.executable, r"C:\\Projects\\adham-agent\\scripts\\generate_msf_cv.py"], check=True)
            except Exception as e:
                log.exception("Failed to build MSF CV on the fly")

        if msf_cv.exists():
            caption = (
                "✅ **تفضل يا أدهم، ملف السيرة الذاتية الأصلي والمخصص لـ MSF France!**\\n\\n"
                "• **المسمى الوظيفي:** Medical Data Entry Operator\\n"
                "• **الحجم:** صفحة واحدة A4 مطابقة 100% لإعلان الوظيفة.\\n"
                "• **رابط تنزيل مباشر بديل:** https://smartglamp.pages.dev/cv.pdf\\n"
                "• **رابط التقديم الرسمي:** https://tally.so/r/NqqLjb"
            )
            try:
                with open(msf_cv, "rb") as doc_file:
                    await msg.reply_document(
                        document=doc_file,
                        filename="MSF_Data_Entry_Adham_Alhabbash_CV.pdf",
                        caption=caption
                    )
                return True
            except Exception as e:
                log.exception("Failed sending reply_document")
                await msg.reply_text("✅ تم تجهيز الملف ويمكنك تنزيله مباشرة من الرابط:\\nhttps://smartglamp.pages.dev/cv.pdf")
                return True

    return False"""

if target in content:
    content = content.replace(target, replacement, 1)
    with open(r'C:\Projects\adham-agent\main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched _handle_social_and_seo_direct in main.py!")
else:
    print("Target not found in main.py")
