"""Clips inbox pipeline: turns externally generated clips (e.g. Google Flow) into ready Shorts.

Drop files into  clips_inbox/  :
    my_clip.mp4              the generated clip (any size; output is 1080x1920 vertical)
    my_clip.ar.txt           Arabic script: FIRST line = title/caption, the rest = voiceover text
    my_clip.en.txt           English script (same format)
Either language is optional; a language without a script file is skipped.

For every clip + language the tool produces  clips_ready/<name>_<lang>.mp4  with a neural voiceover
(edge-tts, free), the clip's own audio ducked underneath, and word-timed karaoke subtitles.
Nothing is published here. Publishing requests are put in the approval queue, ONE per platform per
video, so each platform is approved (or rejected) separately with the usual buttons.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import imageio_ffmpeg

import memory
from tools import video_autocaption, voice_studio

log = logging.getLogger("clips_pipeline")

BASE_DIR = Path(__file__).resolve().parent.parent
INBOX = BASE_DIR / "clips_inbox"
READY = BASE_DIR / "clips_ready"
DONE = INBOX / "_done"
for _d in (INBOX, READY, DONE):
    _d.mkdir(parents=True, exist_ok=True)

VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv"}
LANGS = {
    "ar": {"voice": "ar_male_egypt", "label": "عربي", "tag": "#Shorts"},
    "en": {"voice": "en_male_tech", "label": "English", "tag": "#Shorts"},
}
TIME_BUDGET_S = 120  # stop starting new work after this (tool timeout is 180 s)


def _ffmpeg() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def _probe(path: Path) -> tuple[float, bool]:
    """Returns (duration_seconds, has_audio) by parsing ffmpeg's banner."""
    res = subprocess.run([_ffmpeg(), "-i", str(path)], capture_output=True, text=True, errors="replace")
    err = res.stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", err)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0
    return dur, "Audio:" in err


def _read_script(path: Path) -> tuple[str, str] | None:
    """Returns (title, script) from a sidecar file, or None when missing/empty."""
    if not path.exists():
        return None
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    lines = [ln for ln in lines if ln]
    if not lines:
        return None
    if len(lines) == 1:
        return lines[0][:90], lines[0]
    return lines[0][:90], " ".join(lines[1:])


def _words_for_subtitles(script: str, voice_dur: float) -> list[dict[str, Any]]:
    """Word timings proportional to word length across the voiceover (no network needed)."""
    words = [w for w in script.split() if w]
    if not words:
        return []
    start0, usable = 0.15, max(0.5, voice_dur - 0.15)
    weights = [len(w) + 2 for w in words]
    total = float(sum(weights))
    out, t = [], start0
    for w, wt in zip(words, weights):
        d = usable * wt / total
        out.append({"word": w, "start": t, "end": t + d})
        t += d
    return out


async def _render(clip: Path, voice_mp3: Path, ass_path: Path, out_path: Path) -> None:
    vid_dur, has_audio = _probe(clip)
    voice_dur, _ = _probe(voice_mp3)
    total = max(vid_dur, voice_dur + 0.4)
    pad = max(0.0, total - vid_dur)
    ass_esc = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")

    vf = (
        "[0:v]split=2[a][b];"
        "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
        "[b]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,tpad=stop_mode=clone:stop_duration={pad:.2f},"
        f"ass='{ass_esc}'[v]"
    )
    if has_audio:
        af = "[0:a]volume=0.25[a0];[1:a]volume=1.0[a1];[a0][a1]amix=inputs=2:duration=longest,volume=2[a]"
    else:
        af = "[1:a]anull[a]"
    cmd = [
        _ffmpeg(), "-y", "-i", str(clip), "-i", str(voice_mp3),
        "-filter_complex", f"{vf};{af}",
        "-map", "[v]", "-map", "[a]",
        "-t", f"{total:.2f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
        str(out_path),
    ]
    proc = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, errors="replace")
    if proc.returncode != 0 or not out_path.exists():
        raise RuntimeError(f"FFmpeg failed: {proc.stderr[-500:]}")


async def _make_version(clip: Path, lang: str, title: str, script: str) -> Path:
    cfg = LANGS[lang]
    voice_mp3 = await voice_studio.generate_speech(script, voice_key=cfg["voice"])
    voice_dur, _ = _probe(voice_mp3)
    words = _words_for_subtitles(script, voice_dur)
    ass = video_autocaption.build_ass_karaoke(words, words_per_phrase=4)
    ts = int(time.time())
    ass_path = video_autocaption.CACHE_DIR / f"clip_{clip.stem}_{lang}_{ts}.ass"
    ass_path.write_text(ass, encoding="utf-8")
    out = READY / f"{clip.stem}_{lang}.mp4"
    try:
        await _render(clip, voice_mp3, ass_path, out)
    finally:
        try:
            ass_path.unlink()
        except Exception:
            pass
    (READY / f"{clip.stem}_{lang}.json").write_text(
        json.dumps({"title": title, "lang": lang, "source": clip.name}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return out


def _queue_publish(video: Path, lang: str, title: str, platforms: list[str]) -> list[int]:
    """Puts ONE approval item per platform in the queue. Publishing happens only after the user's button."""
    ids: list[int] = []
    label = LANGS[lang]["label"]
    if "tiktok" in platforms:
        ids.append(memory.add_approval_item(
            "tiktok_upload_video",
            f"نشر على TikTok ({label}): {title}",
            {"video_path": str(video), "caption": title, "tags": ["fyp"]},
        ))
    if "youtube" in platforms:
        ids.append(memory.add_approval_item(
            "youtube_upload_video",
            f"نشر على YouTube Shorts ({label}): {title}",
            {"video_path": str(video), "title": title[:95],
             "description": f"{title}\n\n{LANGS[lang]['tag']}", "privacy": "public", "is_short": True},
        ))
    return ids


async def _handle_process(args: dict[str, Any]) -> str:
    platforms = [p.lower() for p in (args.get("platforms") or ["tiktok", "youtube"])]
    queue = args.get("queue_publish", True)
    max_clips = int(args.get("max_clips") or 2)

    clips = sorted(p for p in INBOX.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXT)
    if not clips:
        return (f"📂 المجلد فارغ: `{INBOX}`\n"
                "ضع فيه المقطع (mp4) ومعه ملف نص لكل لغة: `اسم.ar.txt` و`اسم.en.txt` "
                "(السطر الأول عنوان، وباقي الملف نص التعليق الصوتي).")

    started = time.time()
    report: list[str] = []
    handled = 0
    for clip in clips:
        if handled >= max_clips or time.time() - started > TIME_BUDGET_S:
            break
        scripts = {lg: _read_script(INBOX / f"{clip.stem}.{lg}.txt") for lg in LANGS}
        if not any(scripts.values()):
            report.append(f"⚠️ `{clip.name}`: لا يوجد ملف نص (`{clip.stem}.ar.txt` أو `{clip.stem}.en.txt`). تجاوزته.")
            continue
        handled += 1
        made = 0
        for lg, sc in scripts.items():
            if not sc:
                continue
            title, script = sc
            try:
                out = await _make_version(clip, lg, title, script)
                made += 1
                line = f"✅ {LANGS[lg]['label']}: `{out.name}`"
                if queue:
                    ids = _queue_publish(out, lg, title, platforms)
                    line += f" — طلبات موافقة: {', '.join('#' + str(i) for i in ids)}"
                report.append(line)
            except Exception as e:  # noqa: BLE001
                log.exception("Clip %s (%s) failed", clip.name, lg)
                report.append(f"❌ {LANGS[lg]['label']} للمقطع `{clip.name}`: {str(e)[:200]}")
        if made:
            for f in [clip] + [INBOX / f"{clip.stem}.{lg}.txt" for lg in LANGS]:
                if f.exists():
                    shutil.move(str(f), str(DONE / f.name))

    left = len([p for p in INBOX.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXT])
    head = "🎬 **نتيجة تجهيز المقاطع:**\n"
    tail = f"\n\n📥 متبقي في المجلد: {left} مقطع" if left else ""
    if queue and any("طلبات موافقة" in r for r in report):
        tail += "\n⚠️ لم يُنشر شيء بعد. كل منصة لها زر ✅/❌ خاص بها."
    return head + "\n".join(report) + tail


TOOLS = [
    {
        "name": "process_video_clips_inbox",
        "description": (
            "يجهّز مقاطع الفيديو الموجودة في مجلد clips_inbox (مثل مقاطع Google Flow): يضيف تعليقاً صوتياً "
            "وترجمة متحركة بالعربية و/أو الإنجليزية بحجم عمودي 1080x1920، ثم يضع طلب موافقة منفصلاً "
            "لكل منصة (TikTok و YouTube). لا ينشر شيئاً قبل ضغط أدهم على زر الاعتماد."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "platforms": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["tiktok", "youtube"]},
                    "description": "المنصات المطلوب طلب نشر لها (افتراضياً الاثنتان)",
                },
                "queue_publish": {"type": "boolean", "description": "ضع طلبات النشر في طابور الموافقات (افتراضياً نعم)"},
                "max_clips": {"type": "integer", "description": "أقصى عدد مقاطع في المرة الواحدة (افتراضياً 2)"},
            },
        },
        "handler": _handle_process,
    }
]
