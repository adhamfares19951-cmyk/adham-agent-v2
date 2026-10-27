# Edit plan reference (`plan.json`)

`python scripts/reelkit.py render plan.json -o out.mp4` turns one plan into a finished video.
Paths in the plan are relative to the plan file. Times are in seconds of the **source** video.

```json
{
  "source": "talk.mp4",
  "brand": "brand.json",
  "words": "words.json",
  "faces": "faces.json",
  "matte": "mask.mp4",
  "canvas": [1080, 1920],
  "fps": 30,
  "segments": [
    { "start": 0.0,  "end": 3.1, "layout": "full", "zoom": 1.0, "title": "أهم ٣ أدوات" },
    { "start": 3.4,  "end": 6.0, "layout": "full", "zoom": [1.0, 1.12] },
    { "start": 6.0,  "end": 8.5, "layout": "broll", "broll": "broll/laptop.mp4", "broll_start": 2.0 },
    { "start": 8.5,  "end": 12.0, "layout": "split", "top": "assets/chart.png", "top_zoom": [1.0, 1.08] },
    { "start": 12.0, "end": 15.0, "layout": "screen", "zoom_rect": [0, 0, 960, 540], "speed": 1.5 },
    { "start": 15.0, "end": 18.0, "layout": "depth", "background": "assets/channel.png" },
    { "start": 18.0, "end": 20.0, "layout": "card", "title": "تابعني لأكتر" }
  ],
  "captions": { "words_per_line": 3, "position": 0.78 },
  "music": { "file": "music.mp3", "gain_db": -20 }
}
```

## The user's look: `brand.json`

Every video uses the **user's** colours, theme and font, never the look of the examples in this pack. Ask once,
save the answers in `brand.json` next to their videos, and point every plan at it with `"brand": "brand.json"`:

```json
{
  "theme": "dark",
  "font": "Cairo",
  "text": "#FFFFFF",
  "highlight": "#FFE066",
  "accent": "#2563EB",
  "accent_text": "#FFFFFF",
  "background": "#101418"
}
```

| key | used for |
|---|---|
| `theme` | `dark` or `light`: card backgrounds and the tier-list table |
| `font` | captions and titles. **Cairo** ships with the skill (`fonts/`), so it always works. For any other font, the user installs it or gives the .ttf/.otf files: put them in a folder and set `"fonts_dir": "fonts"` (relative to brand.json) |
| `title_font` | optional second font for titles |
| `text` | caption colour |
| `highlight` | the word being spoken |
| `accent` / `accent_text` | title boxes (hooks, steps, chapters) and their text |
| `outline` | caption outline (default black) |
| `background` | solid card colour (`card` segments with `"blur_speaker": false`) and the tier-list background |

Anything in the plan's `captions` overrides the brand for that one video.

## Top level

| key | meaning |
|---|---|
| `source` | the talking-head or screen recording. Its audio is the voice of the whole video. |
| `brand` | the user's `brand.json` (above). |
| `words` | `words.json` from `transcribe`. Captions are built from it and follow every cut and speed change automatically. |
| `faces` | `faces.json` from `faces`. With it, `"focus": "auto"` (the default) keeps the speaker centred when cropping. |
| `matte` | `mask.mp4` from `matte`. Needed only by `depth` segments. |
| `canvas` | output size. `[1080, 1920]` reels and shorts, `[1920, 1080]` YouTube, `[1080, 1350]` feed. |
| `segments` | the edit, in order. Leave gaps between `end` and the next `start` to cut silences, mistakes and retakes. |
| `captions` | `enabled` (default true), `style` (`word` highlights the spoken word, `line` plain lines), `words_per_line`, `max_chars`, `position` (0 top to 1 bottom), `size`, `uppercase`; and per-video overrides of the brand: `font`, `color`, `highlight`, `outline`, `title_box`, `title_color`, `fonts_dir`. |
| `titles` | extra on-screen titles in **output** time: `[{"text": "...", "start": 1.0, "end": 3.0, "pos": "top"}]`. |
| `music` | `file` and `gain_db` (-18 to -24 sits under a voice). It loops if short and fades out at the end. |

## Segment layouts

| layout | what it shows | extra keys |
|---|---|---|
| `full` | the speaker filling the frame, cropped around the face | `zoom`: a number for a static punch-in (1.15), or `[from, to]` for a smooth push-in; `focus`: `"auto"` or `[x, y]` (0 to 1) |
| `broll` | another clip or image full screen, while the speaker's voice continues | `broll`, `broll_start`, `broll_zoom` `[from, to]` |
| `split` | an image or clip on top, the speaker below | `top`, `top_start`, `top_zoom`, `top_fit` (`cover` or `contain`), `ratio` (top share, default 0.5), `speaker_on_top` |
| `screen` | a screen recording fitted on a blurred copy of itself | `zoom_rect` `[x, y, w, h]` in source pixels to zoom into one area |
| `depth` | a UI, page or image **behind** the speaker, the speaker cut out in front | `background`, `background_start`, `background_zoom` `[from, to]` (default `[1.0, 1.06]`) |
| `card` | a big title over a blurred, darkened speaker (or `background`, or a solid `color` with `"blur_speaker": false`) | `title`, `color` |

Every segment also takes:
- `title`: text shown for the whole segment (top of the frame; centre for `card`). `title_pos`: `top`, `center` or `bottom`.
- `speed`: 1.5 or 2 to speed up slow parts (screen recordings). The voice is sped up too, without changing its pitch.
- `mute`: true to drop the source audio for this segment.
- `no_captions`: true to hide captions during this segment.

## Rules that keep edits clean
- Cut on word boundaries: take `start` from a word's `start` and `end` from a word's `end` in `words.json`, plus about 0.08 s of air on both sides.
- Do not leave a segment shorter than about 0.6 s; it reads as a glitch.
- Alternate the zoom between consecutive `full` segments (1.0, then 1.12, then 1.0) so jump cuts look intentional.
- After rendering, run `python scripts/reelkit.py sheet out.mp4 -o check.jpg` and look at it before you deliver.
