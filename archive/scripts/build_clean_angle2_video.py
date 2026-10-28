import subprocess
import os
from pathlib import Path

raw_video = Path("C:/Projects/adham-agent/workspace_data/media/glamp_cj_raw.mp4")
voice_path = Path("C:/Projects/adham-agent/workspace_data/media/glamp_saudi_voice_v2.mp3")
output_video = Path("C:/Projects/adham-agent/workspace_data/media/glamp_tiktok_angle2.mp4")

# Check voice duration
cmd_dur = [
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", str(voice_path)
]
voice_dur = float(subprocess.check_output(cmd_dur).decode().strip())
print(f"Voiceover duration: {voice_dur:.2f} seconds")

# We design a high converting vertical layout (1080x1920):
# 1. Background: Blurred, zoomed-in loop of the product
# 2. Foreground: Clean centered video cropped to avoid old english text
# 3. Top Header: Arabic badge
# 4. Bottom Banner: Price and COD badge
filter_complex = (
    # Split input
    "[0:v]split=2[bg_raw][fg_raw];"
    # Background: scaled, heavily blurred, darkened
    "[bg_raw]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.25[bg];"
    # Foreground: crop out top 140px of 540x960 to remove English text (take y=140 to 960 -> 540x820), then scale nicely
    "[fg_raw]crop=540:800:0:150,scale=960:1422,format=yuva420p[fg];"
    # Overlay fg on bg
    "[bg][fg]overlay=(W-w)/2:(H-h)/2[base];"
    # Draw top banner box
    "[base]drawbox=x=0:y=120:w=1080:h=180:color=black@0.75:t=fill[top_box];"
    # Draw top text
    "[top_box]drawtext=text='مصباح G-Lamp الذكي 4 في 1':font='Arial':fontsize=56:fontcolor=white:x=(w-text_w)/2:y=150:shadowcolor=purple:shadowx=3:shadowy=3,"
    "drawtext=text='🏆 الأكثر مبيعاً في السعودية والخليج 2026':font='Arial':fontsize=36:fontcolor=#38bdf8:x=(w-text_w)/2:y=225[with_top];"
    # Draw bottom banner box
    "[with_top]drawbox=x=0:y=1600:w=1080:h=220:color=black@0.85:t=fill[bot_box];"
    # Draw bottom text
    "[bot_box]drawtext=text='149 ريال فقط — توصيل مجاني والدفع عند الاستلام':font='Arial':fontsize=44:fontcolor=#4ade80:x=(w-text_w)/2:y=1640:shadowcolor=black:shadowx=2:shadowy=2,"
    "drawtext=text='👇 اطلب الحين من الرابط في البايو وأول تعليق':font='Arial':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=1710[outv]"
)

cmd = [
    "ffmpeg", "-y",
    "-stream_loop", "-1",
    "-i", str(raw_video),
    "-i", str(voice_path),
    "-t", str(voice_dur + 0.3),
    "-filter_complex", filter_complex,
    "-map", "[outv]",
    "-map", "1:a",
    "-c:v", "libx264",
    "-preset", "faster",
    "-crf", "22",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    str(output_video)
]

print("Rendering video with ffmpeg...")
subprocess.run(cmd, check=True)
print(f"Success! Video ready: {output_video} ({output_video.stat().st_size} bytes)")
