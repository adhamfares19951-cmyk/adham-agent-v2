"""Provider layer: brain.py talks only to this file.
Switching providers = change AI_PROVIDER (and MODEL) in .env.

Messages use one neutral format for every provider:
  {"role": "user", "content": str}
  {"role": "assistant", "content": str, "tool_calls": [tool-call dict, ...], "_gemini": <raw>}
  {"role": "tool", "tool_call_id": str, "name": str, "content": str}
A tool call dict is {"id": str, "name": str, "args": dict, "gid": <Gemini's own id or None>}.
Tools are given as [{"name", "description", "parameters": <JSON schema>}].
"""
import asyncio
import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field

import config

log = logging.getLogger("llm")


class LLMError(Exception):
    """Error with a ready Arabic message for the user."""

    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message


class RateLimitError(LLMError):
    pass


class PayloadTooLargeError(LLMError):
    """413 Request Too Large - skip provider for this request only without cooldown."""
    pass


class BillingError(LLMError):
    """402 Insufficient balance - disable provider until restart."""
    pass


class AuthenticationError(LLMError):
    """401/403/404 Invalid key or model - disable provider until restart."""
    pass


class ServerError(LLMError):
    """5xx Server temporary error."""
    pass


RATE_LIMIT_MSG = "وصلنا لحد الاستخدام المجاني عند مزود الذكاء الاصطناعي ⏳ جرّب كمان شوي يا أدهم."
NETWORK_MSG = "ما قدرت أتصل بمزود الذكاء الاصطناعي 🌐 تأكد من الإنترنت وجرّب كمان مرة."
EMPTY_MSG = "ما وصلني رد من الذكاء الاصطناعي، جرّب تعيد صياغة رسالتك."


@dataclass
class Reply:
    text: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    raw_gemini: object = None  # Gemini's own content, re-sent as-is (keeps thought signatures)
    provider: str = ""


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _short_id(value: str, prefix: str = "") -> str:
    """Stable id that every provider accepts (Mistral wants exactly 9 alphanumerics)."""
    return prefix + hashlib.sha1(value.encode()).hexdigest()[:9]


# ---------------------------------------------------------------- Gemini

class GeminiProvider:
    def __init__(self, api_key: str):
        from google import genai
        from google.genai import errors, types

        self._types = types
        self._errors = errors
        self.client = genai.Client(api_key=api_key)
        self.model = config.MODEL

    def _contents(self, messages: list[dict]) -> list:
        types = self._types
        contents = []
        native_ids = {}  # our tool_call id -> Gemini's id, for calls Gemini itself made
        fr_content = None  # current Content collecting function responses
        for m in messages:
            role = m["role"]
            if role == "tool":
                if m["tool_call_id"] in native_ids:
                    part = types.Part(function_response=types.FunctionResponse(
                        id=native_ids[m["tool_call_id"]], name=m["name"],
                        response={"result": m["content"]},
                    ))
                    if fr_content is None:
                        fr_content = types.Content(role="user", parts=[])
                        contents.append(fr_content)
                    fr_content.parts.append(part)
                else:
                    contents.append(types.Content(role="user", parts=[
                        types.Part(text=f"[نتيجة الأداة {m['name']}]:\n{m['content']}")]))
                continue
            fr_content = None
            if role == "assistant":
                if m.get("_gemini") is not None:
                    contents.append(m["_gemini"])
                    for tc in m.get("tool_calls", []):
                        native_ids[tc["id"]] = tc.get("gid")
                    continue
                text = m.get("content") or ""
                for tc in m.get("tool_calls", []):
                    text += f"\n[استدعيت الأداة {tc['name']} بالمعطيات {json.dumps(tc['args'], ensure_ascii=False)}]"
                if text.strip():
                    contents.append(types.Content(role="model", parts=[types.Part(text=text.strip())]))
            else:
                contents.append(types.Content(role="user", parts=[types.Part(text=m["content"])]))
        return contents

    async def generate(self, system: str, messages: list[dict], tools: list[dict] | None = None) -> Reply:
        types = self._types
        cfg = types.GenerateContentConfig(
            system_instruction=system,
            tools=[types.Tool(function_declarations=[
                types.FunctionDeclaration(name=t["name"], description=t["description"],
                                          parameters_json_schema=t["parameters"])
                for t in tools
            ])] if tools else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        try:
            resp = await self._call_with_retry(self._contents(messages), cfg)
        except self._errors.APIError as e:
            code = getattr(e, "code", None)
            log.error("Gemini API error %s: %s", code, e)
            if code == 429:
                raise RateLimitError(RATE_LIMIT_MSG)
            if code in (400, 401, 403) and "key" in str(e).lower():
                raise LLMError("مفتاح Gemini مش شغّال 🔑 تأكد من GEMINI_API_KEY بملف .env")
            if code == 404:
                raise LLMError("اسم الموديل غلط أو مش متاح ❌ تأكد من قيمة MODEL بملف .env")
            if code and code >= 500:
                raise LLMError("خوادم Gemini مضغوطة هلّق، جرّب بعد شوي.")
            raise LLMError(f"صار خطأ من Gemini (رمز {code}). جرّب كمان مرة.")
        except Exception as e:
            log.exception("Gemini connection problem: %s", e)
            raise LLMError(NETWORK_MSG)

        try:
            content = resp.candidates[0].content
            parts = content.parts or []
        except (AttributeError, IndexError, TypeError):
            raise LLMError(EMPTY_MSG)

        reply = Reply(raw_gemini=content)
        for p in parts:
            if p.function_call:
                reply.tool_calls.append({
                    "id": _new_id(), "gid": p.function_call.id,
                    "name": p.function_call.name, "args": dict(p.function_call.args or {}),
                })
            elif p.text and not p.thought:
                reply.text += p.text
        if not reply.text and not reply.tool_calls:
            raise LLMError(EMPTY_MSG)
        return reply

    async def _call_with_retry(self, contents: list, cfg):
        """Retry temporary server overloads (5xx) a few times before giving up."""
        delays = [2, 5]  # seconds to wait before 2nd and 3rd attempts
        for attempt in range(len(delays) + 1):
            try:
                return await self.client.aio.models.generate_content(
                    model=self.model, contents=contents, config=cfg
                )
            except self._errors.APIError as e:
                code = getattr(e, "code", None)
                if code and code >= 500 and attempt < len(delays):
                    log.warning("Gemini %s, retrying in %ss", code, delays[attempt])
                    await asyncio.sleep(delays[attempt])
                    continue
                raise


# ---------------------------------------------------------------- Anthropic

class AnthropicProvider:
    """Used later when AI_PROVIDER=anthropic (needs: pip install anthropic)."""

    def __init__(self):
        try:
            import anthropic
        except ImportError:
            raise SystemExit("[llm] Run: pip install anthropic")
        self._anthropic = anthropic
        self.client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.MODEL

    @staticmethod
    def _messages(messages: list[dict]) -> list[dict]:
        out = []
        for m in messages:
            if m["role"] == "tool":
                block = {"type": "tool_result", "tool_use_id": _short_id(m["tool_call_id"], "t"),
                         "content": m["content"]}
                if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                    out[-1]["content"].append(block)
                else:
                    out.append({"role": "user", "content": [block]})
            elif m["role"] == "assistant":
                blocks = [{"type": "text", "text": m["content"]}] if m.get("content") else []
                blocks += [{"type": "tool_use", "id": _short_id(tc["id"], "t"), "name": tc["name"],
                            "input": tc["args"]} for tc in m.get("tool_calls", [])]
                if blocks:
                    out.append({"role": "assistant", "content": blocks})
            else:
                out.append({"role": "user", "content": m["content"]})
        return out

    async def generate(self, system: str, messages: list[dict], tools: list[dict] | None = None) -> Reply:
        a = self._anthropic
        kwargs = {}
        if tools:
            kwargs["tools"] = [{"name": t["name"], "description": t["description"],
                                "input_schema": t["parameters"]} for t in tools]
        try:
            resp = await self.client.messages.create(
                model=self.model, max_tokens=2048, system=system,
                messages=self._messages(messages), **kwargs,
            )
        except a.RateLimitError:
            raise RateLimitError(RATE_LIMIT_MSG)
        except a.AuthenticationError:
            raise LLMError("مفتاح Anthropic مش شغّال 🔑 تأكد من ANTHROPIC_API_KEY بملف .env")
        except a.NotFoundError:
            raise LLMError("اسم الموديل غلط ❌ تأكد من قيمة MODEL بملف .env")
        except a.APIStatusError as e:
            log.error("Anthropic API error %s: %s", e.status_code, e)
            raise LLMError(f"صار خطأ من Anthropic (رمز {e.status_code}). جرّب كمان مرة.")
        except Exception as e:
            log.exception("Anthropic connection problem: %s", e)
            raise LLMError(NETWORK_MSG)

        reply = Reply()
        for b in resp.content:
            if b.type == "text":
                reply.text += b.text
            elif b.type == "tool_use":
                reply.tool_calls.append({"id": b.id, "gid": None, "name": b.name, "args": dict(b.input or {})})
        if not reply.text and not reply.tool_calls:
            raise LLMError(EMPTY_MSG)
        return reply


# ---------------------------------------------------------------- OpenAI-compatible backups

class OpenAICompatibleProvider:
    """Backup providers that share the OpenAI chat format (Groq, Mistral, OpenRouter, Cerebras, Ollama)."""

    def __init__(self, name: str, url: str, api_key: str, model: str, extra_headers: dict | None = None):
        import httpx  # already installed with python-telegram-bot

        self.name = name
        self.url = url
        self.api_key = api_key
        self.model = model
        self.extra_headers = extra_headers or {}
        self.client = httpx.AsyncClient(timeout=90)

    @staticmethod
    def _messages(system: str, messages: list[dict]) -> list[dict]:
        out = [{"role": "system", "content": system}]
        for m in messages:
            if m["role"] == "tool":
                out.append({"role": "tool", "tool_call_id": _short_id(m["tool_call_id"]),
                            "name": m["name"], "content": m["content"]})
            elif m["role"] == "assistant":
                msg = {"role": "assistant", "content": m.get("content") or ""}
                if m.get("tool_calls"):
                    msg["tool_calls"] = [{
                        "id": _short_id(tc["id"]), "type": "function",
                        "function": {"name": tc["name"], "arguments": json.dumps(tc["args"], ensure_ascii=False)},
                    } for tc in m["tool_calls"]]
                out.append(msg)
            else:
                out.append({"role": "user", "content": m["content"]})
        return out

    async def generate(self, system: str, messages: list[dict], tools: list[dict] | None = None) -> Reply:
        # max_tokens: some providers (Cloudflare) default to a tiny limit and return empty answers.
        payload = {"model": self.model, "messages": self._messages(system, messages), "max_tokens": 4096}
        if tools:
            payload["tools"] = [{"type": "function", "function": {
                "name": t["name"], "description": t["description"], "parameters": t["parameters"]}}
                for t in tools]
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if self.extra_headers:
            headers.update(self.extra_headers)

        try:
            resp = await self.client.post(self.url, json=payload, headers=headers)
        except Exception as e:
            log.exception("%s connection problem: %s", self.name, e)
            raise LLMError(NETWORK_MSG)

        env = self.name.upper()
        if resp.status_code == 429:
            raise RateLimitError(RATE_LIMIT_MSG)
        if resp.status_code in (401, 403):
            raise LLMError(f"مفتاح {self.name} مش شغّال 🔑 تأكد من {env}_API_KEY بملف .env")
        if resp.status_code == 404:
            raise LLMError(f"اسم موديل {self.name} غلط ❌ تأكد من قيمة {env}_MODEL بملف .env")
        if resp.status_code >= 400:
            log.error("%s API error %s: %s", self.name, resp.status_code, resp.text[:500])
            raise LLMError(f"صار خطأ من {self.name} (رمز {resp.status_code}). جرّب كمان مرة.")

        try:
            msg = resp.json()["choices"][0]["message"]
        except (KeyError, IndexError, ValueError, TypeError):
            raise LLMError(EMPTY_MSG)
        reply = Reply(text=msg.get("content") or "")
        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except ValueError:
                args = {}
            reply.tool_calls.append({"id": tc.get("id") or _new_id(), "gid": None,
                                     "name": fn.get("name", ""), "args": args if isinstance(args, dict) else {}})
        if not reply.text and not reply.tool_calls:
            raise LLMError(EMPTY_MSG)
        return reply


# Backup providers list
BACKUPS = [
    ("Groq", "https://api.groq.com/openai/v1/chat/completions"),
    ("Cloudflare", "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions"),
    ("xKiro", "https://api.xkiro.com/v1/chat/completions"),
    ("Cerebras", "https://api.cerebras.ai/v1/chat/completions"),
    ("Mistral", "https://api.mistral.ai/v1/chat/completions"),
    ("OpenRouter", "https://openrouter.ai/api/v1/chat/completions"),
    ("NVIDIA", "https://integrate.api.nvidia.com/v1/chat/completions"),
    ("ZAI", "https://api.z.ai/api/paas/v4/chat/completions"),
    ("Ollama", getattr(config, "OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1/chat/completions")),
]


class FallbackLLM:
    """Try providers in order and use the first one that answers.
    A provider that is busy or out of quota is skipped for a few minutes."""

    COOLDOWN = 5 * 60  # seconds

    def __init__(self, providers: list):
        self.providers = providers  # list of (name, provider)
        self._resting_until: dict[str, float] = {}

    @property
    def main_name(self) -> str:
        return self.providers[0][0] if self.providers else "None"

    async def generate(self, system: str, messages: list[dict], tools: list[dict] | None = None) -> Reply:
        now = time.monotonic()
        ready = [(n, p) for n, p in self.providers if self._resting_until.get(n, 0) <= now]
        # If everyone is resting, try them all anyway rather than give up.
        candidates = ready or self.providers
        last_error = None
        for name, provider in candidates:
            try:
                reply = await provider.generate(system, messages, tools)
            except LLMError as e:
                log.warning("%s failed (%s), trying next provider", name, e.user_message)
                self._resting_until[name] = time.monotonic() + self.COOLDOWN
                last_error = e
                continue
            self._resting_until.pop(name, None)
            reply.provider = name
            return reply
        raise last_error or LLMError(EMPTY_MSG)


# ---------------------------------------------------------------- Smart Hybrid Router

class SmartRouter(FallbackLLM):
    """Enterprise Intelligent Hybrid Router for LLM workloads.
    Wave 1.4: Token boundary task classification, error classification (413 trim, 402/401 disable,
    429/5xx backoff), token estimation before dispatch, pinned provider per loop.
    """

    PROVIDER_LIMITS = {
        "groq": 8000,
        "cloudflare": 8000,
        "ollama": 8000,
        "mistral": 32000,
        "openrouter": 64000,
        "gemini": 1000000,
    }

    def __init__(self, providers: list):
        super().__init__(providers)
        self._provider_map: dict[str, tuple[str, object]] = {
            name.lower(): (name, prov) for name, prov in self.providers
        }
        self._disabled_providers: set[str] = set()
        self._failure_counts: dict[str, int] = {}

    @staticmethod
    def estimate_tokens(system: str, messages: list[dict], tools: list[dict] | None = None) -> int:
        chars = len(system) + sum(len(str(m.get("content") or "")) for m in messages)
        if tools:
            import json
            chars += len(json.dumps(tools, ensure_ascii=False))
        return int(chars / 3.5)

    @staticmethod
    def detect_task_type(system: str, messages: list[dict]) -> str:
        import re
        user_content = ""
        for m in reversed(messages):
            if m.get("role") == "user" and isinstance(m.get("content"), str):
                user_content = m["content"].lower()
                break

        latin_tokens = set(re.findall(r'\b[a-z0-9_]+\b', user_content))
        arabic_tokens = set(re.findall(r'[\u0600-\u06FF]+', user_content))

        coding_latin = {
            "code", "coding", "python", "javascript", "typescript", "flutter", "laravel",
            "script", "bug", "debug", "traceback", "function", "class", "github",
            "repo", "mikrotik", "routeros", "subnet", "vlan", "cidr", "dhcp",
            "solar", "inverter", "battery", "photovoltaic", "sql", "sqlite"
        }
        coding_arabic = {
            "كود", "برمجة", "سكربت", "دالة", "تصحيح", "شبكة", "ميكروتك", "راوتر",
            "انفرتر", "بطارية", "الواح", "ألواح", "سولار", "سيرفر"
        }

        summary_latin = {"summarize", "summary", "brief", "digest", "triage", "tldr"}
        summary_arabic = {"تلخيص", "ملخص", "لخص", "اختصر", "اختصار", "موجز"}

        if (latin_tokens & summary_latin) or (arabic_tokens & summary_arabic):
            return "summary"
        if (latin_tokens & coding_latin) or (arabic_tokens & coding_arabic):
            return "coding"
        return "general"

    def _get_candidates_for_task(self, task_type: str) -> list[tuple[str, object]]:
        task = (task_type or "general").lower().strip()
        if task in ("coding", "network", "code"):
            priority = ["gemini", "mistral", "openrouter", "groq", "ollama"]
        elif task in ("summary", "fast", "triage"):
            priority = ["gemini", "groq", "mistral", "ollama", "openrouter"]
        else:
            return self.providers

        ordered: list[tuple[str, object]] = []
        seen = set()
        for p_name in priority:
            if p_name in self._provider_map:
                name, prov = self._provider_map[p_name]
                ordered.append((name, prov))
                seen.add(p_name)
        for name, prov in self.providers:
            if name.lower() not in seen:
                ordered.append((name, prov))
                seen.add(name.lower())
        return ordered

    async def generate(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        task_type: str = "auto",
        pinned_provider: str | None = None,
    ) -> Reply:
        if not task_type or task_type == "auto":
            effective_task = self.detect_task_type(system, messages)
        else:
            effective_task = task_type.lower().strip()

        candidates_all = self._get_candidates_for_task(effective_task)
        
        # Filter permanently disabled providers (402 balance / 401 invalid key)
        available = [(n, p) for n, p in candidates_all if n.lower() not in self._disabled_providers]

        # Prioritize pinned provider if valid
        if pinned_provider:
            pinned_match = [(n, p) for n, p in available if n.lower() == pinned_provider.lower()]
            if pinned_match:
                available = pinned_match + [cp for cp in available if cp[0].lower() != pinned_provider.lower()]

        now = time.monotonic()
        ready = [(n, p) for n, p in available if self._resting_until.get(n, 0) <= now]
        candidates = ready or available

        if not candidates:
            raise LLMError("جميع مزودي الذكاء الاصطناعي معطلون حالياً. يرجى مراجعة أرصدة ومفاتيح .env.")

        estimated_tokens = self.estimate_tokens(system, messages, tools)
        last_error = None

        for name, provider in candidates:
            # Skip provider if estimated tokens exceed its limit
            p_limit = self.PROVIDER_LIMITS.get(name.lower(), 16000)
            if estimated_tokens > p_limit:
                log.info("[SmartRouter] Skipping %s: estimated tokens %s > limit %s", name, estimated_tokens, p_limit)
                continue

            for attempt in range(2):
                try:
                    reply = await provider.generate(system, messages, tools)
                    self._resting_until.pop(name, None)
                    self._failure_counts.pop(name, None)
                    reply.provider = name
                    return reply

                except PayloadTooLargeError as e:
                    log.warning("[SmartRouter] Provider %s payload too large (%s). Skipping without cooldown.", name, e)
                    last_error = e
                    break

                except (BillingError, AuthenticationError) as e:
                    log.error("[SmartRouter] Disabling provider %s until restart: %s", name, e)
                    self._disabled_providers.add(name.lower())
                    last_error = e
                    break

                except (RateLimitError, ServerError) as e:
                    last_error = e
                    if attempt == 0:
                        delay = 1.5 + (0.5 * (time.monotonic() % 1))
                        log.warning("[SmartRouter] Transient error on %s (%s). Retrying in %.2fs...", name, e, delay)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        log.warning("[SmartRouter] Provider %s failed after retry. Setting cooldown.", name)
                        self._resting_until[name] = time.monotonic() + self.COOLDOWN
                        self._failure_counts[name] = self._failure_counts.get(name, 0) + 1
                        break

                except LLMError as e:
                    log.warning("[SmartRouter] Provider %s LLMError: %s", name, e.user_message)
                    self._resting_until[name] = time.monotonic() + self.COOLDOWN
                    last_error = e
                    break

                except Exception as e:
                    log.warning("[SmartRouter] Provider %s unexpected error: %s", name, e)
                    self._resting_until[name] = time.monotonic() + self.COOLDOWN
                    last_error = LLMError(f"خطأ أثناء الاتصال بمزود {name}: {e}")
                    break

        raise last_error or LLMError(EMPTY_MSG)

_ROUTER_CACHE = None

def get_llm() -> SmartRouter:
    """Builds and returns the configured SmartRouter singleton."""
    global _ROUTER_CACHE
    if _ROUTER_CACHE is not None:
        return _ROUTER_CACHE

    if config.AI_PROVIDER == "anthropic":
        providers = [("Anthropic", AnthropicProvider())]
    else:
        providers = [("Gemini", GeminiProvider(config.GEMINI_API_KEY))]

    if config.GEMINI_API_KEY and config.GEMINI_BACKUP_MODEL:
        lite = GeminiProvider(config.GEMINI_API_KEY)
        lite.model = config.GEMINI_BACKUP_MODEL
        providers.append(("Gemini-Lite", lite))

    if config.GEMINI_API_KEY_2:
        providers.append(("Gemini-2", GeminiProvider(config.GEMINI_API_KEY_2)))

    for name, url in BACKUPS:
        key, model = config.BACKUP_KEYS.get(name, ("", ""))
        if name == "Cloudflare":
            if not config.CLOUDFLARE_ACCOUNT_ID:
                continue
            url = url.format(account_id=config.CLOUDFLARE_ACCOUNT_ID)

        extra_headers = {}
        if name == "OpenRouter":
            extra_headers = {
                "HTTP-Referer": "https://github.com/adham-agent",
                "X-Title": "Adham Agent Enterprise OS",
            }
        elif name == "Ollama":
            url = config.OLLAMA_BASE_URL

        if key and model:
            providers.append((name, OpenAICompatibleProvider(name, url, key, model, extra_headers=extra_headers)))

    # PROVIDER_ORDER in .env decides who goes first; providers not listed keep their place after.
    if config.PROVIDER_ORDER and config.AI_PROVIDER != "anthropic":
        rank = {n.lower(): i for i, n in enumerate(config.PROVIDER_ORDER)}
        providers.sort(key=lambda p: rank.get(p[0].lower(), len(rank)))

    log.info("SmartRouter initialized with providers: %s", " -> ".join(n for n, _ in providers))
    _ROUTER_CACHE = SmartRouter(providers)
    return _ROUTER_CACHE


def get_smart_router() -> SmartRouter:
    return get_llm()


async def generate(system: str, messages: list[dict], tools: list[dict] | None = None, task_type: str = "auto") -> Reply:
    """Module-level generation entry point."""
    router = get_smart_router()
    return await router.generate(system, messages, tools, task_type=task_type)

