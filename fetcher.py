import requests
import os
from config import CONFIG

def run_fetch():
    api_key = os.getenv("ZENROWS_API_KEY")
    target_url = CONFIG["TARGET_URL"]
    
    print(f"--- KASETACK Fetcher v3.3: 最終調整版 ---")
    
    if not api_key:
        print("❌ エラー: ZENROWS_API_KEY が見つかりません。")
        return False

    # 404を避けるため、パラメータを極限までシンプルにしました
    # js_render: Yahooの動的な表を出すために必須
    # antibot: ZenRows独自の「最強の隠れ身の術」を発動
    params = {
        "apikey": api_key,
        "url": target_url,
        "js_render": "true",
        "antibot": "true",      # 👈 premium_proxyより安定する場合があります
        "wait_for": ".listAirplane" # 👈 再びこれを追加（表が出るのを待つ）
    }

    try:
        print(f"🚀 ZenRows AIを起動。羽田へ最終潜入中...")
        # タイムアウトは長めの120秒を確保
        response = requests.get("https://api.zenrows.com/v1/", params=params, timeout=120)
        
        # エラーがあればここで詳細を表示
        if response.status_code != 200:
            print(f"❌ APIエラー報告: ステータスコード {response.status_code}")
            print(f"💡 内容: {response.text[:200]}") # エラーのヒントを表示
            return False
            
        with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print(f"✅ 取得成功！ 鉄壁のガードを突破しました。")
        return True
    except Exception as e:
        print(f"❌ 通信エラー: {e}")
        return False

if __name__ == "__main__":
    run_fetch()
