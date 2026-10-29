"""Skills Engine for adham-agent.
Indexes, searches, and reads all 480 skills installed in .agents/skills/
allowing the bot to autonomously execute any programming, architecture,
security, reverse engineering, machine learning, or DevOps task.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

log = logging.getLogger("skills_engine")

# Skills are untrusted text. Only the project-local "skills" folder is indexed by default.
# Copy the skills you reviewed into adham-agent/skills/<skill-name>/SKILL.md.
# An extra directory can be added explicitly with SKILLS_EXTRA_DIR in .env (off by default).
import os
PROJECT_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = PROJECT_DIR / "skills"
_extra = os.getenv("SKILLS_EXTRA_DIR", "").strip()
GLOBAL_SKILLS_DIR = Path(_extra) if _extra else SKILLS_DIR

_SKILLS_CACHE: list[dict[str, Any]] = []


def _load_skills_index() -> list[dict[str, Any]]:
    global _SKILLS_CACHE
    if _SKILLS_CACHE:
        return _SKILLS_CACHE

    skills: list[dict[str, Any]] = []
    seen: set[str] = set()

    search_dirs = [SKILLS_DIR, GLOBAL_SKILLS_DIR]

    for base_dir in search_dirs:
        if not base_dir.exists():
            continue
        for child in base_dir.iterdir():
            if not child.is_dir():
                continue
            skill_name = child.name
            if skill_name in seen:
                continue

            skill_md = child / "SKILL.md"
            if not skill_md.exists():
                continue

            try:
                content = skill_md.read_text(encoding="utf-8", errors="replace")
                # Parse frontmatter
                desc = ""
                name = skill_name
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        fm = parts[1]
                        for line in fm.splitlines():
                            line_s = line.strip()
                            if line_s.startswith("name:"):
                                name = line_s.replace("name:", "").strip().strip('"\'')
                            elif line_s.startswith("description:"):
                                desc = line_s.replace("description:", "").strip().strip('"\'')

                if not desc:
                    # Grab first non-empty lines after frontmatter
                    for line in content.splitlines()[:15]:
                        if line.startswith("#") or not line.strip() or line.startswith("---"):
                            continue
                        desc = line.strip()
                        break

                skills.append({
                    "id": skill_name,
                    "name": name,
                    "description": desc or "No description",
                    "path": str(child),
                    "md_path": str(skill_md),
                })
                seen.add(skill_name)
            except Exception as e:
                log.warning("Could not parse skill %s: %s", skill_name, e)

    _SKILLS_CACHE = skills
    log.info("Indexed %d workspace skills", len(_SKILLS_CACHE))
    return _SKILLS_CACHE


def search_skills(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Searches indexed skills by keywords in name or description."""
    all_skills = _load_skills_index()
    if not query:
        return all_skills[:limit]

    q_lower = query.lower().strip()
    words = [w for w in re.split(r"\s+", q_lower) if w]

    scored = []
    for s in all_skills:
        score = 0
        s_id = s["id"].lower()
        s_desc = s["description"].lower()

        for w in words:
            if w == s_id:
                score += 15
            elif w in s_id:
                score += 8
            if w in s_desc:
                score += 4

        if score > 0:
            scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:limit]]


def read_skill(skill_id: str, max_chars: int = 8000) -> dict[str, Any]:
    """Reads the SKILL.md content for a given skill."""
    all_skills = _load_skills_index()
    matched = None
    skill_id_clean = skill_id.lower().strip()

    for s in all_skills:
        if s["id"].lower() == skill_id_clean or s["name"].lower() == skill_id_clean:
            matched = s
            break

    if not matched:
        # Try fuzzy containment
        for s in all_skills:
            if skill_id_clean in s["id"].lower():
                matched = s
                break

    if not matched:
        return {"error": f"المهارة '{skill_id}' غير موجودة. جرب البحث أولاً عبر search_skills."}

    md_path = Path(matched["md_path"])
    try:
        content = md_path.read_text(encoding="utf-8", errors="replace")
        truncated = False
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n... (تم اقتطاع الباقي لطول المحتوى)"
            truncated = True

        return {
            "id": matched["id"],
            "name": matched["name"],
            "description": matched["description"],
            "content": content,
            "truncated": truncated,
            "path": str(md_path),
        }
    except Exception as e:
        return {"error": f"فشل في قراءة ملف المهارة: {e}"}


# Tool Definitions for brain.py

async def _tool_search_skills(args: dict) -> str:
    query = str(args.get("query", ""))
    limit = int(args.get("limit", 8))
    results = search_skills(query, limit=limit)
    if not results:
        return f"لم أجد أي مهارات تطابق '{query}'. المهارات المتاحة هي ما نُسخ إلى مجلد skills داخل المشروع."

    out = [f"🔍 وجدنا {len(results)} مهارة مطابقة لـ '{query}':"]
    for s in results:
        out.append(f"• `{s['id']}`: {s['description']}")
    out.append("\n💡 يمكنك قراءة بروتوكول أي مهارة بالكامل باستخدام أداة `read_skill_guide`.")
    return "\n".join(out)


async def _tool_read_skill_guide(args: dict) -> str:
    skill_id = str(args.get("skill_id", ""))
    if not skill_id:
        return "يرجى تحديد معرف المهارة (skill_id)."

    res = read_skill(skill_id)
    if "error" in res:
        return res["error"]

    return (
        f"📘 **بروتوكول ودليل المهارة: {res['name']}** (`{res['id']}`)\n"
        f"📝 الوصف: {res['description']}\n\n"
        f"```markdown\n{res['content']}\n```"
    )


TOOLS = [
    {
        "name": "search_skills",
        "description": (
            "ابحث في ترسانة المهارات المدمجة (480 مهارة متخصصة في البرمجة، هندسة النظم، "
            "الذكاء الاصطناعي، فلاتر، لارافيل، بايثون، اختبار البرمجيات، الديف أوبس، الهندسة العكسية، وغيرها)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "كلمة البحث أو موضوع المهارة مثل flutter, laravel, docker, tdd, reverse-engineering, security",
                },
                "limit": {
                    "type": "integer",
                    "description": "عدد النتائج المطلوب عرضها (افتراضياً 8)",
                },
            },
            "required": ["query"],
        },
        "handler": _tool_search_skills,
    },
    {
        "name": "read_skill_guide",
        "description": "اقرأ البروتوكول الكامل والقواعد التنفيذية لأي مهارة محددة من الـ 480 مهارة في بيئة العمل.",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_id": {
                    "type": "string",
                    "description": "معرف المهارة مثل flutter, laravel, systematic-debugging, test-driven-development, reverse-engineer-anything",
                },
            },
            "required": ["skill_id"],
        },
        "handler": _tool_read_skill_guide,
    },
]
