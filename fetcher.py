import requests
import os
import time
from config import CONFIG

def run_fetch():
    api_key = os.getenv("ZENROWS_API_KEY")
    target_url = CONFIG["TARGET_URL"]
    
    print(f"--- KASETACK Fetcher v3.1: 粘り強い潜入版 ---")
    
    if not api_key:
        print("❌ エラー: ZENROWS_API_KEY が見つかりません。")
        return False

    params = {
        "apikey": api_key,
        "url": target_url,
        "js_render": "true",
        "premium_proxy": "true",
        "wait_for": ".listAirplane",
        "wait": "5000" # 追加：ページ読み込み後にさらに5秒待って安定させる
    }

    # 最大2回まで挑戦する
    for attempt in range(1, 3):
        try:
            print(f"🚀 潜入試行 {attempt}/2 回目 (タイムアウトを120秒に延長中)...")
            # timeoutを120秒に拡大して、じっくり待ちます
            response = requests.get("https://api.zenrows.com/v1/", params=params, timeout=120)
            response.raise_for_status()
            
            with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
                f.write(response.text)
            
            print(f"✅ 取得成功！ ついに本物のデータを掴みました。")
            return True
        except Exception as e:
            print(f"⚠️ 試行 {attempt} でエラーが発生: {e}")
            if attempt < 2:
                print("⏳ 5秒後に再試行します...")
                time.sleep(5)
    
    print("❌ 2回の試行とも失敗しました。")
    return False

if __name__ == "__main__":
    run_fetch()
