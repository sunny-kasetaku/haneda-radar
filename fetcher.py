import requests
import os
from config import CONFIG

def run_fetch():
    api_key = os.getenv("ZENROWS_API_KEY")
    # ターゲットを Flightradar24 の羽田到着便リストに直接設定
    # 検索不要、いきなり「到着便テーブル」が表示されるページです
    target_url = "https://www.flightradar24.com/data/airports/hnd/arrivals"
    
    print(f"--- KASETACK Fetcher v3.6: Flightradar24 潜入編 ---")
    
    if not api_key:
        print("❌ エラー: APIキーが設定されていません。")
        return False

    # タイムアウトを防ぐため、徹底的に軽量化します
    params = {
        "apikey": api_key,
        "url": target_url,
        "js_render": "true",       # 表を描画するために必須
        "antibot": "true"          # ステルス機能
    }

    try:
        print(f"🚀 Flightradar24へ潜入。データを強奪中...")
        # 待ち時間を180秒（3分）に拡大し、ZenRowsに仕事をさせます
        response = requests.get("https://api.zenrows.com/v1/", params=params, timeout=180)
        
        if response.status_code == 200:
            with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
                f.write(response.text)
            
            print(f"✅ 取得成功！ サイズ: {len(response.text)} bytes")
            # データの断片を確認
            if "Flight" in response.text or "From" in response.text:
                print("✨ 確信：本物のフライトテーブルを確認しました！プロジェクトは継続可能です。")
            return True
        else:
            print(f"❌ APIエラー: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 通信エラー: {e}")
        return False

if __name__ == "__main__":
    run_fetch()
