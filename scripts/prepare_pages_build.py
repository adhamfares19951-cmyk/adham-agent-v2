import os
import shutil

dist_dir = r'C:\Projects\adham-agent\dist_pages'
os.makedirs(dist_dir, exist_ok=True)
os.makedirs(os.path.join(dist_dir, 'functions', 'api'), exist_ok=True)

# 1. Render index.html from template
with open(r'C:\Projects\adham-agent\web_platform\templates\glamp_landing.html', 'r', encoding='utf-8') as f:
    template = f.read()

rendered = template.replace('{{ public_url }}', 'https://smartglamp.pages.dev')
rendered = rendered.replace('{{ base_url }}', 'https://smartglamp.pages.dev')

# Replace any trycloudflare URLs in canonical or og tags
import re
rendered = re.sub(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', 'https://smartglamp.pages.dev', rendered)

logo_svg_path = r'C:\Projects\adham-agent\web_platform\static\logo.svg'
if os.path.exists(logo_svg_path):
    shutil.copy(logo_svg_path, os.path.join(dist_dir, 'logo.svg'))
    rendered = rendered.replace('/logo-vector', '/logo.svg')

with open(os.path.join(dist_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(rendered)

# 2. Add robots.txt
robots_content = """User-agent: *
Allow: /
Sitemap: https://smartglamp.pages.dev/sitemap.xml
"""
with open(os.path.join(dist_dir, 'robots.txt'), 'w', encoding='utf-8') as f:
    f.write(robots_content)

# 3. Add sitemap.xml
sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://smartglamp.pages.dev/</loc>
    <lastmod>2026-10-28</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""
with open(os.path.join(dist_dir, 'sitemap.xml'), 'w', encoding='utf-8') as f:
    f.write(sitemap_content)

# 4. Add Cloudflare Pages Function proxy for /api/order
order_function = """export async function onRequestPost(context) {
  try {
    const body = await context.request.json();
    const targetUrl = 'https://necklace-include-tunnel-morris.trycloudflare.com/api/order';
    
    const response = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'CloudflarePages-Proxy/1.0'
      },
      body: JSON.stringify(body)
    });
    
    const data = await response.json();
    return new Response(JSON.stringify(data), {
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  } catch (err) {
    return new Response(JSON.stringify({ success: false, error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
"""
with open(os.path.join(dist_dir, 'functions', 'api', 'order.js'), 'w', encoding='utf-8') as f:
    f.write(order_function)

print("dist_pages build ready at:", dist_dir)
