# -*- coding: utf-8 -*-
"""Passes dynamic base_url to glamp_landing template and replaces static URLs."""
from pathlib import Path

# 1. Update app.py
app_path = Path("C:/Projects/adham-agent/web_platform/app.py")
code = app_path.read_text(encoding="utf-8")
old_glamp = """@app.get("/glamp", response_class=HTMLResponse)
async def glamp_landing_page(request: Request):
    \"\"\"Renders high-converting COD dropshipping landing page for G-Lamp 4-in-1.\"\"\"
    return templates.TemplateResponse(
        request=request,
        name="glamp_landing.html",
        context={},
    )"""

new_glamp = """@app.get("/glamp", response_class=HTMLResponse)
async def glamp_landing_page(request: Request):
    \"\"\"Renders high-converting COD dropshipping landing page for G-Lamp 4-in-1.\"\"\"
    base = _get_base_url()
    return templates.TemplateResponse(
        request=request,
        name="glamp_landing.html",
        context={"base_url": base},
    )"""

if old_glamp in code:
    code = code.replace(old_glamp, new_glamp)
    app_path.write_text(code, encoding="utf-8")
    print("Updated app.py glamp context")

# 2. Update glamp_landing.html
html_path = Path("C:/Projects/adham-agent/web_platform/templates/glamp_landing.html")
html = html_path.read_text(encoding="utf-8")
old_hardcoded = "https://console-duration-sage-troubleshooting.trycloudflare.com"
if old_hardcoded in html:
    html = html.replace(old_hardcoded, "{{ base_url }}")
    html_path.write_text(html, encoding="utf-8")
    print("Updated glamp_landing.html with {{ base_url }}")
