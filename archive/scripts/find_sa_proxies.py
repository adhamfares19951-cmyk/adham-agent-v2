import httpx
import sys

sys.stdout.reconfigure(encoding='utf-8')

sources = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http,socks5&timeout=5000&country=SA,AE&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt",
]

sa_ae_proxies = []

for url in sources:
    try:
        r = httpx.get(url, timeout=10)
        if r.status_code == 200:
            lines = [l.strip() for l in r.text.splitlines() if l.strip() and not l.startswith("#")]
            print(f"Source {url[:40]}... returned {len(lines)} items")
            if "SA,AE" in url:
                sa_ae_proxies.extend(lines)
    except Exception as e:
        print(f"Error fetching from {url[:30]}: {e}")

print(f"Total potential SA/AE from direct source: {len(sa_ae_proxies)}")
for p in sa_ae_proxies[:10]:
    print("Candidate:", p)
