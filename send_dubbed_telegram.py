import os, asyncio, aiohttp
from dotenv import load_dotenv

load_dotenv(r"C:\Projects\adham-agent\.env")
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "1260053668"
video_path = r"C:\Projects\motion-video-studio\workspace\Strawberry_Betrayal_Hollywood_English_Dubbed.mp4"

caption = """🎙️ النسخة المدبلجة بالكامل بالإنجليزية (Hollywood Voice Dubbing):
🔥 "Strawberry Betrayal: Pure Character Acting"

✨ ما قمنا بتحسينه في الدبلجة:
🎭 تمثيل صوتي كامل ومتعدد الشخصيات (Character Acting) وليس مجرد ترجمة أو قراءة نص:
  - الفراولة الرومانسية (Ava) بصوت لطيف وحالم في البداية.
  - لحظة الصدمة والشك بنبرة ارتعاش وهمس واقعي.
  - صدمة الخيانة في المطر بنبرة حزن وألم عميق.
  - صراخ الموز المذنب المرتعب (Guy) برجاء حقيقي.
  - غضب الفراولة الحاسم بنبرة قوية قطعت فيها العلاقة.
  - نبرة الفخامة والانتصار لامرأة أعمال ناجحة (CEO) واثقة من نفسها.
🎵 صوت نقي وواضح 100% مع موازنة خلفية البيانو الدرامية.

شاهدها الآن وقلي رأيك في الفرق بين الترجمة والدبلجة التمثيلية! 👇🎬"""

async def send():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    data = aiohttp.FormData()
    data.add_field("chat_id", CHAT_ID)
    data.add_field("caption", caption)
    data.add_field("video", open(video_path, "rb"), filename="Strawberry_Betrayal_English_Dubbed.mp4", content_type="video/mp4")
    
    print(f"Uploading {os.path.getsize(video_path) / (1024*1024):.2f} MB to Telegram...")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            res = await resp.json()
            print("Telegram response:", res.get("ok"), res.get("description", ""))

if __name__ == "__main__":
    asyncio.run(send())
