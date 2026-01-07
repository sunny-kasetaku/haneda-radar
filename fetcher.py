import asyncio
from playwright.async_api import async_playwright
import os
import sys
from config import CONFIG

async def fetch_flight_data():
    # URLはご提示いただいたものをそのまま継承
    url = "https://www.flightview.com/traveltools/FlightStatusByAirport.asp?airport=HND&at=A"
    
    print("--- KASETACK Fetcher v2.1: Playwright重装甲版 ---")
    
    async with async_playwright() as p:
        try:
            print(f"1. ターゲットURLに潜入中... (Browser: Chromium)")
            # ブラウザ起動
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # ページに移動し、ネットワークが落ち着くまで待機
            await page.goto(url, wait_until="networkidle")
            
            # 5秒待機（JavaScriptによるデータの書き換えを完全に待つ）
            print("2. データの完全展開を待機中 (5s)...")
            await asyncio.sleep(5)
            
            # 展開後のHTMLを取得
            content = await page.content()
            
            if len(content) < 1000: # Playwrightなら通常もっと大きくなるはず
                print("⚠️ 警告: 取得データが少なすぎます")
                await browser.close()
                return False

            # ファイル書き込み
            abs_path = os.path.abspath(CONFIG["DATA_FILE"])
            with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"3. ファイル書き込み完了: {abs_path}")

            # --- 継承：血の掟（精度向上のための調査パッチ） ---
            print("\n--- 🔍 データ中身の簡易調査（血の掟：Playwright実測版） ---")
            content_upper = content.upper()
            
            # キャリア存在チェック
            if any(x in content_upper for x in ["JAL", "JL ", "ANA", "NH "]):
                print("✅ 国内キャリア（JAL/ANA等）の記述が見つかりました！")
            else:
                print("⚠️ 警告：JAL/ANAが見当たりません。")

            # 機材名のヒントチェック
            equipments = ["777", "787", "A350", "737", "767", "A320"]
            found_eq = [eq for eq in equipments if eq in content_upper]
            if found_eq:
                print(f"✅ 機材のヒントを発見: {found_eq} (精度向上の鍵です)")
            else:
                print("ℹ️ 機材情報の記述は見つかりませんでした。")
            print("--------------------------------------------------\n")

            await browser.close()
            print("--- Fetcher 成功完了 ---")
            return True

        except Exception as e:
            print(f"❌ エラー: 潜入失敗: {e}")
            return False

def run_fetch():
    # 非同期処理をキック
    return asyncio.run(fetch_flight_data())

if __name__ == "__main__":
    run_fetch()
