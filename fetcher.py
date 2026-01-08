# ==========================================
# Project: KASETACK - fetcher.py
# ==========================================
import os
import time
import json
from config import CONFIG
from api_handler import AviationStackHandler

def run_fetch():
    print(f"--- KASETACK Fetcher ---")
    
    raw_file = CONFIG["DATA_FILE"]
    
    # 1. キャッシュチェック
    if os.path.exists(raw_file):
        file_age = time.time() - os.path.getmtime(raw_file)
        if file_age < CONFIG["CACHE_LIMIT_SEC"]:
            print(f"♻️ キャッシュ有効 ({int(file_age)}秒)")
            return True

    # 2. APIキー取得 (OS環境変数から CONFIG 参照へ変更)
    # --- [残存（コメントアウト）: 旧取得法] ---
    # api_key = os.getenv("AVIATIONSTACK_API_KEY")
    # ---------------------------------------
    api_key = CONFIG.get("API_KEY")
    
    if not api_key or api_key == "YOUR_AVIATIONSTACK_API_KEY_HERE":
        print("❌ APIキーが config.py に設定されていません")
        return False

    handler = AviationStackHandler(api_key)
    flights = handler.fetch_hnd_arrivals()

    if flights:
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(flights, f, ensure_ascii=False, indent=4)
        print(f"✅ データ新規取得完了")
        return True
    return False
