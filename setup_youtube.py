"""Setup YouTube Channel Authentication for adham-agent.
Double click or run:
    python setup_youtube.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools import youtube_publisher

print("=" * 60)
print("  ربط قناة يوتيوب مع بوت أدهم (Right Hand Bot)")
print("=" * 60)

try:
    msg = youtube_publisher.run_oauth_flow_interactive(port=0)
    print("\n✅ " + msg)
    print("\nجارٍ فحص بيانات القناة الآن...")
    
    import asyncio
    info = asyncio.run(youtube_publisher.get_channel_info())
    if "error" in info:
        print("⚠️ " + info["error"])
    else:
        print(f"\n🎉 مبروك! تم الربط بنجاح مع القناة:")
        print(f"📺 اسم القناة: {info.get('title')}")
        print(f"👥 المشتركون: {info.get('subscribers')}")
        print(f"👁️ المشاهدات: {info.get('views')}")
        print(f"🎥 عدد الفيديوهات: {info.get('videos')}")
        print("\nأصبح البوت الآن جاهزاً للنشر التلقائي عبر تيليجرام!")
except Exception as e:
    print(f"\n❌ حدث خطأ أثناء الربط: {e}")

input("\nاضغط Enter للخروج...")
