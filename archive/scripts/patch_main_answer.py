with open(r'C:\Projects\adham-agent\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    await send_long(update, answer)

    if voice_reply:"""

replacement = """    # Sanitize dead internal IP addresses
    answer = answer.replace("http://136.244.77.61:8080/media/", "https://smartglamp.pages.dev/")
    answer = answer.replace("http://136.244.77.61:8080/", "https://smartglamp.pages.dev/")

    await send_long(update, answer)

    # Auto-dispatch any mentioned existing PDF/document directly to Telegram
    import re
    mentioned_files = re.findall(r'([A-Za-z]:\\\\[^\s<>"\']+\.(?:pdf|docx|png|jpg|mp4))', answer)
    for mf in mentioned_files:
        p = Path(mf)
        if p.exists() and p.is_file() and p.stat().st_size > 0:
            try:
                with open(p, "rb") as df:
                    await msg.reply_document(document=df, filename=p.name, caption=f"📄 {p.name}")
                break
            except Exception:
                pass

    if voice_reply:"""

if target in content:
    content = content.replace(target, replacement, 1)
    with open(r'C:\Projects\adham-agent\main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched _answer in main.py!")
else:
    print("Target not found in main.py")
