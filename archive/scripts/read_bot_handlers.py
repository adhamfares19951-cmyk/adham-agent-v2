import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:\Projects\adham-agent\tools\telegram_bot.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if any(k in l for k in ['def handle', 'def _handle', 'def on_message', 'def process', 'MasterBrain', 'execute_goal', 'chat_history']):
        print(f"{i}: {l.strip()}")
        for j in range(i, min(len(lines), i + 25)):
            print(f"  {lines[j]}", end='')
        print("\n" + "="*40)
