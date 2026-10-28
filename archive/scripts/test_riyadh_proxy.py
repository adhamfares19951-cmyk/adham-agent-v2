import httpx

for proto in ["http", "socks5"]:
    for port in [80, 8443, 443]:
        url = f"{proto}://130.94.58.215:{port}"
        try:
            with httpx.Client(proxy=url, timeout=3) as c:
                resp = c.get("http://ip-api.com/json")
                print(f"SUCCESS with {url}: {resp.json()}")
        except Exception as e:
            print(f"Failed {url}: {type(e).__name__}")
