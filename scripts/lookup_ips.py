import httpx

ips = ["213.6.13.15", "213.244.98.29", "149.154.161.198"]
for ip in ips:
    try:
        r = httpx.get(f"http://ip-api.com/json/{ip}", timeout=5.0)
        d = r.json()
        print(f"IP: {ip}")
        print(f"  Country: {d.get('country')}")
        print(f"  City: {d.get('city')}")
        print(f"  ISP: {d.get('isp')}")
        print(f"  Org: {d.get('org')}")
    except Exception as e:
        print(f"Error for {ip}: {e}")
