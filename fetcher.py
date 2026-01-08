import os
import time
import json
from config import CONFIG
from api_handler_20260108_1534 import AviationStackHandler

def run_fetch():
    print(f"--- KASETACK Fetcher v4.1: キャッシュ優先モード ---")
    
    # キャッシュチェック
    raw_file = CONFIG["DATA_FILE"]
    if os.path.exists(raw_file):
        file_age = time.time() - os.path.getmtime(raw_file)
        if file_age < CONFIG["CACHE_LIMIT_SEC"]:
            print(f"♻️ キャッシュ有効 (経過: {int(file_age)}秒)。API通信をスキップします。")
            return True

    # --- [残存（コメントアウト）: ZenRowsスクレイピング] ---
    # api_key = os.getenv("ZENROWS_API_KEY")
    # params = { ... }
    # response = requests.get("https://api.zenrows.com/v1/", params=params)
    # ---------------------------------------------------

    # --- [修正箇所: APIキーを直接指定] ---
    # 以下の "" の中に、取得したAviationstackのAPIキーを貼り付けてください
    api_key = "ここに取得したキーを貼り付け" 
    
    if not api_key or api_key == "ここに取得したキーを貼り付け":
        print("❌ APIキーが正しく設定されていません。キーを入力してください。")
        return False

    handler = AviationStackHandler(api_key)
    flights = handler.fetch_hnd_arrivals()

    if flights:
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(flights, f, ensure_ascii=False, indent=4)
        print(f"✅ API新規取得成功: {len(flights)} 件")
        return True
    
    return False
