"""Quick health check of every AI provider configured in .env.
Run: venv\\Scripts\\python.exe check_providers.py
Sends one tiny message to each provider and prints whether it answered.
Never prints keys.
"""
import asyncio
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

from llm import LLMError, get_llm  # noqa: E402


async def main() -> None:
    llm = get_llm()
    print(f"\nعدد المزودين المفعّلين: {len(llm.providers)}\n")
    ok = 0
    for name, provider in llm.providers:
        started = time.monotonic()
        try:
            reply = await asyncio.wait_for(
                provider.generate("Reply with one short word.", [{"role": "user", "content": "Say: OK"}]),
                timeout=60,
            )
            seconds = time.monotonic() - started
            print(f"✅ {name:12} شغّال ({seconds:.1f} ث) — رد: {reply.text.strip()[:30]!r}")
            ok += 1
        except LLMError as e:
            print(f"❌ {name:12} {e.user_message}")
        except asyncio.TimeoutError:
            print(f"❌ {name:12} تأخر أكثر من 60 ثانية")
        except Exception as e:  # noqa: BLE001
            print(f"❌ {name:12} خطأ غير متوقع: {type(e).__name__}")
    print(f"\nالنتيجة: {ok} من {len(llm.providers)} شغّالين.")


asyncio.run(main())
