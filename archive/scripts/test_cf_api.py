import json
import urllib.request

with open(r'C:\Projects\adham-agent\sessions\cloudflare_cookies.json', 'r', encoding='utf-8') as f:
    cookies = json.load(f)

cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])

url = 'https://api.cloudflare.com/client/v4/accounts/0d5cfb75481d1c9e9f30bfa147dec860/pages/projects'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Cookie': cookie_str,
    'Accept': 'application/json'
})

try:
    with urllib.request.urlopen(req) as resp:
        print('API Resp:', resp.read().decode('utf-8')[:300])
except urllib.error.HTTPError as e:
    print('API Error:', e.code, e.read().decode('utf-8')[:300])
except Exception as e:
    print('Err:', e)
