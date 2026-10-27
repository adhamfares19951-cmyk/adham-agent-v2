# حزمة السكيلز: ٨ سكيلز مونتاج لـ Claude

من **مدرسة الذكاء الاصطناعي**. الصفحة الكاملة بالشرح:
https://arabianaischool.com/skills/claude-video-skills/

٨ سكيلز بتاخد فيديوهاتك الخام وتطلعها جاهزة: بتقص السكتات واللخبطة، وتعمل زوم وبي رول وسبليت سكرين، وكابشن
عربي كلمة بكلمة.

- افتح `PREVIEW-8-skills.mp4` أو `gallery.html` عشان تشوف كل سكيل بتعمل إيه.

| السكيل | بتعمل إيه | اطلب منها كده |
|---|---|---|
| `depth-ui-reel` | موقعك أو قناتك ورا راسك وإنت متقصوص قدامه، والكابشن تحت | «اعمل ريل depth-ui-reel وحط صفحة قناتي ورايا» |
| `ranking-format` | تير ليست من S لـ F والكروت بتنزل مع كلامك | «اعمل تير ليست لأفضل المنصات لجلب العملاء» |
| `personal-short-form-reels` | ريل سريع: قص السكتات، زوم، البي رول بتاعك، كابشن | «منتجلي الريل ده واستخدم البي رول اللي في فولدر broll» |
| `personal-broll-library` | فهرس للبي رول تدور فيه بكلامك العادي | «دورلي على لقطة ليا بكتب على اللابتوب» |
| `business-short-form-reels` | شاشة كاملة، سبليت مع المنتج، كروت عناوين، كول تو أكشن | «اعمل ريل إعلاني لشركتي بصور المنتج واللوجو» |
| `tutorial-videos` | شرح خطوة بخطوة من تسجيل الشاشة: زوم وعناوين وتسريع | «حوّل تسجيل الشاشة ده لفيديو شرح» |
| `youtube-clips` | أقوى اللحظات من فيديو طويل كشورتس طولي | «طلعلي ٥ شورتس من الحلقة دي» |
| `educational-youtube-editor` | مونتاج درس طويل لليوتيوب بالفصول والترجمة والوصف | «منتج الدرس ده وجهزه لليوتيوب» |

## الشكل بتاعك إنت

قبل أول فيديو، Claude هيسألك على **ألوانك** و**الثيم** (فاتح ولا غامق) و**الخط**: خط **Cairo** موجود جاهز جوه كل
سكيل، أو أي خط تاني تحبه. وبيحفظ إجاباتك في ملف `brand.json` جنب فيديوهاتك، عشان كل فيديوهاتك تطلع بنفس الشكل.

## التثبيت على Claude Code (الأفضل للمونتاج)

السكيلز دي بتشتغل على جهازك لأنها بتتعامل مع ملفات فيديو كبيرة.

1. فك ضغط الملف ده: على ويندوز كليك يمين ثم **Extract All** ثم **Extract**، وعلى ماك دبل كليك.
2. انسخ فولدرات السكيلز (كل فولدر جواه `SKILL.md`) جوه فولدر السكيلز:
   - ويندوز: `C:\Users\<اسمك>\.claude\skills\`
   - ماك ولينكس: `~/.claude/skills/`

   لازم يبقى الشكل كده: `~/.claude/skills/youtube-clips/SKILL.md`
3. ثبّت الأدوات مرة واحدة: Python 3 وffmpeg (ويندوز `winget install Gyan.FFmpeg`، ماك `brew install ffmpeg`)، وبعدين:
   `pip install faster-whisper mediapipe playwright` ثم `playwright install chromium`
4. افتح جلسة Claude Code جديدة.

## التثبيت على Claude (الموقع أو التطبيق)

بينفع للمقاطع القصيرة بس.
1. في Claude: **Settings** ثم **Capabilities**، وشغّل **Code execution and file creation**.
2. فك ضغط الملف ده، وافتح فولدر `upload-to-claude`. فيه ٨ ملفات ZIP، ملف لكل سكيل. **متفكش ضغطهم.**
3. **Customize** ثم **Skills** ثم **Upload a skill**، وارفع ملف السكيل اللي عايزها.

---

# The skills pack: 8 video-editing skills for Claude (English)

Eight skills that turn raw footage into finished reels and YouTube videos: cuts, zooms, B-roll, split screens and
word-by-word captions (Arabic included). Before the first video, Claude asks for the user's colours, theme and font
(Cairo ships with every skill) and saves them in `brand.json`, so every video follows the user's own look.

**Claude Code (recommended):** copy the skill folders into `~/.claude/skills/`, install Python 3, ffmpeg and
`pip install faster-whisper mediapipe playwright` + `playwright install chromium`.
**Claude app:** turn on code execution, then upload the zips from `upload-to-claude/` one by one (short clips only).

## Rights

© 2026 مدرسة الذكاء الاصطناعي (Arabian AI School). Free to use, remix and share, including in your own and client
videos. Please don't resell the pack or re-upload it as your own. The Cairo font inside each skill is by the Cairo
Project Authors under the SIL Open Font License (`fonts/OFL.txt`).

- Website: https://arabianaischool.com
- YouTube: https://www.youtube.com/@ArabianAiSchool
- Instagram: https://www.instagram.com/arabianaischool
- Facebook: https://www.facebook.com/arabianaischool
- X: https://x.com/arabianaischool
