import httpx
import sys

sys.stdout.reconfigure(encoding='utf-8')

proxy_sources = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=8000&country=SA&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=8000&country=SA&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=8000&country=AE&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=8000&country=AE&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
]

candidates = []
for s in proxy_sources:
    try:
        r = httpx.get(s, timeout=6)
        if r.status_code == 200:
            lines = [l.strip() for l in r.text.splitlines() if l.strip() and not l.startswith("#")]
            if "country=SA" in s:
                print(f"Direct SA from {s[:35]}: {len(lines)}")
                candidates.extend([(l, "SA") for l in lines])
            elif "country=AE" in s:
                print(f"Direct AE from {s[:35]}: {len(lines)}")
                candidates.extend([(l, "AE") for l in lines])
            else:
                # add some generic
                pass
    except Exception as e:
        print(f"Error {s[:30]}: {e}")

print("Total direct candidates:", len(candidates))
print(candidates)
