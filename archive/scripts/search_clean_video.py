import httpx
import re

urls = [
    "https://cjdropshipping.com/product/g-shape-led-wireless-charging-speaker-p-1704768310926041088.html",
    "https://cjdropshipping.com/product/g-shape-smart-light-sound-machine-p-1647862734676832256.html"
]

found = set()
for u in urls:
    try:
        r = httpx.get(u, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        matches = re.findall(r'https?://[^\s"\'<>]+\.mp4', r.text)
        found.update(matches)
    except Exception as e:
        print("Error:", e)

print(f"Found {len(found)} mp4 videos:")
for f in found:
    print(f)
