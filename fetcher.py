import asyncio
from playwright.async_api import async_playwright
import os
from config import CONFIG

async def fetch_flight_data():
    url = "https://www.flightview.com/traveltools/FlightStatusByAirport.asp?airport=HND&at=A"
    print("--- KASETACK Fetcher v2.2: 柔軟待機・実利主義版 ---")
    
    async with async_playwright() as p:
        try:
            # ブラウザ起動（少しだけ偽装を強化）
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            print(f"1. ターゲットURLに潜入開始...")
            
            # 待機条件を "load" (基本の読込完了) に変更し、タイムアウトを60秒に延長
            await page.goto(url, wait_until="load", timeout=60000)
            
            # 画面が真っ白な時間を考慮し、5秒ではなく10秒じっくり待ちます
            print("2. JavaScriptによる表の生成を待機中 (10s)...")
            await asyncio.sleep(10)
            
            # 展開後のHTMLを取得
            content = await page.content()
            
            # ファイル書き込み
            with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"3. ファイル保存完了。サイズ: {len(content)} bytes")

            # --- 🔍 血の掟：簡易調査ログ ---
            print("\n--- 🔍 データ中身の簡易調査（Playwright実測） ---")
            content_upper = content.upper()
            if any(x in content_upper for x in ["JAL", "ANA", "JL ", "NH "]):
                print("✅ キャリア発見！ 本物のデータを掴んだ可能性大です。")
            else:
                print("⚠️ まだJAL/ANAが見えません。待機時間が足りないか、表示形式が違います。")
            print("--------------------------------------------------\n")

            await browser.close()
            return True

        except Exception as e:
            print(f"❌ エラー: 潜入中にトラブル発生: {e}")
            return False

def run_fetch():
    return asyncio.run(fetch_flight_data())

if __name__ == "__main__":
    run_fetch()
