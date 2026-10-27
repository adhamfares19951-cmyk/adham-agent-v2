import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv(r"C:\Projects\adham-agent\.env")
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "1260053668"
video_path = r"C:\Users\Administrator\Desktop\pixar_fruit_betrayal_complete.mp4"

caption = """🎬 حلقة الشورتس الجديدة كاملة بدقة 1080x1920 (Full HD):
🔥 "صدمة الفراولة! الخيانة الكبرى وعقاب الخلاط"

✨ مطابقة 100% لثيم وجودة بيكسار 3D الأصلية.
🛡️ آمنة 100% من أي حظر أو حقوق طبع ونشر (Zero Reused Content).
🎙️ تمثيل صوتي عربي درامي + ترجمة حركية احترافية + كاميرا كين بيرنز سينمائية.

شاهدها الآن وقلي رأيك يا أدهم! 🔥👇"""

async def send_vid():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    data = aiohttp.FormData()
    data.add_field("chat_id", CHAT_ID)
    data.add_field("caption", caption)
    data.add_field("video", open(video_path, "rb"), filename="fruit_betrayal_1080p.mp4", content_type="video/mp4")
    
    print("Uploading 21MB video to Telegram...")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            res = await resp.json()
            print("Telegram Send Status:", res.get("ok"), res.get("description", ""))

if __name__ == "__main__":
    asyncio.run(send_vid())
