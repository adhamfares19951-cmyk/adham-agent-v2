"""Automated Test Suite for Stage 3:
- Automated Lead Hunter (Zero-Hallucination)
- Social Studio (Reels / Shorts + Edge-TTS)
- Approval Queue & HITL Preview
- Agency Orchestrator Integration
"""
import asyncio
import os
import sys

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import memory
from tools import lead_hunter, social_studio
import agency_orchestrator


async def main():
    print("==================================================================")
    print("🚀 STARTING STAGE 3 ENTERPRISE INTEGRATION TEST SUITE")
    print("==================================================================")

    # 1. Social Studio Script Generation & Approval Queue
    print("\n[1/4] Testing Social Studio & Approval Queue...")
    script = social_studio.create_social_script("pos")
    qid = script["queue_id"]
    assert qid > 0, "Queue ID must be positive"
    print(f"  ✓ Script generated: '{script['title']}' (Queue ID: #{qid})")

    item = memory.get_approval_item(qid)
    assert item is not None, "Approval item must exist in DB"
    assert item["status"] == "pending", "Status must initially be pending"
    print(f"  ✓ Item verified in DB approval_queue with status: {item['status']}")

    memory.update_approval_status(qid, "approved")
    updated_item = memory.get_approval_item(qid)
    assert updated_item["status"] == "approved", "Status must update to approved"
    print(f"  ✓ Approval status updated successfully to: {updated_item['status']}")

    # 2. Edge-TTS Arabic Voiceover
    print("\n[2/4] Testing Arabic Edge-TTS Voiceover Engine...")
    test_audio = "audio_output/test_voiceover.mp3"
    if os.path.exists(test_audio):
        os.remove(test_audio)

    sample_text = "نظام شامل لإدارة نقاط البيع والكاشير، بدون إنترنت وسرعة فائقة."
    audio_path = await social_studio.generate_arabic_voiceover(sample_text, test_audio)
    assert os.path.exists(audio_path), f"Audio file {audio_path} must exist"
    size = os.path.getsize(audio_path)
    assert size > 2000, f"Audio file size must be > 2000 bytes, got {size}"
    print(f"  ✓ Voiceover MP3 generated: {audio_path} ({size} bytes)")

    # 3. Lead Hunter (Zero-Hallucination & Pitch Generation)
    print("\n[3/4] Testing Lead Hunter & Verified Leads Database...")
    test_phone = "0599000111"
    pitch = lead_hunter.generate_tailored_pitch(
        business_name="سوبرماركت الإيمان",
        sector="سوبرماركت ومواد غذائية",
        location="خانيونس",
    )
    assert "شامل POS" in pitch, "Pitch must offer Shamel POS"
    print(f"  ✓ Tailored pitch created: {pitch[:70]}...")

    wa_link = lead_hunter.format_whatsapp_url(test_phone, pitch)
    assert "wa.me/970599000111" in wa_link, f"WhatsApp link invalid: {wa_link}"
    print(f"  ✓ WhatsApp Direct URL: {wa_link[:50]}...")

    lead_id = memory.add_verified_lead(
        business_name="سوبرماركت الإيمان Test",
        phone=test_phone,
        source_url="https://example.com/verified-source",
        proposed_pitch=pitch,
        status="new"
    )
    assert lead_id > 0, "Lead ID must be positive"
    v_leads = memory.list_verified_leads(limit=50)
    assert any(l["phone"] == test_phone for l in v_leads), "Lead must be found in verified_leads"
    print(f"  ✓ Verified lead stored in DB with ID #{lead_id}")

    # 4. Agency Orchestrator Integration
    print("\n[4/4] Testing Agency Orchestrator Routing...")
    res_mkt = await agency_orchestrator.execute_department_task("marketing_sales", "")
    assert res_mkt["status"] == "success", "Marketing task should succeed"
    print("  ✓ Marketing & Sales department view responded successfully.")

    res_vid = await agency_orchestrator.execute_department_task("video_studio", "توليد سكريبت ريلز تداول")
    assert res_vid["status"] == "success", "Video studio task should succeed"
    print(f"  ✓ Video Studio department executed task successfully.")

    print("\n==================================================================")
    print("🎉 ALL STAGE 3 INTEGRATION TESTS COMPLETED WITH 100% SUCCESS!")
    print("==================================================================")


if __name__ == "__main__":
    asyncio.run(main())
