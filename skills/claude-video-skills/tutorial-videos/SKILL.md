---
name: tutorial-videos
description: "Turn a screen recording (with or without voice) into a clear step-by-step tutorial: dead time cut or sped up, zooms on the part being clicked, step titles and captions, as a 16:9 video or a 9:16 short. Use when the user asks to edit a tutorial, how-to or screen recording, /tutorial-videos, or in Arabic 'فيديو شرح' or 'شرح خطوة بخطوة'."
metadata:
  author: "مدرسة الذكاء الاصطناعي"
  website: "https://arabianaischool.com"
  version: "1.0.0"
---

# Tutorial videos (step by step)

Makes a screen recording easy to follow: waiting and loading are cut or sped up, the view zooms into the area being used, every step gets a numbered title, and the voice gets captions.

**What the user gives you:** A screen recording (and optionally a separate voice recording or a talking-head clip). The steps, if the user has them.

## Setup (check once per machine)

Everything runs on the user's computer with `scripts/reelkit.py` (one Python file in this skill's folder) and ffmpeg.
`scripts/...` below always means the `scripts` folder **inside this skill's folder** (for example
`~/.claude/skills/<this-skill>/scripts/reelkit.py`): call it by that full path while you work in the user's folder.
1. `python scripts/reelkit.py probe <video>` must print the size and duration. If ffmpeg is missing, tell the user:
   Windows `winget install Gyan.FFmpeg`, Mac `brew install ffmpeg`, then open a new terminal.
2. `pip install faster-whisper` (word timings for captions and clean cuts).

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

1. Transcribe and proofread if there is a voice. Without a voice, ask the user for the steps in one line each.
2. Look at the recording: `python scripts/reelkit.py sheet <video> -o work/sheet.jpg --n 24 --cols 6`.
   Find where each step starts and where nothing happens (loading, typing long text, waiting).
3. Write `work/plan.json` with `"canvas": [1920, 1080]` (YouTube) or `[1080, 1920]` (short):
   - Layout `screen` for every segment. For a 9:16 short use `zoom_rect` on most segments, because the full screen
     is too small on a phone.
   - Each step starts with a segment whose `title` is "الخطوة ١: ..." / "Step 1: ..." (short, verb first).
   - Dead time: cut it, or keep it with `"speed": 2` (up to 4) when the viewer needs to see it happen.
   - `zoom_rect` `[x, y, w, h]` (source pixels, same aspect as the canvas works best) when something small is clicked
     or typed; zoom back out on the next segment.
   - Captions: `"style": "line", "words_per_line": 7, "position": 0.9` for 16:9.
4. `python scripts/reelkit.py render work/plan.json -o tutorial.mp4`, plus
   `python scripts/reelkit.py srt work/words.json -o tutorial.srt --plan work/plan.json` for YouTube subtitles.
5. Write `chapters.txt` (one line per step, `00:00 الخطوة ١ ...`, times in the OUTPUT video).

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
