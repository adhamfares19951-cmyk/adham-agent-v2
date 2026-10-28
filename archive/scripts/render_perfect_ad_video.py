import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def shape_ar(text: str) -> str:
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

# 1. Create 1080x1920 overlay
overlay_path = Path("C:/Projects/adham-agent/workspace_data/media/tiktok_overlay.png")
img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Find a good font on Windows
font_candidates = [
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/tahoma.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
]
font_main = None
font_sub = None
font_tag = None

for fc in font_candidates:
    if Path(fc).exists():
        try:
            font_main = ImageFont.truetype(fc, 62)
            font_sub = ImageFont.truetype(fc, 40)
            font_tag = ImageFont.truetype(fc, 32)
            break
        except Exception:
            pass

# Draw Top Header Banner (y: 60 to 360)
# Dark translucent rounded box
draw.rounded_rectangle([(60, 80), (1020, 360)], radius=30, fill=(15, 23, 42, 230), outline=(168, 85, 247, 200), width=4)

# Tagline
t_tag = shape_ar("الأكثر مبيعاً في السعودية والخليج 2026")
draw.text((540, 130), t_tag, font=font_tag, fill=(56, 189, 248), anchor="mm")

# Main Title
t_main = shape_ar("مصباح G-Lamp 4in1 الذكي")
draw.text((540, 210), t_main, font=font_main, fill=(255, 255, 255), anchor="mm")

# Subtitle
t_sub = shape_ar("شحن 15W + سبيكر بلوتوث + إضاءة RGB")
draw.text((540, 290), t_sub, font=font_sub, fill=(216, 180, 254), anchor="mm")

# Draw Bottom Banner (y: 1540 to 1840)
draw.rounded_rectangle([(60, 1530), (1020, 1830)], radius=30, fill=(15, 23, 42, 235), outline=(34, 197, 94, 200), width=4)

# Price & Free delivery
t_price = shape_ar("149 ريال فقط — توصيل مجاني والدفع عند الاستلام")
draw.text((540, 1610), t_price, font=font_sub, fill=(74, 222, 128), anchor="mm")

# CTA
t_cta = shape_ar("اطلب الآن من الرابط في أول تعليق وفي البايو")
draw.text((540, 1700), t_cta, font=font_main, fill=(255, 255, 255), anchor="mm")

t_note = shape_ar("ضمان استبدال ذهبي 14 يوماً ضد عيوب الصناعة")
draw.text((540, 1775), t_note, font=font_tag, fill=(148, 163, 184), anchor="mm")

img.save(str(overlay_path), "PNG")
print(f"Overlay created: {overlay_path}")

# 2. Render Video with ffmpeg
raw_video = Path("C:/Projects/adham-agent/workspace_data/media/glamp_cj_raw.mp4")
voice_path = Path("C:/Projects/adham-agent/workspace_data/media/glamp_saudi_voice_v2.mp3")
output_video = Path("C:/Projects/adham-agent/workspace_data/media/glamp_tiktok_angle2.mp4")

# Get voice duration
cmd_dur = [
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", str(voice_path)
]
voice_dur = float(subprocess.check_output(cmd_dur).decode().strip())
print(f"Voiceover duration: {voice_dur:.2f} seconds")

# Filter:
# - bg: loop video, scale, blur, darken
# - fg: crop out top 240px to completely eliminate English text (y=240 to 960 -> 540x720), scale nicely
# - overlay fg on bg
# - overlay png overlay on top
filter_complex = (
    "[0:v]split=2[bg_raw][fg_raw];"
    "[bg_raw]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.3[bg];"
    "[fg_raw]crop=540:720:0:240,scale=1020:1360,format=yuva420p[fg];"
    "[bg][fg]overlay=(W-w)/2:360[video_combined];"
    "[video_combined][2:v]overlay=0:0[outv]"
)

cmd = [
    "ffmpeg", "-y",
    "-stream_loop", "-1",
    "-i", str(raw_video),
    "-i", str(voice_path),
    "-i", str(overlay_path),
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

print("Rendering high-quality vertical ad...")
subprocess.run(cmd, check=True)
print(f"Video rendered successfully: {output_video} ({output_video.stat().st_size} bytes)")
