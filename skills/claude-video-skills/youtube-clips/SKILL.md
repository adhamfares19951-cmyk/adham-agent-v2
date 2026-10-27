---
name: youtube-clips
description: "Find the best moments in a long video (podcast, lesson, live, YouTube video) and cut them into vertical clips with the speaker centred, captions and a hook title. Use when the user asks for clips, shorts or highlights from a long video, /youtube-clips, or in Arabic 'طلعلي كليبات' or 'شورتس من الفيديو ده'."
metadata:
  author: "مدرسة الذكاء الاصطناعي"
  website: "https://arabianaischool.com"
  version: "1.0.0"
---

# YouTube clips (best moments as shorts)

Reads the whole transcript, picks the moments that work alone (a strong opening line, one clear idea, a payoff), and turns each into a 9:16 clip with the speaker kept in frame, captions and a hook title.

**What the user gives you:** The long video file (the user downloads their own video). Optional: how many clips and how long.

## Setup (check once per machine)

Everything runs on the user's computer with `scripts/reelkit.py` (one Python file in this skill's folder) and ffmpeg.
`scripts/...` below always means the `scripts` folder **inside this skill's folder** (for example
`~/.claude/skills/<this-skill>/scripts/reelkit.py`): call it by that full path while you work in the user's folder.
1. `python scripts/reelkit.py probe <video>` must print the size and duration. If ffmpeg is missing, tell the user:
   Windows `winget install Gyan.FFmpeg`, Mac `brew install ffmpeg`, then open a new terminal.
2. `pip install faster-whisper` (word timings for captions and clean cuts).
3. Optional but recommended: `pip install mediapipe` so the speaker stays centred when cropping to 9:16.

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

1. Transcribe (`--model large-v3` for Arabic if time allows) and proofread the parts you will use.
2. `python scripts/reelkit.py faces <video> -o work/faces.json --step 1` (follows the speaker for the crop).
3. **Choose the clips.** Read the transcript with timestamps and pick 3 to 8 moments, 20 to 60 s each, that:
   start on a line that grabs attention without context, make one idea, and end on a payoff (not mid-thought).
   Show the user a table first: number, start to end, hook title (3 to 6 words), why it works. Wait for a yes
   unless the user said to go ahead.
4. For each clip write `work/clip_N.json`: `full` segments on word boundaries, cutting dead air inside the clip,
   zoom alternating 1.0 / 1.12, `title` on the first segment, `faces` and `words` set, canvas `[1080, 1920]`.
   Two people on camera: split into segments per speaker and set `"focus": [x, y]` on the one talking.
5. `python scripts/reelkit.py render work/clip_N.json -o clips/clip_N.mp4` for each, then check each sheet.
6. Deliver the list: file, length, hook title, and a one-line caption suggestion for posting.

Only clip videos the user owns or has the rights to.

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
