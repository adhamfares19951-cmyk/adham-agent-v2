---
name: personal-broll-library
description: "Catalogue the user's own B-roll folder once, then find clips by describing them in plain words, Arabic or English ('me typing at night', 'لقطة للمكتب'). Use when the user wants to organise or search their B-roll, find a clip, /personal-broll-library, or in Arabic 'دورلي على لقطة' or 'رتّب البي رول'."
metadata:
  author: "مدرسة الذكاء الاصطناعي"
  website: "https://arabianaischool.com"
  version: "1.0.0"
---

# Personal B-roll library

Builds a searchable index of a B-roll folder: every clip gets a contact sheet, size, length and orientation, and you write a short description and tags for it by looking at the sheets. After that the user finds clips by describing them.

**What the user gives you:** A folder of clips and photos.

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


## Workflow

**Build or update the library**
1. `python scripts/reelkit.py index <folder> -o <folder>/broll_index.json`
   It writes one contact sheet per clip in `broll_sheets/` and keeps descriptions you already wrote (run it again
   after adding clips; only new clips need work).
2. Open each new sheet and fill in `description` (one sentence: what is in the shot, place, action, light, mood) and
   `tags` (5 to 10 words) in `broll_index.json`. Write both Arabic and English words so either language finds it.
   Use what you see; never guess names of people or places you cannot see.
3. Tell the user how many clips are indexed and anything odd (very short clips, duplicates, vertical vs horizontal).

**Find clips**
1. `python scripts/reelkit.py search <folder>/broll_index.json "شخص بيكتب على لابتوب بالليل"`
   (`--orientation vertical` for reels). It matches words in descriptions, tags and file names, Arabic or English.
2. Then judge the results yourself: open their sheets, and also read the index for matches that use other words.
3. Answer with the best 3 to 5 clips: file, why it fits, the best moment (from the sheet timestamps), orientation.

The index is plain JSON, so the other video skills in this pack (personal and business reels) use it directly.

## Rules
- Use only the user's own footage, words and assets. Never invent quotes, numbers, names or claims.
- Talk to the user in their language (Arabic if they write in Arabic). Captions follow the language spoken.
- Ask at most one round of questions, only for what you cannot work out; otherwise make sensible choices and say which.

## Credits

Made and maintained by **مدرسة الذكاء الاصطناعي** (Arabian AI School), © 2026.
Website https://arabianaischool.com/skills/claude-video-skills/ · YouTube https://www.youtube.com/@ArabianAiSchool ·
Instagram https://www.instagram.com/arabianaischool · Facebook https://www.facebook.com/arabianaischool · X https://x.com/arabianaischool

Free to use in your own and client videos. Please don't resell or re-upload the pack as your own.
