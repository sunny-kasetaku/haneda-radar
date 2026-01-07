import requests
import os
from config import CONFIG

def run_fetch():
    api_key = os.getenv("ZENROWS_API_KEY")
    target_url = CONFIG["TARGET_URL"]
    
    print(f"--- KASETACK Fetcher v3.6: Flightradar24 安定版 ---")
    
    if not api_key:
        print("❌ エラー: ZENROWS_API_KEY が設定されていません。")
        return False

    params = {
        "apikey": api_key,
        "url": target_url,
        "js_render": "true",
        "antibot": "true"
    }

    try:
        print(f"🚀 Flightradar24へ潜入中 (タイムアウト180秒)...")
        response = requests.get("https://api.zenrows.com/v1/", params=params, timeout=180)
        
        if response.status_code == 200:
            with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"✅ 取得成功！ サイズ: {len(response.text)} bytes")
            return True
        else:
            print(f"❌ APIエラー: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 通信エラー: {e}")
        return False

if __name__ == "__main__":
    run_fetch()
