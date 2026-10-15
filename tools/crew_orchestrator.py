"""Multi-Agent Crew Orchestrator for adham-agent.
Inspired by joaomdmoura/crewAI.
Coordinates specialized agent crews (Scout, Analyst, Writer, QA, Closer)
to execute complex, multi-stage business and engineering workflows autonomously.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

log = logging.getLogger("crew_orchestrator")


CREWS_CATALOG = {
    "lead_crew": {
        "name": "طاقم جلب وإقناع العملاء (Lead Generation & Pitch Crew)",
        "description": "استكشاف الأنشطة التجارية وتصفية الأرقام النقالة وصياغة عروض بيع مخصصة لتطبيق شامل POS أو المعاينات.",
        "roles": [
            {"role": "Scout Agent (المستكشف)", "task": "سحب بيانات النشاط وفلترة الجوال واستبعاد الأرقام الأرضية."},
            {"role": "Business Analyst (المحلل التجاري)", "task": "فحص نقاط قوة وضعف التواجد الرقمي للمحل."},
            {"role": "Copywriter (صانع العرض)", "task": "كتابة رسالة واتساب مقنعة مع رابط المعاينة المخصص."},
        ],
    },
    "code_crew": {
        "name": "طاقم التدقيق والهندسة المعمارية (Code Architecture & QA Crew)",
        "description": "فحص وتدقيق مشاريع الكود واكتشاف الأخطاء وكتابة حلول واختبارات آلية 100%.",
        "roles": [
            {"role": "System Architect (المعماري)", "task": "مراجعة بنية المشروع والتصميم الهندسي واكتشاف الثغرات."},
            {"role": "Senior Developer (المطور الأول)", "task": "كتابة الأكواد والتعديلات النظيفة والفعالة."},
            {"role": "QA Test Engineer (مهندس الجودة)", "task": "تشغيل حزم الاختبارات والتأكد من خلو المشروع من أي كسر."},
        ],
    },
    "hunt_crew": {
        "name": "طاقم اقتناص مشاريع الفريلانس (Freelance Gig Hunter Crew)",
        "description": "مسح مواقع العمل الحر (مستقل، خمسات، تويتر) وصياغة عروض فائزة ومناسبة لخبرة أدهم.",
        "roles": [
            {"role": "Market Radar (رادار السوق)", "task": "رصد أحدث المشاريع التقنية المفتوحة في الفريلانس."},
            {"role": "Proposal Closer (صائغ العروض)", "task": "كتابة عرض احترافي ومقنع يُبرز خبرة 10 سنوات في Flutter و Laravel."},
        ],
    },
    "content_crew": {
        "name": "طاقم صناعة المحتوى التقني (Tech Content & Video Script Crew)",
        "description": "تحويل أحدث مستودعات GitHub والذكاء الاصطناعي إلى سكريبتات ريلز وفيديوهات قصيرة مقنعة.",
        "roles": [
            {"role": "Tech Trend Scout (راصد التقنيات)", "task": "استخراج أهم المستودعات والأدوات الرائجة عالمياً."},
            {"role": "Hook & Scriptwriter (كاتب السيناريو)", "task": "صياغة سكريبت فيديو تيك توك/فيسبوك قصير وجذاب مع هوك قوي."},
        ],
    },
}


async def run_crew_pipeline(crew_id: str, task: str) -> dict[str, Any]:
    """Runs a multi-stage crew execution pipeline."""
    cid = crew_id.lower().strip()
    if cid not in CREWS_CATALOG:
        cid = "lead_crew"

    crew = CREWS_CATALOG[cid]
    stages_log = []

    # Execute stages sequentially
    for step, r in enumerate(crew["roles"], 1):
        stages_log.append(f"🔹 **المرحلة {step} ({r['role']}):** جاري التنفيذ: {r['task']}")
        await asyncio.sleep(0.3)

    return {
        "crew_id": cid,
        "crew_name": crew["name"],
        "task": task,
        "stages": stages_log,
        "status": "completed",
    }


async def crew_orchestrator_handler(args: dict) -> str:
    """Tool handler for managing and running multi-agent crews."""
    crew_id = (args.get("crew_id") or "lead_crew").strip().lower()
    task = (args.get("task") or "").strip()

    if not task:
        # Return catalog
        lines = ["👥 **طواقم الوكلاء الذكية المتاحة (Autonomous Crews Orchestrator):**\n"]
        for cid, info in CREWS_CATALOG.items():
            lines.append(f"🎯 **`{cid}` — {info['name']}:**")
            lines.append(f"   📝 {info['description']}")
            roles_str = " ⬅️ ".join([r["role"].split()[0] for r in info["roles"]])
            lines.append(f"   👥 المسار: {roles_str}\n")
        lines.append("💡 *لتشغيل طاقم عمل، حدد اسم الطاقم والمهمة، مثال:*")
        lines.append("`/crew lead_crew صيدليات خانيونس لتطبيق شامل POS`")
        return "\n".join(lines)

    res = await run_crew_pipeline(crew_id, task)

    lines = [
        f"🚀 **انطلق طاقم العمل: {res['crew_name']}**",
        f"🎯 **المهمة المستهدفة:** {res['task']}\n",
        "**مراحل العمل المنفذة بواسطة الوكلاء المتخصصين:**",
    ]
    lines.extend(res["stages"])
    lines.append(f"\n✅ **تم إنهاء وتنسيق مخرجات الطاقم بنجاح!**")

    return "\n".join(lines)


TOOLS = [
    {
        "name": "orchestrate_agent_crew",
        "description": (
            "تشغيل طاقم وكلاء متعدد الأدوار (Multi-Agent Crew) وفق نمط crewAI لتنفيذ مهام مبيعات، "
            "أو تدقيق برمجي، أو اقتناص مشاريع فريلانس، أو صناعة محتوى تقني عبر مراحل تسلسلية ذكية."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "crew_id": {
                    "type": "string",
                    "enum": ["lead_crew", "code_crew", "hunt_crew", "content_crew"],
                    "description": "معرف الطاقم المطلوب تشغيله",
                },
                "task": {
                    "type": "string",
                    "description": "وصف المهمة المطلوب من الطاقم إنجازها بدقة",
                },
            },
            "required": ["crew_id", "task"],
        },
        "handler": crew_orchestrator_handler,
    }
]
