import httpx

print("Downloading SpeedX HTTP proxies...")
r = httpx.get("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt", timeout=10)
proxies = [l.strip() for l in r.text.splitlines() if l.strip()]
print(f"Total proxies: {len(proxies)}")

# We can query ip-api in batch or check a sample
import random
random.seed(42)
sample = random.sample(proxies, 200)

sa_found = []
for p in sample[:50]:
    try:
        ip = p.split(":")[0]
        # Quick ping to ip-api
        res = httpx.get(f"http://ip-api.com/json/{ip}?fields=countryCode,country", timeout=1.5).json()
        if res.get("countryCode") in ["SA", "AE"]:
            print(f"FOUND {res.get('country')}: {p}")
            sa_found.append((p, res.get('country')))
    except Exception:
        pass

print("SA/AE found:", sa_found)
