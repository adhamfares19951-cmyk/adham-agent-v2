import asyncio
import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import memory
import main

class TestWave2(unittest.TestCase):
    def setUp(self):
        memory.init_db()
        memory.clear_history()

    def tearDown(self):
        memory.clear_history()

    def test_tool_summary_persistence(self):
        # 1. Add user message
        memory.add_message("user", "كم المشاهدات على تيك توك؟")
        # 2. Add assistant message with tools_summary
        tool_sum = "tiktok_get_analytics: views=1520"
        memory.add_message("assistant", "المشاهدات الحالية 1520 مشاهدة.", tools_summary=tool_sum)

        history = memory.get_history(5)
        self.assertEqual(len(history), 2)
        assistant_turn = history[1]
        self.assertIn("المشاهدات الحالية", assistant_turn["content"])
        self.assertIn("tiktok_get_analytics", assistant_turn["content"])

    def test_file_content_placeholder(self):
        # Large simulated uploaded file
        big_content = "[ملف: تقرير.pdf] " + ("x" * 2000)
        memory.add_message("user", big_content)
        history = memory.get_history(5)
        self.assertEqual(len(history), 1)
        self.assertLess(len(history[0]["content"]), 300, "Large file content should be stored as compact placeholder")
        self.assertIn("[ملف:", history[0]["content"])

    def test_rolling_summary(self):
        # Insert 22 messages to trigger rolling summary (>18 threshold)
        for i in range(22):
            role = "user" if i % 2 == 0 else "assistant"
            memory.add_message(role, f"Message number {i} text for conversation")

        with memory._db() as c:
            raw_count = c.execute("SELECT COUNT(*) FROM chat_history").fetchone()[0]
            sum_count = c.execute("SELECT COUNT(*) FROM conversation_summary").fetchone()[0]

        # Raw count should be reduced to 12
        self.assertLessEqual(raw_count, 18)
        self.assertGreaterEqual(sum_count, 1)

        # get_history should include summary anchor
        history = memory.get_history(20)
        self.assertGreater(len(history), 2)
        self.assertIn("ملخص المحادثات والقرارات السابقة", history[0]["content"])

    def test_concurrency_locks(self):
        async def run_concurrent():
            lock = main.get_chat_lock(12345)
            # Verify lock is an asyncio.Lock
            self.assertIsInstance(lock, asyncio.Lock)

            order = []
            async def task1():
                async with lock:
                    order.append("start1")
                    await asyncio.sleep(0.05)
                    order.append("end1")

            async def task2():
                async with lock:
                    order.append("start2")
                    await asyncio.sleep(0.02)
                    order.append("end2")

            # Reset simulation should not be blocked on a different chat
            other_lock = main.get_chat_lock(99999)
            async def reset_task():
                async with other_lock:
                    order.append("reset_done")

            await asyncio.gather(task1(), task2(), reset_task())
            # Verify serialization on same chat lock (task1 and task2 cannot interleave)
            idx_s1, idx_e1 = order.index("start1"), order.index("end1")
            idx_s2, idx_e2 = order.index("start2"), order.index("end2")
            self.assertTrue(idx_e1 < idx_s2 or idx_e2 < idx_s1, "Tasks on same chat lock must be serialized")
            # Verify reset task ran concurrently without being blocked
            self.assertIn("reset_done", order)

        asyncio.run(run_concurrent())


if __name__ == "__main__":
    unittest.main()
