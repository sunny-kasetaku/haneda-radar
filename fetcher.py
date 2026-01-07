import requests
import os
from config import CONFIG

def run_fetch():
    api_key = os.getenv("ZENROWS_API_KEY")
    # ターゲットを羽田空港公式サイト（国内線・到着）に変更
    target_url = "https://tokyo-haneda.com/flight/flight_list_dom.html"
    
    print(f"--- KASETACK Fetcher v3.5: 羽田公式サイト潜入テスト ---")
    
    if not api_key:
        print("❌ エラー: ZENROWS_API_KEY が設定されていません。")
        return False

    params = {
        "apikey": api_key,
        "url": target_url,
        "js_render": "true",       # 公式サイトはJS必須
        "antibot": "true",         # 念のための隠れ身
        "wait_for": ".flight_list_table" # 表が出るまで待機
    }

    try:
        print(f"🚀 羽田公式サイトへ潜入中 (タイムアウト120秒)...")
        response = requests.get("https://api.zenrows.com/v1/", params=params, timeout=120)
        
        if response.status_code == 200:
            content = response.text
            with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
                f.write(content)
            
            # 取得した中身に「航空会社」や「便名」に関連する言葉があるかチェック
            print(f"✅ 取得成功！ サイズ: {len(content)} bytes")
            if "JAL" in content or "ANA" in content or "航空" in content:
                print("✨ 確信：フライトデータらしき文字列を確認しました！プロジェクトは死んでいません。")
            else:
                print("⚠️ 取得はできましたが、中身が空かもしれません。解析が必要です。")
            return True
        else:
            print(f"❌ APIエラー: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 通信エラー: {e}")
        return False

if __name__ == "__main__":
    run_fetch()
