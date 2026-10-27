import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

brain_path = Path(r"C:\Projects\adham-agent\brain.py")
content = brain_path.read_text(encoding="utf-8")

old_rule = """- create_and_publish_trading_short: الأداة الشاملة والذاتية 100% لإنشاء ونشر فيديوهات الشورتس لقناة Core Trade AI (شارت TradingView حقيقي + تعليق صوتي عصبي + موسيقى تقنية لو فاي + كابشن كاريوكي نيون + نشر تلقائي على يوتيوب). إذا طلب أدهم في المحادثة اقتراح فكرة شورتس أو عمل فيديو ونشره، استدعِ هذه الأداة فوراً بموضوع الفيديو (topic) أو الفكرة!"""

new_rule = """- create_and_publish_trading_short: مخصصة حصراً وفقط لتحليلات الأسواق المالية والفوركس والعملات الرقمية والذهب لقناة Core Trade AI. ⛔ ممنوع منعاً باتاً استدعاء هذه الأداة لأي منتج تجاري أو متجر أو مصباح G-Lamp!
- broadcast_social_platforms / execute_tiktok_video: الأداة المعتمدة لفيديوهات المتجر والمنتجات (مصباح G-Lamp) لنشر فيديوهات المنتج الحقيقية 9:16 مع الصوت والترجمة على تيك توك وإنستغرام ريلز."""

old_guard = """- **إذا طلب أدهم تصميم شارت أو فيديو ونشره**: استدعِ أداة `create_and_publish_trading_short` للشورتس، أو `create_long_trading_video` للفيديوهات الطويلة، أو وجّهه للأوامر المباشرة `/publish_short` و `/publish_long`!"""

new_guard = """- **إذا طلب أدهم فيديو للمتجر أو شورتس لمصباح G-Lamp**: استدعِ حصراً أدوات المتجر الرسمية (`broadcast_social_platforms` أو `tiktok_upload_video` أو `publish_instagram_reel`) باستخدام فيديو المنتج الحقيقي، وإياك نهائياً تركيب صوت المصباح على شارتات التداول والشموع اليابانية!
- **فقط إذا طلب أدهم صراحة شارت تداول أو فيديو فوركس/كريبتو**: استدعِ أداة `create_and_publish_trading_short`."""

if old_rule in content:
    content = content.replace(old_rule, new_rule, 1)
    print("Patched create_and_publish_trading_short description.")
else:
    print("Warning: old_rule not found.")

if old_guard in content:
    content = content.replace(old_guard, new_guard, 1)
    print("Patched old_guard in brain.py.")
else:
    print("Warning: old_guard not found.")

brain_path.write_text(content, encoding="utf-8")
print("brain.py updated.")
