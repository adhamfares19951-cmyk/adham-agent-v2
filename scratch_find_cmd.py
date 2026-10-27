with open(r"C:\Projects\adham-agent\main.py", 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'def fruitdrama_command' in line or 'CommandHandler("fruitdrama"' in line:
            print(f"{i+1}: {line.strip()}")
