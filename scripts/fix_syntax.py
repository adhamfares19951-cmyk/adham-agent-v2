from pathlib import Path

p = Path("C:/Projects/adham-agent/main.py")
lines = p.read_text(encoding="utf-8").splitlines()

fixed_lines = []
for i, line in enumerate(lines):
    if 'await msg.reply_text("✅ يمكنك تنزيل' in line:
        fixed_lines.append('                await msg.reply_text("✅ يمكنك تنزيل ملف السيرة الذاتية مباشرة من الرابط:\\nhttps://smartglamp.pages.dev/cv.pdf")')
    elif 'https://smartglamp.pages.dev/cv.pdf")' in line and (i > 0 and 'await msg.reply_text' in lines[i-1]):
        # skip this leftover line
        continue
    else:
        fixed_lines.append(line)

p.write_text("\n".join(fixed_lines), encoding="utf-8")
print("Cleanly fixed lines!")
