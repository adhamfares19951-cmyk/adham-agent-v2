import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:\Projects\adham-agent\brain.py', 'r', encoding='utf-8') as f:
    text = f.read()

print("Length of brain.py:", len(text))
for line in text.splitlines()[:50]:
    print(line)
