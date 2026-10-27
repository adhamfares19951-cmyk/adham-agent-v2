brain_path = r"C:\Projects\adham-agent\brain.py"
with open(brain_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace any \Projects or \Users or other unescaped backslashes in SYSTEM_PROMPT with double backslash or forward slash
text = text.replace(r"C:\Projects", r"C:/Projects")
text = text.replace(r"C:\Users", r"C:/Users")
text = text.replace(r"workspace_data\media", r"workspace_data/media")

with open(brain_path, "w", encoding="utf-8") as f:
    f.write(text)

print("SUCCESS: Escapes fixed in brain.py")
