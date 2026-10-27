# `adham-agent` Architecture & Workspace Context Rulebook
> **Master Blueprint & Strict Operational Guidelines**  
> *Target System*: Autonomous Multi-Agent System & Personal Digital Twin  
> *Target Runtime*: Python 3.11+ / Windows & Linux VPS  

---

## 1. System Vision & Architecture Overview

`adham-agent` is an asynchronous, autonomous multi-agent swarm and digital twin designed to represent and execute technical operations on behalf of **Adham (أدهم)**. The system operates on a decentralized, task-driven blackboard architecture where specialized agents act on shared state rather than uncontrolled conversational loops.

```
                              ┌────────────────────────────────────────┐
                              │      Inbound Ingress & Interfaces      │
                              │  (Telegram Bot, CLI, Webhook Trigger)  │
                              └───────────────────┬────────────────────┘
                                                  │
                                                  ▼
                              ┌────────────────────────────────────────┐
                              │       Master Brain / Orchestrator      │
                              │     (Gemini Flash Structured Router)   │
                              └───────────────────┬────────────────────┘
                                                  │
                     ┌────────────────────────────┼────────────────────────────┐
                     ▼                            ▼                            ▼
      ┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐
      │      YouTube Agent       │  │   Hunter/Career Agent    │  │    Dev & Sys Agents      │
      │ (SEO, Script, Auto-Pub)  │  │ (Scraper, Match, ATS CV) │  │ (Coding, VPS, MikroTik)  │
      └──────────────┬───────────┘  └─────────────┬────────────┘  └─────────────┬────────────┘
                     │                            │                             │
                     └────────────────────────────┼─────────────────────────────┘
                                                  ▼
                              ┌────────────────────────────────────────┐
                              │    Unified SQLite Blackboard Store     │
                              │     (`agent_tasks`, `blackboard.db`)   │
                              └───────────────────┬────────────────────┘
                                                  │
                                                  ▼
                              ┌────────────────────────────────────────┐
                              │            Dual-LLM Router             │
                              │  Gemini 2.5 Flash  ◄►  DeepSeek Chat   │
                              └────────────────────────────────────────┘
```

---

## 2. The 5 Non-Negotiable Core Engineering Rules

Every developer, AI agent, and subagent modifying or interacting with this workspace MUST strictly obey these 5 core engineering rules:

### Rule 1: No Chat Fluff in Inter-Agent Communication
- Agents never communicate with each other through unstructured conversational banter, conversational tokens, or markdown chatter.
- **Communication Protocol**:
  - All inter-agent data exchanges, tool payloads, and task transfers must use **strict Pydantic schemas** (`pydantic.BaseModel` with typed fields).
  - When invoking Gemini or DeepSeek for structured output, enforce `response_schema` / JSON Schema guarantees.
  - State persistence, task claiming, progress updates, and completion artifacts are logged directly to the SQLite `agent_tasks` blackboard table:
    ```sql
    CREATE TABLE IF NOT EXISTS agent_tasks (
        task_id TEXT PRIMARY KEY,
        parent_task_id TEXT,
        assigned_agent TEXT NOT NULL,
        status TEXT CHECK(status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED')) NOT NULL,
        input_payload JSON NOT NULL,
        output_payload JSON,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ```

### Rule 2: Modern Google SDK Enforcement
- **MANDATORY**: Always use the official modern Google GenAI SDK:
  ```python
  from google import genai
  from google.genai import types
  ```
- **STRICTLY FORBIDDEN**: Never import or invoke the legacy, deprecated `google.generativeai` package.
- All Gemini calls must configure explicit model instances, typed generation parameters (`types.GenerateContentConfig`), and structured JSON response schemas when schema compliance is required.

### Rule 3: Dual-Model Hybrid Routing Policy
The system leverages a dual-engine architecture optimizing for latency, cost, and specialized technical reasoning:
1. **Primary Engine — Google Gemini Flash (`gemini-2.5-flash`)**:
   - Master Brain orchestration and high-level routing.
   - Pydantic JSON structuring and extraction.
   - Multimodal analysis (Video, Audio, Images, PDF inspection).
   - Creative workflows: YouTube script ideation, viral hook composition, SEO tagging, and description generation.
2. **Specialized Engine — DeepSeek (`deepseek-chat` / DeepSeek Coder via OpenAI client)**:
   - Complex technical reasoning, code generation, script debugging, and AST refactoring.
   - Algorithmic problem solving and system configuration (MikroTik scripting, Dockerfiles, SQL queries).
3. **Resilience & Automatic Fallback**:
   - If Gemini encounters rate limits (HTTP 429) or quota saturation, non-multimodal tasks automatically fail over to DeepSeek.
   - If DeepSeek experiences latency spikes or connection timeouts, tasks route back to Gemini Flash with zero pipeline disruption.

### Rule 4: Async-First Execution Standard
- Concurrency is mandatory for multi-agent parallelism.
- All LLM client calls (`genai.Client.aio` / `AsyncOpenAI`), database operations (`aiosqlite`), browser automation (`playwright.async_api`), and file I/O must be written as native `asyncio` coroutines.
- Blocking synchronous operations (`time.sleep()`, synchronous `requests`, synchronous file locks) are strictly prohibited inside orchestrator loops or agent steps. Use `asyncio.sleep()` and non-blocking executors.

### Rule 5: Production-Ready Code Standard
- Zero placeholders: Code must be complete, tested, and executable immediately.
- Never write `pass`, `# TODO: implement later`, or mock returns in core business logic, agent tools, or database migrations.
- Handle all error boundaries explicitly: log structured exceptions, write failure states to the `agent_tasks` blackboard, and return graceful typed fallback responses.

---

## 3. Directory Layout & Package Roles

```
adham-agent/ (and workspace root)
├── core/                         # Core execution engine
│   ├── __init__.py
│   ├── brain.py                  # Master Brain orchestrator & agent loop
│   ├── llm_router.py             # Dual-LLM wrapper (Gemini Flash + DeepSeek)
│   └── database.py               # Async SQLite blackboard connection & models
│
├── agents/                       # Autonomous specialized sub-agents
│   ├── __init__.py
│   ├── youtube_agent.py          # Watcher, scriptwriter, SEO, auto-uploader
│   ├── career_agent.py           # Job hunter, ReliefWeb/Mostaql scraper, ATS CV builder
│   ├── dev_agent.py              # Autonomous coding, code audit, git operations
│   └── sys_agent.py              # VPS health, MikroTik manager, server diagnostics
│
├── tools/                        # Executable agent tools & integrations
│   ├── __init__.py
│   ├── youtube_uploader.py       # YouTube Data API v3 OAuth uploader
│   ├── playwright_scraper.py     # Resilient headless browser scraper
│   ├── cv_docx_builder.py        # Tailored ATS Word/PDF CV & Cover Letter builder
│   └── file_ops.py               # Safe local file system manager
│
├── config/                       # Configuration & settings management
│   ├── __init__.py
│   └── settings.py               # Pydantic BaseSettings environment loader
│
├── workspace_data/               # Persistent runtime artifacts & blackboard
│   ├── youtube_ready/            # Watched folder for rendered videos ready to publish
│   ├── generated_cvs/            # Output folder for generated ATS CVs & Cover Letters
│   ├── logs/                     # Rotating execution logs
│   └── agent_blackboard.db       # Unified SQLite blackboard database
│
├── .env.example                  # Environment template
├── requirements.txt              # Pinned modern dependencies
└── ARCHITECTURE.md               # Master blueprint (this document)
```

---

## 4. Environment & Secrets Management
- All sensitive credentials (`GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `TELEGRAM_BOT_TOKEN`, `YOUTUBE_CLIENT_SECRETS_FILE`) are loaded exclusively from `.env` via `config.settings.settings`.
- **Absolute Rule**: Never print, log, or commit `.env` contents to git or display secret keys in terminal outputs.

---

## 5. Verification Protocol
Before marking any feature, agent, or tool complete:
1. Run syntax and import checks across all modified packages.
2. Verify that `workspace_data/` directories exist and are writeable.
3. Verify dual-LLM connectivity and error boundary responses.
4. Ensure zero linting errors and 100% adherence to the 5 Core Engineering Rules.
