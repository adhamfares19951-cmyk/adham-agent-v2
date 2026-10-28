"""Loads all settings from .env in one place."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _get(name: str, required: bool = True) -> str:
    value = os.getenv(name, "").strip().strip('"').strip("'")
    if required and not value:
        raise SystemExit(f"[config] Missing value in .env: {name}")
    return value


TELEGRAM_TOKEN = _get("TELEGRAM_TOKEN")
AI_PROVIDER = _get("AI_PROVIDER").lower()
MODEL = _get("MODEL")
GEMINI_API_KEY = _get("GEMINI_API_KEY", required=False)
GEMINI_API_KEY_2 = _get("GEMINI_API_KEY_2", required=False)  # optional extra quota
# Optional second Gemini model on the same key: Google counts the free quota per model.
GEMINI_BACKUP_MODEL = _get("GEMINI_BACKUP_MODEL", required=False)
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY", required=False)

# Hybrid Smart Router configuration (Ollama + OpenRouter + Gemini)
OLLAMA_BASE_URL = _get("OLLAMA_BASE_URL", required=False) or "http://127.0.0.1:11434/v1/chat/completions"
OLLAMA_API_KEY = _get("OLLAMA_API_KEY", required=False) or "ollama"
OLLAMA_MODEL = _get("OLLAMA_MODEL", required=False) or "qwen2.5-coder:14b"

OPENROUTER_API_KEY = _get("OPENROUTER_API_KEY", required=False)
OPENROUTER_MODEL = _get("OPENROUTER_MODEL", required=False) or "deepseek/deepseek-chat"

# Optional backup providers: used only when the main provider is busy or out of quota.
# Each one is enabled only when both its key and model are filled in .env.
BACKUP_KEYS = {
    name: (_get(f"{name.upper()}_API_KEY", required=False), _get(f"{name.upper()}_MODEL", required=False))
    for name in ("Groq", "Cloudflare", "xKiro", "Cerebras", "Mistral", "OpenRouter", "NVIDIA", "ZAI", "Ollama")
}

# Ensure native Ollama and OpenRouter are correctly mapped in BACKUP_KEYS
if not BACKUP_KEYS.get("Ollama") or not BACKUP_KEYS["Ollama"][0] or not BACKUP_KEYS["Ollama"][1]:
    BACKUP_KEYS["Ollama"] = (OLLAMA_API_KEY, OLLAMA_MODEL)
if OPENROUTER_API_KEY:
    BACKUP_KEYS["OpenRouter"] = (OPENROUTER_API_KEY, OPENROUTER_MODEL or BACKUP_KEYS.get("OpenRouter", ("", ""))[1] or "deepseek/deepseek-chat")

CLOUDFLARE_ACCOUNT_ID = _get("CLOUDFLARE_ACCOUNT_ID", required=False)
# Try providers in this order, e.g. "xKiro,Gemini-Lite,Groq" (empty = default order).
PROVIDER_ORDER = [n.strip() for n in _get("PROVIDER_ORDER", required=False).split(",") if n.strip()]

try:
    OWNER_ID = int(_get("OWNER_ID"))
except ValueError:
    raise SystemExit("[config] OWNER_ID must be numbers only (your Telegram user id).")

if AI_PROVIDER not in ("gemini", "anthropic"):
    raise SystemExit("[config] AI_PROVIDER must be 'gemini' or 'anthropic'.")
if AI_PROVIDER == "gemini" and not GEMINI_API_KEY:
    raise SystemExit("[config] AI_PROVIDER is gemini but GEMINI_API_KEY is empty.")
if AI_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
    raise SystemExit("[config] AI_PROVIDER is anthropic but ANTHROPIC_API_KEY is empty.")

TIMEZONE = "Asia/Gaza"
MAX_HISTORY = 20  # past messages sent to the AI with each new message

try:
    DAILY_MESSAGE_LIMIT = int(_get("DAILY_MESSAGE_LIMIT", required=False) or 200)
    JOB_SCAN_MINUTES = max(10, int(_get("JOB_SCAN_MINUTES", required=False) or 30))
except ValueError:
    raise SystemExit("[config] DAILY_MESSAGE_LIMIT and JOB_SCAN_MINUTES must be numbers.")

# Default morning brief time (can also be changed from chat). "off" disables it.
MORNING_BRIEF_TIME = _get("MORNING_BRIEF_TIME", required=False) or "08:00"
if MORNING_BRIEF_TIME != "off":
    try:
        _h, _m = map(int, MORNING_BRIEF_TIME.split(":"))
        assert 0 <= _h < 24 and 0 <= _m < 60
    except (ValueError, AssertionError):
        raise SystemExit("[config] MORNING_BRIEF_TIME must look like 08:00 (or off).")

# ReliefWeb API name (free, must be approved by ReliefWeb). Empty = ReliefWeb not checked.
RELIEFWEB_APPNAME = _get("RELIEFWEB_APPNAME", required=False)

# LLM Generation Parameters
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_OUTPUT_TOKENS = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "4096"))
