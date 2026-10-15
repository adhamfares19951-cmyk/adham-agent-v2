import httpx
import json
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cookie_file = Path("sessions/facebook_cookies.json")
if not cookie_file.exists():
    print("Error: sessions/facebook_cookies.json not found!")
    sys.exit(1)

with open(cookie_file, "r", encoding="utf-8") as f:
    cookies = json.load(f)["cookies"]

c_user = cookies.get("c_user", "100087516376683")

# Common desktop headers
desktop_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}

print(f"[*] Authenticating with Facebook for user ID: {c_user}...")
all_items = []
seen_ids = set()

# Step 1: Fetch initial /saved/ page
with httpx.Client(headers=desktop_headers, cookies=cookies, timeout=25, follow_redirects=True) as client:
    resp = client.get("https://www.facebook.com/saved/")
    if resp.status_code != 200:
        print(f"Error fetching /saved/: Status {resp.status_code}")
        sys.exit(1)
    
    html = resp.text
    print(f"[+] Loaded main /saved/ page ({len(html)} bytes).")
    
    # Extract DTSG Token
    dtsg_m = re.findall(r'"DTSGInitialData",\[\],{"token":"([^"]+)"', html)
    if not dtsg_m:
        dtsg_m = re.findall(r'\["DTSGInitData",\[\],{"token":"([^"]+)"', html)
    if not dtsg_m:
        dtsg_m = re.findall(r'"token":"(NA[A-Za-z0-9_-]+:[0-9]+:[0-9]+)"', html)
    
    fb_dtsg = dtsg_m[0] if dtsg_m else "NAfwmkqhFIM72rROXdib3qDuaz-_dFTSHOmGWcXbcTsgRkZ4kS_2hhA:16:1789285954"
    print(f"[+] Extracted fb_dtsg token: {fb_dtsg[:30]}...")

    # Extract initial Relay stream cache
    matches = re.finditer(r'\["RelayPrefetchedStreamCache",\s*"next",\s*\[\],\s*\["(.*?)",\s*({.*?})\]\]', html)
    initial_cursor = None
    has_next_page = False
    
    for m in matches:
        key = m.group(1)
        if "CometSaveDashboardRoot" in key:
            try:
                val = json.loads(m.group(2))
                data = val.get("__bbox", {}).get("result", {}).get("data", {})
                all_saves = data.get("viewer", {}).get("saver_info", {}).get("all_saves", {})
                edges = all_saves.get("edges", [])
                pinfo = all_saves.get("page_info", {})
                has_next_page = pinfo.get("has_next_page", False)
                initial_cursor = pinfo.get("end_cursor")
                
                print(f"[+] Initial batch loaded: {len(edges)} items. Next page: {has_next_page}")
                for e in edges:
                    node = e.get("node", {})
                    nid = node.get("id")
                    if nid and nid not in seen_ids:
                        seen_ids.add(nid)
                        savable = node.get("savable", {}) or {}
                        container = node.get("container_savable", {}) or {}
                        actors = [a.get("name") for a in container.get("savable_actors", []) if a.get("name")]
                        lists = [l.get("name") for l in node.get("containing_lists", {}).get("nodes", []) if l.get("name")]
                        
                        all_items.append({
                            "id": nid,
                            "type": savable.get("__typename") or savable.get("savable_default_category"),
                            "title": (savable.get("savable_title") or {}).get("text", "").strip(),
                            "url": savable.get("url") or savable.get("savable_permalink"),
                            "author": ", ".join(actors) if actors else "غير محدد",
                            "collections": lists if lists else ["العامة"],
                            "attributes": [a.get("text") for a in savable.get("savable_attributes", []) if a.get("text")],
                        })
            except Exception as ex:
                print(f"Error parsing initial relay cache: {ex}")

# Step 2: Loop GraphQL Pagination
graphql_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.facebook.com",
    "Referer": "https://www.facebook.com/saved/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Fb-Friendly-Name": "CometSaveDashboardAllItemsPaginationQuery",
}

doc_id = "27174039202273427"
current_cursor = initial_cursor
page_num = 1
max_pages = 25  # Safety threshold up to 250 items

with httpx.Client(headers=graphql_headers, cookies=cookies, timeout=25) as client:
    while has_next_page and current_cursor and page_num <= max_pages:
        page_num += 1
        print(f"[*] Fetching page {page_num} (cursor: {current_cursor[:20]}...)...")
        payload = {
            "av": c_user,
            "__user": c_user,
            "__a": "1",
            "__req": str(page_num),
            "__hs": "20376.HYP:comet_pkg.2.1..0.0",
            "dpr": "1",
            "__ccg": "EXCELLENT",
            "__rev": "1016843400",
            "fb_dtsg": fb_dtsg,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "CometSaveDashboardAllItemsPaginationQuery",
            "variables": json.dumps({
                "count": 15,
                "cursor": current_cursor,
                "content_filter": None,
                "use_case": "SAVE_DEFAULT",
                "scale": 1,
            }),
            "doc_id": doc_id,
        }
        
        try:
            resp = client.post("https://www.facebook.com/api/graphql/", data=payload)
            if resp.status_code != 200:
                print(f"[!] GraphQL returned status {resp.status_code}")
                break
                
            lines = [l.strip() for l in resp.text.split("\n") if l.strip()]
            new_items_count = 0
            has_next_page = False
            
            for line in lines:
                try:
                    d = json.loads(line)
                    if "data" in d:
                        all_saves = d["data"].get("viewer", {}).get("saver_info", {}).get("all_saves", {})
                        edges = all_saves.get("edges", [])
                        pinfo = all_saves.get("page_info", {})
                        has_next_page = pinfo.get("has_next_page", False)
                        current_cursor = pinfo.get("end_cursor")
                        
                        for e in edges:
                            node = e.get("node", {})
                            nid = node.get("id")
                            if nid and nid not in seen_ids:
                                seen_ids.add(nid)
                                new_items_count += 1
                                savable = node.get("savable", {}) or {}
                                container = node.get("container_savable", {}) or {}
                                actors = [a.get("name") for a in container.get("savable_actors", []) if a.get("name")]
                                lists = [l.get("name") for l in node.get("containing_lists", {}).get("nodes", []) if l.get("name")]
                                
                                all_items.append({
                                    "id": nid,
                                    "type": savable.get("__typename") or savable.get("savable_default_category"),
                                    "title": (savable.get("savable_title") or {}).get("text", "").strip(),
                                    "url": savable.get("url") or savable.get("savable_permalink"),
                                    "author": ", ".join(actors) if actors else "غير محدد",
                                    "collections": lists if lists else ["العامة"],
                                    "attributes": [a.get("text") for a in savable.get("savable_attributes", []) if a.get("text")],
                                })
                except Exception:
                    pass
                    
            print(f"    -> Extracted {new_items_count} items from page {page_num}. Total so far: {len(all_items)}. Next page: {has_next_page}")
            if not new_items_count:
                print("[*] No new items in this batch; reached end.")
                break
                
            time.sleep(0.5)  # Respectful pacing
        except Exception as e:
            print(f"[!] Error on page {page_num}: {e}")
            break

print(f"\n==========================================")
print(f"[✓] CRAWL COMPLETE! Total saved items: {len(all_items)}")
print(f"==========================================")

# Save JSON file
json_output = Path("facebook_saved_items.json")
with open(json_output, "w", encoding="utf-8") as out:
    json.dump({
        "user_id": c_user,
        "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_items": len(all_items),
        "items": all_items
    }, out, ensure_ascii=False, indent=2)

print(f"[+] Saved structured JSON to: {json_output.resolve()}")

# Generate Clean Markdown Report
md_output = Path("facebook_saved_items.md")
with open(md_output, "w", encoding="utf-8") as f:
    f.write(f"# 📌 تقرير العناصر المحفوظة في فيسبوك (Facebook Saved Items)\n\n")
    f.write(f"- **المستخدم**: `{c_user}`\n")
    f.write(f"- **تاريخ وساعة الاستخراج**: `{time.strftime('%Y-%m-%d %H:%M:%S')}`\n")
    f.write(f"- **إجمالي العناصر المستخرجة**: **{len(all_items)} عنصراً**\n\n")
    f.write(f"---\n\n")
    
    # Group by collection
    by_coll = {}
    for it in all_items:
        for c in it["collections"]:
            by_coll.setdefault(c, []).append(it)
            
    f.write(f"## 🗂️ توزيع المجموعات والمجلدات:\n")
    for cname, citems in by_coll.items():
        f.write(f"- **مجموعة `{cname}`**: {len(citems)} عنصراً\n")
    f.write(f"\n---\n\n")
    
    f.write(f"## 📋 قائمة كافة العناصر المحفوظة:\n\n")
    for i, it in enumerate(all_items, 1):
        type_icon = "🎥 فيديو / ريلز" if "video" in str(it['type']).lower() else "📝 منشور"
        colls_str = ", ".join(it['collections'])
        f.write(f"### {i}. {it['title'][:90].replace(chr(10), ' ')}...\n")
        f.write(f"- **النوع**: {type_icon} (`{it['type']}`)\n")
        f.write(f"- **الناشر / المصدر**: **{it['author']}**\n")
        f.write(f"- **المجموعة**: `{colls_str}`\n")
        if it['attributes']:
            f.write(f"- **الوسوم**: {' | '.join(it['attributes'])}\n")
        f.write(f"- **الرابط المباشر**: [{it['url']}]({it['url']})\n\n")
        if it['title']:
            f.write(f"> **نص المنشور / الوصف**:\n> {it['title'].replace(chr(10), chr(10) + '> ')}\n\n")
        f.write(f"---\n\n")

print(f"[+] Saved Markdown report to: {md_output.resolve()}")
