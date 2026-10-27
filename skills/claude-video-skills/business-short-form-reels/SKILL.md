---
name: business-short-form-reels
description: "Edit a business or brand reel from a talking-head video: full screen, split screen with product shots or screenshots, animated title cards, punch-ins and captions, ending on a call to action. Use when the user asks for a business, brand, product or client reel, /business-short-form-reels, or in Arabic 'ريل للبيزنس' or 'فيديو إعلاني لشركتي'."
metadata:
  author: "مدرسة الذكاء الاصطناعي"
  website: "https://arabianaischool.com"
  version: "1.0.0"
---

# Business short-form reels

A brand reel that holds attention: the speaker full screen for the human moments, split screen with the product, the website or proof (numbers, reviews) when they explain, animated title cards for the key points, and a clear call to action at the end.

**What the user gives you:** A talking-head video and the brand assets: logo, product photos, screenshots, short product clips. Optional: brand colours and font, music.

## Setup (check once per machine)

Everything runs on the user's computer with `scripts/reelkit.py` (one Python file in this skill's folder) and ffmpeg.
`scripts/...` below always means the `scripts` folder **inside this skill's folder** (for example
`~/.claude/skills/<this-skill>/scripts/reelkit.py`): call it by that full path while you work in the user's folder.
1. `python scripts/reelkit.py probe <video>` must print the size and duration. If ffmpeg is missing, tell the user:
   Windows `winget install Gyan.FFmpeg`, Mac `brew install ffmpeg`, then open a new terminal.
2. `pip install faster-whisper` (word timings for captions and clean cuts).
3. Optional: `pip install mediapipe` to keep the face centred (`faces`).

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

1. Ask only for what is missing: the video, the assets, the call to action (what should viewers do?) and the format.
2. Transcribe and proofread; `silences` and `faces` as in the other skills.
3. Write `work/plan.json`:
   - Hook (first 2 s): the boldest claim or result, `full` with a `title`.
   - When the speaker explains the product or shows proof: `split` with the matching asset on top
     (`"top_zoom": [1.0, 1.08]` for photos; `"top_fit": "contain"` for screenshots so nothing is cropped).
   - Key points (3 at most): a short `card` segment with the point as `title`, over the blurred speaker.
   - The rest: `full`, alternating zoom 1.0 / 1.12.
   - End: a `card` with the call to action, or `split` with the logo on top.
   - Colours and font come from `brand.json` (above); use the brand colour for the call-to-action card.
4. `python scripts/reelkit.py render work/plan.json -o business_reel.mp4`

Never invent numbers, prices, reviews or claims; use only what the user said or gave you.

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
