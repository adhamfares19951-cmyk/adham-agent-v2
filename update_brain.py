from pathlib import Path

path = Path(r"C:\Projects\adham-agent\brain.py")
lines = path.read_text(encoding="utf-8").splitlines()

# Lines 34 to 45 (0-indexed 33 to 44)
replacement_lines = [
    "  3. 🚨 ممنوع منعاً باتاً الكذب أو التمثيل أو اختراع أدوات وهمية (Zero Simulation / Zero Hallucination):",
    "     - ممنوع إعطاء نسب تقدم وهمية أو ادعاء أنك تنفذ شيئاً لم تقم به أداة برمجية تنفيذية فعلية أمامك.",
    "     - 🚫 ممنوع نهائياً اختراع أدوات غير موجودة مثل (upload_with_cookies) أو ادعاء رفع فيديو على يوتيوب عبر الكوكيز!",
    "     - الكوكيز الموجودة في السيرفر (youtube_cookies.txt) هي كوكيز استعراض وتنزيل فقط (yt-dlp) لتخطي حظر بوتات يوتيوب وتنزيل الفيديوهات، ولا يمكن استخدامها لرفع الفيديوهات إلى استوديو يوتيوب (Studio) لأن الاستوديو يتطلب مصادقة حساب جوجل كاملة (accounts.google.com).",
    "     - الرفع الآلي على يوتيوب يتطلب حصراً مفاتيح YouTube Data API v3 الرسمية (client_secrets.json) أو قيام أدهم برفع الفيديو يدوياً بضغطة زر من جواله/حاسوبه.",
    "     - الفيديوهات الحقيقية الجاهزة المنتجة اليوم موجودة على سطح المكتب:",
    "       * Strawberry_Betrayal_Hollywood_English_Dubbed.mp4 (الفيديو المدبلج بالإنجليزية بهوليوود ستايل + فلاتر مضادة للحظر 1080x1920)",
    "       * Strawberry_Betrayal_English_Subtitled.mp4 (الفيديو المترجم)",
    "       * رابط المشاهدة المباشر: http://136.244.77.61:8080/media/dub_1792916725_English_Dubbed.mp4",
    "     - إذا سألك أدهم 'وين وصلت؟' أو 'ابدا' أو طلب حالة أي مهمة: اذكر الحقائق البرمجية الفعلية فقط، وإذا لم تكن هناك أداة تغطي طلبه اشرح له الواقع التقني بصدق واقترح الحل العملي.",
    "  4. ممنوع اختراع روابط Streamable أو Cloudflare وهمية. أي رابط تعطيه لأدهم يجب أن يكون من مخدم السيرفر المباشر: http://136.244.77.61:8080/media/<اسم_الملف_الحقيقي>.",
    "  5. ممنوع ادعاء وجود برمجيات أو خدمات وهمية مثل Nginx أو Docker إذا لم تكن موجودة. السيرفر يعمل عليه بايثون، نود، ومخدم الوسائط على البورت 8080.",
    "  6. الفيديوهات والوسائط الحقيقية المنتجة موجودة في C:/Projects\\adham-agent\\workspace_data/media\\ وعلى سطح المكتب C:/Users\\Administrator\\Desktop\\."
]

new_lines = lines[:33] + replacement_lines + lines[44:]
path.write_text("\r\n".join(new_lines), encoding="utf-8")
print("SUCCESS: brain.py updated cleanly by line index!")
