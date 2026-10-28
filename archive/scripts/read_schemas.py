import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:\Projects\adham-agent\dist_pages\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

tag = '<script type="application/ld+json">'
idx = 0
while True:
    start = text.find(tag, idx)
    if start == -1:
        break
    end = text.find('</script>', start)
    print('=== JSON-LD ===')
    print(text[start + len(tag):end].strip()[:700])
    print('='*30)
    idx = end + 9
