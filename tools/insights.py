"""Proactive career insights: looks for patterns across the job/freelance
opportunities already found for Adham (recurring missing skills, strong
matches) instead of throwing each one away after it's sent once.
"""
import memory

PROMPT = """These are job/freelance opportunity cards already sent to Adham over the last
period (title, score, why it fit, what he's missing — parsed from the saved card text):

{cards}

Look for real patterns across them (not each one individually):
1. Skills or certifications that keep showing up as "missing" — these are the highest-value
   gaps to close.
2. What kind of roles/keywords he's scoring highest on — where his real strength is.
3. 2-3 concrete, specific next steps (a course, a keyword to add to his CV, a type of role to
   target more).

Answer in Palestinian Arabic, short and direct, no fluff. If there isn't enough data yet
(fewer than 5 cards), say so plainly instead of inventing patterns."""


async def career_insights(args: dict) -> str:
    from brain import llm

    rows = memory.recent_matches(limit=30)
    if len(rows) < 3:
        return "لسا ما في فرص كافية اتبعتلك (أقل من 3) لأطلع أنماط حقيقية منها. جرب كمان كم يوم."

    cards = "\n\n---\n\n".join(r["card"] for r in rows)
    reply = await llm.generate("You are a career-pattern analyst. Be concrete and honest.",
                                [{"role": "user", "content": PROMPT.format(cards=cards)}])
    memory.add_usage("llm_call")
    return reply.text.strip()


TOOLS = [
    {
        "name": "career_insights",
        "description": (
            "Analyze patterns across all job/freelance opportunities already found for Adham: "
            "recurring missing skills, where he scores highest, and concrete next steps. "
            "Use this instead of guessing when he asks about his skill gaps or job-search trends."
        ),
        "parameters": {"type": "object", "properties": {}},
        "handler": career_insights,
    },
]
