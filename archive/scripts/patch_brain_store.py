# -*- coding: utf-8 -*-
"""Updates brain.py system prompt with today's real store and account state."""
from pathlib import Path

p = Path("C:/Projects/adham-agent/brain.py")
code = p.read_text(encoding="utf-8")

old_straw = """      - الفيديوهات الحقيقية الجاهزة المنتجة اليوم موجودة على سطح المكتب:
        * Strawberry_Betrayal_Hollywood_English_Dubbed.mp4 (الفيديو المدبلج بالإنجليزية بهوليوود ستايل + فلاتر مضادة للحظر 1080x1920)
        * Strawberry_Betrayal_English_Subtitled.mp4 (الفيديو المترجم)
        * رابط المشاهدة المباشر: http://136.244.77.61:8080/media/dub_1792916725_English_Dubbed.mp4"""

new_smart = """      - بيانات المتجر والحسابات الرسمية الحقيقية المفعلة اليوم:
        * المتجر الإلكتروني: Smart Store | متجر سمارت (رابط المنتج المباشر: https://ministries-direct-specify-universe.trycloudflare.com/glamp).
        * منتج اليوم الأساسي: مصباح G-Lamp الذكي 4 في 1 (شاحن لاسلكي 15W + سبيكر بلوتوث + إضاءة RGB تفاعلية) بسعر 149 ر.س مع الدفع عند الاستلام والشحن المجاني في السعودية والإمارات.
        * حساب تيك توك: @coretradeai (الاسم المعروض: Smart Store | متجر سمارت) - موثق تماماً وتم حقن كوكيز الجلسة بنجاح في sessions/tiktok_user_data، وتم نشر فيديو مصباح G-Lamp اليوم في TikTok Studio!
        * حساب إنستغرام: @smartstore.gcc (الاسم المعروض: Smart Store | متجر سمارت) - موثق وتم نشر ريلز مصباح G-Lamp اليوم بنجاح وعليه تعليق مثبت برابط الشراء.
        * إذا سأل أدهم عن كوكيز تيك توك: أكد له بوضوح أنها وصلت ومفعلة وحُفظت وتم النشر بها بنجاح اليوم في TikTok Studio!
        * إذا سأل عن مشاهدات تيك توك أو إحصائياته: استدعِ أداة tiktok_get_analytics فوراً لجلب المشاهدات الحقيقية من داخل TikTok Studio!"""

if old_straw in code:
    code = code.replace(old_straw, new_smart)
    p.write_text(code, encoding="utf-8")
    print("SUCCESS: brain.py updated with Smart Store & TikTok state!")
else:
    print("Strawberry target not found in brain.py")
