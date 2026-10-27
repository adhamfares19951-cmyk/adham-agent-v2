"""Dual-Model Hybrid LLM Engine for adham-agent.

Implements architectural rule 3 from ARCHITECTURE.md:
- Gemini Flash (official google-genai SDK) for fast orchestration, structured outputs, YouTube creative/SEO.
- DeepSeek (via OpenAI-compatible AsyncOpenAI) for complex coding, debugging, and technical reasoning.
- Automatic mutual failover, schema validation, and async-first execution.
- Smart Auto-Fallback: Instantly catches Gemini 503 UNAVAILABLE / 429 rate limit errors and seamlessly
  switches to DeepSeek without crashing active sessions.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from google import genai
from google.genai import types
from google.genai.errors import APIError, ClientError, ServerError
from openai import AsyncOpenAI, APIConnectionError, APIStatusError, RateLimitError
from pydantic import BaseModel

from config.settings import settings

logger = logging.getLogger("adham_agent.llm")

T = TypeVar("T", bound=BaseModel)

# Known stable modern fallback models for Gemini when legacy model names are retired
GEMINI_MODERN_CANDIDATES = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-3.8-flash",
]


def clean_schema_for_gemini(schema: Any) -> Any:
    """Recursively removes 'additionalProperties' from JSON schema for Gemini Developer API compliance."""
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        schema = schema.model_json_schema()
    if isinstance(schema, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in schema.items():
            if k == "additionalProperties":
                continue
            if isinstance(v, dict):
                cleaned[k] = clean_schema_for_gemini(v)
            elif isinstance(v, list):
                cleaned[k] = [clean_schema_for_gemini(item) for item in v]
            else:
                cleaned[k] = v
        return cleaned
    return schema


def is_gemini_overload_or_rate_limit(err: Exception) -> bool:
    """Detect if an exception is a Gemini 503 (Unavailable/Overloaded), 429 (Rate Limit/Quota), or transient server error."""
    # 1. Inspect HTTP status / code attribute (google.genai errors or httpx responses)
    code = getattr(err, "code", None) or getattr(err, "status_code", None)
    if code in (503, 429, 500, 502, 504):
        return True

    # 2. Inspect exception string signatures
    err_str = str(err).lower()
    overload_signatures = [
        "503",
        "unavailable",
        "overload",
        "high demand",
        "resource_exhausted",
        "resourceexhausted",
        "rate limit",
        "ratelimit",
        "quota",
        "429",
        "too many requests",
        "server error",
        "service unavailable",
        "temporarily unavailable",
        "deadline exceeded",
    ]
    return any(sig in err_str for sig in overload_signatures)


def extract_and_parse_json(raw_text: str, schema: Type[T]) -> T:
    """Robustly extract and validate JSON content from LLM output into a Pydantic model."""
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("Cannot parse empty response into JSON schema")

    # 1. Direct validation if clean JSON
    try:
        return schema.model_validate_json(text)
    except Exception:
        pass

    # 2. Markdown fenced codeblock extraction (```json ... ``` or ``` ...)
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if code_block_match:
        extracted = code_block_match.group(1).strip()
        try:
            return schema.model_validate_json(extracted)
        except Exception:
            pass

    # 3. Outer brace extraction heuristic (from first '{' to last '}')
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        extracted = text[first_brace : last_brace + 1].strip()
        try:
            return schema.model_validate_json(extracted)
        except Exception:
            pass

        # 4. Standard json.loads fallback with model_validate
        try:
            parsed_dict = json.loads(extracted)
            return schema.model_validate(parsed_dict)
        except Exception:
            pass

    # Final attempt to surface exact validation error
    return schema.model_validate_json(text)


class LLMEngine:
    """Dual-Model Hybrid Engine managing Gemini Flash & DeepSeek routing with automatic failover."""

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        deepseek_base_url: Optional[str] = None,
        gemini_model: Optional[str] = None,
        deepseek_model: Optional[str] = None,
    ) -> None:
        self.gemini_api_key = gemini_api_key or settings.GEMINI_API_KEY
        self.deepseek_api_key = deepseek_api_key or settings.DEEPSEEK_API_KEY
        self.deepseek_base_url = deepseek_base_url or settings.DEEPSEEK_BASE_URL
        self.gemini_model = gemini_model or settings.GEMINI_MODEL
        self.deepseek_model = deepseek_model or settings.DEEPSEEK_MODEL

        # Initialize Google GenAI client (official modern SDK)
        self._gemini_client: Optional[genai.Client] = None
        if self.gemini_api_key:
            try:
                self._gemini_client = genai.Client(api_key=self.gemini_api_key)
            except Exception as e:
                logger.error("Failed to initialize Google GenAI Client: %s", e)

        # Initialize DeepSeek client (AsyncOpenAI SDK)
        self._deepseek_client: Optional[AsyncOpenAI] = None
        effective_key = self.deepseek_api_key or settings.DEEPSEEK_API_KEY
        if effective_key and effective_key != "EMPTY_KEY":
            try:
                self._deepseek_client = AsyncOpenAI(
                    api_key=effective_key,
                    base_url=self.deepseek_base_url,
                )
            except Exception as e:
                logger.error("Failed to initialize AsyncOpenAI DeepSeek Client: %s", e)

    @property
    def gemini_client(self) -> genai.Client:
        """Get the active Google GenAI client, re-initializing if necessary."""
        if self._gemini_client is None:
            effective_key = self.gemini_api_key or settings.GEMINI_API_KEY
            if not effective_key:
                raise ValueError("GEMINI_API_KEY is not configured in environment or settings.")
            self._gemini_client = genai.Client(api_key=effective_key)
        return self._gemini_client

    @property
    def deepseek_client(self) -> AsyncOpenAI:
        """Get the active DeepSeek client, re-initializing if necessary."""
        effective_key = self.deepseek_api_key or settings.DEEPSEEK_API_KEY
        if not effective_key or effective_key == "EMPTY_KEY":
            raise ValueError(
                "DEEPSEEK_API_KEY is not configured in environment or settings. "
                "Please configure DEEPSEEK_API_KEY (or OPENROUTER_API_KEY) in .env"
            )
        if self._deepseek_client is None:
            self._deepseek_client = AsyncOpenAI(
                api_key=effective_key,
                base_url=self.deepseek_base_url,
            )
        return self._deepseek_client

    # =========================================================================
    # Strict Structured Output Generation
    # =========================================================================

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: str = "",
        provider: str = "gemini",
        temperature: float = 0.7,
    ) -> T:
        """Generate strictly-typed Pydantic structured output with automatic provider failover."""
        provider_lower = provider.lower().strip()

        if provider_lower == "gemini":
            try:
                return await self._call_gemini_structured(
                    prompt=prompt,
                    response_schema=response_schema,
                    system_instruction=system_instruction,
                    temperature=temperature,
                )
            except Exception as gemini_err:
                if is_gemini_overload_or_rate_limit(gemini_err):
                    logger.warning(
                        "Gemini overloaded, switching to DeepSeek fallback... (Error: %s)",
                        gemini_err,
                    )
                else:
                    logger.warning(
                        "Primary provider 'gemini' structured generation failed: %s. Initiating fallback to DeepSeek...",
                        gemini_err,
                    )
                try:
                    return await self._call_deepseek_structured(
                        prompt=prompt,
                        response_schema=response_schema,
                        system_instruction=system_instruction,
                        temperature=temperature,
                    )
                except Exception as deepseek_err:
                    logger.error("Secondary provider 'deepseek' fallback also failed: %s", deepseek_err)
                    raise RuntimeError(
                        f"Dual-model structured generation failed on both providers. "
                        f"Gemini error: {gemini_err} | DeepSeek error: {deepseek_err}"
                    ) from deepseek_err

        elif provider_lower == "deepseek":
            try:
                return await self._call_deepseek_structured(
                    prompt=prompt,
                    response_schema=response_schema,
                    system_instruction=system_instruction,
                    temperature=temperature,
                )
            except Exception as deepseek_err:
                logger.warning(
                    "Primary provider 'deepseek' structured generation failed: %s. Initiating fallback to Gemini Flash...",
                    deepseek_err,
                )
                try:
                    return await self._call_gemini_structured(
                        prompt=prompt,
                        response_schema=response_schema,
                        system_instruction=system_instruction,
                        temperature=temperature,
                    )
                except Exception as gemini_err:
                    logger.error("Secondary provider 'gemini' fallback also failed: %s", gemini_err)
                    raise RuntimeError(
                        f"Dual-model structured generation failed on both providers. "
                        f"DeepSeek error: {deepseek_err} | Gemini error: {gemini_err}"
                    ) from gemini_err

        else:
            raise ValueError(f"Unknown LLM provider '{provider}'. Must be 'gemini' or 'deepseek'.")

    async def _call_gemini_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: str,
        temperature: float,
    ) -> T:
        """Execute structured call against Google Gemini Flash with sanitized schema enforcement."""
        client = self.gemini_client
        clean_schema = clean_schema_for_gemini(response_schema)

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=clean_schema,
            system_instruction=system_instruction if system_instruction else None,
            temperature=temperature,
        )

        models_to_try = [self.gemini_model]
        for candidate in GEMINI_MODERN_CANDIDATES:
            if candidate not in models_to_try:
                models_to_try.append(candidate)

        last_error: Optional[Exception] = None
        for model_name in models_to_try:
            try:
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                raw_text = response.text
                if not raw_text:
                    raise ValueError(f"Empty text response from Gemini model '{model_name}'")
                return response_schema.model_validate_json(raw_text)
            except ClientError as e:
                # If model is 404 (retired), try next candidate
                if e.code == 404:
                    logger.warning("Gemini model '%s' returned 404 NOT_FOUND. Trying alternative modern candidate...", model_name)
                    last_error = e
                    continue
                # If 429 rate limit or quota, break immediately to trigger DeepSeek fallback without wasting time
                last_error = e
                break
            except ServerError as e:
                # 503 / 5xx server overload: break immediately for instant DeepSeek failover
                last_error = e
                break
            except Exception as e:
                last_error = e
                if is_gemini_overload_or_rate_limit(e):
                    break
                break

        if last_error:
            raise last_error
        raise RuntimeError("Failed to generate structured output with Gemini models")

    async def _call_deepseek_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: str,
        temperature: float,
    ) -> T:
        """Execute structured call against DeepSeek with JSON schema injection and validation."""
        client = self.deepseek_client
        schema_dict = response_schema.model_json_schema()
        schema_json = json.dumps(schema_dict, indent=2, ensure_ascii=False)

        augmented_system = (
            f"{system_instruction}\n\n" if system_instruction else ""
        ) + (
            f"CRITICAL CONSTRAINT: You must return ONLY a single valid JSON object that strictly adheres to this JSON Schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Do not include any conversational preamble, explanation, or markdown formatting outside the JSON."
        )

        messages = [
            {"role": "system", "content": augmented_system},
            {"role": "user", "content": prompt},
        ]

        response = await client.chat.completions.create(
            model=self.deepseek_model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError(f"DeepSeek ({self.deepseek_model}) returned an empty response")

        return extract_and_parse_json(content, response_schema)

    # =========================================================================
    # Standard Async Text & Code Generation
    # =========================================================================

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str = "",
        provider: str = "deepseek",
        temperature: float = 0.4,
    ) -> str:
        """Generate freeform text, code, or technical reasoning with automatic provider fallback."""
        provider_lower = provider.lower().strip()

        if provider_lower == "deepseek":
            try:
                return await self._call_deepseek_text(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=temperature,
                )
            except Exception as deepseek_err:
                logger.warning(
                    "Primary provider 'deepseek' text generation failed: %s. Falling back to Gemini Flash...",
                    deepseek_err,
                )
                try:
                    return await self._call_gemini_text(
                        prompt=prompt,
                        system_instruction=system_instruction,
                        temperature=temperature,
                    )
                except Exception as gemini_err:
                    logger.error("Secondary provider 'gemini' fallback also failed: %s", gemini_err)
                    raise RuntimeError(
                        f"Dual-model text generation failed on both providers. "
                        f"DeepSeek error: {deepseek_err} | Gemini error: {gemini_err}"
                    ) from gemini_err

        elif provider_lower == "gemini":
            try:
                return await self._call_gemini_text(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=temperature,
                )
            except Exception as gemini_err:
                if is_gemini_overload_or_rate_limit(gemini_err):
                    logger.warning(
                        "Gemini overloaded, switching to DeepSeek fallback... (Error: %s)",
                        gemini_err,
                    )
                else:
                    logger.warning(
                        "Primary provider 'gemini' text generation failed: %s. Falling back to DeepSeek...",
                        gemini_err,
                    )
                try:
                    return await self._call_deepseek_text(
                        prompt=prompt,
                        system_instruction=system_instruction,
                        temperature=temperature,
                    )
                except Exception as deepseek_err:
                    logger.error("Secondary provider 'deepseek' fallback also failed: %s", deepseek_err)
                    raise RuntimeError(
                        f"Dual-model text generation failed on both providers. "
                        f"Gemini error: {gemini_err} | DeepSeek error: {deepseek_err}"
                    ) from deepseek_err

        else:
            raise ValueError(f"Unknown LLM provider '{provider}'. Must be 'gemini' or 'deepseek'.")

    async def _call_gemini_text(
        self,
        prompt: str,
        system_instruction: str,
        temperature: float,
    ) -> str:
        """Execute text generation with Google Gemini Flash."""
        client = self.gemini_client
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction if system_instruction else None,
        )

        models_to_try = [self.gemini_model]
        for candidate in GEMINI_MODERN_CANDIDATES:
            if candidate not in models_to_try:
                models_to_try.append(candidate)

        last_error: Optional[Exception] = None
        for model_name in models_to_try:
            try:
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                return response.text or ""
            except ClientError as e:
                if e.code == 404:
                    logger.warning("Gemini model '%s' returned 404 NOT_FOUND. Trying alternative candidate...", model_name)
                    last_error = e
                    continue
                last_error = e
                break
            except ServerError as e:
                last_error = e
                break
            except Exception as e:
                last_error = e
                if is_gemini_overload_or_rate_limit(e):
                    break
                break

        if last_error:
            raise last_error
        raise RuntimeError("Failed to generate text with Gemini models")

    async def _call_deepseek_text(
        self,
        prompt: str,
        system_instruction: str,
        temperature: float,
    ) -> str:
        """Execute text generation with DeepSeek."""
        client = self.deepseek_client
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=self.deepseek_model,
            messages=messages,
            temperature=temperature,
        )

        return response.choices[0].message.content or ""


# Global default LLM engine instance
llm_engine = LLMEngine()
