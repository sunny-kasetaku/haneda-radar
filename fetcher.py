import requests
import os
from config import CONFIG

def run_fetch():
    api_key = os.getenv("ZENROWS_API_KEY")
    print(f"--- KASETACK Fetcher v3.8: 422回避・安定版 ---")
    
    if not api_key:
        print("❌ APIキー未設定")
        return False

    # wait_for を外し、単純な wait (ミリ秒) に変更することで422を回避
    params = {
        "apikey": api_key,
        "url": CONFIG["TARGET_URL"],
        "js_render": "true",
        "antibot": "true",
        "wait": "5000", # 5秒間、JavaScriptの描画を待機
        "premium_proxy": "true"
    }

    try:
        print(f"🚀 Flightradar24へ潜入。描画を5秒間待ちます...")
        response = requests.get("https://api.zenrows.com/v1/", params=params, timeout=180)
        
        if response.status_code == 200:
            with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"✅ 取得成功: {len(response.text)} bytes")
            return True
        else:
            print(f"❌ エラー発生 (Code: {response.status_code})")
            print(f"💡 内容: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ 通信失敗: {e}")
        return False

if __name__ == "__main__":
    run_fetch()
