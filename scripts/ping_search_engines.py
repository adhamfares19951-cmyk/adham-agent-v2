import urllib.request
import json

# 1. IndexNow API Ping
indexnow_payload = {
    'host': 'smartglamp.pages.dev',
    'key': 'a8f3b2e7c9d14682b5e0f7193245cba8',
    'keyLocation': 'https://smartglamp.pages.dev/a8f3b2e7c9d14682b5e0f7193245cba8.txt',
    'urlList': [
        'https://smartglamp.pages.dev/',
        'https://smartglamp.pages.dev/sitemap.xml'
    ]
}

req = urllib.request.Request(
    'https://api.indexnow.org/indexnow',
    data=json.dumps(indexnow_payload).encode('utf-8'),
    headers={'Content-Type': 'application/json; charset=utf-8', 'User-Agent': 'Mozilla/5.0'},
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print('IndexNow Ping Status:', resp.status)
except Exception as e:
    print('IndexNow error:', e)

# 2. Bing Ping
try:
    bing_url = 'https://www.bing.com/ping?sitemap=https%3A%2F%2Fsmartglamp.pages.dev%2Fsitemap.xml'
    req_bing = urllib.request.Request(bing_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_bing, timeout=10) as resp:
        print('Bing Sitemap Ping Status:', resp.status)
except Exception as e:
    print('Bing ping error:', e)

# 3. Google Ping
try:
    google_url = 'https://www.google.com/ping?sitemap=https%3A%2F%2Fsmartglamp.pages.dev%2Fsitemap.xml'
    req_google = urllib.request.Request(google_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_google, timeout=10) as resp:
        print('Google Sitemap Ping Status:', resp.status)
except Exception as e:
    print('Google ping error:', e)
