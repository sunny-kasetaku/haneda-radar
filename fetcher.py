# ==========================================
# Project: KASETACK - fetcher.py
# ==========================================
import os
import time
import json
from config import CONFIG
from api_handler import AviationStackHandler

def run_fetch():
    raw_file = CONFIG["DATA_FILE"]
    if os.path.exists(raw_file):
        file_age = time.time() - os.path.getmtime(raw_file)
        if file_age < CONFIG["CACHE_LIMIT_SEC"]:
            print(f"♻️ キャッシュ利用")
            return True

    api_key = CONFIG.get("API_KEY")
    if not api_key: return False

    handler = AviationStackHandler(api_key)
    flights = handler.fetch_hnd_arrivals()
    if flights:
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(flights, f, ensure_ascii=False, indent=4)
        print(f"✅ 新規取得成功")
        return True
    return False
