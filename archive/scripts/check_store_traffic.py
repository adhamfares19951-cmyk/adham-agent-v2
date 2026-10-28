# -*- coding: utf-8 -*-
import json
import urllib.request
from pathlib import Path

cookie_file = Path(r"C:\Projects\adham-agent\sessions\cloudflare_cookies.json")
if not cookie_file.exists():
    print("No cloudflare cookies found.")
    exit(0)

cookies = json.loads(cookie_file.read_text(encoding="utf-8"))
cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
account_id = "0d5cfb75481d1c9e9f30bfa147dec860"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Cookie": cookie_str,
    "Accept": "application/json"
}

# 1. Project details & deployments
url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/smartglamp"
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        res = data.get("result", {})
        print("Project Name:", res.get("name"))
        print("Subdomain:", res.get("subdomain"))
        print("Production Branch:", res.get("production_branch"))
        latest = res.get("latest_deployment", {})
        print("Latest Deployment ID:", latest.get("id"))
        print("Latest Deployment Created On:", latest.get("created_on"))
        print("Latest Deployment Environment:", latest.get("environment"))
        print("URL:", latest.get("url"))
except Exception as e:
    print("Project info error:", e)

# 2. Deployments history
dep_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/smartglamp/deployments"
try:
    req_dep = urllib.request.Request(dep_url, headers=headers)
    with urllib.request.urlopen(req_dep) as resp:
        dep_data = json.loads(resp.read().decode("utf-8"))
        deps = dep_data.get("result", [])
        print(f"Total Cloudflare Deployments: {len(deps)}")
        for d in deps[:3]:
            print(f"  - Deployment {d.get('id')[:8]} | {d.get('created_on')} | status: {d.get('latest_stage', {}).get('status')}")
except Exception as e:
    print("Deployments error:", e)
