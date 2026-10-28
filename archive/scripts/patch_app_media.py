import re
from pathlib import Path

app_path = Path("C:/Projects/adham-agent/web_platform/app.py")
code = app_path.read_text(encoding="utf-8")

old_target = """@app.get("/video")
async def get_ad_video():
    \"\"\"Returns the ready-to-post 9:16 TikTok / Reels / Snap ad video.\"\"\"
    vid_path = Path("C:/Projects/adham-agent/workspace_data/media/glamp_tiktok_final.mp4")
    if vid_path.exists():
        return FileResponse(str(vid_path), media_type="video/mp4", filename="glamp_ad.mp4")
    raise HTTPException(status_code=404, detail="Video not found")"""

new_target = """@app.get("/video")
async def get_ad_video():
    \"\"\"Returns the latest ready-to-post 9:16 TikTok / Reels / Snap ad video.\"\"\"
    vid_path = Path("C:/Projects/adham-agent/workspace_data/media/glamp_tiktok_angle2.mp4")
    if not vid_path.exists():
        vid_path = Path("C:/Projects/adham-agent/workspace_data/media/glamp_tiktok_final.mp4")
    if vid_path.exists():
        return FileResponse(str(vid_path), media_type="video/mp4", filename="glamp_ad_angle2.mp4")
    raise HTTPException(status_code=404, detail="Video not found")


@app.get("/media/{filename:path}")
async def get_media_file(filename: str):
    \"\"\"Serves media files dynamically from workspace_data/media directory.\"\"\"
    media_dir = Path("C:/Projects/adham-agent/workspace_data/media").resolve()
    file_path = (media_dir / filename).resolve()
    if not str(file_path).startswith(str(media_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    if file_path.exists() and file_path.is_file():
        media_type = "video/mp4" if file_path.suffix == ".mp4" else ("audio/mpeg" if file_path.suffix == ".mp3" else "application/octet-stream")
        return FileResponse(str(file_path), media_type=media_type, filename=file_path.name)
    raise HTTPException(status_code=404, detail="File not found")"""

if old_target in code:
    code = code.replace(old_target, new_target)
    app_path.write_text(code, encoding="utf-8")
    print("Successfully patched web_platform/app.py")
else:
    code_norm = code.replace("\r\n", "\n")
    if old_target in code_norm:
        code_norm = code_norm.replace(old_target, new_target)
        app_path.write_text(code_norm, encoding="utf-8")
        print("Successfully patched web_platform/app.py (normalized)")
    else:
        print("Old target not found in app.py")
