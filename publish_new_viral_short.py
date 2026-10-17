import asyncio
from pathlib import Path
import httpx
from tools import youtube_publisher
import config

async def upload_and_notify():
    video_path = Path("e:/Users/adham/Desktop/new/adham-agent/videos/subtitled_raw_smc_1792227465_1792227473.mp4")
    title = "Why Banks Always Hunt Your Stop Loss? | SMC Liquidity Sweep"
    description = (
        "Why do banks always hunt your Stop Loss?\n\n"
        "Retail traders place stop losses at obvious levels. "
        "Institutional algorithms sweep those levels to fill massive orders. "
        "At Core Trade AI, we track the smart money footprint. "
        "Stop being the liquidity, become the hunter.\n\n"
        "Subscribe to Core Trade AI: https://youtube.com/@coretradeai\n\n"
        "#Shorts #Trading #Forex #SMC #LiquiditySweep #Gold #XAUUSD #TradingView #CoreTradeAI"
    )
    
    print("1. Uploading new viral video to YouTube...")
    yt_res = await youtube_publisher.upload_video(
        video_path=video_path,
        title=title,
        description=description,
        privacy_status="public",
        is_short=True
    )
    print("YouTube Upload Success:", yt_res["url"])
    
    print("2. Sending new video directly to Adham on Telegram...")
    async with httpx.AsyncClient(timeout=120) as client:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendVideo"
        with open(video_path, "rb") as vf:
            data = {
                "chat_id": config.OWNER_ID,
                "caption": (
                    "🔥 **فيديو Core Trade AI بالشارت الحقيقي المطور جاهز!**\n\n"
                    "✨ **التطويرات البصرية المعتمدة فوراً**:\n"
                    "• شارت تداول مؤسساتي حقيقي 100% (XAU/USD 15M) بكامل التفاصيل والشموع والأوردر بلوك.\n"
                    "• هوك علوي نيون زجاجي يخطف العين في أول ثانيتين.\n"
                    "• كابشن كاريوكي أصفر مشع متزامن كلمة بكلمة مع الصوت العصبي.\n"
                    "• موسيقى لو-فاي تكنولوجية هادئة مدمجة (Auto-Ducked BGM).\n\n"
                    f"📺 **الرابط على يوتيوب**: {yt_res['url']}\n\n"
                    "🚀 تم نشره على القناة بنجاح!"
                ),
                "parse_mode": "Markdown"
            }
            files = {"video": ("core_trade_viral_short.mp4", vf, "video/mp4")}
            resp = await client.post(url, data=data, files=files)
            print("Telegram Send Status:", resp.status_code, resp.json().get("ok"))

if __name__ == "__main__":
    asyncio.run(upload_and_notify())
