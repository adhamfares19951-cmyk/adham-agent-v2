"""Accumulated technical-experience memory: log a problem + how Adham solved
it, so similar future problems can be recalled instead of re-searched.
"""
import memory


async def log_experience(args: dict) -> str:
    problem = (args.get("problem") or "").strip()
    solution = (args.get("solution") or "").strip()
    if not problem or not solution:
        return "خطأ: لازم وصف المشكلة والحل الاثنين."
    exp_id = memory.add_experience(problem, solution)
    return f"تم حفظ الخبرة (رقم {exp_id})."


TOOLS = [
    {
        "name": "log_experience",
        "description": (
            "Save a technical problem Adham fixed and how he fixed it, to his personal experience "
            "log. Use when he describes a fault he resolved (network, hardware, printer, CCTV, etc.), "
            "especially after a photo of the issue. Similar future problems will surface this automatically."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "problem": {"type": "string", "description": "The problem/symptom, one or two sentences."},
                "solution": {"type": "string", "description": "How Adham fixed it, one or two sentences."},
            },
            "required": ["problem", "solution"],
        },
        "handler": log_experience,
    },
]
