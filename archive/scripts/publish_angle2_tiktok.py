import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import asyncio, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from tools.tiktok_publisher import upload_video

video_path = Path("C:/Projects/adham-agent/workspace_data/media/glamp_tiktok_angle2.mp4")

caption = (
    "أفضل جهاز سيت اب وغرف نوم لعام 2026! مصباح G-Lamp الذكي 4 في 1 💡🔥 "
    "شاحن لاسلكي سريع 15W + سبيكر بلوتوث نقي + إضاءة محيطية تفاعلية تتزامن مع الموسيقى! "
    "توصيل مجاني سريع والدفع عند الاستلام لكافة مناطق المملكة والإمارات 🚚🇸🇦🇦🇪 "
    "الرابط المباشر للطلب في أول تعليق وفي البايو 👇"
)

tags = ["السعودية", "الرياض", "جدة", "دبي", "سيت_اب", "جيمنغ", "glamp", "fyp", "viral"]

async def main():
    print("==================================================")
    print("🚀 Starting TikTok Publishing for New Clean Angle2 Video")
    print(f"Video file: {video_path} ({video_path.stat().st_size} bytes)")
    print("==================================================")
    
    result = await upload_video(
        video_path=video_path,
        caption=caption,
        tags=tags
    )
    print("\n✅ TikTok Publish Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
