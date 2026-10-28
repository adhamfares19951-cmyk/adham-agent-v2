import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import asyncio, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from tools.tiktok_publisher import upload_video

video_path = Path("workspace_data/media/glamp_tiktok_final.mp4").resolve()

caption = (
    "مصباح G-Lamp الذكي 4 في 1 🔥 شاحن لاسلكي سريع 15W + سبيكر سينمائي نقي + إضاءة RGB تفاعلية! "
    "شحن مجاني وسريع والدفع عند الاستلام لكافة مناطق المملكة والإمارات 🇸🇦 🇦🇪 "
    "للطلب والاستفسار تواصل معنا عبر الخاص (DM)"
)

tags = ["السعودية", "الرياض", "جدة", "سيت_اب", "ديكور", "شاحن_لاسلكي", "fyp", "viral"]

async def main():
    print("==================================================")
    print("🚀 Starting TikTok Publishing for G-Lamp Ad Video")
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
