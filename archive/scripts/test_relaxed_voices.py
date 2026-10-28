import asyncio
import edge_tts
from pathlib import Path

# A relaxed, natural, conversational Arabic script with real pauses and zero robotic jargon
# Instead of "آر جي بي" -> "إضاءة ملونة هادية"
# Instead of "4 في 1" -> "أربعة في واحد"
# Natural pauses (...) and commas

script_relaxed = (
    "يا هلا والله... "
    "شوفوا هالجهاز الرهيب اللي مستحيل تستغني عنه في غرفتك أو على مكتبك... "
    "مصباح جي لامب الذكي، أربعة في واحد. "
    "أول شيء، حط جوالك عليه، ويشحن لاسلكي سريع وبكل سهولة. "
    "ثاني شيء، فيه سبيكر بلوتوث صوته نقي وواضح لأغانيك والبودكاست. "
    "وفوق هذا كله، إضاءة هادية ومريحة تتحكم بألوانها على جوك... ومعها ساعة ومنبه لطيف يصحيك برواق. "
    "والأحلى من كذا؟ سعره مية وتسعة وأربعين ريال بس... "
    "والتوصيل مجاني لباب بيتك، وما تدفع ولا هللة إلا عند الاستلام لما تعاينه بنفسك. "
    "الرابط موجود في البايو وأول تعليق... اطلبه الحين قبل يخلص."
)

voices = [
    ("zariyah_female_sa", "ar-SA-ZariyahNeural", "-4%"),
    ("hamdan_male_ae", "ar-AE-HamdanNeural", "-4%"),
    ("hamed_male_sa_relaxed", "ar-SA-HamedNeural", "-6%"),
]

output_dir = Path("C:/Projects/adham-agent/workspace_data/media/voice_tests")
output_dir.mkdir(parents=True, exist_ok=True)

async def generate():
    for name, voice, rate in voices:
        out_file = output_dir / f"{name}.mp3"
        comm = edge_tts.Communicate(text=script_relaxed, voice=voice, rate=rate)
        await comm.save(str(out_file))
        print(f"Generated {name}: {out_file.stat().st_size} bytes (rate: {rate})")

if __name__ == "__main__":
    asyncio.run(generate())
