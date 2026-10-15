## Environment
You are running in Claude Code on my Windows PC, inside the adham-agent folder.
Create and edit files yourself and run commands yourself — don't ask me to copy-paste code.
Create the .env file with empty values, then tell me to fill in my keys myself in Notepad.
Never read, print, or display the contents of .env.


# Project: "Right Hand" (دراع اليمين) — Personal AI Agent

## Who I am
My name is Adham Alhabbash. I live in Khan Younis, Gaza, Palestine.
I am an IT Support & Network Technician with ~10 years of experience: MikroTik routers,
wired/wireless networks, VLANs, ISP street networks (450+ subscribers, 500+ Wi-Fi routers),
hardware repair, printers, CCTV, Active Directory, Windows.
I worked with Nasser Medical Complex (UNDP project + wartime volunteer), Palestinian Red Crescent,
a municipality, and ISPs. Diploma in Computer Technical Support (UCST, 2015).
Training: CCNA, CompTIA A+, ICDL. Arabic native, English good (technical).
I am looking for an IT support or network role with an NGO or international organization.
My full CV is uploaded in the project files.

IMPORTANT: I am NOT a programmer. I am comfortable with computers, Windows, and basic
command-line use, but I cannot write or debug Python myself. YOU write 100% of the code.
My job is only to copy files, run commands, and send you any errors.

## Language rules
- Talk to me in Arabic (Levantine dialect is fine).
- Everything the bot shows me (messages, buttons, reminders, summaries) must be in Arabic.
- Code, variable names, and code comments in English.
- The bot calls me "أدهم".

## What the agent does
I talk to it on Telegram and ask it for anything:
1. Reminders: "ذكرني الساعة 5 أتصل بفلان", recurring ("كل يوم أحد"), snooze ("أجّلها ربع ساعة").
   It must understand natural Arabic time expressions. Timezone: Asia/Gaza.
2. Job search: finds IT support / network / ICT roles that fit my CV, focusing on NGOs,
   UN agencies, and international organizations (Gaza, Palestine region, and remote).
   Sources like ReliefWeb, UN Careers, UNjobs, Devex, jobs.ps and similar. For each job:
   match score, why it fits, what I'm missing, deadline, and link.
   On request, writes a tailored English cover letter and suggests CV tweaks.
3. Courses: suggests courses/certifications that close gaps between my skills and the jobs
   it finds (e.g. CompTIA Network+, MikroTik MTCNA, CCNA exam, Microsoft 365, Security+),
   preferring free or low-cost options.
4. Gmail + Google Calendar: read, summarize, draft, and send emails; manage events.
5. Daily morning brief at a time I choose: today's reminders, new matching jobs,
   important emails, one suggested course.
6. Website-client outreach (later phase): find local businesses without websites,
   write a personalized message for each, generate a simple demo website for them,
   and track replies.
7. General daily-life help with memory of past conversations.

## Technical decisions (fixed unless I ask to change them)
- Python 3 on Windows locally first, then a small VPS later.
- Telegram: python-telegram-bot, Long Polling mode, reminders via the built-in JobQueue.
- Brain: Google Gemini API (free tier) with function calling, behind a provider-agnostic layer.
- Database: SQLite.
- WhatsApp later via the official WhatsApp Cloud API only. Never unofficial libraries.

## AI provider — READ CAREFULLY
- I cannot pay for the Anthropic API right now, so the brain uses the Google Gemini API
  free tier (google-genai Python SDK) with function calling.
- The code must be provider-agnostic: brain.py talks to an "llm" layer, and the provider is
  chosen by AI_PROVIDER in .env (gemini now, anthropic later when I can pay).
  Switching providers must only require editing .env.
- Never hardcode the model name; always read MODEL from .env. Tell me which current
  Gemini Flash model name to use, and if you are unsure, tell me how to check it in AI Studio.
- Respect free-tier rate limits: handle "rate limit / quota exceeded" errors gracefully
  and tell me in Arabic to try again later instead of crashing.
- Later, when I have credit: Anthropic model "claude-sonnet-5" (current and correct).
  Claude 3 / 3.5 model names are retired — never use them.

## Secrets (.env)
- Keys: TELEGRAM_TOKEN, AI_PROVIDER, GEMINI_API_KEY, ANTHROPIC_API_KEY (empty for now),
  OWNER_ID, MODEL.
- I will put my real keys in .env myself. Never ask me to paste keys into the chat.
  If I accidentally paste a key, tell me to revoke it and create a new one.

## Project structure
adham-agent/
├── main.py          # Telegram bot entry point
├── brain.py         # the agent logic + tool-use loop
├── llm.py           # provider layer (Gemini now, Anthropic later)
├── memory.py        # SQLite: profile, conversation history, reminders, usage
├── config.py        # loads all settings from .env in one place
├── tools/           # one file per tool: reminders, web_search, jobs, courses, gmail, ...
├── .env
└── .gitignore       # includes .env, venv/, and the SQLite database file

## Non-negotiable rules
1. The bot only responds to OWNER_ID and silently ignores everyone else.
2. Anything sent outside in my name (email, WhatsApp, message to a business) must first be
   shown to me as a draft with Telegram buttons (✅ إرسال / ✏️ تعديل / ❌ إلغاء) and wait
   for my approval, unless I explicitly enable auto-send for a specific task.
3. Daily usage limit, with usage logged in the database.
4. No keys or tokens in code — only .env.
5. Telegram messages are limited to 4096 characters — always split long replies.
6. Use update.effective_message instead of update.message.
7. Handle errors gracefully: the bot should tell me in Arabic what went wrong, never crash silently.

## Current status
NOTHING is done yet. I have not installed Python or created any files.
I already have: a Telegram bot token (from BotFather), a Gemini API key, and my Telegram user ID.
Start from zero: install Python on Windows, create the project folder, virtual environment,
.env file, and then Phase 1.

## Roadmap
1. Setup + basic bot: Telegram bot that replies using Gemini, locked to OWNER_ID.
2. Memory (SQLite: conversation history + my profile from the CV) + tool-use loop
   + reminders tool + web search tool.
3. Job search + course suggestions + morning brief.
4. Gmail and Google Calendar via OAuth.
5. Website-client outreach pipeline.
6. WhatsApp (Cloud API).
7. Deploy to a VPS so it runs 24/7.

## How to work with me
- Work one phase at a time. Don't move on until the current phase runs on my machine.
- Always give me COMPLETE files ready to copy-paste, never partial snippets
  (unless the change is 1–2 lines, and then tell me exactly where they go).
- Give exact step-by-step instructions: which file to create, where to save it,
  which command to run, and what I should see if it worked.
- Always list new libraries with the exact pip install command.
- For anything that needs setup outside the code (Google Cloud, OAuth, VPS),
  walk me through it click by click, assuming I've never done it before.
- When I send you an error, explain the cause simply in Arabic and give me the fixed file.
- Keep explanations short and practical. I don't need to understand Python in depth.
- Be honest: if something is risky, costly, against a platform's rules, or you're unsure
  about a library's current API, tell me.