import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:\Projects\adham-agent\tools\__init__.py', 'r', encoding='utf-8') as f:
    text = f.read()

print("Length of tools/__init__.py:", len(text))
for line in text.splitlines()[:60]:
    print(line)
