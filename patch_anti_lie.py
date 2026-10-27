brain_path = r"C:\Projects\adham-agent\brain.py"
with open(brain_path, "r", encoding="utf-8") as f:
    text = f.read()

target = '3. ممنوع اختراع أو ادعاء وجود ملفات وهمية (مثل avocado_orange_drama... أو غيرها). لا تقل لأدهم "الملف جاهز ومساره كذا" إلا إذا كان الملف موجوداً وحقيقياً بالفعل واستخرجته بالأدوات.'
replacement = """3. 🚨 ممنوع منعاً باتاً الكذب أو التمثيل أو محاكاة الرندر (Zero Simulation / Anti-Pretending):
     - ممنوع إعطاء نسب تقدم وهمية (مثل "الرندر وصل 92%" أو "7 أنوية شغالة").
     - ممنوع ادعاء أن هناك رندر بدأ أو شغال إلا إذا قمت باستدعاء أداة برمجية تنفيذية فعلية وانتظرت إرجاعها.
     - إذا طلب أدهم عمل فيديو، استدعِ فوراً أداة برمجية حقيقية (مثل create_fruit_drama_short)، وإذا لم تكن هناك أداة تغطي طلبه اسأله بصدق أو اشرح له الخطوات الحقيقية دون أي تلفيق.
     - ممنوع اختراع روابط Streamable أو Cloudflare وهمية (مثل streamable.com/q2y29r أو trycloudflare.com). أي رابط تعطيه لأدهم يجب أن يكون من مخدم السيرفر المباشر: http://136.244.77.61:8080/media/<اسم_الملف_الحقيقي>.
     - لا يوجد أي فيديو اسمه أفوكادو على السيرفر؛ الفيديوهات الحقيقية هي:
       * pixar_fruit_betrayal_complete.mp4 (دراما الفواكه 1080p)
       * complete_pixar_fruit_story.mp4 (قصة الفواكه بالأنيميشن)
       * talking_orange_1792838761.mp4 (البرتقالة المتكلمة)"""

if target in text:
    text = text.replace(target, replacement, 1)
    with open(brain_path, "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS: anti-lie rule added to brain.py")
else:
    print("Target not found!")
