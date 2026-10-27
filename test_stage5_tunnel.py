"""Comprehensive Test Suite for Stage 5:
- Automated Cloudflare Tunnel Integration (core/tunnel_manager.py)
- Binary Presence and Execution (bin/cloudflared.exe)
- Public URL Discovery and SQLite Persistence
- Marketing Pitch Integration with Live URL (tools/lead_hunter.py)
- Unified Agency OS Supervisor Architecture (run_agency_os.py)
"""
import asyncio
import os
import re
import sys
import time

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from core.tunnel_manager import get_tunnel_manager, TunnelManager
import memory
from tools import lead_hunter
import agency_orchestrator
import run_agency_os


async def main():
    print("==================================================================")
    print("🚀 STARTING STAGE 5: CLOUDFLARE TUNNEL & PUBLIC ACCESS TEST SUITE")
    print("==================================================================")

    # --------------------------------------------------------------------------
    # 1. Binary Readiness & Version Verification
    # --------------------------------------------------------------------------
    print("\n[1/5] Testing cloudflared Standalone Binary...")
    tm = get_tunnel_manager()
    bin_path = tm.get_cloudflared_executable()
    assert os.path.exists(bin_path), f"cloudflared binary not found at: {bin_path}"
    bin_size = os.path.getsize(bin_path)
    assert bin_size > 10 * 1024 * 1024, f"Binary size suspicious: {bin_size} bytes"
    print(f"  ✓ Binary verified at: {bin_path} ({bin_size / (1024*1024):.1f} MB)")

    # --------------------------------------------------------------------------
    # 2. Test Quick Tunnel Spawn & Public URL Regex Capture
    # --------------------------------------------------------------------------
    print("\n[2/5] Testing Quick Tunnel Launch & Public URL Capture...")
    # Clean previous state
    tm.stop_tunnel()
    t0 = time.time()
    res = await tm.start_tunnel(port=8080, wait_seconds=15)
    elapsed = round(time.time() - t0, 2)

    assert res.get("status") in ("active", "already_running"), f"Tunnel start failed: {res}"
    pub_url = res.get("public_url", "")
    assert pub_url, "Public URL must not be empty"
    assert re.match(r"https://[a-zA-Z0-9-]+\.(?:trycloudflare|cfargotunnel)\.com", pub_url), (
        f"Public URL '{pub_url}' does not match Cloudflare domain pattern"
    )
    print(f"  ✓ Cloudflare Tunnel launched successfully in {elapsed}s")
    print(f"  ✓ Discovered Public URL: {pub_url}")

    # --------------------------------------------------------------------------
    # 3. Test State Persistence in SQLite Settings
    # --------------------------------------------------------------------------
    print("\n[3/5] Testing Persistence in SQLite & State Getters...")
    stored_url = memory.get_setting("public_web_url", "")
    assert stored_url == pub_url, f"Stored URL '{stored_url}' != discovered '{pub_url}'"
    assert tm.get_public_url() == pub_url, "tm.get_public_url() must match discovered URL"
    status = tm.get_status()
    assert status["is_running"] is True, "Tunnel must report running status"
    assert status["local_port"] == 8080, "Local port must be 8080"
    print(f"  ✓ URL persisted in agent_memory.db (settings table: public_web_url)")
    print(f"  ✓ TunnelManager status verified: PID={status.get('pid')}, Uptime={status.get('uptime_seconds')}s")

    # --------------------------------------------------------------------------
    # 4. Test Lead Hunter Pitch & Marketing Integration
    # --------------------------------------------------------------------------
    print("\n[4/5] Testing Lead Hunter Pitch & Store Department Integration...")
    pitch = lead_hunter.generate_tailored_pitch(
        business_name="سوبرماركت المدينة التجريبي",
        sector="سوبرماركت",
        location="خانيونس",
    )
    assert pub_url in pitch, f"Pitch must contain active public tunnel URL '{pub_url}'"
    assert "حاسبة الطاقة الشمسية" in pitch, "Pitch should mention solar calculator preview"
    print("  ✓ Tailored pitch automatically included live public URL for client preview:")
    print(f"    _{pitch[-110:].strip()}_")

    # Test Department view in agency_orchestrator
    store_view = await agency_orchestrator.execute_department_task("store_web", "")
    assert pub_url in store_view["output"], "Store & Web department view must display public URL"
    print("  ✓ Store & Web department view in /panel includes live public URL.")

    # --------------------------------------------------------------------------
    # 5. Test Unified Agency OS Supervisor Architecture
    # --------------------------------------------------------------------------
    print("\n[5/5] Testing Unified Supervisor Configuration (run_agency_os.py)...")
    supervisor = run_agency_os.AgencyOSSupervisor()
    service_names = [s.name for s in supervisor.services]
    assert "WebPlatform" in service_names, "WebPlatform service missing"
    assert "TelegramBot" in service_names, "TelegramBot service missing"
    assert "CloudflareTunnel" in service_names, "CloudflareTunnel service missing"
    assert len(supervisor.services) == 3, f"Expected 3 managed services, found {len(supervisor.services)}"
    print(f"  ✓ Supervisor correctly manages 3 concurrent services: {', '.join(service_names)}")

    # Stop test tunnel cleanly
    tm.stop_tunnel()
    assert tm.get_status()["is_running"] is False, "Tunnel must be stopped"
    print("  ✓ Tunnel stopped cleanly after test.")

    print("\n==================================================================")
    print("🎉 ALL STAGE 5 TUNNEL TESTS PASSED 100% WITH ZERO ERRORS!")
    print("==================================================================")


if __name__ == "__main__":
    asyncio.run(main())
