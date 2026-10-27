# -*- coding: utf-8 -*-
"""Makes sitemap.xml and robots.txt in web_platform/app.py 100% dynamic with memory.get_setting('public_web_url')."""
from pathlib import Path

app_path = Path("C:/Projects/adham-agent/web_platform/app.py")
code = app_path.read_text(encoding="utf-8")

old_robots = """@app.get("/robots.txt", response_class=PlainTextResponse)
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
    return Response(content=xml_content, media_type="application/xml")"""

new_robots = """def _get_base_url() -> str:
    return (memory.get_setting("public_web_url") or "http://127.0.0.1:8080").rstrip("/")


@app.get("/robots.txt", response_class=PlainTextResponse)
async def get_robots_txt():
    \"\"\"Search Engine crawling permissions & dynamic sitemap declaration.\"\"\"
    base = _get_base_url()
    content = (
        "User-agent: *\\n"
        "Allow: /\\n"
        "Allow: /glamp\\n"
        "Allow: /logo\\n"
        "Allow: /logo-vector\\n"
        "Allow: /video\\n"
        f"Sitemap: {base}/sitemap.xml\\n"
    )
    return PlainTextResponse(content, media_type="text/plain")


@app.get("/sitemap.xml")
async def get_sitemap_xml():
    \"\"\"Dynamic XML Sitemap for Google, Bing, and Search Engine indexers.\"\"\"
    base = _get_base_url()
    xml_content = f\"\"\"<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>{base}/</loc>
    <lastmod>2026-10-27</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{base}/glamp</loc>
    <lastmod>2026-10-27</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
    <image:image>
      <image:loc>{base}/logo</image:loc>
      <image:title>مصباح G-Lamp الذكي 4 في 1</image:title>
    </image:image>
  </url>
</urlset>\"\"\"
    return Response(content=xml_content, media_type="application/xml")"""

if old_robots in code:
    code = code.replace(old_robots, new_robots)
    app_path.write_text(code, encoding="utf-8")
    print("SUCCESS: web_platform/app.py updated with dynamic base URL!")
else:
    print("Target block not matched.")
