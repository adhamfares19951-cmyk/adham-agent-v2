import httpx
import sys

sys.stdout.reconfigure(encoding='utf-8')

candidates = [
    ("socks5://2.50.191.129:10810", "socks5"),
    ("http://2.50.191.129:10810", "http"),
    ("http://47.91.104.88:3129", "http"),
    ("http://47.91.121.127:8443", "http"),
]

for p, proto in candidates:
    print(f"Testing {p}...")
    try:
        with httpx.Client(proxy=p, timeout=5) as client:
            resp = client.get("http://ip-api.com/json")
            if resp.status_code == 200:
                data = resp.json()
                print(f"SUCCESS {p} -> Country: {data.get('country')}, City: {data.get('city')}, ISP: {data.get('isp')}")
            else:
                print(f"Response {resp.status_code}")
    except Exception as e:
        print(f"FAILED {p}: {type(e).__name__} - {e}")
