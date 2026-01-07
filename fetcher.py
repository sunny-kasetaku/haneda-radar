import asyncio
from playwright.async_api import async_playwright
import os
from config import CONFIG

async def fetch_stealth():
    # 🌟 ここを修正：config.py の URL を使用するようにしました
    url = CONFIG["TARGET_URL"]
    
    print(f"--- KASETACK Fetcher v2.5: URL連動・確定版 ---")
    print(f"🚀 ターゲット: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Yahooはモバイル表示の方がシンプルで抜きやすいためiPhone偽装を継続
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
        )
        page = await context.new_page()
        
        try:
            # 潜入
            await page.goto(url, wait_until="load", timeout=60000)
            
            # Yahooは読み込みが早いため、待機は3秒で十分です
            print("⏳ データの展開を待機中...")
            await asyncio.sleep(3)
            
            content = await page.content()
            
            # 保存
            with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
                f.write(content)
            
            # 🌟 成功の証拠：サイズが劇的に小さくなるはずです（数万〜数十万バイト）
            print(f"✅ 取得成功。サイズ: {len(content)} bytes")
            
            # 簡易生存確認
            if "羽田" in content or "JAL" in content or "ANA" in content:
                print("✨ ログに日本語のフライト情報を確認！勝利は目前です。")
            
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
