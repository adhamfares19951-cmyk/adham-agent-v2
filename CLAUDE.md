# CLAUDE.md — adham-agent Operational Manual & Project Rules

## Environment & Deployment
- **Target OS:** Windows 10/11 / Windows Server (Python 3.11+, local virtual environment in env).
- **Primary Launcher:** start_watchdog.bat is the ONE official 24/7 self-healing launcher.
- **Local-Only:** The bot runs locally on this Windows machine only. Any cloud services (e.g., Railway) have been stopped to prevent Telegram polling conflict (Conflict: terminated by other getUpdates).
- **Single Instance Guard:** A PID lockfile (ot.lock) ensures only one instance runs at any time.

---

## 0. Non-Negotiable Rules
1. **Communication:**
   - Talk to me in Arabic (Levantine / Palestinian dialect).
   - The bot calls me "أدهم".
   - Code, variable names, and code comments in English.
   - When writing Arabic with English technical terms, put each English term on its own line or clearly set apart.
2. **Secrets:**
   - NEVER read, print, display, or commit .env, credentials.json, 	oken.json, youtube_cookies.txt, or anything under sessions/.
   - If a new environment variable is needed, add it to .env.example with an empty value and instruct me in Arabic to fill it in Notepad.
   - No passwords or tokens in code or logs. Never log full message text.
3. **Engineering Standard:**
   - Before editing any file, copy it to ackups\<YYYYMMDD_HHMM>\<same relative path>.
   - Async-first: No blocking operations (subprocess.run, 	ime.sleep, heavy sync SQLite) on the event loop. Use syncio.to_thread / async clients.
   - Google Gemini: use ONLY rom google import genai (google-genai). NEVER google.generativeai. Always read MODEL from .env.
   - Provider-agnostic LLM layer stays: switching providers only requires editing .env.
   - No placeholders: no pass, # TODO, or mock returns in real logic.
   - Split replies exceeding 4096 characters (send_long). Use update.effective_message.
   - Owner-only: The bot only responds to OWNER_ID and silently ignores everyone else, including all callback queries.
   - External actions gate: Anything sent or published outside in my name (email, WhatsApp, TikTok/Instagram/YouTube publish, messages to businesses) MUST show a draft/summary first with buttons (✅ إرسال / ✏️ تعديل / ❌ إلغاء) and wait for approval (pproval_queue table).
   - Every error must be logged with traceback and explained in Arabic. Nothing fails silently.
   - Keep daily usage limits and usage logging working.

---

## Architecture Overview
`
adham-agent/
├── main.py                  # Telegram bot ingress, handlers, single-instance lock guard
├── brain.py                 # Core agent reasoning loop (SYSTEM_PROMPT <= 1500 tokens, repetition detection)
├── llm.py                   # SmartRouter multi-provider layer (Gemini, Groq, Mistral, OpenRouter, Ollama)
├── memory.py                # SQLite storage (agent_memory.db, rolling summary, tool turns, approval_queue)
├── config.py                # Centralized environment loader from .env
├── tools/                   # 122 executable tools categorized into 8 functional groups (cap <= 25 per turn)
│   ├── reminders.py         # Asia/Gaza natural-language reminders & JobQueue scheduler
│   ├── jobs.py              # Automated job hunter & ATS CV match evaluator
│   ├── tiktok_publisher.py  # Playwright headless publisher with safe retry
│   ├── youtube_publisher.py # YouTube Data API v3 OAuth publisher with invalid_grant detection
│   └── ...                  # Social, media, network/mikrotik, leads, finance, and dev tools
├── tests/                   # Automated unit tests and evaluation suite
└── start_watchdog.bat       # Official 24/7 supervisor launcher
`

## Running Tests
Run all unit tests using the project virtual environment:
`powershell
.\venv\Scripts\python.exe -m unittest discover tests
`
