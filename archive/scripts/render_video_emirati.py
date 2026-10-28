import subprocess
from pathlib import Path

raw_video = Path("C:/Projects/adham-agent/workspace_data/media/glamp_cj_raw.mp4")
voice_path = Path("C:/Projects/adham-agent/workspace_data/media/voice_tests/hamdan_male_ae.mp3")
overlay_path = Path("C:/Projects/adham-agent/workspace_data/media/tiktok_overlay.png")
output_video = Path("C:/Projects/adham-agent/workspace_data/media/glamp_tiktok_emirati_v4.mp4")

cmd_dur = [
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", str(voice_path)
]
voice_dur = float(subprocess.check_output(cmd_dur).decode().strip())
print(f"Emirati Voiceover duration: {voice_dur:.2f} seconds")

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

print("Rendering video with Emirati voice (Hamdan)...")
subprocess.run(cmd, check=True)
print(f"Video rendered successfully: {output_video} ({output_video.stat().st_size} bytes)")
