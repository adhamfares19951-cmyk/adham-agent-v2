---
name: educational-youtube-editor
description: "Edit a long recorded lesson into a finished YouTube video: silences, mistakes and retakes removed, punch-in zooms that hide the cuts, chapter title cards, subtitles file, chapters and description. Use when the user asks to edit a lesson, course video or long YouTube video, /educational-youtube-editor, or in Arabic 'منتج الدرس ده' or 'جهز الفيديو لليوتيوب'."
metadata:
  author: "مدرسة الذكاء الاصطناعي"
  website: "https://arabianaischool.com"
  version: "1.0.0"
---

# Educational YouTube editor

Turns a long, raw lesson into a clean 16:9 YouTube edit: every pause, stumble and retake removed, alternating punch-in zooms so the cuts feel intentional, a title card per chapter, plus subtitles, chapters and a description ready to paste.

**What the user gives you:** The lesson recording (camera, screen recording, or both cut into one file). Optional: the lesson outline.

## Setup (check once per machine)

Everything runs on the user's computer with `scripts/reelkit.py` (one Python file in this skill's folder) and ffmpeg.
`scripts/...` below always means the `scripts` folder **inside this skill's folder** (for example
`~/.claude/skills/<this-skill>/scripts/reelkit.py`): call it by that full path while you work in the user's folder.
1. `python scripts/reelkit.py probe <video>` must print the size and duration. If ffmpeg is missing, tell the user:
   Windows `winget install Gyan.FFmpeg`, Mac `brew install ffmpeg`, then open a new terminal.
2. `pip install faster-whisper` (word timings for captions and clean cuts).
3. Optional: `pip install mediapipe` for face-centred zooms (`faces`).

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

1. Transcribe (`--model large-v3` for Arabic is worth it here) and proofread.
2. `python scripts/reelkit.py silences <video> -o work/keep.json --min 0.6` for the talking parts, and `faces`.
3. **Find the retakes.** Read the transcript: when a sentence is said, then said again, keep the last good take and
   drop the first. Drop "um / يعني / خلينا نشوف" filler when it stands alone.
4. **Chapters.** Split the lesson into 4 to 10 chapters by topic. Each chapter starts with a short `card` segment
   (the first 1.5 to 2.5 s of its first sentence) whose `title` is the chapter name.
5. Write `work/plan.json` with `"canvas": [1920, 1080]`:
   - `full` segments for camera parts, `screen` for screen parts (with `zoom_rect` on small details).
   - Alternate zoom 1.0 and 1.1 on every cut inside a chapter (a jump cut with a zoom looks deliberate).
   - Captions off for YouTube (`"captions": {"enabled": false}`): ship the `.srt` instead, which viewers can turn on.
6. Render: `python scripts/reelkit.py render work/plan.json -o lesson_edit.mp4`
   Subtitles: `python scripts/reelkit.py srt work/words.json -o lesson_edit.srt --plan work/plan.json`
7. Write `youtube.md`: a title (3 options), a description (what they will learn, 3 to 5 lines), the chapters list
   in output time (`00:00 مقدمة` ... the first must be 00:00), and a thumbnail idea in one line.
8. Tell the user how much was cut (raw length to final length).

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
