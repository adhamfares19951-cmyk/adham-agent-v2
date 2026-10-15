"""Agency Experts tool: Connects Adham Agent to 270+ specialized agency personas.
Allows autonomous or manual consultation of senior specialists across Engineering,
Sales, Marketing, Security, Finance, Product, Design, and Strategy.
"""
import json
import logging
import re
from pathlib import Path
from typing import Optional

import config

log = logging.getLogger("tools.agency")

AGENCY_DIR = config.BASE_DIR / "agency_agents"
INDEX_PATH = AGENCY_DIR / "agents_index.json"

_INDEX = []


def _load_index():
    global _INDEX
    if not _INDEX and INDEX_PATH.exists():
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                _INDEX = json.load(f)
        except Exception as e:
            log.error("Failed to load agency agents index: %s", e)
    return _INDEX


def find_expert(query: str) -> Optional[dict]:
    """Find the best matching expert by ID, filename, name, or keywords."""
    index = _load_index()
    if not index:
        return None

    q = query.lower().strip()

    # Exact ID match (e.g., 'sales/sales-outbound-strategist')
    for a in index:
        if a["id"].lower() == q or a["filename"].lower().replace(".md", "") == q:
            return a

    # Direct name match
    for a in index:
        if a["name"].lower() == q:
            return a

    # Arabic and domain intent keyword mapping
    ar_mapping = {
        "كولد ايميل": "sales/sales-outbound-strategist",
        "كولد": "sales/sales-outbound-strategist",
        "outreach": "sales/sales-outbound-strategist",
        "مبيعات": "sales/sales-deal-strategist",
        "صفقات": "sales/sales-deal-strategist",
        "عرض بيع": "sales/sales-offer-lead-gen-strategist",
        "pitch": "sales/sales-offer-lead-gen-strategist",
        "proposal": "sales/sales-proposal-strategist",
        "بروبوزال": "sales/sales-proposal-strategist",
        "سيرة ذاتية": "specialized/resume-tailor",
        "cv": "specialized/resume-tailor",
        "resume": "specialized/resume-tailor",
        "وظائف": "engineering/engineering-ats-validator-architect",
        "مقابلة": "specialized/resume-tailor",
        "أمن": "security/security-appsec-engineer",
        "سيكيورتي": "security/security-appsec-engineer",
        "اختراق": "security/security-appsec-engineer",
        "ثغرة": "security/security-appsec-engineer",
        "تسويق": "marketing/marketing-content-strategist",
        "seo": "marketing/marketing-seo-strategist",
        "سيو": "marketing/marketing-seo-strategist",
        "محتوى": "marketing/marketing-content-strategist",
        "إعلان": "paid-media/paid-media-paid-search-strategist",
        "تسعير": "specialized/specialized-pricing-analyst",
        "مالية": "finance/finance-financial-analyst",
        "دراسة جدوى": "finance/finance-financial-analyst",
        "تصميم": "design/design-ui-designer",
        "واجهات": "design/design-ui-designer",
        "ui/ux": "design/design-ui-designer",
        "شبكات": "engineering/engineering-devops-automator",
        "سيرفر": "engineering/engineering-devops-automator",
        "ديف اوبس": "engineering/engineering-devops-automator",
        "كود": "engineering/engineering-code-reviewer",
        "برمجة": "engineering/engineering-api-platform-engineer",
        "باك اند": "engineering/engineering-api-platform-engineer",
        "فرونت اند": "engineering/engineering-frontend-specialist",
        "مشاريع": "project-management/project-management-project-shepherd",
        "agile": "project-management/project-management-jira-workflow-steward",
    }

    for k, target_id in ar_mapping.items():
        if k in q:
            for a in index:
                if a["id"].lower() == target_id.lower():
                    return a

    # Word/token overlap in id, name, or description
    words = [w for w in re.split(r"\W+", q) if len(w) > 2]
    matches = []
    for a in index:
        score = 0
        text_corpus = f"{a['id']} {a['name']} {a['division']} {a['description']}".lower()
        for w in words:
            if w in a["id"].lower():
                score += 8
            elif w in a["name"].lower():
                score += 6
            elif w in a["division"].lower():
                score += 4
            elif w in text_corpus:
                score += 1
        if score > 0:
            matches.append((score, a))

    if matches:
        matches.sort(key=lambda x: x[0], reverse=True)
        return matches[0][1]

    return None


async def consult_agency_expert(args: dict) -> str:
    """Consult a specialized Agency Expert for deep, senior-level guidance."""
    expert_query = args.get("expert_query_or_id", "").strip()
    task_desc = args.get("task_description", "").strip()

    if not expert_query:
        return "يرجى تحديد اسم أو تخصص الخبير المطلوب (مثال: sales, security, devops, marketing)."

    expert = find_expert(expert_query)
    if not expert:
        return (
            f"لم أجد خبيراً مطابقاً بالظبط لـ '{expert_query}'. "
            "يمكنك استعراض الأقسام عبر أداة list_agency_experts (مثل: sales, marketing, engineering, security, finance)."
        )

    file_path = AGENCY_DIR / expert["rel_path"]
    if not file_path.exists():
        return f"ملف الخبير {expert['name']} غير موجود على القرص."

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"خطأ في قراءة ملف الخبير: {e}"

    # Strip YAML frontmatter for cleaner prompt
    clean_prompt = re.sub(r"^---\s*\n.*?\n---\s*", "", content, flags=re.DOTALL)
    # Truncate if exceptionally long (keep top 6000 chars of core instructions)
    if len(clean_prompt) > 7000:
        clean_prompt = clean_prompt[:7000] + "\n...[تم استيعاب بقية منهجية الخبير]"

    return (
        f"🎯 **تم استحضار الخبير المتخصص**: {expert['emoji']} **{expert['name']}** ({expert['division'].upper()})\n"
        f"📌 **الوصف**: {expert['description']}\n\n"
        f"--- **تعليمات ومنهجية الخبير** ---\n"
        f"{clean_prompt}\n\n"
        f"--- **المهمة المطلوب حلها لأدهم** ---\n"
        f"{task_desc or 'تطبيق المنهجية بدقة وخبرة عملية لتقديم الحل الأمثل لأدهم.'}"
    )


async def list_agency_experts(args: dict) -> str:
    """List available Agency divisions or experts in a specific category."""
    division = args.get("division", "").strip().lower()
    keyword = args.get("keyword", "").strip().lower()

    index = _load_index()
    if not index:
        return "فهرس الخبراء غير متاح حالياً."

    divisions_labels = {
        "engineering": ("الهندسة والبرمجة والشبكات", "💻"),
        "security": ("الأمن السيبراني وحماية الأنظمة", "🛡️"),
        "sales": ("المبيعات واقتناص الصفقات والـ Outreach", "💼"),
        "marketing": ("التسويق الرقمي والمحتوى والـ SEO", "📢"),
        "finance": ("المالية والتسعير ودراسات الجدوى", "💰"),
        "design": ("تصميم الواجهات وتجربة المستخدم UI/UX", "🎨"),
        "product": ("إدارة وتخطيط المنتجات الرقمية", "📦"),
        "project-management": ("إدارة المشاريع والتنظيم الرشيق Agile", "📋"),
        "support": ("خدمة العملاء والدعم الفني", "🛟"),
        "testing": ("فحص الجودة والاختبارات الآلية QA", "🧪"),
        "strategy": ("التخطيط الاستراتيجي والنمو", "♟️"),
        "specialized": ("المهام التخصصية والاستشارات", "✨"),
        "academic": ("التطوير المهني والمسار الوظيفي", "🎓"),
        "paid-media": ("الإعلانات الممولة والحملات الرقمية", "🎯"),
    }

    if not division and not keyword:
        # Show overview of all divisions
        counts = {}
        for a in index:
            d = a["division"]
            counts[d] = counts.get(d, 0) + 1

        lines = ["🏢 **وكالة الخبراء المتكاملة لدراع اليمين (270 خبير متخصص)**:\n"]
        for d, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            info = divisions_labels.get(d, (d.title(), "🔹"))
            lines.append(f"{info[1]} **{info[0]}** (`{d}`): {count} خبير")

        lines.append(
            "\n💡 *يمكنك استدعاء أي خبير في أي وقت بكتابة:* `استدعِ خبير [التخصص]` "
            "أو سيقوم دراع اليمين باستحضار الخبير الأنسب لمشكلتك تلقائياً!"
        )
        return "\n".join(lines)

    # Filter by division or keyword
    results = []
    for a in index:
        if division and a["division"].lower() != division:
            continue
        if keyword:
            q = keyword.lower()
            if q not in a["name"].lower() and q not in a["description"].lower() and q not in a["id"].lower():
                continue
        results.append(a)

    if not results:
        return f"لم يتم العثور على خبراء يطابقون: division='{division}', keyword='{keyword}'."

    div_title = divisions_labels.get(division, (division, "🔹"))[0] if division else "البحث"
    lines = [f"📋 **قائمة الخبراء المتاحين في {div_title}** ({len(results)} خبير):\n"]
    for r in results[:25]:  # limit to top 25 to prevent message overflows
        lines.append(f"{r['emoji']} **{r['name']}** (`{r['id']}`)\n   _{r['description']}_\n")

    if len(results) > 25:
        lines.append(f"... وغيرهم {len(results) - 25} خبير آخر في هذا القسم.")

    return "\n".join(lines)


TOOLS = [
    {
        "name": "consult_agency_expert",
        "description": (
            "استدعاء واستشارة خبير متخصص من وكالة الخبراء (The Agency - 270 خبير متخصص) في كافة المجالات: "
            "مبيعات (Sales/Outbound/Cold Pitch/Deals), تسويق (Marketing/Copywriting/SEO), هندسة برمجية (DevOps/Backend/Frontend/Architecture), "
            "أمن سيبراني (Security/AppSec/PenTesting), مالية وتوافق (Finance/Pricing), تصميم (UI/UX), وإدارة مشاريع. "
            "تمنحك الأداة منهجية وخبرة الخبير الأول في هذا المجال بدقة متناهية."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expert_query_or_id": {
                    "type": "string",
                    "description": "اسم الخبير أو تخصص المجال (مثل: sales, outbound, security, devops, pricing, copywriter, seo, marketing)",
                },
                "task_description": {
                    "type": "string",
                    "description": "المهمة أو السؤال المحدد الذي يحتاج أدهم لحله بالاعتماد على منهجية هذا الخبير.",
                },
            },
            "required": ["expert_query_or_id", "task_description"],
        },
        "handler": consult_agency_expert,
    },
    {
        "name": "list_agency_experts",
        "description": "استعراض أقسام وتخصصات الخبراء المتوفرين في الوكالة (270 خبير) للبحث عن خبير في مجال معين.",
        "parameters": {
            "type": "object",
            "properties": {
                "division": {
                    "type": "string",
                    "description": "القسم المطلوب استعراضه (sales, marketing, engineering, security, finance, design, product, project-management)",
                },
                "keyword": {
                    "type": "string",
                    "description": "كلمة مفتاحية للبحث عن خبير معين (مثل: cold email, kubernetes, pitch, pricing)",
                },
            },
        },
        "handler": list_agency_experts,
    },
]
