---
name: personal-short-form-reels
description: "Edit a fast personal reel from a talking-head video and the user's own B-roll: silences cut, punch-in zooms, B-roll cutaways and split screens on the right words, word-by-word captions. Use when the user asks to edit their reel or short, /personal-short-form-reels, or in Arabic 'منتجلي الريل' or 'اعمل ريل من الفيديو ده'."
metadata:
  author: "مدرسة الذكاء الاصطناعي"
  website: "https://arabianaischool.com"
  version: "1.0.0"
---

# Personal short-form reels

Turns a raw talking-head take into a tight 9:16 reel: dead air and stumbles removed, a punch-in on every cut, the user's own B-roll on the words it illustrates, and word-by-word captions.

**What the user gives you:** A talking-head video and a folder of the user's B-roll (clips or photos). Optional: music.

## Setup (check once per machine)

Everything runs on the user's computer with `scripts/reelkit.py` (one Python file in this skill's folder) and ffmpeg.
`scripts/...` below always means the `scripts` folder **inside this skill's folder** (for example
`~/.claude/skills/<this-skill>/scripts/reelkit.py`): call it by that full path while you work in the user's folder.
1. `python scripts/reelkit.py probe <video>` must print the size and duration. If ffmpeg is missing, tell the user:
   Windows `winget install Gyan.FFmpeg`, Mac `brew install ffmpeg`, then open a new terminal.
2. `pip install faster-whisper` (word timings for captions and clean cuts).
3. Optional: `pip install mediapipe` to keep the face centred when cropping (`faces`).

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

1. Transcribe and proofread. Run `python scripts/reelkit.py silences <video> -o work/keep.json` for the talking parts.
2. `python scripts/reelkit.py faces <video> -o work/faces.json` (if mediapipe is installed).
3. **Know the B-roll.** If the folder has a `broll_index.json` (from the personal-broll-library skill), search it:
   `python scripts/reelkit.py search broll_index.json "laptop desk"`. Otherwise run
   `python scripts/reelkit.py index <broll folder> -o work/broll_index.json`, look at the contact sheets it makes and
   write a short description for each clip you might use.
4. **Write the edit** in `work/plan.json` (9:16):
   - The first 2 seconds are the hook: start on the strongest sentence, with a `title`.
   - Remove silences, false starts and repeated takes (keep the last, cleanest take).
   - `full` segments alternate `zoom` 1.0 and 1.12 to 1.15; an occasional `[1.0, 1.1]` push on a key line.
   - Cut to `broll` when the speaker names something visual (about 1.5 to 3 s each, never the first second).
     Use `split` (B-roll on top, speaker below) when the face matters too.
   - Aim for 25 to 45 seconds unless the user says otherwise.
5. `python scripts/reelkit.py render work/plan.json -o reel.mp4` (add `"music"` for a bed at -20 dB if given).

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
