# -*- coding: utf-8 -*-
"""Adds /robots.txt and /sitemap.xml endpoints to web_platform/app.py."""
from pathlib import Path

app_path = Path("C:/Projects/adham-agent/web_platform/app.py")
code = app_path.read_text(encoding="utf-8")

# 1. Update imports
if "from fastapi.responses import HTMLResponse, JSONResponse, FileResponse" in code:
    code = code.replace(
        "from fastapi.responses import HTMLResponse, JSONResponse, FileResponse",
        "from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse, Response"
    )

# 2. Add routes before health check
routes_to_add = """

@app.get("/robots.txt", response_class=PlainTextResponse)
async def get_robots_txt():
    \"\"\"Search Engine crawling permissions & sitemap declaration.\"\"\"
    content = (
        "User-agent: *\\n"
        "Allow: /\\n"
        "Allow: /glamp\\n"
        "Allow: /logo\\n"
        "Allow: /video\\n"
        "Sitemap: https://console-duration-sage-troubleshooting.trycloudflare.com/sitemap.xml\\n"
    )
    return PlainTextResponse(content, media_type="text/plain")


@app.get("/sitemap.xml")
async def get_sitemap_xml():
    \"\"\"Dynamic XML Sitemap for Google, Bing, and Search Engine indexers.\"\"\"
    xml_content = \"\"\"<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>https://console-duration-sage-troubleshooting.trycloudflare.com/</loc>
    <lastmod>2026-10-27</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://console-duration-sage-troubleshooting.trycloudflare.com/glamp</loc>
    <lastmod>2026-10-27</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
    <image:image>
      <image:loc>https://console-duration-sage-troubleshooting.trycloudflare.com/logo</image:loc>
      <image:title>مصباح G-Lamp الذكي 4 في 1</image:title>
    </image:image>
  </url>
</urlset>\"\"\"
    return Response(content=xml_content, media_type="application/xml")
"""

if "@app.get(\"/health\")" in code and "get_sitemap_xml" not in code:
    code = code.replace("@app.get(\"/health\")", routes_to_add + "\n\n@app.get(\"/health\")")

app_path.write_text(code, encoding="utf-8")
print("SUCCESS: web_platform/app.py updated with /robots.txt and /sitemap.xml!")
