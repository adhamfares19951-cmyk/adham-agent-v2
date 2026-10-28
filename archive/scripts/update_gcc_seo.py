import re

index_path = r'C:\Projects\adham-agent\dist_pages\index.html'
with open(index_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Title and Canonical to root
html = html.replace('<link rel="canonical" href="https://smartglamp.pages.dev/glamp">', '<link rel="canonical" href="https://smartglamp.pages.dev/">')
html = html.replace('href="https://smartglamp.pages.dev/glamp"', 'href="https://smartglamp.pages.dev/"')
html = html.replace('content="https://smartglamp.pages.dev/glamp"', 'content="https://smartglamp.pages.dev/"')

# 2. Add GCC Geo Meta Tags & hreflang right before </head>
gcc_meta = """  <!-- GCC Regional Geo-Targeting & Multi-Country hreflang -->
  <meta name="geo.region" content="SA;AE;KW;QA;BH;OM">
  <meta name="geo.placename" content="Riyadh, Jeddah, Dammam, Dubai, Abu Dhabi, Kuwait City, Doha, Manama, Muscat">
  <meta name="geo.position" content="24.7136;46.6753">
  <meta name="ICBM" content="24.7136, 46.6753">
  
  <link rel="alternate" hreflang="ar" href="https://smartglamp.pages.dev/" />
  <link rel="alternate" hreflang="ar-SA" href="https://smartglamp.pages.dev/" />
  <link rel="alternate" hreflang="ar-AE" href="https://smartglamp.pages.dev/" />
  <link rel="alternate" hreflang="ar-KW" href="https://smartglamp.pages.dev/" />
  <link rel="alternate" hreflang="ar-QA" href="https://smartglamp.pages.dev/" />
  <link rel="alternate" hreflang="ar-BH" href="https://smartglamp.pages.dev/" />
  <link rel="alternate" hreflang="ar-OM" href="https://smartglamp.pages.dev/" />
  <link rel="alternate" hreflang="x-default" href="https://smartglamp.pages.dev/" />

  <!-- GCC OpenGraph Locales -->
  <meta property="og:locale:alternate" content="ar_AE">
  <meta property="og:locale:alternate" content="ar_KW">
  <meta property="og:locale:alternate" content="ar_QA">
  <meta property="og:locale:alternate" content="ar_BH">
  <meta property="og:locale:alternate" content="ar_OM">
"""

# Replace keywords with supercharged GCC keywords
gcc_keywords = 'مصباح g-lamp, مصباح جي لامب الذكي الاصلي, شاحن لاسلكي وسبيكر, اضاءة سيت اب جيمنج, اضاءة غرف نوم ذكية, مصباح طاولة ذكي متعدد الوظائف, مصباح g-lamp السعودية, مصباح جي لامب الرياض جدة, مصباح جي لامب الامارات دبي, مصباح g lamp الكويت, شحن مجاني دفع عند الاستلام, هدايا شباب وبنات فخمة, g lamp saudi arabia, g lamp uae, smart wireless charger lamp rgb'
html = re.sub(r'<meta name="keywords" content=".*?">', f'<meta name="keywords" content="{gcc_keywords}">', html)

# Insert GCC meta if not present
if 'geo.region' not in html:
    html = html.replace('</head>', f'{gcc_meta}\n</head>')

# 3. Add OnlineStore JSON-LD schema
store_schema = """
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "OnlineStore",
    "name": "Smart Store Gulf | متجر سمارت الخليج",
    "url": "https://smartglamp.pages.dev",
    "logo": "https://smartglamp.pages.dev/logo.svg",
    "description": "المتجر الإلكتروني الرائد في أحدث الأجهزة الذكية ومستلزمات السيت اب والإضاءة التفاعلية في السعودية ودول الخليج العربي.",
    "areaServed": [
      {"@type": "Country", "name": "Saudi Arabia"},
      {"@type": "Country", "name": "United Arab Emirates"},
      {"@type": "Country", "name": "Kuwait"},
      {"@type": "Country", "name": "Qatar"},
      {"@type": "Country", "name": "Bahrain"},
      {"@type": "Country", "name": "Oman"}
    ],
    "currenciesAccepted": "SAR, AED, KWD, QAR, BHD, OMR",
    "paymentAccepted": "Cash on Delivery, الدفع عند الاستلام"
  }
  </script>
"""

if 'OnlineStore' not in html:
    html = html.replace('</head>', f'{store_schema}\n</head>')

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("index.html updated with GCC SEO successfully!")
