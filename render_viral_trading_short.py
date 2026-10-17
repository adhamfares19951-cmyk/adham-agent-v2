import asyncio
import logging
from pathlib import Path
import subprocess
import time
import imageio_ffmpeg
import edge_tts
import httpx

from tools import video_autocaption, media_studio

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

BASE_DIR = Path(__file__).resolve().parent
VIDEOS_DIR = BASE_DIR / "videos"
SLIDE_PNG = VIDEOS_DIR / "trading_slide_test.png"

SCRIPT_TEXT = (
    "Why do banks always hunt your stop loss? "
    "Retail traders place stop losses at obvious levels. "
    "Institutional algorithms sweep those levels to fill massive orders. "
    "At Core Trade AI, we track the smart money footprint. "
    "Stop being the liquidity, become the hunter. "
    "Subscribe to Core Trade AI."
)

VOICE = "en-US-ChristopherNeural"

async def generate_voiceover(text: str, output_wav: Path) -> Path:
    output_mp3 = output_wav.with_suffix(".mp3")
    comm = edge_tts.Communicate(text, voice=VOICE, rate="+3%", pitch="-1Hz")
    await comm.save(str(output_mp3))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg, "-y", "-i", str(output_mp3), "-ar", "44100", "-ac", "2", str(output_wav)]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_wav

def get_audio_duration(audio_file: Path) -> float:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg, "-i", str(audio_file)]
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    import re
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    if m:
        hrs, mins, secs = m.groups()
        return int(hrs) * 3600 + int(mins) * 60 + float(secs)
    return 20.0

async def render_viral_trading_short():
    ts = int(time.time())
    voice_wav = VIDEOS_DIR / f"voice_smc_{ts}.wav"
    print("1. Generating voiceover...")
    await generate_voiceover(SCRIPT_TEXT, voice_wav)
    duration = get_audio_duration(voice_wav)
    print(f"Voiceover duration: {duration:.2f}s")

    print("2. Mixing Lo-Fi Tech BGM with auto-ducking...")
    bgm_wav = VIDEOS_DIR / f"voice_bgm_smc_{ts}.wav"
    try:
        await media_studio.mix_audio_with_ambient_bgm(voice_wav, bgm_wav, bgm_volume=0.13)
        final_audio = bgm_wav
    except Exception as e:
        print("BGM fallback:", e)
        final_audio = voice_wav

    print("3. Rendering dynamic 1080x1920 video with FFmpeg...")
    raw_video = VIDEOS_DIR / f"raw_smc_{ts}.mp4"
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    fps = 30
    total_frames = int((duration + 0.4) * fps)
    
    # Smooth subtle zoom from 1.00 to 1.05 centered near the liquidity sweep zone
    filter_complex = (
        f"zoompan=z='min(zoom+0.00025,1.06)':x='iw/2-(iw/zoom/2)':y='ih*0.35-(ih/zoom*0.35)':"
        f"d={total_frames}:s=1080x1920:fps={fps},"
        f"format=yuv420p"
    )

    cmd = [
        ffmpeg, "-y",
        "-loop", "1",
        "-i", str(SLIDE_PNG),
        "-i", str(final_audio),
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-preset", "faster",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{duration + 0.3:.2f}",
        "-pix_fmt", "yuv420p",
        str(raw_video)
    ]
    subprocess.run(cmd, check=True)
    print("Raw video rendered:", raw_video)

    print("4. Burning word-by-word yellow karaoke captions...")
    res_c = await video_autocaption.burn_karaoke_subtitles(raw_video, language="en")
    final_video = Path(res_c["video_path"])
    print("FINAL VIRAL TRADING VIDEO READY:", final_video)
    print(f"Size: {final_video.stat().st_size / (1024*1024):.2f} MB")
    return final_video

if __name__ == "__main__":
    v = asyncio.run(render_viral_trading_short())
    print("Done:", v)
