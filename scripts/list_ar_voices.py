import asyncio
import edge_tts

async def main():
    voices = await edge_tts.list_voices()
    for v in voices:
        if v["Locale"].startswith("ar-"):
            print(f"{v['ShortName']} ({v['Locale']}) - {v['Gender']}")

if __name__ == "__main__":
    asyncio.run(main())
