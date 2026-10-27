#!/usr/bin/env python3
"""reelkit: the editing engine behind the video skills in this pack.

One file, no install beyond Python 3.9+ and ffmpeg. Optional extras switch on
features when present:
  faster-whisper          transcribe (word timings for captions and cuts)
  mediapipe               faces (keep the speaker centred when cropping to 9:16)
                          and matte (cut the speaker out for UI-behind-the-head)

Commands (run `python reelkit.py <command> -h` for options):
  probe      <media>                       size, fps, duration, audio
  transcribe <media> -o words.json         word-level transcript (any language, Arabic included)
  silences   <media> -o keep.json          the parts where someone is talking
  faces      <video> -o faces.json         where the speaker's head is over time
  matte      <video> -o mask.mp4           a black/white mask of the person, frame by frame
  render     <plan.json> -o out.mp4        cut, lay out, zoom, caption and mix a video from an edit plan
  srt        <words.json> -o out.srt       subtitles file (optionally retimed through a plan)
  sheet      <video> -o sheet.jpg          contact sheet of thumbnails, to look at a clip quickly
  index      <folder> -o broll_index.json  catalogue a B-roll folder (with contact sheets)
  search     <broll_index.json> "words"    find B-roll by description, Arabic or English

The edit plan format is documented in PLAN.md next to this file.
Made by مدرسة الذكاء الاصطناعي (Arabian AI School) · https://arabianaischool.com
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
from pathlib import Path

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".mts"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}


def die(msg: str) -> None:
    sys.exit(f"reelkit: {msg}")


def need(tool: str) -> None:
    if not shutil.which(tool):
        die(f"{tool} is not installed or not on PATH (Windows: winget install Gyan.FFmpeg, Mac: brew install ffmpeg)")


def run(cmd: list, quiet: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        tail = "\n".join(r.stderr.strip().splitlines()[-15:])
        die(f"command failed: {' '.join(map(str, cmd[:6]))} ...\n{tail}")
    return r


# ----------------------------------------------------------------------------- probe
def probe(path: str) -> dict:
    need("ffprobe")
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,width,height,r_frame_rate,sample_rate,channels",
             "-of", "json", path])
    data = json.loads(r.stdout)
    info = {"path": path, "duration": float(data.get("format", {}).get("duration") or 0), "video": None, "audio": None}
    for s in data.get("streams", []):
        if s.get("codec_type") == "video" and not info["video"]:
            num, den = (s.get("r_frame_rate") or "0/1").split("/")
            fps = float(num) / float(den) if float(den) else 0
            info["video"] = {"width": s["width"], "height": s["height"], "fps": round(fps, 3)}
        if s.get("codec_type") == "audio" and not info["audio"]:
            info["audio"] = {"sample_rate": int(s.get("sample_rate") or 0), "channels": s.get("channels")}
    return info


# ----------------------------------------------------------------------------- transcribe
def transcribe(media: str, out: str, model: str = "small", lang: str | None = None, prompt: str | None = None) -> dict:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        die("transcribe needs faster-whisper: pip install faster-whisper")
    device, compute = "cpu", "int8"
    try:
        import torch  # optional, only to detect a GPU
        if torch.cuda.is_available():
            device, compute = "cuda", "float16"
    except Exception:
        pass
    print(f"loading whisper '{model}' on {device} (first run downloads the model)...", flush=True)
    wm = WhisperModel(model, device=device, compute_type=compute)
    segments, info = wm.transcribe(media, language=lang, word_timestamps=True, vad_filter=True,
                                   initial_prompt=prompt, beam_size=5)
    words, lines = [], []
    for seg in segments:
        lines.append({"start": round(seg.start, 3), "end": round(seg.end, 3), "text": seg.text.strip()})
        for w in seg.words or []:
            text = w.word.strip()
            if text:
                words.append({"w": text, "start": round(w.start, 3), "end": round(w.end, 3)})
        print(f"\r  {seg.end:7.1f}s transcribed", end="", flush=True)
    print()
    result = {"language": info.language, "duration": round(info.duration, 3), "words": words, "segments": lines}
    Path(out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {out}: {len(words)} words, language={info.language}")
    return result


# ----------------------------------------------------------------------------- silences
def silences(media: str, out: str, noise: str = "-32dB", min_silence: float = 0.45, pad: float = 0.12,
             min_keep: float = 0.25) -> list:
    need("ffmpeg")
    dur = probe(media)["duration"]
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", media, "-af",
                        f"silencedetect=noise={noise}:d={min_silence}", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    if len(ends) < len(starts):
        ends.append(dur)
    keep, cursor = [], 0.0
    for s, e in zip(starts, ends):
        if s - cursor > 0:
            keep.append([max(0.0, cursor - pad), min(dur, s + pad)])
        cursor = e
    if dur - cursor > 0:
        keep.append([max(0.0, cursor - pad), dur])
    merged = []
    for a, b in keep:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    merged = [[round(a, 3), round(b, 3)] for a, b in merged if b - a >= min_keep]
    talk = sum(b - a for a, b in merged)
    Path(out).write_text(json.dumps({"source": media, "duration": dur, "keep": merged}, indent=1), encoding="utf-8")
    print(f"wrote {out}: {len(merged)} talking parts, {talk:.1f}s of {dur:.1f}s kept")
    return merged


# ----------------------------------------------------------------------------- faces
def load_segmenter():
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision
    except ImportError:
        die("this command needs mediapipe: pip install mediapipe")
    cache = Path.home() / ".cache" / "reelkit"
    cache.mkdir(parents=True, exist_ok=True)
    model = cache / "selfie_segmenter.tflite"
    if not model.exists():
        print("downloading the person-segmentation model (250 KB, once)...")
        urllib.request.urlretrieve(SELFIE_MODEL, model)
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=str(model)), running_mode=vision.RunningMode.IMAGE,
        output_confidence_masks=True))

    def run_mask(rgb):
        import numpy as np
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        m = seg.segment(img).confidence_masks[0].numpy_view()
        return m.reshape(rgb.shape[0], rgb.shape[1]).astype("float32")

    return run_mask


def frames_rgb(video: str, width: int, fps: float | None = None):
    """Yield (time, HxWx3 uint8) frames scaled to `width`, optionally resampled to `fps`."""
    import numpy as np
    info = probe(video)
    W, H = info["video"]["width"], info["video"]["height"]
    rate = fps or info["video"]["fps"] or 30
    w = min(width, W)
    h = int(round(H * w / W / 2) * 2)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={rate},scale={w}:{h}",
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n, size = 0, w * h * 3
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        yield n / rate, np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        n += 1
    proc.wait()


def faces(video: str, out: str, step: float = 0.5) -> dict:
    """Where the speaker's head is over time, from the person mask (top of the silhouette)."""
    import numpy as np
    run_mask = load_segmenter()
    info = probe(video)
    samples = []
    for t, rgb in frames_rgb(video, 384, 1 / step):
        m = run_mask(rgb) > 0.5
        rows = np.where(m.any(axis=1))[0]
        if len(rows) < 4:
            continue
        top, bottom = rows[0], rows[-1]
        head = m[top: top + max(2, int((bottom - top) * 0.25))]
        cols = np.where(head.any(axis=0))[0]
        if not len(cols):
            continue
        h, w = m.shape
        cx = float(np.mean(np.where(head)[1])) / w
        cy = (top + (bottom - top) * 0.12) / h
        samples.append({"t": round(t, 2), "cx": round(cx, 4), "cy": round(float(cy), 4),
                        "size": round(len(cols) / w, 4)})
    data = {"source": video, "width": info["video"]["width"], "height": info["video"]["height"], "samples": samples}
    Path(out).write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"wrote {out}: speaker found in {len(samples)} samples")
    return data


def face_focus(faces_data: dict | None, a: float, b: float, default=(0.5, 0.42)) -> tuple:
    if not faces_data:
        return default
    pts = [s for s in faces_data.get("samples", []) if a - 0.25 <= s["t"] <= b + 0.25]
    if not pts:
        pts = faces_data.get("samples", [])
    if not pts:
        return default
    xs = sorted(p["cx"] for p in pts)
    ys = sorted(p["cy"] for p in pts)
    return (xs[len(xs) // 2], ys[len(ys) // 2])


# ----------------------------------------------------------------------------- matte
SELFIE_MODEL = "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite"


def matte(video: str, out: str, smooth: float = 0.6, work_width: int = 640) -> None:
    """A grayscale video, white where the person is, same size and length as the source."""
    need("ffmpeg")
    import numpy as np
    run_mask = load_segmenter()
    info = probe(video)
    W, H, fps = info["video"]["width"], info["video"]["height"], info["video"]["fps"] or 30
    writer = None
    prev, n = None, 0
    for _, rgb in frames_rgb(video, work_width):
        h, w = rgb.shape[:2]
        if writer is None:
            writer = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray",
                                       "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
                                       "-vf", f"scale={W}:{H}:flags=bicubic,format=gray",
                                       "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out],
                                      stdin=subprocess.PIPE)
        m = run_mask(rgb)
        if prev is not None and smooth:  # temporal smoothing hides edge flicker
            m = smooth * prev + (1 - smooth) * m
        prev = m
        writer.stdin.write((np.clip((m - 0.35) / 0.3, 0, 1) * 255).astype(np.uint8).tobytes())
        n += 1
        if n % int(fps) == 0:
            print(f"\r  {n / fps:6.1f}s masked", end="", flush=True)
    if writer is None:
        die("could not read any frame from the video")
    writer.stdin.close()
    writer.wait()
    print(f"\nwrote {out}: {n} frames")


# ----------------------------------------------------------------------------- ASS helpers
ARABIC = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")


def ass_color(hex_color: str, alpha: int = 0) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def ass_time(t: float) -> str:
    t = max(0.0, t)
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def ass_header(W: int, H: int, cap: dict) -> str:
    # Encoding -1 = libass lays out the whole line as one bidi paragraph. Without it,
    # every colour tag restarts right-to-left ordering and Arabic words come out scrambled.
    font = cap.get("font", "Cairo")
    size = int(cap.get("size", round(H * 0.045)))
    outline = cap.get("outline", max(3, size // 12))
    tfont = cap.get("title_font", font)
    tsize = int(cap.get("title_size", round(H * (0.05 if H > W else 0.085))))
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},{size},{ass_color(cap.get('color', '#FFFFFF'))},&H000000FF,{ass_color(cap.get('outline_color', '#000000'))},&H64000000,-1,0,0,0,100,100,0,0,1,{outline},{cap.get('shadow', 2)},5,40,40,0,-1
Style: Title,{tfont},{tsize},{ass_color(cap.get('title_color', '#FFFFFF'))},&H000000FF,{ass_color(cap.get('title_box', '#111111'))},&H00000000,-1,0,0,0,100,100,0,0,3,{max(10, tsize // 4)},0,5,60,60,0,-1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def group_words(words: list, per_line: int = 3, max_gap: float = 0.45, max_chars: int = 22) -> list:
    groups, cur = [], []
    for w in words:
        if cur and (len(cur) >= per_line or w["start"] - cur[-1]["end"] > max_gap
                    or sum(len(x["w"]) + 1 for x in cur) + len(w["w"]) > max_chars
                    or re.search(r"[.!?؟،,:;]$", cur[-1]["w"])):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    return groups


def caption_events(words: list, W: int, H: int, cap: dict) -> list:
    """One Dialogue line per spoken word: the whole group shows, the current word is highlighted."""
    if not words:
        return []
    y = int(H * float(cap.get("position", 0.78)))
    hi = ass_color(cap.get("highlight", "#FFE066"))
    base = ass_color(cap.get("color", "#FFFFFF"))
    upper = cap.get("uppercase", False)
    style = cap.get("style", "word")  # word = highlight the spoken word, line = plain line
    events = []
    groups = group_words(words, int(cap.get("words_per_line", 3)), float(cap.get("max_gap", 0.45)),
                         int(cap.get("max_chars", 22)))
    for k, g in enumerate(groups):
        texts = [ass_escape(x["w"].upper() if upper else x["w"]) for x in g]
        g_start = g[0]["start"]
        # hold the line a moment after the last word, but never into the next line
        nxt = groups[k + 1][0]["start"] if k + 1 < len(groups) else math.inf
        g_end = min(g[-1]["end"] + 0.05, nxt) - 0.05
        pop = "{\\fscx92\\fscy92\\t(0,90,\\fscx100\\fscy100)}"
        if style == "line":
            events.append(f"Dialogue: 1,{ass_time(g_start)},{ass_time(g_end + 0.05)},Cap,,0,0,0,,{{\\an5\\pos({W // 2},{y})}}{pop}{' '.join(texts)}")
            continue
        for i, w in enumerate(g):
            a = w["start"] if i else g_start
            b = g[i + 1]["start"] if i + 1 < len(g) else g_end + 0.05
            if b <= a:
                continue
            parts = [f"{{\\c{hi}}}{t}{{\\c{base}}}" if j == i else t for j, t in enumerate(texts)]
            first = pop if i == 0 else ""
            events.append(f"Dialogue: 1,{ass_time(a)},{ass_time(b)},Cap,,0,0,0,,{{\\an5\\pos({W // 2},{y})}}{first}{' '.join(parts)}")
    return events


def title_event(text: str, a: float, b: float, W: int, H: int, pos: str = "top") -> str:
    y = {"top": int(H * 0.115), "center": H // 2, "bottom": int(H * 0.62)}.get(pos, int(H * 0.115))
    anim = "{\\fad(120,120)\\fscx80\\fscy80\\t(0,160,\\fscx104\\fscy104)\\t(160,260,\\fscx100\\fscy100)}"
    return f"Dialogue: 2,{ass_time(a)},{ass_time(b)},Title,,0,0,0,,{{\\an5\\pos({W // 2},{y})}}{anim}{ass_escape(text)}"


# ----------------------------------------------------------------------------- render
def even(x: float) -> int:
    return max(2, int(round(x / 2)) * 2)


def cover(src_w, src_h, W, H, fx=0.5, fy=0.5, zoom=1.0) -> str:
    """scale+crop so the source fills WxH, centred on (fx, fy) in source coordinates."""
    s = max(W / src_w, H / src_h) * zoom
    sw, sh = even(src_w * s), even(src_h * s)
    x = min(max(fx * sw - W / 2, 0), sw - W)
    y = min(max(fy * sh - H / 2, 0), sh - H)
    return f"scale={sw}:{sh}:flags=lanczos,crop={W}:{H}:{int(x)}:{int(y)},setsar=1"


def animated_cover(src_w, src_h, W, H, fx, fy, z0, z1, frames, fps) -> str:
    """Smooth push-in/out: cover at 2x, then zoompan down to WxH (half-pixel precision)."""
    W2, H2 = W * 2, H * 2
    base = cover(src_w, src_h, W2, H2, fx, fy, 1.0)
    n = max(1, frames - 1)
    z = f"({z0}+({z1}-{z0})*on/{n})"
    return (f"{base},zoompan=z='{z}':x='(iw-iw/zoom)*{fx:.4f}':y='(ih-ih/zoom)*{fy:.4f}':d=1:s={W}x{H}:fps={fps},setsar=1")


def media_input(path: str, start: float = 0.0, dur: float | None = None, loop_image: bool = True) -> list:
    ext = Path(path).suffix.lower()
    if ext in IMAGE_EXT:
        args = ["-loop", "1", "-framerate", "30"] if loop_image else []
        return args + (["-t", f"{dur:.3f}"] if dur else []) + ["-i", path]
    args = ["-ss", f"{start:.3f}"] if start else []
    return args + (["-t", f"{dur:.3f}"] if dur else []) + ["-i", path]


def atempo_chain(speed: float) -> str:
    parts, s = [], speed
    while s > 2.0:
        parts.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        parts.append("atempo=0.5")
        s /= 0.5
    parts.append(f"atempo={s:.4f}")
    return ",".join(parts)


def render_segment(i: int, seg: dict, plan: dict, src: dict, faces_data, tmp: Path, base: Path) -> tuple:
    W, H = plan["canvas"]
    fps = plan.get("fps", 30)
    source = plan["source"]
    a, b = float(seg["start"]), float(seg["end"])
    speed = float(seg.get("speed", 1.0))
    dur = b - a
    out_dur = dur / speed
    frames = max(1, int(round(out_dur * fps)))
    sw, sh = src["video"]["width"], src["video"]["height"]
    layout = seg.get("layout", "full")
    focus = seg.get("focus", "auto")
    fx, fy = face_focus(faces_data, a, b) if focus == "auto" else tuple(focus)
    zoom = seg.get("zoom", 1.0)
    p = lambda f: str((base / f).resolve()) if not os.path.isabs(f) else f  # noqa: E731

    inputs = ["-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", source]
    speed_v = f",setpts=PTS/{speed}" if speed != 1 else ""

    def speaker(Wt, Ht, label="spk"):
        if isinstance(zoom, list):
            f = animated_cover(sw, sh, Wt, Ht, fx, fy, zoom[0], zoom[1], frames, fps)
        else:
            f = cover(sw, sh, Wt, Ht, fx, fy, float(zoom))
        return f"[0:v]fps={fps}{speed_v},{f}[{label}]"

    def asset_chain(idx, path, Wt, Ht, start=0.0, fit="cover", az=None):
        info = probe(p(path))
        aw, ah = info["video"]["width"], info["video"]["height"]
        if fit == "contain":
            s = min(Wt / aw, Ht / ah)
            f = f"scale={even(aw * s)}:{even(ah * s)}:flags=lanczos,pad={Wt}:{Ht}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
        elif az:
            f = animated_cover(aw, ah, Wt, Ht, 0.5, 0.5, az[0], az[1], frames, fps)
        else:
            f = cover(aw, ah, Wt, Ht, 0.5, 0.5, 1.0)
        return f"[{idx}:v]fps={fps},trim=duration={out_dur:.3f},setpts=PTS-STARTPTS,{f}"

    chains = []
    if layout == "full":
        chains.append(speaker(W, H, "v"))
    elif layout == "broll":
        inputs += media_input(p(seg["broll"]), float(seg.get("broll_start", 0)), out_dur + 0.5)
        chains.append(asset_chain(1, seg["broll"], W, H, az=seg.get("broll_zoom")) + "[v]")
    elif layout == "split":
        ratio = float(seg.get("ratio", 0.5))
        top_h = even(H * ratio)
        inputs += media_input(p(seg["top"]), float(seg.get("top_start", 0)), out_dur + 0.5)
        chains.append(asset_chain(1, seg["top"], W, top_h, fit=seg.get("top_fit", "cover"), az=seg.get("top_zoom")) + "[top]")
        chains.append(speaker(W, H - top_h, "bot"))
        order = "[bot][top]" if seg.get("speaker_on_top") else "[top][bot]"
        chains.append(f"{order}vstack=inputs=2[v]")
    elif layout == "screen":
        rect = seg.get("zoom_rect")
        crop = f"crop={int(rect[2])}:{int(rect[3])}:{int(rect[0])}:{int(rect[1])}," if rect else ""
        cw, ch = (rect[2], rect[3]) if rect else (sw, sh)
        s = min(W / cw, H / ch)
        fg = f"scale={even(cw * s)}:{even(ch * s)}:flags=lanczos"
        bg = f"{cover(cw, ch, W, H)},boxblur=30:3,eq=brightness=-0.12"
        chains.append(f"[0:v]fps={fps}{speed_v},{crop}split[s1][s2]")
        chains.append(f"[s1]{bg}[bg]")
        chains.append(f"[s2]{fg}[fg]")
        chains.append("[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[v]")
    elif layout == "depth":
        inputs += media_input(p(seg["background"]), float(seg.get("background_start", 0)), out_dur + 0.5)
        inputs += ["-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", p(seg.get("matte") or plan["matte"])]
        bgz = seg.get("background_zoom", [1.0, 1.06])
        chains.append(asset_chain(1, seg["background"], W, H, az=bgz) + "[bg]")
        sz = zoom if not isinstance(zoom, list) else zoom[0]
        chains.append(f"[0:v]fps={fps}{speed_v},{cover(sw, sh, W, H, fx, fy, float(sz))},format=rgba[fg]")
        chains.append(f"[2:v]fps={fps}{speed_v},{cover(sw, sh, W, H, fx, fy, float(sz))},format=gray[m]")
        chains.append("[fg][m]alphamerge[cut]")
        chains.append("[bg][cut]overlay=0:0:format=auto,setsar=1[v]")
    elif layout == "card":
        color = seg.get("color", plan.get("_card_color", "#111111")).lstrip("#")
        if seg.get("background"):
            inputs += media_input(p(seg["background"]), 0, out_dur + 0.5)
            chains.append(asset_chain(1, seg["background"], W, H) + ",boxblur=24:2,eq=brightness=-0.18[v]")
        elif seg.get("blur_speaker", True):
            chains.append(f"[0:v]fps={fps}{speed_v},{cover(sw, sh, W, H, fx, fy)},boxblur=30:3,eq=brightness=-0.2[v]")
        else:
            inputs += ["-f", "lavfi", "-t", f"{out_dur:.3f}", "-i", f"color=c=0x{color}:s={W}x{H}:r={fps}"]
            chains.append("[1:v]setsar=1[v]")
    else:
        die(f"segment {i}: unknown layout '{layout}' (full, broll, split, screen, depth, card)")

    chains.append(f"[v]trim=end_frame={frames},format=yuv420p[vout]")
    if src["audio"] and not seg.get("mute"):
        chains.append(f"[0:a]aresample=48000,{atempo_chain(speed) if speed != 1 else 'anull'},"
                      f"apad,atrim=duration={frames / fps:.4f},afade=t=in:d=0.015,"
                      f"afade=t=out:st={max(0, frames / fps - 0.02):.4f}:d=0.02[aout]")
        amap = ["-map", "[aout]"]
    else:
        inputs += ["-f", "lavfi", "-t", f"{frames / fps:.4f}", "-i", "anullsrc=r=48000:cl=stereo"]
        amap = ["-map", f"{inputs.count('-i') - 1}:a"]
    out = tmp / f"seg_{i:03d}.mp4"
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chains), "-map", "[vout]", *amap,
         "-r", str(fps), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(out)])
    return out, frames / fps


def retime_words(words: list, segments: list, fps: int = 30) -> list:
    """Map source-time words onto output time through the plan's segments."""
    out, cursor = [], 0.0
    for seg in segments:
        a, b, sp = float(seg["start"]), float(seg["end"]), float(seg.get("speed", 1.0))
        length = round((b - a) / sp * fps) / fps
        if not seg.get("no_captions"):
            for w in words:
                mid = (w["start"] + w["end"]) / 2
                if a <= mid < b:
                    s = cursor + max(0.0, w["start"] - a) / sp
                    e = cursor + min(b - a, w["end"] - a) / sp
                    out.append({"w": w["w"], "start": round(s, 3), "end": round(max(e, s + 0.05), 3)})
        cursor += length
    return out


SKILL_FONTS = Path(__file__).resolve().parent.parent / "fonts"  # Cairo ships with every skill


def load_brand(plan: dict, base: Path) -> dict:
    """brand.json holds the user's own look. It fills the caption/title style; the plan can still override."""
    ref = plan.get("brand")
    if not ref:
        return {}
    path = Path(ref) if os.path.isabs(ref) else base / ref
    if not path.exists():
        die(f"brand file not found: {path}")
    b = json.loads(path.read_text(encoding="utf-8"))
    style = {k: v for k, v in {
        "font": b.get("font"),
        "title_font": b.get("title_font"),
        "fonts_dir": (str((path.parent / b["fonts_dir"]).resolve()) if b.get("fonts_dir") else None),
        "color": b.get("text"),
        "highlight": b.get("highlight"),
        "title_box": b.get("accent"),
        "title_color": b.get("accent_text"),
        "outline_color": b.get("outline"),
    }.items() if v}
    if b.get("background"):
        plan["_card_color"] = b["background"]
    return style


def render(plan_path: str, out: str, keep_temp: bool = False) -> None:
    need("ffmpeg")
    base = Path(plan_path).resolve().parent
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    plan.setdefault("canvas", [1080, 1920])
    plan.setdefault("fps", 30)
    if not os.path.isabs(plan["source"]):
        plan["source"] = str((base / plan["source"]).resolve())
    if plan.get("matte") and not os.path.isabs(plan["matte"]):
        plan["matte"] = str((base / plan["matte"]).resolve())
    brand_style = load_brand(plan, base)
    src = probe(plan["source"])
    if not src["video"]:
        die("the plan's source has no video stream")
    W, H = plan["canvas"]
    fps = plan["fps"]
    segs = plan.get("segments") or [{"start": 0, "end": src["duration"], "layout": "full"}]
    faces_data = None
    if plan.get("faces"):
        faces_data = json.loads((base / plan["faces"]).read_text(encoding="utf-8"))
    tmp = Path(tempfile.mkdtemp(prefix="reelkit_"))
    try:
        parts, timeline = [], 0.0
        events = []
        for i, seg in enumerate(segs):
            print(f"\rsegment {i + 1}/{len(segs)} ({seg.get('layout', 'full')})", end="", flush=True)
            path, length = render_segment(i, seg, plan, src, faces_data, tmp, base)
            parts.append(path)
            if seg.get("title"):
                events.append(title_event(seg["title"], timeline + 0.05, timeline + length - 0.05, W, H,
                                          seg.get("title_pos", "top" if seg.get("layout") != "card" else "center")))
            timeline += length
        print()
        concat = tmp / "list.txt"
        concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
        joined = tmp / "joined.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", concat, "-c", "copy", joined])

        cap = {**brand_style, **plan.get("captions", {})}
        if cap.get("enabled", True) and plan.get("words"):
            wpath = plan["words"] if os.path.isabs(plan["words"]) else base / plan["words"]
            words = json.loads(Path(wpath).read_text(encoding="utf-8"))["words"]
            events += caption_events(retime_words(words, segs, fps), W, H, cap)
        for t in plan.get("titles", []):
            events.append(title_event(t["text"], float(t["start"]), float(t["end"]), W, H, t.get("pos", "top")))

        vf = []
        if events:
            ass = tmp / "subs.ass"
            ass.write_text(ass_header(W, H, cap) + "\n".join(events) + "\n", encoding="utf-8")
            esc = ass.as_posix().replace(":", "\\:")
            fonts = cap.get("fonts_dir")
            fonts = Path(base / fonts) if fonts else (SKILL_FONTS if SKILL_FONTS.exists() else None)
            vf.append(f"ass='{esc}'" + (f":fontsdir='{fonts.as_posix().replace(':', chr(92) + ':')}'" if fonts else ""))
        music = plan.get("music")
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", joined]
        if music:
            mpath = music["file"] if os.path.isabs(music["file"]) else str(base / music["file"])
            cmd += ["-stream_loop", "-1", "-i", mpath]
            g = float(music.get("gain_db", -20))
            fc = (f"[1:a]volume={g}dB,atrim=duration={timeline:.3f},afade=t=out:st={max(0, timeline - 1.5):.3f}:d=1.5[m];"
                  f"[0:a][m]amix=inputs=2:duration=first:normalize=0[a]")
            cmd += ["-filter_complex", fc, "-map", "0:v", "-map", "[a]"]
        if vf:
            cmd += ["-vf", ",".join(vf)]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(plan.get("crf", 18)), "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
        if not music:
            cmd[cmd.index("-c:v"):cmd.index("-c:v")] = ["-map", "0:v", "-map", "0:a"]
        run(cmd)
        print(f"wrote {out}: {timeline:.1f}s, {W}x{H}, {len(segs)} segments")
    finally:
        if keep_temp:
            print(f"temp files kept in {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------------- srt
def srt(words_path: str, out: str, plan_path: str | None = None, per_line: int = 7) -> None:
    words = json.loads(Path(words_path).read_text(encoding="utf-8"))["words"]
    if plan_path:
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
        words = retime_words(words, plan.get("segments", []), plan.get("fps", 30))

    def ts(t):
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    lines = []
    for n, g in enumerate(group_words(words, per_line, 0.8, 42), 1):
        lines.append(f"{n}\n{ts(g[0]['start'])} --> {ts(g[-1]['end'])}\n{' '.join(w['w'] for w in g)}\n")
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}: {len(lines)} subtitles")


# ----------------------------------------------------------------------------- sheet
def sheet(video: str, out: str, n: int = 12, cols: int = 4, width: int = 320) -> None:
    need("ffmpeg")
    dur = probe(video)["duration"] or 1
    rows = math.ceil(n / cols)
    fps = n / dur
    run(["ffmpeg", "-y", "-v", "error", "-i", video, "-vf",
         f"fps={fps:.5f},scale={width}:-2,drawtext=text='%{{pts\\:hms}}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6,tile={cols}x{rows}:padding=4:color=white",
         "-frames:v", "1", "-q:v", "3", out])
    print(f"wrote {out}")


# ----------------------------------------------------------------------------- broll index / search
def index(folder: str, out: str) -> None:
    root = Path(folder).resolve()
    sheets = Path(out).resolve().parent / "broll_sheets"
    sheets.mkdir(exist_ok=True)
    old = {}
    if Path(out).exists():
        old = {c["file"]: c for c in json.loads(Path(out).read_text(encoding="utf-8")).get("clips", [])}
    clips = []
    files = sorted(p for p in root.rglob("*") if p.suffix.lower() in VIDEO_EXT | IMAGE_EXT)
    for k, f in enumerate(files, 1):
        rel = f.relative_to(root).as_posix()
        entry = old.get(rel, {"file": rel, "description": "", "tags": []})
        if f.suffix.lower() in VIDEO_EXT:
            info = probe(str(f))
            v = info["video"] or {}
            entry.update({"kind": "video", "duration": round(info["duration"], 2), "width": v.get("width"),
                          "height": v.get("height"), "has_audio": bool(info["audio"])})
            sheet_file = sheets / (re.sub(r"[^\w.-]+", "_", rel) + ".jpg")
            if not sheet_file.exists():
                sheet(str(f), str(sheet_file), n=6, cols=3, width=240)
            entry["sheet"] = sheet_file.relative_to(Path(out).resolve().parent).as_posix()
        else:
            from_img = probe(str(f))["video"] or {}
            entry.update({"kind": "image", "width": from_img.get("width"), "height": from_img.get("height")})
        w, h = entry.get("width") or 0, entry.get("height") or 0
        entry["orientation"] = "vertical" if h > w else "horizontal" if w > h else "square"
        clips.append(entry)
        print(f"\r  {k}/{len(files)} indexed", end="", flush=True)
    print()
    Path(out).write_text(json.dumps({"root": str(root), "clips": clips}, ensure_ascii=False, indent=1), encoding="utf-8")
    todo = sum(1 for c in clips if not c.get("description"))
    print(f"wrote {out}: {len(clips)} clips ({todo} still need a description; look at broll_sheets/ and fill them in)")


AR_FOLD = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي"})


STOP = set("""على في من الى إلى عن مع و او أو ان إن اللي الي ده دي دا هو هي انا انت فيه بتاع بتاعة كده زي
the a an of on in at to with and or for from by is are this that my your""".split())
STOP = {w.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"})) for w in STOP} | STOP


def norm(s: str) -> list:
    s = unicodedata.normalize("NFKC", s.lower()).translate(AR_FOLD)
    s = re.sub(r"[ً-ْـ]", "", s)  # tashkeel and tatweel
    toks = re.findall(r"[\w]+", s)
    out = []
    for t in toks:
        if len(t) > 3 and t.startswith("ال"):
            t = t[2:]
        if t not in STOP and len(t) > 1:
            out.append(t)
    return out


def search(index_path: str, query: str, top: int = 8, orientation: str | None = None) -> list:
    data = json.loads(Path(index_path).read_text(encoding="utf-8"))
    q = set(norm(query))
    results = []
    for c in data.get("clips", []):
        if orientation and c.get("orientation") != orientation:
            continue
        hay = norm(" ".join([c.get("description", ""), " ".join(c.get("tags", [])), c["file"]]))
        score = 0.0
        for t in q:
            if t in hay:
                score += 2
            elif any(h.startswith(t[:4]) for h in hay if len(t) >= 4):
                score += 1
        if score:
            results.append((score, c))
    results.sort(key=lambda r: (-r[0], r[1].get("duration") or 0))
    for score, c in results[:top]:
        print(f"{score:4.0f}  {c['file']}  [{c.get('orientation')}, {c.get('duration', '-')}s]  {c.get('description', '')[:90]}")
    if not results:
        print("no match; try other words, or describe more clips in the index")
    return [c for _, c in results[:top]]


# ----------------------------------------------------------------------------- cli
def main() -> None:
    for stream in (sys.stdout, sys.stderr):  # Arabic output on Windows consoles
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="reelkit", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("probe"); s.add_argument("media")
    s = sub.add_parser("transcribe"); s.add_argument("media"); s.add_argument("-o", "--out", default="words.json")
    s.add_argument("--model", default="small", help="tiny, base, small, medium, large-v3 (bigger = better Arabic, slower)")
    s.add_argument("--lang", help="force a language code, e.g. ar or en"); s.add_argument("--prompt", help="spelling hints: names, brands")
    s = sub.add_parser("silences"); s.add_argument("media"); s.add_argument("-o", "--out", default="keep.json")
    s.add_argument("--noise", default="-32dB"); s.add_argument("--min", type=float, default=0.45, dest="min_silence")
    s.add_argument("--pad", type=float, default=0.12)
    s = sub.add_parser("faces"); s.add_argument("video"); s.add_argument("-o", "--out", default="faces.json")
    s.add_argument("--step", type=float, default=0.5)
    s = sub.add_parser("matte"); s.add_argument("video"); s.add_argument("-o", "--out", default="mask.mp4")
    s.add_argument("--smooth", type=float, default=0.6)
    s = sub.add_parser("render"); s.add_argument("plan"); s.add_argument("-o", "--out", default="out.mp4")
    s.add_argument("--keep-temp", action="store_true")
    s = sub.add_parser("srt"); s.add_argument("words"); s.add_argument("-o", "--out", default="captions.srt")
    s.add_argument("--plan"); s.add_argument("--per-line", type=int, default=7)
    s = sub.add_parser("sheet"); s.add_argument("video"); s.add_argument("-o", "--out", default="sheet.jpg")
    s.add_argument("--n", type=int, default=12); s.add_argument("--cols", type=int, default=4)
    s = sub.add_parser("index"); s.add_argument("folder"); s.add_argument("-o", "--out", default="broll_index.json")
    s = sub.add_parser("search"); s.add_argument("index"); s.add_argument("query"); s.add_argument("--top", type=int, default=8)
    s.add_argument("--orientation", choices=["vertical", "horizontal", "square"])
    a = ap.parse_args()
    if a.cmd == "probe":
        print(json.dumps(probe(a.media), indent=1))
    elif a.cmd == "transcribe":
        transcribe(a.media, a.out, a.model, a.lang, a.prompt)
    elif a.cmd == "silences":
        silences(a.media, a.out, a.noise, a.min_silence, a.pad)
    elif a.cmd == "faces":
        faces(a.video, a.out, a.step)
    elif a.cmd == "matte":
        matte(a.video, a.out, a.smooth)
    elif a.cmd == "render":
        render(a.plan, a.out, a.keep_temp)
    elif a.cmd == "srt":
        srt(a.words, a.out, a.plan, a.per_line)
    elif a.cmd == "sheet":
        sheet(a.video, a.out, a.n, a.cols)
    elif a.cmd == "index":
        index(a.folder, a.out)
    elif a.cmd == "search":
        search(a.index, a.query, a.top, a.orientation)


if __name__ == "__main__":
    main()
