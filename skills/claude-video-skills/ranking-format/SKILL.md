---
name: ranking-format
description: "Make a tier-list reel: an S to F table where cards drop into their rank as the speaker names them, full screen or on top with the speaker below. Use when the user asks for a ranking, tier list, 'rank these', /ranking-format, or in Arabic 'ترتيب' or 'تير ليست' or 'رتّب لي'."
metadata:
  author: "مدرسة الذكاء الاصطناعي"
  website: "https://arabianaischool.com"
  version: "1.0.0"
---

# Ranking format (tier list reel)

A tier-list table (S, A, B, C, D, F) with a title. Each item drops into its row with a bounce at the exact moment the speaker says it, so the ranking lands on the beat of the voice.

**What the user gives you:** The items and their tiers (or a talking-head video that ranks them; you find the moments in the transcript). Optional: a talking-head video to sit under the table.

## Setup (check once per machine)

Everything runs on the user's computer with `scripts/reelkit.py` (one Python file in this skill's folder) and ffmpeg.
`scripts/...` below always means the `scripts` folder **inside this skill's folder** (for example
`~/.claude/skills/<this-skill>/scripts/reelkit.py`): call it by that full path while you work in the user's folder.
1. `python scripts/reelkit.py probe <video>` must print the size and duration. If ffmpeg is missing, tell the user:
   Windows `winget install Gyan.FFmpeg`, Mac `brew install ffmpeg`, then open a new terminal.
2. `pip install faster-whisper` (word timings for captions and clean cuts).
3. `pip install playwright` then `playwright install chromium` (renders the animated table).

Use `python3` where `python` is not found. In Claude.ai (code execution) this works for short clips; if a package or
model cannot be downloaded there, say so plainly and suggest Claude Code on the user's computer.

Work in a `work/` folder next to the user's files and keep their originals untouched.

## Style first: the user's look, not ours

The examples and screenshots of this pack show one creator's style. Never copy it. Every video uses the **user's**
colours, theme and font.
1. If `brand.json` already exists next to the user's videos, show it in one line and ask whether anything changed.
2. Otherwise ask, in one message (in the user's language), and wait for the answer:
   - **Colours:** their main brand colour, caption colour and the highlight colour for the spoken word. They can
     also send a logo, a screenshot or a website and you take the colours from it.
   - **Theme:** light or dark.
   - **Font:** Cairo (included, works for Arabic and English), or another font: then they install it or send the
     .ttf/.otf file.
   If the user says "anything" or "you choose", pick a clean, readable set and tell them what you picked.
3. Save the answers in `brand.json` (format in `PLAN.md`) and put `"brand": "../brand.json"` (path from the plan
   to the file) in every plan. Use the same file for every later video so the look stays consistent.

## Transcript (word timings)

1. `python scripts/reelkit.py transcribe <video> -o work/words.json`
   - Arabic: add `--model large-v3` for the best spelling (slower on CPU); `small` is the quick default.
   - Add `--prompt "names, brands, product words"` so they are spelled right.
2. **Proofread before using it.** Open `work/words.json`, read the text and fix misheard words in place (keep each
   word's `start`/`end`; when you merge or split words, split the time between them). Captions show every mistake.

## Workflow

1. Get the title, the items and their tiers. With a video, transcribe it and read where each item is said.
2. Write `work/ranking.json`:
   ```json
   {"title": "أفضل المنصات لجلب العملاء", "tiers": ["S","A","B","C","D","F"],
    "items": [{"label": "لينكدإن", "tier": "C", "t": 2.4}, {"label": "YouTube", "tier": "S", "t": 4.1}]}
   ```
   `t` is when the card drops, in seconds of the video: the word's `start` from `words.json` minus 0.2.
   Keep labels short (1 to 2 words). Up to about 5 cards fit in a row.
3. **Table only (9:16):**
   `python scripts/render.py scripts/template.html ranking.mp4 --data work/ranking.json --brand brand.json --dur <seconds>`
4. **Table on top, speaker below:** render the table at half height, then use it as the `top` of a `split`:
   `python scripts/render.py scripts/template.html work/table.mp4 --data work/ranking.json --brand brand.json --w 1080 --h 960 --dur <video length>`
   and a plan with one segment `{"start": 0, "end": <length>, "layout": "split", "top": "table.mp4"}` plus `words`
   for captions (`"position": 0.9`), then `python scripts/reelkit.py render work/plan.json -o ranking_reel.mp4`.
5. Check a still first: `python scripts/render.py scripts/template.html work/still.png --data work/ranking.json --brand brand.json --still 6`.

Always pass `--brand brand.json` so the table uses the user's background, text colour, accent and font (Cairo by
default). Tier colours can be changed with `--set S=ff6b6b --set A=ffa94d`; `--alpha` gives a transparent overlay. Tiers can be renamed (`["Top", "Good", "Meh"]`); add colours for new names with `--set`.

## Check, then deliver

1. `python scripts/reelkit.py sheet <out.mp4> -o work/check.jpg` and **look at the image**: speaker framed (head not
   cut), captions inside the frame and readable, titles not covering the face, no black bars, no frozen frames.
2. Fix the plan and render again until it is right. Never claim a check you did not do.
3. Deliver the file path, its length and size, and one line per thing you did.

The full plan format (layouts, zoom, captions, titles, music) is in `PLAN.md` next to this file.

## Rules
- Use only the user's own footage, words and assets. Never invent quotes, numbers, names or claims.
- Talk to the user in their language (Arabic if they write in Arabic). Captions follow the language spoken.
- Ask at most one round of questions, only for what you cannot work out; otherwise make sensible choices and say which.

## Credits

Made and maintained by **مدرسة الذكاء الاصطناعي** (Arabian AI School), © 2026.
Website https://arabianaischool.com/skills/claude-video-skills/ · YouTube https://www.youtube.com/@ArabianAiSchool ·
Instagram https://www.instagram.com/arabianaischool · Facebook https://www.facebook.com/arabianaischool · X https://x.com/arabianaischool

Free to use in your own and client videos. Please don't resell or re-upload the pack as your own.
