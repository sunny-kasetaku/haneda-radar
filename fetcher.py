import os
import time
import json
from config import CONFIG

# --- [修正箇所: 累積加算（引かずに足す）] ---
# --- [残存（コメントアウト）: 20260108_1534 エラー箇所] ---
# from api_handler_20260108_1534 import AviationStackHandler
# -------------------------------------------------------

# 汎用的な名前に修正
from api_handler import AviationStackHandler

def run_fetch():
    print(f"--- KASETACK Fetcher v4.3: インポート固定版 ---")
    
    raw_file = CONFIG["DATA_FILE"]
    if os.path.exists(raw_file):
        file_age = time.time() - os.path.getmtime(raw_file)
        if file_age < CONFIG["CACHE_LIMIT_SEC"]:
            print(f"♻️ キャッシュ有効 ({int(file_age)}秒経過)。")
            return True

    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    if not api_key:
        print("❌ APIキー未設定")
        return False

    handler = AviationStackHandler(api_key)
    flights = handler.fetch_hnd_arrivals()

    if flights:
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(flights, f, ensure_ascii=False, indent=4)
        print(f"✅ API新規取得成功: {len(flights)} 件")
        return True
    
    return False
