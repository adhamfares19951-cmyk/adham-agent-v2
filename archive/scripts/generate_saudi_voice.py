import asyncio
import edge_tts
from pathlib import Path

script_text = (
    "تدري وش الجهاز اللي قالب غرف النوم وسيت اب الجيمنغ هالأيام؟ "
    "مصباح G-Lamp الذكي 4 في 1! "
    "حط جوالك يشحن لاسلكي سريع بقوة 15 واط، "
    "شغل أغانيك وبودكاستك على سبيكر بلوتوث نقي، "
    "واستمتع بإضاءة آر جي بي خرافية تتفاعل مع النغمات بأكثر من 250 نمط! "
    "وفوق كذا ساعة رقمية ومنبه يحاكي شروق الشمس. "
    "كل هذا بسعر 149 ريال بس! "
    "والتوصيل مجاني لباب بيتك والدفع عند الاستلام. "
    "الرابط في أول تعليق وفي البايو، اطلبه الحين قبل نفاد الدفعة!"
)

output_audio = Path("C:/Projects/adham-agent/workspace_data/media/glamp_saudi_voice_v2.mp3")
output_audio.parent.mkdir(parents=True, exist_ok=True)

async def generate():
    communicate = edge_tts.Communicate(
        text=script_text,
        voice="ar-SA-HamedNeural",
        rate="+5%",
        pitch="+0Hz"
    )
    await communicate.save(str(output_audio))
    print(f"Generated {output_audio} successfully! Size: {output_audio.stat().st_size} bytes")

if __name__ == "__main__":
    asyncio.run(generate())
