import requests
import os
from config import CONFIG

def run_fetch():
    api_key = os.getenv("ZENROWS_API_KEY")
    print(f"--- KASETACK Fetcher v3.7: 完遂版 ---")
    
    if not api_key:
        print("❌ APIキー未設定")
        return False

    params = {
        "apikey": api_key,
        "url": CONFIG["TARGET_URL"],
        "js_render": "true",
        "antibot": "true",
        "wait_for": CONFIG["WAIT_SELECTOR"], # 👈 表が出るまで最大2分待機
        "premium_proxy": "true"
    }

    try:
        print(f"🚀 Flightradar24の表が出るまで粘ります...")
        response = requests.get("https://api.zenrows.com/v1/", params=params, timeout=150)
        
        if response.status_code == 200:
            with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"✅ 取得成功: {len(response.text)} bytes")
            return True
        else:
            print(f"❌ エラー: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 通信失敗: {e}")
        return False

if __name__ == "__main__":
    run_fetch()
