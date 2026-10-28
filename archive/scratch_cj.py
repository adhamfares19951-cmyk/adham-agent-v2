import asyncio
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright


async def main():
    with open("C:/Projects/adham-agent/workspace_data/cj_cookies.json", "r", encoding="utf-8") as f:
        cookies = json.load(f)
    pw_cookies = [
        {"name": c["name"], "value": c["value"], "domain": c["domain"], "path": c.get("path", "/")}
        for c in cookies
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies(pw_cookies)
        page = await context.new_page()

        print("Navigating to CJ Trending Products...")
        await page.goto("https://cjdropshipping.com/list/trending-products", wait_until="domcontentloaded", timeout=40000)
        await asyncio.sleep(6)

        # Extract product cards from DOM
        js_code = """
        () => {
            const cards = document.querySelectorAll('.product-card, .goods-item, div[class*="productCard"], div[class*="product-card"], a[href*="/product/"]');
            const list = [];
            const seen = new Set();
            cards.forEach(c => {
                const titleEl = c.querySelector('h3, [class*="title"], [class*="name"], [title]');
                const priceEl = c.querySelector('[class*="price"], [class*="amount"]');
                const imgEl = c.querySelector('img');
                const linkEl = c.tagName === 'A' ? c : c.querySelector('a');
                
                let title = titleEl ? (titleEl.innerText || titleEl.getAttribute('title') || '') : '';
                let price = priceEl ? priceEl.innerText : '';
                let img = imgEl ? (imgEl.src || imgEl.getAttribute('data-src') || '') : '';
                let link = linkEl ? linkEl.href : '';
                
                title = title.trim();
                price = price.trim();
                if (title && title.length > 5 && !seen.has(title)) {
                    seen.add(title);
                    list.push({title, price, img, link});
                }
            });
            return list;
        }
        """
        items = await page.evaluate(js_code)
        print(f"Total extracted: {len(items)}")

        # Save to json file
        with open("C:/Projects/adham-agent/workspace_data/cj_trending.json", "w", encoding="utf-8") as out_f:
            json.dump(items, out_f, ensure_ascii=False, indent=2)

        for i, it in enumerate(items[:10]):
            print(f"\n[{i+1}] {it['title']}")
            print(f"    💰 Price: {it['price']}")
            print(f"    🔗 Link: {it['link']}")
            print(f"    🖼️ Img: {it['img']}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
