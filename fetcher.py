import requests
import os
import time
from config import CONFIG

def run_fetch():
    api_key = os.getenv("ZENROWS_API_KEY")
    target_url = CONFIG["TARGET_URL"]
    
    print(f"--- KASETACK Fetcher v3.2: 軽量潜入版 ---")
    
    if not api_key:
        print("❌ エラー: ZENROWS_API_KEY が見つかりません。")
        return False

    # パラメータを最小限にして「待機エラー」を防ぎます
    params = {
        "apikey": api_key,
        "url": target_url,
        "js_render": "true",       # JSは動かす
        "premium_proxy": "true",    # ステルスも維持
        "proxy_country": "jp"       # 👈 日本の回線を明示的に指定
    }

    try:
        print(f"🚀 日本の一般回線から潜入中 (タイムアウト120秒)...")
        # 120秒あれば、JSのレンダリングは通常終わります
        response = requests.get("https://api.zenrows.com/v1/", params=params, timeout=120)
        response.raise_for_status()
        
        content = response.text
        with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✅ 取得完了。サイズ: {len(content)} bytes")
        return True
    except Exception as e:
        print(f"❌ 潜入失敗: {e}")
        return False

if __name__ == "__main__":
    run_fetch()
