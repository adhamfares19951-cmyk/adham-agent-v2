import os

env_path = r"C:\Projects\adham-agent\.env"
with open(env_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith("GROQ_MODEL="):
        new_lines.append("GROQ_MODEL=openai/gpt-oss-120b\n")
    elif line.startswith("PROVIDER_ORDER="):
        new_lines.append("PROVIDER_ORDER=Gemini,Groq,Cloudflare,Mistral,xKiro,OpenRouter\n")
    else:
        new_lines.append(line)

with open(env_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("SUCCESS: .env updated!")
