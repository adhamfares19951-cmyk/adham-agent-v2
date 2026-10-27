import re

with open(r"C:\Projects\adham-agent\main.py", 'r', encoding='utf-8') as f:
    text = f.read()

cmds = re.findall(r'CommandHandler\(["\'](\w+)["\']', text)
print('Command handlers in main.py:', cmds)
