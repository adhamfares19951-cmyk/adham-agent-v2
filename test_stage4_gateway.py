"""Comprehensive Test Suite for Stage 4:
- Central API Gateway (SQLite Caching, Token-Bucket Rate Limiter, Retry Logic)
- Live Data Hub (Gold XAU, Bitcoin BTC, Forex USD/ILS, IP-API, OpenStreetMap)
- Tools Registration & Integration in tools._TOOLS
- Unified Agency OS Runner Architecture & Panel Callbacks
"""
import asyncio
import os
import sys
import time

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from core.api_gateway import APIGateway, get_api_gateway, TokenBucket
from tools import live_data_hub
import tools


async def main():
    print("==================================================================")
    print("🚀 STARTING STAGE 4: CENTRAL GATEWAY & LIVE DATA HUB TEST SUITE")
    print("==================================================================")

    # --------------------------------------------------------------------------
    # 1. Test Token-Bucket Rate Limiter
    # --------------------------------------------------------------------------
    print("\n[1/5] Testing Token-Bucket Rate Limiter...")
    bucket = TokenBucket(capacity=2.0, refill_rate=2.0)
    w1 = await bucket.acquire(1.0)
    assert w1 == 0.0, "First token acquire should not wait"
    w2 = await bucket.acquire(1.0)
    assert w2 == 0.0, "Second token acquire should not wait"
    t_start = time.monotonic()
    w3 = await bucket.acquire(1.0)
    elapsed = time.monotonic() - t_start
    assert elapsed >= 0.4, f"Depleted bucket should wait for refill, elapsed={elapsed:.2f}s"
    print(f"  ✓ TokenBucket rate limiter successfully throttled burst (waited {elapsed:.2f}s)")

    # --------------------------------------------------------------------------
    # 2. Test APIGateway Persistent SQLite Caching
    # --------------------------------------------------------------------------
    print("\n[2/5] Testing APIGateway SQLite Caching & TTL...")
    gw = get_api_gateway()
    test_url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

    # Call 1: Force live network request
    t0 = time.monotonic()
    resp1 = await gw.get(test_url, ttl_seconds=60, force_refresh=True)
    lat1 = int((time.monotonic() - t0) * 1000)
    assert resp1.status_code == 200, f"Expected HTTP 200, got {resp1.status_code}"
    assert resp1.cache_hit is False, "First request must be live (cache_hit=False)"
    data1 = resp1.json()
    assert "price" in data1, "Binance response must contain 'price'"
    print(f"  ✓ Live Network Request: {test_url} -> HTTP 200 ({lat1}ms) - Price: {data1.get('price')}")

    # Call 2: Must be served from cache with near-zero latency
    t0 = time.monotonic()
    resp2 = await gw.get(test_url, ttl_seconds=60)
    lat2 = int((time.monotonic() - t0) * 1000)
    assert resp2.status_code == 200, f"Expected HTTP 200, got {resp2.status_code}"
    assert resp2.cache_hit is True, "Second request must be served from cache (cache_hit=True)"
    assert lat2 <= 50, f"Cache latency should be <50ms, got {lat2}ms"
    print(f"  ✓ SQLite Cache HIT: Latency dropped from {lat1}ms to {lat2}ms (Cache Hit: True)")

    stats = gw.get_cache_stats()
    assert stats["active_entries"] >= 1, "Cache must have active entries"
    print(f"  ✓ Cache Table Stats verified: {stats}")

    # --------------------------------------------------------------------------
    # 3. Test Live Data Hub: Financial Markets & Gold Radar
    # --------------------------------------------------------------------------
    print("\n[3/5] Testing Live Financial Markets Radar (Gold, BTC, Forex)...")
    market_data = await live_data_hub.get_live_market_prices()
    assert "gold" in market_data, "Market data must contain 'gold'"
    assert "crypto" in market_data, "Market data must contain 'crypto'"
    assert "forex" in market_data, "Market data must contain 'forex'"

    gold_price = market_data.get("gold", {}).get("price", 0.0)
    btc_price = market_data.get("crypto", {}).get("BTC/USDT", {}).get("price", 0.0)
    ils_rate = market_data.get("forex", {}).get("USD/ILS", 0.0)

    assert gold_price > 1000.0, f"Gold price seems invalid: {gold_price}"
    assert btc_price > 10000.0, f"Bitcoin price seems invalid: {btc_price}"
    assert ils_rate > 2.0, f"USD/ILS rate seems invalid: {ils_rate}"

    report = live_data_hub.format_market_prices_report(market_data)
    assert "الذهب العالمي" in report, "Report must mention gold"
    assert "العملات الرقمية" in report, "Report must mention crypto"
    print(f"  ✓ Live Gold Price:    ${gold_price:,.2f} / oz")
    print(f"  ✓ Live Bitcoin Price: ${btc_price:,.2f}")
    print(f"  ✓ Live USD/ILS Rate:  {ils_rate} ₪")
    print("  ✓ Financial Bulletin formatted cleanly in Arabic.")

    # --------------------------------------------------------------------------
    # 4. Test Live Data Hub: Engineering IP & OpenStreetMap
    # --------------------------------------------------------------------------
    print("\n[4/5] Testing Engineering IP Diagnostic & OpenStreetMap Radar...")
    # IP Test
    target_ip = "1.1.1.1"
    net_data = await live_data_hub.inspect_network_target(target_ip)
    assert net_data.get("status") == "success", f"IP diagnostic failed: {net_data}"
    assert "Cloudflare" in (net_data.get("isp") or "") or "APNIC" in (net_data.get("as") or ""), "ISP/AS mismatch"
    print(f"  ✓ Network Target Diagnostic: {target_ip} -> ISP: {net_data.get('isp')} | AS: {net_data.get('as')}")

    # OSM Test
    osm_items = await live_data_hub.search_osm_businesses(query="supermarket", location="Khan Yunis", limit=2)
    assert len(osm_items) > 0, "OpenStreetMap should return at least 1 venue in Khan Yunis"
    first_biz = osm_items[0]
    assert first_biz.get("name"), "Venue must have a name"
    assert first_biz.get("osm_url"), "Venue must have an OSM URL"
    print(f"  ✓ OpenStreetMap Discovery: Found {len(osm_items)} real venues in Khan Yunis")
    print(f"    - First Venue: '{first_biz['name']}' ({first_biz.get('category')}) -> {first_biz.get('osm_url')[:45]}...")

    # --------------------------------------------------------------------------
    # 5. Test Tools Registry & Unified OS Runner Components
    # --------------------------------------------------------------------------
    print("\n[5/5] Testing Tools Registration & Unified Runner Integrity...")
    required_tools = [
        "get_live_market_prices",
        "inspect_network_target",
        "search_osm_businesses",
        "get_api_gateway_status",
    ]
    for r_tool in required_tools:
        assert r_tool in tools._TOOLS, f"Tool '{r_tool}' must be registered in tools._TOOLS"
    print(f"  ✓ All {len(required_tools)} Live Data Hub tools registered in tools._TOOLS")

    # Verify run_agency_os.py exists and parses cleanly
    import run_agency_os
    supervisor = run_agency_os.AgencyOSSupervisor()
    assert len(supervisor.services) >= 2, "Supervisor must manage WebPlatform, TelegramBot, and services"
    print(f"  ✓ Unified Agency OS Supervisor validated ({len(supervisor.services)} services configured)")

    # Verify start_agency_os.bat exists
    assert os.path.exists("start_agency_os.bat"), "start_agency_os.bat must exist"
    assert os.path.getsize("start_agency_os.bat") > 50, "start_agency_os.bat must not be empty"
    print("  ✓ start_agency_os.bat launcher verified.")

    # Clean up gateway client
    await gw.close()

    print("\n==================================================================")
    print("🎉 ALL STAGE 4 TESTS PASSED 100% WITH ZERO ERRORS!")
    print("==================================================================")


if __name__ == "__main__":
    asyncio.run(main())
