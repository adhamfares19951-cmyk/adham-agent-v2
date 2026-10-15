"""Long-term memory: facts Adham wants the bot to keep (shown to the AI in every conversation)."""
import memory


async def remember_fact(args: dict) -> str:
    fact = (args.get("fact") or "").strip()
    if not fact:
        return "خطأ: المعلومة فاضية."
    fact_id = memory.add_fact(fact)
    return f"تم الحفظ (رقم {fact_id}): {fact}"


async def forget_fact(args: dict) -> str:
    try:
        fact_id = int(args.get("fact_id"))
    except (TypeError, ValueError):
        return "خطأ: لازم رقم المعلومة."
    if memory.delete_fact(fact_id):
        return f"تم حذف المعلومة رقم {fact_id}."
    return f"ما في معلومة محفوظة برقم {fact_id}."


TOOLS = [
    {
        "name": "remember_fact",
        "description": (
            "Save a lasting fact about Adham or his preferences to long-term memory "
            "(e.g. 'his cousin Ahmad's number is in his phone as أبو محمد', 'prefers remote jobs'). "
            "Use when he asks you to remember something, or shares stable personal info worth keeping. "
            "Never save passwords, keys or card numbers."
        ),
        "parameters": {
            "type": "object",
            "properties": {"fact": {"type": "string", "description": "The fact, one clear sentence in Arabic."}},
            "required": ["fact"],
        },
        "handler": remember_fact,
    },
    {
        "name": "forget_fact",
        "description": "Delete a saved fact by its number (numbers are listed in the system prompt).",
        "parameters": {
            "type": "object",
            "properties": {"fact_id": {"type": "integer"}},
            "required": ["fact_id"],
        },
        "handler": forget_fact,
    },
]
