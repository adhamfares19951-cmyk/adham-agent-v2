# ARCHITECTURE.md — Reality-Aligned Master Blueprint

## 1. System Vision & Architecture Overview
dham-agent is an asynchronous, zero-hallucination Telegram AI Agent and executive digital twin built for **Adham Al-Habbash**.
It automates reminders, job opportunities evaluation, marketing, publishing, networking, and business tasks with deterministic tool execution and human-in-the-loop approval.

### Operational Stack:
- **Runtime:** Python 3.11+ running locally on Windows.
- **Process Supervisor:** start_watchdog.bat runs watchdog.py which supervises main.py.
- **Single-Instance Enforcement:** Process ID lockfile ot.lock ensures zero Telegram conflict errors.
- **Telegram Interface:** python-telegram-bot with Long Polling, drop_pending_updates=False, concurrent_updates(True), and per-chat syncio.Lock.

---

## 2. Core Subsystems

### A. Brain & Reasoning Loop (rain.py)
- **System Prompt:** Ultra-concise (<= 1500 tokens), warm Levantine/Palestinian dialect, results-oriented, with dynamic slots for current time (<<NOW>>), calendar, profile facts, and few-shot examples.
- **Zero-Hallucination Policy:** The agent never claims a fact, publication, or file unless returned by a real tool in the conversation turn.
- **Loop Safeguards:** Max 25 steps per message; detects repeated identical tool calls and breaks loops; requests a final non-tool summary if MAX_STEPS is reached instead of crashing.
- **Usage Counting:** Messages are counted towards DAILY_MESSAGE_LIMIT only after a successful reply.

### B. Multi-Provider LLM Layer (llm.py)
- **SmartRouter:** Orchestrates GeminiProvider (primary) with fallbacks to Groq, Mistral, OpenRouter, and local Ollama.
- **Token Estimation & Circuit Breaking:** Estimates prompt tokens prior to dispatch; skips providers whose limits cannot fit the payload.
- **Error Classification:**
  - 413 Payload Too Large: Skips provider for the request without 5-minute cooldown.
  - 402 Payment Required & 401/403/404: Disables provider until process restart.
  - 429 Rate Limit & 5xx: Retries with exponential backoff + jitter.
- **Pinned Provider:** The provider chosen at step 0 is pinned for the entire tool loop to maintain coherent context.

### C. Tool Registry & Intent Selection (	ools/)
- **122 Executable Tools** categorized into 8 functional groups:
  1. core: Memory, basic search, web reader, calendar. (Always active).
  2. 
eminders_jobs: Natural-language reminders, job hunter, career insights.
  3. social_publishing: TikTok, Instagram, YouTube automation, social dispatcher.
  4. 
etwork_mikrotik: Subnet calculation, MikroTik router scripts, solar sizing.
  5. dev_workspace: Git operations, workspace file management, server ops.
  6. media: Motion masterclass, viral video assembly, edge-tts studio.
  7. leads_sales: Verified B2B lead extraction, proposals, WhatsApp bridge, Gmail.
  8. inance: Store products, client orders, financial ledger.
- **Dynamic Selection (select_tools):** Limits tool schemas to <= 25 per turn based on user intent keywords.
- **Validation & Sandboxing:** JSON schema validation of all tool arguments before handler invocation.
- **Timeouts & Truncation:** syncio.wait_for (60s default, 180s for media) and result truncation at ~6,000 characters.
- **Untrusted Source Delimiter:** Web and email outputs are demarcated as untrusted data to stop prompt injection.

### D. Security & Approval Gate (Rule 14)
- **Approval Queue:** All sensitive external operations (execute_server_command, workspace_write_file, self_modify_agent_code, social publishing, email sending) are diverted to the pproval_queue table and require explicit button approval (✅ / ✏️ / ❌).
- **Shell Denylist:** Destructive commands (ormat, del /s, 
mdir /s, powershell -enc, etc.) are blocked by a hard second layer.

### E. Memory & History (memory.py)
- **Database:** SQLite (gent_memory.db) with WAL mode.
- **Tool Turns Persistence:** Compact summaries (<= 300 chars) of tool outputs are saved with assistant messages.
- **Rolling Summarization:** Automatically rolls older turns into conversation_summary when messages exceed threshold, maintaining the last 12 raw turns.
- **Large File Protection:** Replaces uploaded code/PDF dumps with compact metadata placeholders.

---

## 3. Data Flow Diagram
`
Telegram User Input
        │
        ▼
   main.py (Single-Instance Guard: bot.lock, Concurrent Updates, Chat Lock)
        │
        ▼
   brain.py (Intent Tool Selection <= 25 tools, System Prompt <= 1500 tokens)
        │
        ├──► llm.py (SmartRouter -> Gemini / Fallback with Error Classification)
        │        ▲
        │        │ Function Calls
        ▼        ▼
   tools/__init__.py (JSON Schema Validation, 60s Timeout, Approval Gate)
        │
        ▼
   memory.py (SQLite: Tool Summary Persistence, Rolling History Anchor)
        │
        ▼
   Telegram Response Delivery (Split at 4096 chars, Sanitized Errors)
`
