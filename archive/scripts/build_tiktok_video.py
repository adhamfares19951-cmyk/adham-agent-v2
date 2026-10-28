import urllib.request, subprocess, json
from pathlib import Path

video_url = "https://video-cf.cjdropshipping.com/f094eca48cfc71efad6d0764b3ec0102/53acaa93f41446b78020a87ebd2190c5-745c5c7cc576ca4293e990e987098805-ld.mp4"
raw_video = Path("workspace_data/media/glamp_cj_raw.mp4")
voice_path = Path("audio_output/glamp_ad_voice.mp3").resolve()
output_video = Path("workspace_data/media/glamp_tiktok_final.mp4").resolve()

raw_video.parent.mkdir(parents=True, exist_ok=True)

print("1. Downloading CJ product demo video...")
urllib.request.urlretrieve(video_url, str(raw_video))
print(f"Downloaded: {raw_video} ({raw_video.stat().st_size} bytes)")

# Get audio duration
cmd_dur = [
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", str(voice_path)
]
voice_dur = float(subprocess.check_output(cmd_dur).decode().strip())
print(f"Voiceover duration: {voice_dur:.2f} seconds")

# Render video with ffmpeg:
# - Loop or trim video to match voiceover duration
# - Scale/pad to 9:16 vertical (1080x1920) suitable for TikTok
# - Replace audio with voiceover
print("2. Rendering TikTok 9:16 ad video with ffmpeg...")
cmd_ffmpeg = [
    "ffmpeg", "-y",
    "-stream_loop", "-1",
    "-i", str(raw_video),
    "-i", str(voice_path),
    "-t", str(voice_dur + 0.5),
    "-filter_complex",
    "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[v]",
    "-map", "[v]",
    "-map", "1:a",
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "22",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    str(output_video)
]
subprocess.run(cmd_ffmpeg, check=True)
print(f"3. Final TikTok video ready: {output_video} ({output_video.stat().st_size} bytes)")
