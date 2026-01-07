import requests
import os
from config import CONFIG

def run_fetch():
    # GitHubの金庫からキーを呼び出します
    api_key = os.getenv("ZENROWS_API_KEY")
    target_url = CONFIG["TARGET_URL"]
    
    print(f"--- KASETACK Fetcher v3.0: ZenRows 搭載版 ---")
    
    if not api_key:
        print("❌ エラー: ZENROWS_API_KEY が見つかりません。")
        return False

    # 魔法の設定：一般人のフリをしてJavaScriptを動かした後のHTMLを貰う
    params = {
        "apikey": api_key,
        "url": target_url,
        "js_render": "true",       # JSを動かす
        "premium_proxy": "true",    # 一般家庭のIPを使う（これが最強のステルス）
        "wait_for": ".listAirplane" # フライト表が出るまで待つ
    }

    try:
        print(f"🚀 プロ用API経由で羽田へ潜入開始...")
        response = requests.get("https://api.zenrows.com/v1/", params=params, timeout=60)
        response.raise_for_status()
        
        with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print(f"✅ 取得成功！ 本物のデータを持ち帰りました。")
        return True
    except Exception as e:
        print(f"❌ API潜入失敗: {e}")
        return False

if __name__ == "__main__":
    run_fetch()
