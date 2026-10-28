import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:\Projects\adham-agent\main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Total lines in main.py:", len(lines))

for i, l in enumerate(lines):
    if any(k in l for k in ['chat_history', 'message_handler', 'process_user_message', 'handle_message', 'on_message', 'pdf', 'File not found']):
        print(f"Line {i}: {l.strip()[:100]}")
