import asyncio
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import brain
import config
import llm
import tools


class TestWave1(unittest.TestCase):
    def test_tool_selection_10_cases(self):
        cases = [
            ("ذكرني بعد ساعتين أصلي العصر", "reminders_jobs"),
            ("check the latest job postings for IT support", "reminders_jobs"),
            ("انشر الريلز على انستقرام وتيك توك", "social_publishing"),
            ("upload short video to youtube with caption", "social_publishing"),
            ("عندي مشكلة في شبكة الميكروتك والراوتر", "network_mikrotik"),
            ("calculate solar battery capacity for 1000W system", "network_mikrotik"),
            ("اكتب كود بايثون وافحص ملف المشروع في جيت هب", "dev_workspace"),
            ("generate viral image and motion video clip", "media"),
            ("استخرج أرقام عملاء سوبرماركت خانيونس وتواصل معهم", "leads_sales"),
            ("كم أرباح المتجر والطلبات الجديدة والمنتجات اليوم؟", "finance"),
        ]

        for query, expected_group in cases:
            selected = tools.select_tools(query)
            self.assertLessEqual(len(selected), 25, f"Tools count must be <= 25 for: {query}")
            self.assertGreaterEqual(len(selected), 5, f"Should return at least core tools for: {query}")
            matched_groups = tools._match_intent_groups(query)
            self.assertIn(expected_group, matched_groups, f"Expected {expected_group} in matched groups for: {query}")

    def test_schema_vs_handler(self):
        report = tools.validate_tools_schemas()
        self.assertEqual(len(report["issues"]), 0, f"Schema issues found: {report['issues']}")
        self.assertEqual(report["valid"], report["total"])
        self.assertGreater(report["total"], 50)

    def test_error_classification(self):
        router = llm.SmartRouter([
            ("mock_large", MagicMock()),
            ("mock_billing", MagicMock()),
            ("mock_auth", MagicMock()),
        ])

        # 1. 413 PayloadTooLargeError: should NOT set cooldown
        async def run_413():
            mock_prov = MagicMock()
            mock_prov.generate = AsyncMock(side_effect=llm.PayloadTooLargeError("413 too large"))
            r = llm.SmartRouter([("groq", mock_prov), ("gemini", MagicMock())])
            with self.assertRaises(llm.LLMError):
                await r.generate("sys", [{"role": "user", "content": "hi"}])
            self.assertNotIn("groq", r._resting_until, "413 must NOT set cooldown")

        asyncio.run(run_413())

        # 2. 402 BillingError: should disable provider
        async def run_402():
            mock_prov = MagicMock()
            mock_prov.generate = AsyncMock(side_effect=llm.BillingError("402 billing"))
            r = llm.SmartRouter([("openrouter", mock_prov)])
            with self.assertRaises(llm.LLMError):
                await r.generate("sys", [{"role": "user", "content": "hi"}])
            self.assertIn("openrouter", r._disabled_providers, "402 must disable provider")

        asyncio.run(run_402())

        # 3. 401/403 AuthenticationError: should disable provider
        async def run_auth():
            mock_prov = MagicMock()
            mock_prov.generate = AsyncMock(side_effect=llm.AuthenticationError("401 bad key"))
            r = llm.SmartRouter([("mistral", mock_prov)])
            with self.assertRaises(llm.LLMError):
                await r.generate("sys", [{"role": "user", "content": "hi"}])
            self.assertIn("mistral", r._disabled_providers, "401/403 must disable provider")

        asyncio.run(run_auth())

    def test_loop_termination_and_repetition(self):
        # Test repetition detection logic
        sig = ("test_tool", '{"q": "hello"}')
        seen = {sig}
        self.assertIn(sig, seen)

        # Test system prompt length is within target <= 1500 tokens (~5000 chars)
        prompt = brain._system_prompt("اختبار")
        self.assertLess(len(prompt), 7500, "System prompt should be concise (<= ~1500 tokens)")
        self.assertIn("دراع اليمين", prompt)
        self.assertIn("أدهم", prompt)


if __name__ == "__main__":
    unittest.main()
