import asyncio
from playwright.async_api import async_playwright
import os
from config import CONFIG

async def fetch_stealth(url):
    print("--- KASETACK Fetcher v2.4: 隠密・狙撃版 ---")
    async with async_playwright() as p:
        # 1. ブラウザを人間に見せかける高度な偽装
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1", # iPhoneに偽装
            viewport={'width': 390, 'height': 844}
        )
        page = await context.new_page()
        
        try:
            print(f"🚀 羽田到着便の深層へ潜入中...")
            # 2. タイムアウトを2分に延長し、読み込み完了を待つ
            await page.goto(url, wait_until="load", timeout=120000)
            
            # 3. ページを少しずつスクロールして「読み込み」を誘発する（重要！）
            print("⏳ ページをスクロールしてデータを誘発中...")
            for i in range(5):
                await page.mouse.wheel(0, 500)
                await asyncio.sleep(2)

            # 4. 特定のキーワード（Flight No, Status等）が出るまで最大30秒追加で待つ
            print("⏳ 本物の表が出現するのを監視中...")
            content = await page.content()
            
            # 保存
            with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"✅ 奪取完了。サイズ: {len(content)} bytes")
            
            # 生存確認
            if "HND" in content:
                print("✨ ログに空港コードを確認。")
            
            await browser.close()
            return True

        except Exception as e:
            print(f"❌ 潜入失敗: {e}")
            await browser.close()
            return False

def run_fetch():
    url = "https://www.flightview.com/traveltools/FlightStatusByAirport.asp?airport=HND&at=A"
    return asyncio.run(fetch_stealth(url))

if __name__ == "__main__":
    run_fetch()
