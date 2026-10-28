import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:\Projects\adham-agent\main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(95, 150):
    print(f"{i}: {lines[i]}", end='')
