# -*- coding: utf-8 -*-
"""
Test suite for Ollama / Qwen thinking control and <think> tag stripping:
1. Disables thinking for normal/routine requests (reasoning_effort="none", /no_think in system, options.thinking=False).
2. Enables thinking only for coding and deep analysis requests.
3. Wipes <think>...</think> completely from text displayed to Adham.
4. Simple reminder query generates response consuming < 150 tokens.
"""

import unittest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import llm
from llm import OpenAICompatibleProvider, strip_think_tags, Reply, SmartRouter


class TestQwenThinkingControl(unittest.TestCase):
    # ----------------------------------------------------------------
    # 1. <think> tag stripping
    # ----------------------------------------------------------------
    def test_strip_think_tags_complete_block(self):
        raw = "<think>\nLet me think about how to answer Adham.\nFirst step is checking database.\n</think>\nأهلاً يا أدهم! تفضل كيف بقدر أساعدك؟"
        cleaned = strip_think_tags(raw)
        self.assertEqual(cleaned, "أهلاً يا أدهم! تفضل كيف بقدر أساعدك؟")
        self.assertNotIn("<think>", cleaned)
        self.assertNotIn("</think>", cleaned)

    def test_strip_think_tags_unclosed_block(self):
        raw = "<think>\nThinking in progress that was cut off..."
        cleaned = strip_think_tags(raw)
        self.assertEqual(cleaned, "")

    def test_strip_think_tags_orphaned_close_tag(self):
        raw = "تم تأكيد طلبك بنجاح </think>"
        cleaned = strip_think_tags(raw)
        self.assertEqual(cleaned, "تم تأكيد طلبك بنجاح")

    def test_strip_think_tags_clean_text(self):
        raw = "رسالة عادية بدون وسوم تفكير"
        cleaned = strip_think_tags(raw)
        self.assertEqual(cleaned, "رسالة عادية بدون وسوم تفكير")

    # ----------------------------------------------------------------
    # 2. Task detection: coding vs analysis vs general/reminder
    # ----------------------------------------------------------------
    def test_detect_task_type_general_reminder(self):
        task = SmartRouter.detect_task_type("system", [{"role": "user", "content": "ذكرني بكرا الساعة 9 الصبح بالاجتماع"}])
        self.assertEqual(task, "general")

    def test_detect_task_type_coding(self):
        task = SmartRouter.detect_task_type("system", [{"role": "user", "content": "اكتب سكربت بايثون لتحميل ملفات"}])
        self.assertEqual(task, "coding")

    def test_detect_task_type_analysis(self):
        task = SmartRouter.detect_task_type("system", [{"role": "user", "content": "بدي تحليل استراتيجي ومقارنة شاملة لأنظمة الشبكات"}])
        self.assertEqual(task, "analysis")

    # ----------------------------------------------------------------
    # 3. Ollama payload: disabled thinking for regular requests
    # ----------------------------------------------------------------
    def test_ollama_regular_request_disables_thinking(self):
        provider = OpenAICompatibleProvider(
            name="Ollama",
            url="http://127.0.0.1:11434/v1/chat/completions",
            api_key="ollama",
            model="qwen3:8b",
        )

        captured_payload = {}

        async def mock_post(url, json=None, headers=None):
            nonlocal captured_payload
            captured_payload = json
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "<think>Thinking disabled test</think>تمت الجدولة بنجاح يا أدهم."
                    }
                }],
                "usage": {
                    "prompt_tokens": 45,
                    "completion_tokens": 18,
                    "total_tokens": 63,
                }
            }
            return mock_resp

        with patch.object(provider.client, "post", side_effect=mock_post):
            reply = asyncio.run(provider.generate(
                system="أنت مساعد شخصي لأدهم",
                messages=[{"role": "user", "content": "ذكرني بكرا الساعة 9"}],
                task_type="general",
            ))

        # Check payload fields
        self.assertEqual(captured_payload["reasoning_effort"], "none")
        self.assertEqual(captured_payload["options"]["thinking"], False)
        
        # Check system message received /no_think
        sys_msg = [m for m in captured_payload["messages"] if m["role"] == "system"][0]
        self.assertIn("/no_think", sys_msg["content"])

        # Check that reply text stripped <think> tag
        self.assertEqual(reply.text, "تمت الجدولة بنجاح يا أدهم.")
        self.assertNotIn("<think>", reply.text)

    # ----------------------------------------------------------------
    # 4. Ollama payload: enabled thinking for coding and analysis
    # ----------------------------------------------------------------
    def test_ollama_coding_request_enables_thinking(self):
        provider = OpenAICompatibleProvider(
            name="Ollama",
            url="http://127.0.0.1:11434/v1/chat/completions",
            api_key="ollama",
            model="qwen3:8b",
        )

        captured_payload = {}

        async def mock_post(url, json=None, headers=None):
            nonlocal captured_payload
            captured_payload = json
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "<think>\nAlgorithm design steps\n</think>\ndef solve(): return True"
                    }
                }],
                "usage": {
                    "prompt_tokens": 80,
                    "completion_tokens": 40,
                    "total_tokens": 120,
                }
            }
            return mock_resp

        with patch.object(provider.client, "post", side_effect=mock_post):
            reply = asyncio.run(provider.generate(
                system="أنت خبير برمجي لأدهم",
                messages=[{"role": "user", "content": "اكتب دالة solve"}],
                task_type="coding",
            ))

        # Check thinking enabled
        self.assertEqual(captured_payload.get("reasoning_effort"), "medium")
        self.assertNotIn("options", captured_payload)  # thinking: False was NOT set

        # Check system message did NOT receive /no_think
        sys_msg = [m for m in captured_payload["messages"] if m["role"] == "system"][0]
        self.assertNotIn("/no_think", sys_msg["content"])

        # Check that <think> was stripped from final reply
        self.assertEqual(reply.text, "def solve(): return True")

    # ----------------------------------------------------------------
    # 5. Simple reminder query token budget (< 150 tokens)
    # ----------------------------------------------------------------
    def test_simple_reminder_consumes_under_150_tokens(self):
        provider = OpenAICompatibleProvider(
            name="Ollama",
            url="http://127.0.0.1:11434/v1/chat/completions",
            api_key="ollama",
            model="qwen3:8b",
        )

        async def mock_post(url, json=None, headers=None):
            # In Qwen without thinking, output is a direct concise answer or tool call
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "تم يا أدهم، جدولتها ورح أذكرك بكرة الساعة 09:00 إن شاء الله."
                    }
                }],
                "usage": {
                    "prompt_tokens": 65,
                    "completion_tokens": 22,
                    "total_tokens": 87,
                }
            }
            return mock_resp

        with patch.object(provider.client, "post", side_effect=mock_post):
            reply = asyncio.run(provider.generate(
                system="أنت مساعد أدهم الهباش",
                messages=[{"role": "user", "content": "ذكرني بكرة 9 الصبح بالاجتماع"}],
                task_type="general",
            ))

        self.assertLess(reply.usage.get("total_tokens", 0), 150)
        self.assertLess(reply.usage.get("completion_tokens", 0), 150)
        self.assertEqual(reply.text, "تم يا أدهم، جدولتها ورح أذكرك بكرة الساعة 09:00 إن شاء الله.")


if __name__ == "__main__":
    unittest.main()
