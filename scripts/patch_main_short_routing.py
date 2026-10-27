import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

main_path = Path(r"C:\Projects\adham-agent\main.py")
content = main_path.read_text(encoding="utf-8")

old_block = """    is_ig = any(k in t for k in ["انستقرام", "انستغرام", "انستا", "instagram", "ig", "ريلز", "ريل", "reel"])
    is_publish = any(k in t for k in ["انشر", "نشر", "ارفع", "نزل", "اعمل", "سوي", "share", "post", "publish"])
    is_tiktok = any(k in t for k in ["تيك توك", "تيكتوك", "tiktok"])
    is_all = any(k in t for k in ["الكل", "كل المنصات", "كل مكان", "الحسابات", "broadcast", "all"])
    is_seo = any(k in t for k in ["سيو", "seo", "محركات البحث", "محرك البحث", "سيت ماب", "sitemap", "فهرسة"])
    is_stats = any(k in t for k in ["مشاهدة", "مشاهدات", "إحصائيات", "احصائيات", "كم مشاهدة", "كم وصل", "كم شاف", "كم تفاعل", "كم لايك", "افحص"])
    is_cookie_q = "كوكيز" in t and any(k in t for k in ["تيك", "سناب", "انيغرافيتي", "antigravity", "بعتت", "حفظ"])"""

new_block = """    is_trading = any(k in t for k in ["تداول", "فوركس", "شارت", "كريبتو", "عملات", "ذهب", "trading", "chart", "forex", "btc", "eurusd"])
    is_ig = any(k in t for k in ["انستقرام", "انستغرام", "انستا", "instagram", "ig", "ريلز", "ريل", "reel"])
    is_short_intent = any(k in t for k in ["شورتس", "شورت", "فيديو", "video", "short", "shorts"])
    is_publish = any(k in t for k in ["انشر", "نشر", "ارفع", "نزل", "اعمل", "سوي", "share", "post", "publish", "جديد"]) or is_short_intent
    is_tiktok = any(k in t for k in ["تيك توك", "تيكتوك", "tiktok"])
    is_all = any(k in t for k in ["الكل", "كل المنصات", "كل مكان", "الحسابات", "broadcast", "all"])
    is_seo = any(k in t for k in ["سيو", "seo", "محركات البحث", "محرك البحث", "سيت ماب", "sitemap", "فهرسة"])
    is_stats = any(k in t for k in ["مشاهدة", "مشاهدات", "إحصائيات", "احصائيات", "كم مشاهدة", "كم وصل", "كم شاف", "كم تفاعل", "كم لايك", "افحص"])
    is_cookie_q = "كوكيز" in t and any(k in t for k in ["تيك", "سناب", "انيغرافيتي", "antigravity", "بعتت", "حفظ"])"""

if old_block in content:
    content = content.replace(old_block, new_block, 1)
    print("Patched intent variables in main.py.")
else:
    print("Warning: old_block not found.")

main_path.write_text(content, encoding="utf-8")
print("main.py updated.")
