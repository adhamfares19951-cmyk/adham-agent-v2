# -*- coding: utf-8 -*-
"""
Evaluation test suite for adham-agent.
Evaluates >= 30 realistic Arabic queries across all domains:
1. Reminders & Scheduling
2. Jobs & Career
3. Social & Publishing
4. Network & MikroTik
5. Dev & Code (including security / approval checks)
6. Media & Video Generation
7. Leads & Sales
8. Finance & Store
9. General & Honesty Verification
"""

import unittest
import asyncio
import re
import config
import memory
import tools
from brain import SYSTEM_PROMPT


class TestEvaluationSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        memory.init_db()

    def setUp(self):
        memory.clear_history()

    # ---------------------------------------------------------
    # Domain 1: Reminders & Scheduling (4 queries)
    # ---------------------------------------------------------
    def test_reminders_01_set_reminder(self):
        query = "ذكرني بكرا الساعة 9 الصبح باجتماع الزوم"
        groups = tools._match_intent_groups(query)
        self.assertIn("reminders_jobs", groups)
        selected = tools.select_tools(query)
        self.assertLessEqual(len(selected), 25)
        names = [t["name"] for t in selected]
        self.assertTrue(any("reminder" in n for n in names))

    def test_reminders_02_check_today(self):
        query = "شو في عندي تذكيرات ومواعيد اليوم؟"
        groups = tools._match_intent_groups(query)
        self.assertIn("reminders_jobs", groups)
        selected = tools.select_tools(query)
        self.assertLessEqual(len(selected), 25)

    def test_reminders_03_cancel_reminder(self):
        query = "احذف تذكير موعد الطبيب"
        groups = tools._match_intent_groups(query)
        self.assertIn("reminders_jobs", groups)

    def test_reminders_04_english_token_remind(self):
        query = "remind me to check server at 8pm"
        groups = tools._match_intent_groups(query)
        self.assertIn("reminders_jobs", groups)

    # ---------------------------------------------------------
    # Domain 2: Jobs & Career (4 queries)
    # ---------------------------------------------------------
    def test_jobs_01_search_gaza_jobs(self):
        query = "ابحث عن وظائف إدخال بيانات في غزة اليوم"
        groups = tools._match_intent_groups(query)
        self.assertIn("reminders_jobs", groups)
        selected = tools.select_tools(query)
        self.assertLessEqual(len(selected), 25)
        names = [t["name"] for t in selected]
        self.assertTrue(any("job" in n for n in names))

    def test_jobs_02_mostaql_freelance(self):
        query = "في وظائف ميكروتك وشبكات جديدة على مستقل؟"
        groups = tools._match_intent_groups(query)
        self.assertIn("reminders_jobs", groups)

    def test_jobs_03_apply_cv_request(self):
        query = "بدي سيرة ذاتية لوظيفة أطباء بلا حدود MSF"
        groups = tools._match_intent_groups(query)
        self.assertIn("reminders_jobs", groups)
        selected = tools.select_tools(query)
        self.assertLessEqual(len(selected), 25)

    def test_jobs_04_english_career(self):
        query = "check recent remote jobs for python dev"
        groups = tools._match_intent_groups(query)
        self.assertIn("reminders_jobs", groups)

    # ---------------------------------------------------------
    # Domain 3: Social & Publishing (4 queries)
    # ---------------------------------------------------------
    def test_social_01_publish_reels(self):
        query = "انشر الريلز على انستقرام الآن مع الكابشن"
        groups = tools._match_intent_groups(query)
        self.assertIn("social_publishing", groups)
        selected = tools.select_tools(query)
        self.assertLessEqual(len(selected), 25)
        names = [t["name"] for t in selected]
        self.assertTrue(any("publish" in n or "instagram" in n for n in names))

    def test_social_02_tiktok_analytics(self):
        query = "كم مشاهدات آخر فيديو على تيك توك؟"
        groups = tools._match_intent_groups(query)
        self.assertIn("social_publishing", groups)
        selected = tools.select_tools(query)
        self.assertLessEqual(len(selected), 25)
        names = [t["name"] for t in selected]
        self.assertTrue(any("tiktok" in n or "analytics" in n for n in names))

    def test_social_03_schedule_post(self):
        query = "جدول بوست فيسبوك لبكرا الساعة 5 العصر"
        groups = tools._match_intent_groups(query)
        self.assertIn("social_publishing", groups)

    def test_social_04_youtube_upload(self):
        query = "ارفع الفيديو الجديد على قناة يوتيوب"
        groups = tools._match_intent_groups(query)
        self.assertIn("social_publishing", groups)

    # ---------------------------------------------------------
    # Domain 4: Network & MikroTik (4 queries)
    # ---------------------------------------------------------
    def test_network_01_solar_calculation(self):
        query = "احسب بطارية طاقة شمسية لانفرتر 1000W شغال 8 ساعات"
        groups = tools._match_intent_groups(query)
        self.assertIn("network_mikrotik", groups)
        selected = tools.select_tools(query)
        self.assertLessEqual(len(selected), 25)

    def test_network_02_mikrotik_script(self):
        query = "اكتب سكربت ميكروتك لحظر التيك توك واليوتيوب"
        groups = tools._match_intent_groups(query)
        self.assertIn("network_mikrotik", groups)

    def test_network_03_ping_latency(self):
        query = "افحص سرعة الشبكة والـ Ping للراوتر"
        groups = tools._match_intent_groups(query)
        self.assertIn("network_mikrotik", groups)

    def test_network_04_english_vlan_subnet(self):
        query = "configure vlan subnet for local network"
        groups = tools._match_intent_groups(query)
        self.assertIn("network_mikrotik", groups)

    # ---------------------------------------------------------
    # Domain 5: Dev, Code & Dangerous Tool Approvals (4 queries)
    # ---------------------------------------------------------
    def test_dev_01_python_script(self):
        query = "اكتب كود بايثون لتحميل ملفات من رابط وحفظها"
        groups = tools._match_intent_groups(query)
        self.assertIn("dev_workspace", groups)
        selected = tools.select_tools(query)
        self.assertLessEqual(len(selected), 25)

    def test_dev_02_inspect_files(self):
        query = "افحص ملفات المشروع واقرأ config.py"
        groups = tools._match_intent_groups(query)
        self.assertIn("dev_workspace", groups)

    def test_dev_03_shell_command_requires_approval(self):
        # Dangerous action must require approval before running
        res = asyncio.run(tools.execute_tool("execute_server_command", {"command": "dir"}))
        self.assertIn("طابور الموافقات", res)
        self.assertIn("موافقة أدهم", res)
        items = memory.get_pending_approvals()
        self.assertGreaterEqual(len(items), 1)
        self.assertTrue(any(it["action_type"] == "execute_server_command" for it in items))

    def test_dev_04_write_file_requires_approval(self):
        # Workspace write file is dangerous and must require approval when valid args passed
        res = asyncio.run(tools.execute_tool("workspace_write_file", {"project": "agent", "file_path": "test.txt", "content": "hi"}))
        self.assertIn("طابور الموافقات", res)
        self.assertIn("موافقة أدهم", res)

    # ---------------------------------------------------------
    # Domain 6: Media Generation (3 queries)
    # ---------------------------------------------------------
    def test_media_01_video_generation(self):
        query = "اعمل فيديو إعلاني للمتجر بلهجة سعودية"
        groups = tools._match_intent_groups(query)
        self.assertIn("media", groups)
        selected = tools.select_tools(query)
        self.assertLessEqual(len(selected), 25)

    def test_media_02_ai_image_generation(self):
        query = "ولد صورة بالذكاء الاصطناعي لمنتج قهوة مختصة"
        groups = tools._match_intent_groups(query)
        self.assertIn("media", groups)

    def test_media_03_arabic_voiceover(self):
        query = "حول النص لصوت عربي طبيعي باللهجة الخليجية"
        groups = tools._match_intent_groups(query)
        self.assertIn("media", groups)

    # ---------------------------------------------------------
    # Domain 7: Leads & Sales (3 queries)
    # ---------------------------------------------------------
    def test_leads_01_extract_local_leads(self):
        query = "استخرج ليدز ومحلات تجارية في مدينة خانيونس"
        groups = tools._match_intent_groups(query)
        self.assertIn("leads_sales", groups)
        selected = tools.select_tools(query)
        self.assertLessEqual(len(selected), 25)

    def test_leads_02_draft_quotation_pitch(self):
        query = "صيغ عرض سعر احترافي لخدمة تركيب شبكات"
        groups = tools._match_intent_groups(query)
        self.assertIn("leads_sales", groups)

    def test_leads_03_whatsapp_outreach(self):
        query = "جهز رسالة واتساب للتواصل مع العملاء المهتمين"
        groups = tools._match_intent_groups(query)
        self.assertIn("leads_sales", groups)

    # ---------------------------------------------------------
    # Domain 8: Finance & Store (3 queries)
    # ---------------------------------------------------------
    def test_finance_01_store_profits(self):
        query = "كم أرباح المتجر والمبيعات اليوم؟"
        groups = tools._match_intent_groups(query)
        self.assertIn("finance", groups)
        selected = tools.select_tools(query)
        self.assertLessEqual(len(selected), 25)

    def test_finance_02_new_store_orders(self):
        query = "استعرض الطلبات الجديدة في متجر سلة"
        groups = tools._match_intent_groups(query)
        self.assertIn("finance", groups)

    def test_finance_03_monthly_balance(self):
        query = "كم رصيد الحساب والمصاريف المدفوعة هذا الشهر؟"
        groups = tools._match_intent_groups(query)
        self.assertIn("finance", groups)

    # ---------------------------------------------------------
    # Domain 9: General, Honesty & Anti-Hallucination (3 queries)
    # ---------------------------------------------------------
    def test_general_01_who_are_you(self):
        query = "مين انت وشو بتقدر تساعدني يا أدهم؟"
        groups = tools._match_intent_groups(query)
        # General query defaults to core + high-value groups
        self.assertIn("core", groups)
        selected = tools.select_tools(query)
        self.assertLessEqual(len(selected), 25)

    def test_general_02_honesty_rule_in_prompt(self):
        # Prompt must forbid fabricating facts, claiming fake success, or lying about cookies
        self.assertTrue("Zero-Hallucination" in SYSTEM_PROMPT or "اختلاق" in SYSTEM_PROMPT)
        self.assertIn("أدهم", SYSTEM_PROMPT)
        # Verify prompt size <= 1500 tokens (~6000 chars)
        self.assertLessEqual(len(SYSTEM_PROMPT), 6000)

    def test_general_03_untrusted_data_boundary_in_prompt(self):
        # Verify prompt contains instruction to treat external fetched data as untrusted
        self.assertTrue("غير موثوقة" in SYSTEM_PROMPT or "Untrusted Data" in SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
