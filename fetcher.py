import asyncio
from playwright.async_api import async_playwright
import os
from config import CONFIG

async def fetch_with_retry(url, max_retries=3):
    print(f"--- KASETACK Fetcher v2.3: 不屈の奪取版 ---")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 人間に見せかけるためのコンテキスト設定
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        for attempt in range(max_retries):
            page = await context.new_page()
            # タイムアウトを90秒に延長
            page.set_default_timeout(90000)
            
            try:
                print(f"🚀 潜入試行 {attempt + 1}/{max_retries}...")
                
                # "domcontentloaded" は "load" より早めに切り上げます
                await page.goto(url, wait_until="domcontentloaded")
                
                # 重要なデータ（JavaScript）が動くのを15秒じっくり待ちます
                print("⏳ データの展開を待機中 (15s)...")
                await asyncio.sleep(15)
                
                content = await page.content()
                
                if len(content) > 10000:
                    with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"✅ 奪取成功！ サイズ: {len(content)} bytes")
                    
                    # 簡易調査
                    if "JAL" in content.upper() or "ANA" in content.upper():
                        print("✨ ログにJAL/ANAを確認。勝利は近いです。")
                    
                    await browser.close()
                    return True
                else:
                    print("⚠️ データが薄すぎます。リトライします。")
                    
            except Exception as e:
                print(f"❌ 試行 {attempt + 1} 失敗: {str(e)[:100]}")
            
            finally:
                await page.close()
                
            # リトライ前に少し休憩
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
                
        await browser.close()
        return False

def run_fetch():
    url = "https://www.flightview.com/traveltools/FlightStatusByAirport.asp?airport=HND&at=A"
    return asyncio.run(fetch_with_retry(url))

if __name__ == "__main__":
    run_fetch()
