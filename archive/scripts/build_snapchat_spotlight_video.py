import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def shape_ar(text: str) -> str:
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def create_snapchat_overlay(output_path: Path):
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fonts
    font_candidates = [
        "C:/Windows/Fonts/arialbd.ttf", # Arial Bold
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    font_title = None
    font_sub = None
    font_tag = None
    font_price = None

    for fc in font_candidates:
        if Path(fc).exists():
            try:
                font_title = ImageFont.truetype(fc, 64)
                font_price = ImageFont.truetype(fc, 52)
                font_sub = ImageFont.truetype(fc, 38)
                font_tag = ImageFont.truetype(fc, 32)
                break
            except Exception:
                pass

    # 1. Top Card (Safe zone y: 80 to 350)
    # Glassmorphism dark card with Snapchat yellow border
    draw.rounded_rectangle([(50, 80), (1030, 350)], radius=32, fill=(15, 23, 42, 235), outline=(255, 252, 0, 220), width=4)

    # Top Tag
    t_tag = shape_ar("🔥 الأكثر طلباً وترند في السعودية والخليج 2026")
    draw.text((540, 135), t_tag, font=font_tag, fill=(255, 252, 0), anchor="mm")

    # Main Title
    t_main = shape_ar("مصباح G-Lamp الذكي 4 في 1")
    draw.text((540, 215), t_main, font=font_title, fill=(255, 255, 255), anchor="mm")

    # Features Subtitle
    t_sub = shape_ar("شاحن لاسلكي 15W ⚡ سبيكر نقي 🎵 إضاءة RGB 🌈")
    draw.text((540, 290), t_sub, font=font_sub, fill=(203, 213, 225), anchor="mm")

    # 2. Bottom Card (Safe zone y: 1420 to 1740, leaves 180px for Snapchat UI)
    draw.rounded_rectangle([(50, 1420), (1030, 1740)], radius=32, fill=(15, 23, 42, 240), outline=(74, 222, 128, 220), width=4)

    # Price Tag
    t_price = shape_ar("149 ريال بس 🇸🇦 — الدفع عند الاستلام")
    draw.text((540, 1485), t_price, font=font_price, fill=(74, 222, 128), anchor="mm")

    # Trust Badges
    t_trust = shape_ar("🚚 شحن مجاني سريع لباب بيتك • ضمان استبدال 14 يوم")
    draw.text((540, 1565), t_trust, font=font_tag, fill=(226, 232, 240), anchor="mm")

    # Inner Yellow CTA Button
    draw.rounded_rectangle([(140, 1625), (940, 1705)], radius=24, fill=(255, 252, 0, 245), outline=(255, 255, 255, 255), width=2)
    t_cta = shape_ar("👇 اطلب الحين من الرابط أسفل الشاشة أو بالبايو")
    draw.text((540, 1665), t_cta, font=font_sub, fill=(15, 23, 42), anchor="mm")

    img.save(str(output_path), "PNG")
    print(f"Snapchat overlay created at: {output_path}")

def render_video():
    raw_video = Path("C:/Projects/adham-agent/workspace_data/media/glamp_cj_raw.mp4")
    voice_path = Path("C:/Projects/adham-agent/workspace_data/media/voice_tests/snap_saudi_hamed.mp3")
    overlay_path = Path("C:/Projects/adham-agent/workspace_data/media/snapchat_overlay.png")
    output_video = Path("C:/Projects/adham-agent/workspace_data/media/glamp_snapchat_spotlight_v1.mp4")

    create_snapchat_overlay(overlay_path)

    cmd_dur = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(voice_path)
    ]
    voice_dur = float(subprocess.check_output(cmd_dur).decode().strip())
    print(f"Saudi Voiceover duration: {voice_dur:.2f} seconds")

    filter_complex = (
        "[0:v]split=2[bg_raw][fg_raw];"
        "[bg_raw]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.32[bg];"
        "[fg_raw]crop=540:700:0:220,scale=1020:1322,format=yuva420p[fg];"
        "[bg][fg]overlay=(W-w)/2:365[video_combined];"
        "[video_combined][2:v]overlay=0:0[outv]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(raw_video),
        "-i", str(voice_path),
        "-i", str(overlay_path),
        "-t", str(voice_dur + 0.4),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "faster",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_video)
    ]

    print("Rendering high quality Snapchat Spotlight video...")
    subprocess.run(cmd, check=True)
    print(f"Video rendered successfully: {output_video} ({output_video.stat().st_size} bytes)")

if __name__ == "__main__":
    render_video()
