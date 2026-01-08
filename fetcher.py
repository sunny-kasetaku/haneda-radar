import os
from config import CONFIG
# 新規APIハンドラーをインポート
from api_handler_20260108_1455 import AviationStackHandler

def run_fetch():
    # --- [残存（コメントアウト）: ZenRowsスクレイピング 20260108_1028] ---
    # api_key = os.getenv("ZENROWS_API_KEY")
    # params = {
    #     "apikey": api_key,
    #     "url": CONFIG["TARGET_URL"],
    #     "js_render": "true",
    #     "antibot": "true",
    #     "wait": "5000",
    #     "premium_proxy": "true"
    # }
    # response = requests.get("https://api.zenrows.com/v1/", params=params)
    # ...
    # ---------------------------------------------------------------

    print(f"--- KASETACK Fetcher v4.0: API実装版 ---")
    
    # Aviationstack APIキーを取得（環境変数またはconfigから）
    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    
    if not api_key:
        print("❌ APIキー(AVIATIONSTACK_API_KEY)が設定されていません")
        return False

    handler = AviationStackHandler(api_key)
    flights = handler.fetch_hnd_arrivals()

    if flights:
        # 解析用に中間データをJSONで保存（analyzer.pyが読み取れる形式にする）
        import json
        with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
            json.dump(flights, f, ensure_ascii=False, indent=4)
        print(f"✅ API取得成功: {len(flights)} 件のフライトデータを確保")
        return True
    
    return False
