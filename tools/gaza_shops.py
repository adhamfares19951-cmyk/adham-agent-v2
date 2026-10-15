"""Gaza & Khan Younis local business scanner & Shamel POS sales pitching suite.
Helps Adham identify shops in Gaza that operate without software (or have outdated paper systems),
diagnose their retail pain points, formulate winning local pitches, and plan field sales visits.
"""
import json
import logging
import re
from typing import Optional

import memory
from tools.web_search import web_search

log = logging.getLogger("gaza_shops")

# Curated repository of Gaza retail sectors and operational profiles
GAZA_SECTORS_CATALOG = {
    "supermarket": {
        "title": "السوبرماركت والميني ماركت والبقالات التموينية",
        "keywords": ["سوبرماركت", "ماركت", "تموينات", "بقالة", "مواد غذائية"],
        "target_areas": ["خانيونس - شارع جلال", "خانيونس - البلد", "خانيونس - شارع البحر", "القرارة", "دير البلح", "النصيرات"],
        "current_status": "أغلبهم شغالين على دفتر شكك ورقي، أو إكسل على لابتوب قديم، أو بيعتمدوا على الذاكرة بدون جرد حقيقي.",
        "daily_pains": [
            "تذبذب أسعار البضاعة والشحن يومياً وصعوبة معرفة تكلفة الصنف الحقيقية وتحديد سعر البيع.",
            "الشراء من الموردين بالكرتونة والطرد والبيع للزبائن بالقطعة والعلبة.",
            "كثرة الأصناف وصعوبة الجرد بالباركود مع انقطاع الكهرباء.",
            "ديون الزبائن (الشكك / على الحساب) وضياع سجلات الدفاتر الورقية."
        ],
        "shamel_pos_solution": [
            "تطبيق أوفلاين 100% يعمل على أي هاتف أندرويد أو تابلت مع باور بانك دون الحاجة لكهرباء أو مولد.",
            "ميزة احتساب متوسط التكلفة المرجح (WAC) تلقائياً عند كل عملية توريد بالكرتونة أو القطعة.",
            "مرونة سعة الكرتونة (24، 48، 20 قطعة) وتحويل فوري للقطع بالمخزن.",
            "مسح الباركود بكاميرا الجوال بدون الحاجة لشراء قارئ باركود خارجي مكلف.",
            "تصنيفات سوبرماركت جاهزة: مواد غذائية، ألبان، مشروبات، منظفات، خضار، فواكه، مجمدات.",
            "تصدير واستيراد البضاعة بملف إكسل ومشاركة الفواتير بالواتساب أو PDF."
        ],
    },
    "roastery": {
        "title": "المحامص والمطاحن والبهارات والمكسرات",
        "keywords": ["محمصة", "مطحنة", "بهارات", "مكسرات", "عطارة"],
        "target_areas": ["خانيونس - شارع جلال", "خانيونس - شارع السكة", "البلد", "مخيم خانيونس", "دير البلح"],
        "current_status": "حسابات يدوية على ورق أو آلة حاسبة، بدون ربط بين الميزان وقيمة البيع.",
        "daily_pains": [
            "البيع بالوزن والجرامات (أوقية، ربع كيلو، 100 غرام) وصعوبة الحساب السريع في ساعات الزحمة.",
            "خلط أسعار المكسرات والبهارات مع التغير المستمر في أسعار التوريد.",
            "عدم وجود إيصالات سريعة للزبائن."
        ],
        "shamel_pos_solution": [
            "دعم الباركود الوزني ورموز الـ PLU للميزان الإلكتروني.",
            "تسعير فوري بالوزن أو بالقطعة بالعملة المعتمدة (الشيكل ₪).",
            "أزرار لمس سريعة للأصناف الأكثر طلباً (قهوة، مكسرات، بهارات).",
            "تطبيق خفيف جداً على التابلت بجانب الميزان."
        ],
    },
    "wholesale": {
        "title": "تجار الجملة وموزعو المواد التموينية",
        "keywords": ["تجارة جملة", "موزع", "مخزن تمويني", "طرد وكرتونة"],
        "target_areas": ["خانيونس - المنطقة الصناعية", "خانيونس - طريق رفح الغربي", "دير البلح", "البلد"],
        "current_status": "فواتير يدوية كربونية، متابعة صعبة لحركة الكراتين والأرصدة في المخزن.",
        "daily_pains": [
            "توريد كميات ضخمة بالكرتونة وتوزيعها لمحلات التجزئة بأسعار متفاوتة.",
            "متابعة دقيقة لرصيد المخزن لمنع العجز والسرقة أو التلف.",
            "حاجة ملحة لحساب متوسط سعر التكلفة مع تغير سعر صرف الدولار والشيكل."
        ],
        "shamel_pos_solution": [
            "إدارة المخزون بنظام الكراتين والطرود مع تحديد سعة الكرتونة الدقيقة.",
            "كشف حساب فوري للأرباح وهوامش الربح الحقيقية عبر متوسط التكلفة WAC.",
            "تصدير تقارير الجرد والمخزن إلى ملف إكسل بضغطة زر لمشاركتها مع المحاسب أو الشركاء."
        ],
    },
    "restaurant_cafe": {
        "title": "المطاعم ومحلات الشاورما والسناك والكافيهات",
        "keywords": ["مطعم", "شاورما", "سناك", "كافيه", "فلافل", "عصائر"],
        "target_areas": ["شارع البحر - خانيونس", "شارع جلال", "جامعة الأقصى", "دير البلح - البحر"],
        "current_status": "طلبات شفهية أو أوراق طلبات ملصقة، مشاكل في تنظيم الطلبات وتعليق الفواتير في وقت الذروة.",
        "daily_pains": [
            "طوابير الزبائن والحاجة لخدمة زبون جديد ريثما يجهز طلب الزبون السابق.",
            "تلف المواد الأولية وصعوبة تتبع مبيعات الوجبات السريعة يومياً.",
            "الحاجة لقائمة طعام رقمية أو مشاركة الفاتورة مع الزبون عبر الواتساب."
        ],
        "shamel_pos_solution": [
            "ميزة تعليق الفواتير واسترجاعها (Hold / Park Cart) لتسريع خدمة الزبائن بدون انتظار.",
            "تعديل السعر المباشر داخل الفاتورة لتقديم خصومات فورية أو عروض الوجبات.",
            "مشاركة الفواتير كـ PDF عبر الواتساب مباشرة للزبون.",
            "ربط إضافي مع خدمة إنشاء مواقع ومنيو إلكتروني تفاعلي للمطعم عبر منصة أدهم (lead-preview-bot)."
        ],
    },
    "phones_electronics": {
        "title": "محلات الجوالات والإكسسوارات وصيانة الأجهزة",
        "keywords": ["محل جوالات", "صيانة هواتف", "إكسسوارات", "كمبيوتر", "أجهزة إلكترونية"],
        "target_areas": ["شارع جلال", "البلد", "شارع السكة", "مفترق بني سهيلا", "النصيرات"],
        "current_status": "تسجيل أجهزة الصيانة في دفتر ورقي، وإكسسوارات كثيرة بدون باركود أو تسعير واضح.",
        "daily_pains": [
            "مئات قطع الإكسسوارات الصغيرة (كوابل، شواحن، كفرات، لزقات شاشة) وصعوبة جردها.",
            "تتبع أجهزة الصيانة وحالتها ومستحقاتها المالية.",
            "بيع كروت وبطاقات الإنترنت وشحن الرصيد وتتبع أرباحها."
        ],
        "shamel_pos_solution": [
            "مسح باركود الإكسسوارات بالكاميرا أو إدخال سريع بالاسم ورقم الصنف.",
            "تطبيق سريع يشتغل بدون كهرباء ويوثق كل حركة بيع مع الأرباح الصافية.",
            "فرصة لأدهم كمهندس شبكات وصيانة لتقديم بكج متكامل (نظام كاشير + ضبط راوترات وميكروتك المحل)."
        ],
    },
    "frozen_meat": {
        "title": "محلات المجمدات واللحوم والدواجن والأسماك",
        "keywords": ["مجمدات", "لحوم", "دواجن", "أسماك", "قصاب"],
        "target_areas": ["سوق الأربعاء خانيونس", "البلد", "شارع جلال", "مخيم خانيونس", "دير البلح"],
        "current_status": "بيع بالوزن والقطعة، أسعار تتغير يومياً بحسب البضاعة القادمة، إدارة ورقية بدائية.",
        "daily_pains": [
            "تغير أسعار كيلو اللحوم والدواجن يومياً بحسب المورد وسعر السوق.",
            "الحاجة لمعرفة صافي ربح اليوم بدقة قبل أن يذوب رأس المال.",
            "تسجيل شكك وديون زبائن المنطقة."
        ],
        "shamel_pos_solution": [
            "تصنيف مجمدات ولحوم مخصص مع إمكانية تعديل سعر الكيلو مباشرة داخل الفاتورة.",
            "احتساب متوسط التكلفة لحماية رأس المال من تقلب الأسعار المفاجئ.",
            "تقارير مبيعات وأرباح فورية بضغطة زر نهاية كل يوم."
        ],
    }
}


async def scan_gaza_shops(args: dict) -> str:
    """Scan and list business sectors, potential target areas, and specific retail software gaps in Gaza."""
    sector_key = (args.get("sector") or "").strip().lower()
    area = (args.get("area") or "خانيونس").strip()
    online_search = str(args.get("online_search", "")).lower() in ("true", "1", "yes")

    output = []
    output.append(f"📍 **دليل الفرص التجارية وأنظمة الكاشير في غزة ({area})**\n")

    # Match sector
    matched_sectors = []
    if sector_key:
        for k, v in GAZA_SECTORS_CATALOG.items():
            if k == sector_key or any(sector_key in kw for kw in v["keywords"]) or sector_key in v["title"]:
                matched_sectors.append((k, v))
    if not matched_sectors:
        matched_sectors = list(GAZA_SECTORS_CATALOG.items())

    for k, v in matched_sectors:
        output.append(f"🏪 **{v['title']}**")
        output.append(f"• **المناطق المستهدفة**: {', '.join(v['target_areas'])}")
        output.append(f"• **الوضع الحالي**: {v['current_status']}")
        output.append(f"• **المشاكل والوجع اليومي (Pain Points)**:")
        for p in v["daily_pains"][:3]:
            output.append(f"  - {p}")
        output.append(f"• **حل تطبيق شامل POS (Adham's Solution)**:")
        for s in v["shamel_pos_solution"][:3]:
            output.append(f"  ✓ {s}")
        output.append("")

    if online_search:
        search_query = f"محلات {sector_key or 'سوبرماركت'} في {area} غزة فيسبوك دليل"
        try:
            web_res = await web_search({"query": search_query})
            if web_res:
                output.append("🔍 **عينة من الأنشطة والمحلات النشطة المستخرجة من البحث المحلي:**")
                output.append(web_res[:600] + "...\n")
        except Exception as e:
            log.warning("Web search in gaza scan failed: %s", e)

    output.append("💡 **الخطوة التالية**: استخدم أداة `pitch_shamel_pos` لتجهيز رسالة تسويقية وكلام ميداني لأي محل محدد.")
    return "\n".join(output)


async def pitch_shamel_pos(args: dict) -> str:
    """Draft a persuasive, high-converting Palestinian Arabic pitch for a specific Gaza shop owner."""
    business_name = (args.get("business_name") or "المحل").strip()
    sector = (args.get("sector") or "سوبرماركت").strip()
    area = (args.get("area") or "خانيونس").strip()
    owner_name = (args.get("owner_name") or "أبو فلان / صاحب المحل").strip()
    auto_save = str(args.get("auto_save_lead", "true")).lower() not in ("false", "0", "no")

    # Match sector profile
    profile = GAZA_SECTORS_CATALOG.get("supermarket")
    for k, v in GAZA_SECTORS_CATALOG.items():
        if k in sector.lower() or any(kw in sector for kw in v["keywords"]):
            profile = v
            break

    pitch_text = f"""🎯 **عرض شامل POS المخصص لـ: {business_name} ({area})**
النشاط: {sector}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🗣️ **1. سيناريو الحديث الميداني المباشر (وجهاً لوجه مع صاحب المحل):**
"يعطيك ألف عافية يا {owner_name}، كيف حال الشغل اليوم الله يرزقك ويفتحها بوجهك.
أنا أدهم الهباش، مهندس شبكات وتقنية هون من خانيونس. شفت شغلك ما شاء الله وحبيت أخدمك بشغلة بتريح راسك عالآخر.
عارف الوضع عندنا بغزة:
- الكهربا بتقطع وبتجيش.
- النت مش دايماً واصل.
- البضاعة والأسعار كل يوم بسعر جديد والكرتونة غير القطعة.
- والدفاتر والورق بيضيعوا وبيغلبوا بالجرد.

عملت تطبيق اسمه **شامل POS** خصيصاً للتجار عندنا:
1. بيشتغل على جوالك أو أي تابلت أندرويد شغال ببطارية أو باور بانك بدون ما تحتاج مولد ولا كهربا 24 ساعة.
2. أوفلاين 100% ما بيطلب ولا نت ولا سيرفر خارجي، بياناتك بجيبتك ومحلك بأمان.
3. بالعملة المعتمدة عندنا (الشيكل ₪).
4. بيحسبلك متوسط تكلفة الشراء (WAC) وسعة الكرتونة تلقائياً عشان لو شريت اليوم بسعر وبكرة بسعر تعرف ربحك وما تخسر قرش.
5. باركود بالكاميرا وتعديل سعر فوري وتعليق فواتير لو في زحمة.

أنا ما بدي تشتري مني هلّق، بدي أوريك إياه هان على جوالي بدقيقة واحدة، وإذا عجبك بنزلك إياه تجربة مجانية كاملة وتشوف كيف رح يريحك!"

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 **2. رسالة واتساب / مسنجر جاهزة للإرسال:**
"السلام عليكم ورحمة الله وبركاته يا غالي،
معاك أخوك المهندس أدهم الهباش من خانيونس.
لأننا بنعرف صعوبة متابعة الحسابات والأسعار مع انقطاع الكهرباء والنت المستمر في غزة، جهزنالك تطبيق **شامل POS** لإدارة الكاشير والمخازن:

⚡ **مميزات التطبيق لمحلك:**
✅ شغال أوفلاين 100% بدون إنترنت نهائياً.
✅ يشتغل على أي جوال أو تابلت أندرويد (ما بيحتاج كهربا، بطارية الجوال بتكفي طول اليوم).
✅ بالعملة المعتمدة (الشيكل ₪).
✅ شراء بالكرتونة وتجزئة للقطعة مع احتساب متوسط التكلفة آلياً لمواجهة تذبذب الأسعار.
✅ مسح الباركود بكاميرا الجوال وإصدار ومشاركة فواتير PDF عبر الواتساب.
✅ ميزة تعليق الفواتير في أوقات الزحمة.

🎁 **هدية التجربة:**
النسخة التجريبية جاهزة للتثبيت فوراً كملف APK. جاهز أمر عليك ونضبطه سوا وندخل البضاعة الأساسية ونجربه عملياً بالمحل.
تحياتي واحترامي،
م. أدهم الهباش — خانيونس"

━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 **3. الباقة السعرية المقترحة لغزة (نموذج ربحي مريح):**
• **الخيار الأول (تركيب + رخصة دائمة)**: 150 - 200 ₪ لمرة واحدة (تشمل تثبيت الـ APK، تدريب صاحب المحل أو الكاشير، وإدخال الأصناف الأساسية).
• **الخيار الثاني (باقة شاملة + دعم فني وشبكة)**: 250 - 350 ₪ (تشمل نظام الكاشير + فحص شبكة الراوتر والميكروتك وصيانة أجهزة المحل إن لزم).
• **الخيار الثالث (دعم دوري اختياري)**: 30 - 50 ₪ شهرياً لنسخ احتياطي للداتا وتحديث الأصناف وتغيير الأسعار عبر إكسل.
"""

    if auto_save:
        lead_id = memory.add_lead(
            business_name=business_name,
            sector=sector,
            location=area,
            contact_info=f"Owner: {owner_name}"
        )
        pitch_text += f"\n📌 **تم حفظ المحل كعميل محتمل في النظام برقم:** #{lead_id} (الحالة: new)"

    return pitch_text


async def gaza_field_sales_plan(args: dict) -> str:
    """Generate an actionable daily field-sales routine and objection-handling playbook for Gaza shops."""
    area = (args.get("area") or "خانيونس (شارع جلال والبلد)").strip()
    target_count = args.get("target_count", 5)

    plan = f"""📋 **خطة النزول الميداني والمبيعات لـ: {area}**
الهدف اليومي: زيارة {target_count} محلات تجارية وتقديم عروض تجريبية مجانية لتطبيق شامل POS.

🎒 **1. حقيبة النزول الميداني للمهندس أدهم:**
1. هاتف أندرويد شخصي أو تابلت مشحون 100% مثبت عليه `Shamel POS v1.2.0` ومضاف عليه أصناف تجريبية جاهزة (شيبس، عصير، كرتونة تونة، بهارات، رصيد).
2. كابل OTG أو فلاشة / رابط تيليجرام مباشر لتحميل وتثبيت ملف APK [Shamel_POS_v1.2.0.apk].
3. باور بانك مشحون ووصلات شحن سريعة.
4. دفتر ملاحظات صغير أو تسجيل فوري للعملاء عبر أوامر البوت (`add_lead`).

⏰ **2. التوقيت الذهبي للزيارة الميدانية:**
• **الفترة الأولى (10:30 صباحاً - 12:30 ظهراً)**: بعد انتهاء الزحمة الصباحية وتفريغ البضاعة، وقبل وقت صلاة الظهر.
• **الفترة الثانية (4:00 عصراً - 6:30 مساءً)**: فترة هدوء نسبي قبل الذروة المسائية، ويكون صاحب المحل الأساسي (مش العامل) متواجداً في المحل.
• ❌ **تجنب**: ساعات الصباح الباكر (تفريغ سيارات الموزعين)، وساعات الذروة بعد المغرب.

⏱️ **3. خطة الديمو في 60 ثانية (The 60-Second Live Demo):**
1. افتح التطبيق قدام التاجر على شاشة الكاشير.
2. اضغط على الكاميرا وامسح أي باركود موجود على علبة قدامه بالمحل (أو اضغط صنف من الشاشة).
3. اضغط على الصنف بالسلة، فرجيه كيف بضغطة واحدة بتغير السعر وتعمل خصم للزبون.
4. فرجيه زر "تعليق السلة" واحكيله: "لو زبون نسي مصاريه بالسيارة، بتعلق فاتورته وتخدم اللي وراه وبترجعله بثانية".
5. ادخل على شاشة المخزن واضغط "توريد بالكرتونة" وفرجيه كيف التطبيق بيحسب متوسط التكلفة تلقائياً لو السعر اختلف.
6. سكر الفاتورة واضغط مشاركة واتساب وابعثها لجواله!

🛡️ **4. معالجة أشهر اعتراضات التجار في غزة (Objection Handling):**
• **اعتراض 1: "الكهربا قاطعة وما عندي لابتوب أو UPS":**
  ↳ *الرد*: "هذا هو السر! التطبيق مصمم لأندرويد، بيشتغل على جوالك أو تابلت، وبطارية الجوال بتكفيك يومين بدون ما تحتاج سلك كهربا واحد."
• **اعتراض 2: "النت عندنا مقطوع وبفصل كثير":**
  ↳ *الرد*: "التطبيق أوفلاين 100%، ما بحتاج ولا ذرة نت. بياناتك ومبيعاتك كلها مخزنة بجهازك مش على سيرفر برا."
• **اعتراض 3: "الأسعار كل يوم بسعر وما بنلحق نعدل":**
  ↳ *الرد*: "التطبيق فيه نظام WAC (متوسط التكلفة المرجح)، يعني لما تشتري كرتونة بـ 50 وبكرة بـ 60 التطبيق لحاله بحسبلك السعر العادل وربحك الصافي بدون ما تتلخبط."
• **اعتراض 4: "أنا متعود على الدفتر والورقة وما بفهم بالكمبيوتر":**
  ↳ *الرد*: "لو بتعرف تستخدم واتساب رح تعرف تستخدم هاد البرنامج بنص ساعة. وأنا ابن منطقتك رح أقعد معاك وأدربك وأدخل بضاعتك خطوة بخطوة."
• **اعتراض 5: "معيش سيولة أدفع لبرامج":**
  ↳ *الرد*: "ولا تدفع ولا قرش اليوم، خود هي التطبيق مجاناً جربه 3 أيام بالمحل، وإذا ريحك وما خلاك تخسر بنحكي بالمصاريف وهي مبلغ بسيط برجعلك من أول يومين شغل."
"""
    return plan


TOOLS = [
    {
        "name": "scan_gaza_shops",
        "description": (
            "Scan and explore commercial sectors and shops in Gaza, Khan Younis, Deir Al-Balah, and central area. "
            "Identifies which retail sectors operate on paper/no software, their operational headaches (power, internet, price fluctuations, carton wholesale), "
            "and how Shamel POS (Android APK) solves their pain points. Can do live local web/directory search if online_search is True."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sector": {
                    "type": "string",
                    "description": "Sector: supermarket, roastery, wholesale, restaurant_cafe, phones_electronics, frozen_meat, or Arabic name like 'سوبرماركت', 'محامص', 'مطاعم'."
                },
                "area": {
                    "type": "string",
                    "description": "City or commercial street in Gaza: e.g., 'خانيونس', 'شارع جلال', 'دير البلح', 'النصيرات', 'شارع البحر'."
                },
                "online_search": {
                    "type": "string",
                    "enum": ["true", "false"],
                    "description": "Set 'true' to query live web and social directories for active businesses, or 'false' for catalog."
                }
            },
        },
        "handler": scan_gaza_shops,
    },
    {
        "name": "pitch_shamel_pos",
        "description": (
            "Generate a customized, high-converting Palestinian Arabic sales pitch and outreach message for a specific Gaza shop owner. "
            "Includes: face-to-face field conversation script, ready WhatsApp/Messenger message, 60-second live demo steps, and realistic Gaza pricing tiers. "
            "Automatically saves the business as a tracked lead in the system."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "business_name": {"type": "string", "description": "Name of the target shop or market in Gaza."},
                "sector": {"type": "string", "description": "Retail sector, e.g. 'سوبرماركت', 'محمصة', 'محلات جملة', 'مطعم', 'جوالات'."},
                "area": {"type": "string", "description": "Location or street in Gaza, e.g. 'خانيونس - شارع جلال'."},
                "owner_name": {"type": "string", "description": "Owner name if known, e.g. 'أبو العبد', 'أبو محمد'."},
                "auto_save_lead": {
                    "type": "string",
                    "enum": ["true", "false"],
                    "description": "Whether to auto-save to tracked leads in database (defaults to 'true')."
                }
            },
            "required": ["business_name", "sector"],
        },
        "handler": pitch_shamel_pos,
    },
    {
        "name": "gaza_field_sales_plan",
        "description": (
            "Generate a field sales game plan for visiting shops in Gaza/Khan Younis, including packing kit, golden visit hours, 60-second live demo flow, and counter-arguments for common objections (power cuts, no PC, price volatility, paper habit)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "area": {"type": "string", "description": "Street or locality, e.g. 'خانيونس - شارع جلال والبلد'."},
                "target_count": {"type": "integer", "description": "Number of shops to target in the visit (default 5)."}
            }
        },
        "handler": gaza_field_sales_plan,
    }
]
