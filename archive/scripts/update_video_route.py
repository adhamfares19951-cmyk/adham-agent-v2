from pathlib import Path

p = Path("C:/Projects/adham-agent/web_platform/app.py")
code = p.read_text(encoding="utf-8")

old = 'vid_path = Path("C:/Projects/adham-agent/workspace_data/media/glamp_tiktok_angle2.mp4")'
new = 'vid_path = Path("C:/Projects/adham-agent/workspace_data/media/glamp_tiktok_natural_v3.mp4")'

if old in code:
    code = code.replace(old, new, 1)
    p.write_text(code, encoding="utf-8")
    print("Updated /video in app.py")
else:
    print("Could not find old string")
