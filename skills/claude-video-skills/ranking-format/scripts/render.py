#!/usr/bin/env python3
"""Render a motion template (template.html) to MP4 / transparent MOV / PNG still.

Every template exposes window.renderFrame(t) and draws deterministically, so each
frame is exact (no real-time playback, no dropped frames).

Examples
  python3 render.py template.html out.mp4
  python3 render.py template.html out.mp4 --w 1080 --h 1080 --dur 5 --text "MAKE IT MOVE"
  python3 render.py template.html overlay.mov --alpha            # ProRes 4444 with transparency
  python3 render.py template.html still.png --still 2.5          # single frame
  python3 render.py template.html out.mp4 --data ranking.json --w 1080 --h 1920
  python3 render.py template.html top.mp4 --data ranking.json --w 1080 --h 960   # top half, for a split with the speaker

Needs: pip install playwright && playwright install chromium ; ffmpeg on PATH.
"""
import argparse, base64, json, pathlib, subprocess, sys, urllib.parse

ap = argparse.ArgumentParser()
ap.add_argument('template'); ap.add_argument('out')
ap.add_argument('--w', type=int, default=1080); ap.add_argument('--h', type=int, default=1920)
ap.add_argument('--fps', type=int, default=30); ap.add_argument('--dur', type=float)
ap.add_argument('--text'); ap.add_argument('--sub')
ap.add_argument('--set', action='append', default=[], help='colour override, e.g. c1=ff2a1a (no #)')
ap.add_argument('--alpha', action='store_true', help='transparent background (.mov ProRes 4444 or .webm VP9)')
ap.add_argument('--still', type=float, help='render one frame at this time to a .png')
ap.add_argument('--audio', help='optional audio file to mux (trimmed to length)')
ap.add_argument('--crf', type=int, default=16)
ap.add_argument('--data', help='JSON file with title, tiers and items (see SKILL.md)')
ap.add_argument('--font', help='font family (default Cairo, included); any other must be installed on this machine')
ap.add_argument('--brand', help="the user's brand.json: colours, theme and font (see PLAN.md)")
a = ap.parse_args()

from playwright.sync_api import sync_playwright

q = {'render': '1', 'w': a.w, 'h': a.h}
if a.dur: q['dur'] = a.dur
if a.text is not None: q['text'] = a.text
if a.sub is not None: q['sub'] = a.sub
if a.alpha: q['alpha'] = '1'
if a.data:
    raw = pathlib.Path(a.data).read_text(encoding='utf-8')
    json.loads(raw)  # fail early on a broken file
    q['data'] = base64.urlsafe_b64encode(raw.encode('utf-8')).decode('ascii')
if a.brand:
    b = json.loads(pathlib.Path(a.brand).read_text(encoding='utf-8'))
    dark = b.get('theme') == 'dark'
    pick = {'bg': b.get('background'), 'ink': b.get('text'), 'c1': b.get('accent'),
            'card': b.get('card') or ('#1c1c1c' if dark else '#ffffff'),
            'strip': b.get('strip') or ('#2a2a2a' if dark else '#e8e8e8')}
    for k, v in pick.items():
        if v: q[k] = v.lstrip('#')
    if b.get('font') and not a.font: q['font'] = b['font']
if a.font: q['font'] = a.font
for kv in a.set:
    k, v = kv.split('=', 1); q[k] = v.lstrip('#')
url = pathlib.Path(a.template).resolve().as_uri() + '?' + urllib.parse.urlencode(q)

with sync_playwright() as p:
    br = p.chromium.launch(args=['--disable-gpu-vsync'])
    pg = br.new_page(viewport={'width': min(a.w, 1920), 'height': min(a.h, 1920)})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(url); pg.wait_for_function('typeof window.renderFrame === "function"', timeout=20000)
    pg.evaluate('document.fonts ? document.fonts.ready.then(()=>1) : 1')
    if errs: sys.exit('template error: ' + errs[0])
    dur = pg.evaluate('window.__dur')
    fmt = 'image/png' if (a.alpha or a.still is not None) else 'image/jpeg'
    grab = "([t,f])=>{renderFrame(t);return document.getElementById('c').toDataURL(f,0.95)}"
    if a.still is not None:
        d = pg.evaluate(grab, [a.still, 'image/png'])
        pathlib.Path(a.out).write_bytes(base64.b64decode(d.split(',', 1)[1])); print('wrote', a.out); br.close(); sys.exit()
    n = int(round(dur * a.fps))
    ext = pathlib.Path(a.out).suffix.lower()
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'png' if fmt == 'image/png' else 'mjpeg', '-framerate', str(a.fps), '-i', '-']
    if a.audio: cmd += ['-i', a.audio, '-map', '0:v', '-map', '1:a', '-shortest', '-c:a', 'aac', '-b:a', '192k']
    if a.alpha and ext == '.webm': cmd += ['-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '24']
    elif a.alpha: cmd += ['-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le']
    else: cmd += ['-c:v', 'libx264', '-preset', 'slow', '-crf', str(a.crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
    ff = subprocess.Popen(cmd + [a.out], stdin=subprocess.PIPE)
    for i in range(n):
        d = pg.evaluate(grab, [i / a.fps, fmt])
        ff.stdin.write(base64.b64decode(d.split(',', 1)[1]))
        if i % a.fps == 0: print(f'\rframe {i}/{n}', end='', flush=True)
    ff.stdin.close(); ff.wait(); br.close()
    print(f'\rwrote {a.out}  ({n} frames, {dur}s @ {a.fps}fps, {a.w}x{a.h})')
