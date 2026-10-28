import os, asyncio, aiohttp
from dotenv import load_dotenv

load_dotenv(r"C:\Projects\adham-agent\.env")
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "1260053668"
video_path = r"C:\Projects\motion-video-studio\workspace\final_english_subtitled.mp4"

caption = """🇺🇸 النسخة الإنجليزية الجاهزة للنشر العالمي فوراً! 🔥
🎬 "Strawberry Betrayal: From Heartbreak to CEO"

✨ مميزات هذه النسخة:
🎙️ تمثيل صوتي إنجليزي سينمائي متقن (Ava للأداء الدرامي للفراولة + Guy لشخصية الموز المذنب).
🎵 دمج احترافي مع موسيقى البيانو والأوتار الحزينة (Ducking متوازن).
📝 ترجمة نصوص متحركة أنيقة وواضحة (Viral Shorts Captions) لرفع نسبة المشاهدة والإكمال.
🛡️ خالية 100% من أي حقوق طبع ونشر أو حظر.

شاهدها وقلي رأيك يا أدهم! جاهزة للرفع على يوتيوب شورتس، تيك توك، وإنستغرام ريلز 🚀👇"""

async def send():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    data = aiohttp.FormData()
    data.add_field("chat_id", CHAT_ID)
    data.add_field("caption", caption)
    data.add_field("video", open(video_path, "rb"), filename="Strawberry_Betrayal_English_Subtitled.mp4", content_type="video/mp4")
    
    print(f"Uploading {os.path.getsize(video_path) / (1024*1024):.2f} MB to Telegram...")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            res = await resp.json()
            print("Telegram response:", res.get("ok"), res.get("description", ""))

if __name__ == "__main__":
    asyncio.run(send())
