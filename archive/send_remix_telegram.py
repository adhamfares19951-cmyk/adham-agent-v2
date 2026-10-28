import os, asyncio, aiohttp
from dotenv import load_dotenv

load_dotenv(r"C:\Projects\adham-agent\.env")
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "1260053668"
video_path = r"C:\Projects\motion-video-studio\workspace\remix_telegram_ready.mp4"

caption = """🎬 تم تجهيز الفيديو المطلوب (بدون تعليق صوتي وبفلاتر مكافحة الحظر):
🔥 "قصة الفراولة والموزة - الحب والخيانة والتحدي"

🛡️ التعديلات التي قمنا بها لحماية قناتك من الحظر:
1️⃣ حذف التعليق الصوتي القديم بالكامل 100% لإسقاط بصمة الصوت (Audio Content ID).
2️⃣ استبدال الصوت بموسيقى بيانو درامية ملحمية مرخصة بدون حقوق طبع ونشر (Copyright-Free).
3️⃣ تعديل أبعاد الفيديو (Crop 4%) ورفع الدقة لـ Full HD (1080x1920).
4️⃣ تسريع طفيف (1.04x) لكسر البصمة الزمنية (Temporal Hash) ليوتيوب.
5️⃣ فلترة الألوان والتشبع وإضافة Noise مجهري لكسر الـ Visual Hash.

شاهد الفيديو الآن يا أدهم وجربه في القناة وقلي النتيجة! 🔥👇"""

async def send():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    data = aiohttp.FormData()
    data.add_field("chat_id", CHAT_ID)
    data.add_field("caption", caption)
    data.add_field("video", open(video_path, "rb"), filename="Strawberry_Betrayal_AntiBan.mp4", content_type="video/mp4")
    
    print(f"Uploading {os.path.getsize(video_path) / (1024*1024):.2f} MB to Telegram...")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            res = await resp.json()
            print("Telegram response:", res.get("ok"), res.get("description", ""))

if __name__ == "__main__":
    asyncio.run(send())
