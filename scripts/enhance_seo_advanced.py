# -*- coding: utf-8 -*-
"""Advanced SEO enhancements for glamp_landing.html following the SEO skill guidelines:
1. Add FAQPage Schema.org structured data.
2. Add Interactive FAQ Section with targeted search keywords.
3. Add Core Web Vitals hero image preloading.
4. Align brand name across footer and meta.
"""
from pathlib import Path

landing_file = Path("C:/Projects/adham-agent/web_platform/templates/glamp_landing.html")
html = landing_file.read_text(encoding="utf-8")

# 1. Add hero preload inside <head>
preload_tag = '<link rel="preload" as="image" href="https://cf.cjdropshipping.com/5651039d-38e6-4851-aaef-38be1445e4a4.jpg">\n  '
if 'rel="preload"' not in html:
    html = html.replace('<!-- Favicon -->', preload_tag + '<!-- Favicon -->')

# 2. Add FAQPage Schema.org to JSON-LD
faq_schema = """  <!-- FAQPage Schema for Google Rich Snippets -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "هل يدعم مصباح G-Lamp الشحن اللاسلكي السريع لجميع الهواتف؟",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "نعم، يدعم تقنية الشحن اللاسلكي السريع بقوة 15 واط المتوافقة مع جميع أجهزة iPhone من الإصدار 8 حتى iPhone 16 Pro Max، وكافة هواتف سامسونج جالاكسي وهواوي وشاومي الداعمة لتقنية Qi."
        }
      },
      {
        "@type": "Question",
        "name": "كيف تتم عملية الدفع عند الاستلام في السعودية والإمارات؟",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "لن تدفع أي مبالغ مقدماً عند الطلب. يتم دفع قيمة المنتج نقداً أو عبر بطاقة مدى/Apple Pay لمندوب التوصيل بعد استلام المنتج ومعاينته شخصياً أمام المندوب."
        }
      },
      {
        "@type": "Question",
        "name": "كم تستغرق مدة توصيل مصباح G-Lamp؟",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "الشحن مجاني وسريع لكافة مدن ومناطق المملكة العربية السعودية (الرياض، جدة، مكة، الدمام، إلخ) ودولة الإمارات (دبي، أبوظبي، الشارقة) ويستغرق التوصيل من يومين إلى 4 أيام عمل كحد أقصى."
        }
      },
      {
        "@type": "Question",
        "name": "هل يوجد ضمان على مصباح G-Lamp الذكي؟",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "نعم، نقدم ضماناً ذهبياً لمدة عام كامل ضد أي عيوب مصنعية، مع إمكانية الاستبدال الفوري بدون أي تكاليف إضافية."
        }
      },
      {
        "@type": "Question",
        "name": "كيف يمكن التحكم بالإضاءة التفاعلية وسبيكر البلوتوث؟",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "يمكنك ربط مكبر الصوت بالبلوتوث 5.3 فورياً بأي هاتف لتشغيل المقاطع الصوتية، والتحكم بـ 256 نمطاً لونياً للإضاءة المتزامنة مع رتم الصوت إما عبر أزرار المصباح مباشرة أو عبر تطبيق الهاتف الذكي."
        }
      }
    ]
  }
  </script>
"""

if "FAQPage" not in html:
    html = html.replace('</head>', faq_schema + '</head>')

# 3. Add FAQ Section before </main>
faq_html_section = """
    <!-- Search-Engine Optimized FAQ Section -->
    <section class="max-w-2xl mx-auto mt-12 mb-8">
      <div class="text-center mb-6">
        <span class="bg-purple-900/60 text-purple-300 border border-purple-500/30 text-xs font-semibold px-3 py-1 rounded-full">
          💡 إجابات لكل استفساراتك
        </span>
        <h2 class="text-2xl md:text-3xl font-black text-white mt-2">الأسئلة الشائعة حول مصباح G-Lamp</h2>
      </div>

      <div class="space-y-3">
        <div class="bg-[#131b2e] border border-gray-800 rounded-xl p-4">
          <h3 class="font-bold text-white text-sm md:text-base flex items-center gap-2 mb-1">
            <span class="text-purple-400">❓</span> هل يدعم الشحن اللاسلكي السريع لجميع الجوالات؟
          </h3>
          <p class="text-gray-300 text-xs md:text-sm leading-relaxed pr-6">
            نعم، يدعم شحن Qi اللاسلكي السريع حتى 15W لكافة هواتف آيفون (من 8 حتى 16 Pro Max)، وهواتف سامسونج جالاكسي، وهواوي، وسماعات AirPods الداعمة للشحن اللاسلكي.
          </p>
        </div>

        <div class="bg-[#131b2e] border border-gray-800 rounded-xl p-4">
          <h3 class="font-bold text-white text-sm md:text-base flex items-center gap-2 mb-1">
            <span class="text-purple-400">❓</span> كيف يعمل الدفع عند الاستلام؟
          </h3>
          <p class="text-gray-300 text-xs md:text-sm leading-relaxed pr-6">
            طلبك مجاني 100% الآن بدون أي دفع مسبق. الدفع نقداً أو بالشبكة عند وصول المندوب لباب منزلك بعد فحص ومعاينة المنتج.
          </p>
        </div>

        <div class="bg-[#131b2e] border border-gray-800 rounded-xl p-4">
          <h3 class="font-bold text-white text-sm md:text-base flex items-center gap-2 mb-1">
            <span class="text-purple-400">❓</span> كم يستغرق الشحن والتوصيل؟
          </h3>
          <p class="text-gray-300 text-xs md:text-sm leading-relaxed pr-6">
            التوصيل مجاني وسريع خلال 2 إلى 4 أيام عمل لكافة مناطق ومحافظات المملكة العربية السعودية والإمارات العربية المتحدة.
          </p>
        </div>

        <div class="bg-[#131b2e] border border-gray-800 rounded-xl p-4">
          <h3 class="font-bold text-white text-sm md:text-base flex items-center gap-2 mb-1">
            <span class="text-purple-400">❓</span> ما هو الضمان وسياسة الاستبدال؟
          </h3>
          <p class="text-gray-300 text-xs md:text-sm leading-relaxed pr-6">
            نوفر ضماناً ذهبياً لمدة عام كامل ضد العيوب المصنعية، مع استبدال فوري للجهاز إذا واجهت أي مشكلة فنية.
          </p>
        </div>
      </div>
    </section>
"""

if "الأسئلة الشائعة حول مصباح G-Lamp" not in html:
    html = html.replace('<!-- Customer Reviews -->', faq_html_section + '\n    <!-- Customer Reviews -->')

# 4. Update Footer Brand name
html = html.replace('متجر النخبة الذكي (Smart Elite Store)', 'Smart Store GCC — متجر سمارت الخليج')

landing_file.write_text(html, encoding="utf-8")
print("SUCCESS: Advanced SEO FAQ section and schema markup added!")
