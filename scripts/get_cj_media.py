import json, httpx, re
from pathlib import Path

product_url = 'https://cjdropshipping.com/product/new-intelligent-g-shaped-led-lamp-bluetooth-speake-wireless-charger-atmosphere-lamp-app-control-for-bedroom-home-decor-p-1592715415925567488.html'
cookies = json.load(open('workspace_data/cj_cookies.json', 'r', encoding='utf-8'))
jar = {c['name']: c['value'] for c in cookies}
headers = {'User-Agent': 'Mozilla/5.0'}

with httpx.Client(cookies=jar, headers=headers, follow_redirects=True, timeout=15) as c:
    r = c.get(product_url)
    print('Status:', r.status_code)
    images = set(re.findall(r'https://[^"\'<>\s]+?\.(?:jpg|jpeg|png)', r.text))
    videos = set(re.findall(r'https://[^"\'<>\s]+?\.mp4', r.text))
    print('Found images:', len(images))
    print('Found videos:', len(videos))
    for v in videos:
        print('Video:', v)
    for img in sorted(list(images))[:10]:
        print('Image:', img)
