import os
import time
import json
from config import CONFIG
from api_handler import AviationStackHandler

def run_fetch():
    print(f"--- KASETACK Fetcher ---")
    raw_file = CONFIG["DATA_FILE"]

    # --- [累積加算：旧キャッシュロジック（暫定版）] ---
    # if os.path.exists(raw_file): return True
    # ----------------------------------------------

    # 最新キャッシュ判定
    if os.path.exists(raw_file):
        file_age = time.time() - os.path.getmtime(raw_file)
        if file_age < CONFIG["CACHE_LIMIT_SEC"]:
            print(f"♻️ キャッシュ利用中 ({int(file_age)}秒)")
            return True

    # --- [累積加算：ZenRowsスクレイピング（API移行前）] ---
    # api_key = os.getenv("ZENROWS_API_KEY")
    # url = f"https://api.zenrows.com/v1/?apikey={api_key}&url={target_url}"
    # ---------------------------------------------------

    api_key = CONFIG.get("API_KEY")
    if not api_key: return False

    handler = AviationStackHandler(api_key)
    flights = handler.fetch_hnd_arrivals()
    if flights:
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(flights, f, ensure_ascii=False, indent=4)
        print(f"✅ データ新規取得成功")
        return True
    return False
