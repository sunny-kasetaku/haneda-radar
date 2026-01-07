import asyncio
from playwright.async_api import async_playwright
import os
from config import CONFIG

async def fetch_stealth():
    url = CONFIG["TARGET_URL"]
    print(f"--- KASETACK Fetcher v2.6: 確定待機版 ---")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
        )
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="load", timeout=60000)
            
            # 🌟 修正ポイント: Yahooの表（.listAirplane）が現れるまで最大15秒待つ
            print("⏳ フライト表の出現を待機中...")
            try:
                await page.wait_for_selector(".listAirplane", timeout=15000)
            except:
                print("⚠️ 表の特定に失敗しましたが、続行します。")
            
            content = await page.content()
            with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"✅ 取得成功。サイズ: {len(content)} bytes")
            await browser.close()
            return True
        except Exception as e:
            print(f"❌ 潜入失敗: {e}")
            await browser.close()
            return False

def run_fetch():
    return asyncio.run(fetch_stealth())

if __name__ == "__main__":
    run_fetch()
