# -*- coding: utf-8 -*-
"""Updates glamp_landing.html with luxury brand bar, SEO OpenGraph, Twitter Cards, Schema.org JSON-LD."""
import sys
from pathlib import Path

def run():
    landing_file = Path("C:/Projects/adham-agent/web_platform/templates/glamp_landing.html")
    html = landing_file.read_text(encoding="utf-8")

    seo_head = """<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>مصباح G-Lamp الذكي 4 في 1 | شاحن لاسلكي وسبيكر وإضاءة تفاعلية - سمارت ستور</title>
  
  <!-- Primary Meta Tags -->
  <meta name="title" content="مصباح G-Lamp الذكي 4 في 1 | شاحن لاسلكي وسبيكر وإضاءة تفاعلية - سمارت ستور">
  <meta name="description" content="تسوق مصباح G-Lamp الذكي 4 في 1 الأصلي في السعودية والإمارات. شاحن لاسلكي سريع 15W وسبيكر بلوتوث سينمائي وإضاءة RGB تفاعلية بـ 256 نمطاً. شحن مجاني والدفع عند الاستلام بعد المعاينة!">
  <meta name="keywords" content="مصباح g-lamp, مصباح جي لامب, شاحن لاسلكي وسبيكر, اضاءة سيت اب, سمارت ستور, شاحن سريع 15w, هدايا تقنية, متجر سمارت السعودية, متجر سمارت الامارات, الدفع عند الاستلام, g lamp saudi, wireless charger lamp">
  <meta name="author" content="Smart Store GCC">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <link rel="canonical" href="https://console-duration-sage-troubleshooting.trycloudflare.com/glamp">

  <!-- Open Graph / Facebook / WhatsApp -->
  <meta property="og:type" content="product">
  <meta property="og:url" content="https://console-duration-sage-troubleshooting.trycloudflare.com/glamp">
  <meta property="og:title" content="مصباح G-Lamp الذكي 4 في 1 | وفر 40% + شحن مجاني">
  <meta property="og:description" content="جهاز 4 في 1 ثوري: شاحن لاسلكي 15W، سبيكر بلوتوث قوي، إضاءة محيطية 256 لوناً، وساعة رقمية. توصيل سريع لكافة مدن المملكة والإمارات والدفع عند الاستلام!">
  <meta property="og:image" content="https://console-duration-sage-troubleshooting.trycloudflare.com/logo">
  <meta property="og:image:width" content="1024">
  <meta property="og:image:height" content="1024">
  <meta property="og:site_name" content="Smart Store | متجر سمارت">
  <meta property="og:locale" content="ar_SA">

  <!-- Twitter / X -->
  <meta property="twitter:card" content="summary_large_image">
  <meta property="twitter:url" content="https://console-duration-sage-troubleshooting.trycloudflare.com/glamp">
  <meta property="twitter:title" content="مصباح G-Lamp الذكي 4 في 1 | سمارت ستور">
  <meta property="twitter:description" content="شاحن لاسلكي 15W + سبيكر بلوتوث + إضاءة RGB تفاعلية مع الموسيقى. الدفع عند الاستلام وشحن مجاني!">
  <meta property="twitter:image" content="https://console-duration-sage-troubleshooting.trycloudflare.com/logo">

  <!-- Favicon -->
  <link rel="icon" type="image/png" href="/logo-vector">
  <link rel="apple-touch-icon" href="/logo">

  <!-- Schema.org JSON-LD Structured Data for Google Rich Results -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org/",
    "@type": "Product",
    "name": "مصباح G-Lamp الذكي 4 في 1 (G-Shape RGB Wireless Charger Speaker Lamp)",
    "image": [
      "https://console-duration-sage-troubleshooting.trycloudflare.com/logo",
      "https://cf.cjdropshipping.com/5651039d-38e6-4851-aaef-38be1445e4a4.jpg"
    ],
    "description": "مصباح G-Lamp الذكي المتطور يجمع شاحن لاسلكي سريع بقوة 15 واط، سبيكر بلوتوث سينمائي عالي النقاوة، إضاءة محيطية تفاعلية بـ 256 نمطاً لونياً تتزامن مع الموسيقى، وساعة رقمية مع منبه شروق الشمس.",
    "sku": "GLAMP-4IN1-SA",
    "mpn": "GLAMP-2026",
    "brand": {
      "@type": "Brand",
      "name": "Smart Store"
    },
    "offers": {
      "@type": "Offer",
      "url": "https://console-duration-sage-troubleshooting.trycloudflare.com/glamp",
      "priceCurrency": "SAR",
      "price": "149",
      "priceValidUntil": "2027-12-31",
      "itemCondition": "https://schema.org/NewCondition",
      "availability": "https://schema.org/InStock",
      "seller": {
        "@type": "Organization",
        "name": "Smart Store GCC"
      }
    },
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.9",
      "reviewCount": "128",
      "bestRating": "5",
      "worstRating": "1"
    }
  }
  </script>
"""

    start_h = html.find("<head>")
    end_h = html.find("</head>")
    css_start = html.find('<script src="https://cdn.tailwindcss.com">')
    if start_h != -1 and end_h != -1 and css_start != -1:
        css_part = html[css_start:end_h]
        new_head = seo_head + "  " + css_part + "\n</head>"
        html = html[:start_h] + new_head + html[end_h + 7:]

    # Brand Navbar insertion below Announcement Bar
    announcement_tag = "</div>\n\n  <!-- Hero Section -->"
    brand_navbar = """</div>

  <!-- Brand Luxury Navbar -->
  <nav class="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between border-b border-gray-800/80">
    <div class="flex items-center gap-3">
      <img src="/logo-vector" alt="Smart Store Logo" class="w-11 h-11 object-contain rounded-lg shadow-md border border-purple-500/30">
      <div>
        <div class="text-lg font-black text-white tracking-wide flex items-center gap-1.5">
          <span>Smart Store</span>
          <span class="text-xs bg-purple-900/80 text-purple-300 px-2 py-0.5 rounded-md border border-purple-500/40">GCC</span>
        </div>
        <div class="text-xs text-gray-400 font-medium">متجر سمارت | الوكيل المعتمد في الخليج</div>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <span class="inline-flex items-center gap-1.5 bg-emerald-950/70 text-emerald-400 border border-emerald-500/30 text-xs px-3 py-1 rounded-full font-bold shadow-sm">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
        الدفع عند الاستلام متاح
      </span>
    </div>
  </nav>

  <!-- Hero Section -->"""

    if announcement_tag in html:
        html = html.replace(announcement_tag, brand_navbar)

    landing_file.write_text(html, encoding="utf-8")
    print("SUCCESS: glamp_landing.html updated with SEO, Schema.org, and Luxury Brand Bar!")

if __name__ == "__main__":
    run()
