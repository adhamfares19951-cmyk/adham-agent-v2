"""Interactive TikTok Login Setup Script.
Launches an Edge or Chrome browser window so the user can log into their TikTok account once.
The session cookies and storage tokens are saved permanently to sessions/tiktok_user_data.
Future uploads run completely silently in headless mode.
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from tools import tiktok_publisher


async def main():
    print("=" * 65)
    print("🚀 مرحباً بك في أداة ربط حساب تيك توك التلقائي لـ Core Trade AI")
    print("=" * 65)
    print("سيتم الآن فتح متصفح Edge لتسجيل الدخول إلى حسابك في تيك توك...")
    print("بعد تسجيل الدخول بنجاح، يمكنك إغلاق نافذة المتصفح لحفظ بيانات الدخول.")
    print("-" * 65)
    
    success = await tiktok_publisher.launch_interactive_login()
    if success:
        print("\n🎉 ممتاز! تم حفظ جلسة تيك توك بنجاح في sessions/tiktok_user_data.")
        print("الآن يستطيع البوت رفع أي فيديو تلقائياً إلى تيك توك بدون طلب الدخول مجدداً!")
    else:
        print("\n⚠️ لم يتم العثور على جلسة نشطة. يمكنك تشغيل السكربت مرة أخرى لتسجيل الدخول.")


if __name__ == "__main__":
    asyncio.run(main())
