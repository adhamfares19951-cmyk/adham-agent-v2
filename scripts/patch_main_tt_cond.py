import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

main_path = Path(r"C:\Projects\adham-agent\main.py")
content = main_path.read_text(encoding="utf-8")

old_tt = """    # 3. TikTok Upload
    if is_publish and is_tiktok and not is_ig:"""

new_tt = """    # 3. TikTok Upload or Product Short Video
    if is_publish and (is_tiktok or is_short_intent) and not is_ig and not is_trading:"""

if old_tt in content:
    content = content.replace(old_tt, new_tt, 1)
    print("Patched TikTok upload condition in main.py.")
else:
    print("Warning: old_tt not found.")

main_path.write_text(content, encoding="utf-8")
print("main.py updated.")
