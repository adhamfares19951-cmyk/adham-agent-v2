---
name: depth-ui-reel
description: "Put a UI behind the speaker's head: a website, YouTube channel, app or any screenshot sits behind them, the speaker is cut out in front, captions at the bottom. Use when the user asks for a depth or UI-behind-head reel, 'put my channel/site behind me', /depth-ui-reel, or in Arabic 'حط الموقع ورايا' or 'ريل الواجهة ورا راسي'."
metadata:
  author: "مدرسة الذكاء الاصطناعي"
  website: "https://arabianaischool.com"
  version: "1.0.0"
---

# Depth UI reel (UI behind your head)

The speaker stays in front, cut out from their background, and a real UI (a channel page, a website, an app, a dashboard) moves slowly behind them. Captions run at the bottom. It makes a plain talking head feel designed.

**What the user gives you:** A talking-head video (any orientation, a clear outline of the person helps) and one or more backgrounds: screenshots or screen recordings of what they talk about.

## Setup (check once per machine)

Everything runs on the user's computer with `scripts/reelkit.py` (one Python file in this skill's folder) and ffmpeg.
`scripts/...` below always means the `scripts` folder **inside this skill's folder** (for example
`~/.claude/skills/<this-skill>/scripts/reelkit.py`): call it by that full path while you work in the user's folder.
1. `python scripts/reelkit.py probe <video>` must print the size and duration. If ffmpeg is missing, tell the user:
   Windows `winget install Gyan.FFmpeg`, Mac `brew install ffmpeg`, then open a new terminal.
2. `pip install faster-whisper` (word timings for captions and clean cuts).
3. `pip install mediapipe` (cuts the person out; downloads a 250 KB model on first use).

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

1. Ask only for what is missing: the video, the background(s) and the format (default 9:16).
2. Transcribe and proofread (above).
3. `python scripts/reelkit.py faces <video> -o work/faces.json` and
   `python scripts/reelkit.py matte <video> -o work/mask.mp4` (the cut-out mask, same length as the video).
4. Write `work/plan.json` with `"matte": "mask.mp4"` and `"faces": "faces.json"`:
   - `depth` segments for the moments the background matters (`"background": "../assets/channel.png"`), each with
     a slow push (`"background_zoom": [1.0, 1.06]`). Change the background when the topic changes.
   - `full` segments in between (alternate `zoom` 1.0 and 1.12) so it never feels static.
   - A `title` on the first segment: the hook in 2 to 5 words.
   - Cut silences and stumbles by leaving gaps between segments (word boundaries from `words.json`).
5. `python scripts/reelkit.py render work/plan.json -o depth_reel.mp4`
6. Look at a frame from each `depth` segment: the edge around hair and shoulders should be clean. If the mask
   flickers, run `matte` again with `--smooth 0.75`. If the person was missed in some frames, use `full` there.

Tips: busy UI behind a busy shirt is hard to read; prefer clean pages, and scroll positions where the important part
sits beside the head, not behind it.

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
