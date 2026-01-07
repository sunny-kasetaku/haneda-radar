import asyncio
from playwright.async_api import async_playwright
import os
from config import CONFIG

async def fetch_stealth():
    url = CONFIG["TARGET_URL"]
    print(f"--- KASETACK Fetcher v2.7: ステルス突破版 ---")
    
    async with async_playwright() as p:
        # ステルス性を高めるため、ブラウザ起動オプションを調整
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            viewport={'width': 390, 'height': 844},
            is_mobile=True
        )
        
        # ボット検知回避用のスクリプト注入 (webdriver: false)
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        
        try:
            print(f"🚀 ターゲットに潜入中: {url}")
            # ページ読み込み完了まで待機
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 🌟 最重要: JavaScriptが動いて「フライト表」が現れるのを最大20秒待つ
            # 以前のログにあった「JavaScriptを有効に〜」をこれで突破します
            print("⏳ JavaScriptの展開を待機中...")
            await page.wait_for_timeout(5000) # 強制的に5秒待機して安定させる
            
            # フライト情報のリスト（.listAirplane）が現れるか確認
            try:
                await page.wait_for_selector(".listAirplane", timeout=15000)
                print("✅ フライト表を確認。本物のデータを捕捉しました。")
            except:
                print("⚠️ フライト表が見当たりません。ページ構造が特殊な可能性があります。")
            
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
