import os
import re
import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config

def match_publish_intent(text: str):
    t = text.lower()
    latin_words = set(re.findall(r'\b[a-z0-9_]+\b', t))
    arabic_tokens = set(re.findall(r'[\u0600-\u06FF]+', t))

    is_ig = bool(latin_words & {"ig", "instagram", "reel", "reels"}) or bool(arabic_tokens & {"انستقرام", "انستغرام", "انستا", "ريلز", "ريل"})
    is_tiktok = bool(latin_words & {"tiktok"}) or bool(arabic_tokens & {"تيكتوك"}) or ("تيك" in arabic_tokens and "توك" in arabic_tokens)
    is_all = bool(latin_words & {"all", "broadcast"}) or bool(arabic_tokens & {"الكل"}) or ("كل" in arabic_tokens and ("المنصات" in arabic_tokens or "مكان" in arabic_tokens))

    is_negation = any(neg in t for neg in [
        "مش ارفع", "مش انشر", "لا ترفع", "لا تنشر", "ما ترفع", "ما تنشر",
        "مش للنشر", "مش رفع", "بدون نشر", "بدون رفع", "مش راضي", "مش فيديو"
    ])
    is_search_intent = any(k in t for k in [
        "ابحث", "بحث", "دور", "فتش", "أفكار", "افكار", "شو رأيك", "أفضل", "افضل",
        "ترند", "ناجح", "ناجحة", "search", "find", "منافسين", "تحليل"
    ])

    is_publish_word = (bool(latin_words & {"post", "publish"}) or bool(arabic_tokens & {"انشر", "ارفع", "نزل"})) and not is_negation and not is_search_intent
    is_publish = is_publish_word and (is_tiktok or is_ig or is_all)
    return {
        "is_publish": is_publish,
        "is_ig": is_ig,
        "is_tiktok": is_tiktok,
        "is_all": is_all,
    }

def match_cv_intent(text: str):
    t = text.lower()
    latin_words = set(re.findall(r'\b[a-z0-9_]+\b', t))
    arabic_tokens = set(re.findall(r'[\u0600-\u06FF]+', t))
    is_explicit_cv = bool(latin_words & {"cv", "msf"}) or bool(arabic_tokens & {"سيرتي", "السيرة"}) or any(p in t for p in ["سيرة ذاتية", "ملف السيرة", "ابعث السيرة", "ارسل السيرة", "سيرة msf", "اطباء بلا حدود"])
    return is_explicit_cv and not any(k in t for k in ["فيديو", "موقع", "سناب", "تيك", "انستا"])


class TestWave0(unittest.TestCase):
    def test_matcher_false_positives(self):
        # 1. "design" must NOT trigger is_ig
        res_design = match_publish_intent("please review the design")
        self.assertFalse(res_design["is_ig"], "'design' should not match 'ig'")
        self.assertFalse(res_design["is_publish"])

        # 2. "install" must NOT trigger is_all
        res_install = match_publish_intent("install the packages")
        self.assertFalse(res_install["is_all"], "'install' should not match 'all'")
        self.assertFalse(res_install["is_publish"])

        # 3. "call" must NOT trigger is_all
        res_call = match_publish_intent("call me later")
        self.assertFalse(res_call["is_all"], "'call' should not match 'all'")
        self.assertFalse(res_call["is_publish"])

        # 4. "post a design" must NOT trigger publishing
        res_post_design = match_publish_intent("post a design draft")
        self.assertFalse(res_post_design["is_publish"], "'post a design' must not trigger publishing")

    def test_matcher_true_positives(self):
        res_tiktok = match_publish_intent("انشر الفيديو على تيك توك")
        self.assertTrue(res_tiktok["is_publish"])
        self.assertTrue(res_tiktok["is_tiktok"])

        res_ig = match_publish_intent("ارفع ريلز على انستقرام")
        self.assertTrue(res_ig["is_publish"])
        self.assertTrue(res_ig["is_ig"])

        res_all = match_publish_intent("انشر على كل المنصات")
        self.assertTrue(res_all["is_publish"])
        self.assertTrue(res_all["is_all"])

    def test_cv_trigger(self):
        # Mere file or pdf mention must NOT trigger CV
        self.assertFalse(match_cv_intent("وين الملف"))
        self.assertFalse(match_cv_intent("ارسل لي ملف pdf للتقرير"))
        self.assertFalse(match_cv_intent("ملف البوت مش شغال"))

        # Explicit CV queries MUST trigger CV
        self.assertTrue(match_cv_intent("ابعث السيرة الذاتية"))
        self.assertTrue(match_cv_intent("ارسل سيرتي الذاتية"))
        self.assertTrue(match_cv_intent("where is your cv"))
        self.assertTrue(match_cv_intent("ملف السيرة لو سمحت"))

    def test_bot_lock_guard(self):
        import main
        lock_file = config.BASE_DIR / "bot.lock"
        # Test acquiring lock
        acquired = main.acquire_bot_lock()
        self.assertTrue(acquired)
        self.assertTrue(lock_file.exists())
        self.assertEqual(lock_file.read_text(encoding="utf-8").strip(), str(os.getpid()))
        # Clean up
        lock_file.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()
