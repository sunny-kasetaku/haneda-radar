import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v8.1: 暗黒大陸・全域探索版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        content = f.read()

    print(f"DEBUG: 総容量 {len(content)} bytes をスキャン中...")

    # --- 1. 都市名・キーワードの生存確認（日本語・英語両方） ---
    # 日本語の都市名が1つでもあるか？
    found_jap = [c for c in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]) if c in content]
    # 運行関連の英語があるか？
    keywords = ["ARRIVED", "LANDED", "ON TIME", "DELAYED", "SCHEDULED", "HND"]
    found_eng = [k for k in keywords if k in content.upper()]

    print(f"🔎 生存確認: 日本語キーワード={found_jap}")
    print(f"🔎 生存確認: 運行キーワード={found_eng}")

    # --- 2. もしキーワードが見つかったら、その周辺を強制露出 ---
    if found_eng:
        print("\n--- 📜 核心部の構造ダンプ ---")
        first_key = found_eng[0]
        pos = content.upper().find(first_key)
        # 前後500文字を出す。ここがフライト情報の「現場」です。
        dump = content[max(0, pos-300) : pos+700]
        # HTMLタグが邪魔な場合があるので、タグを除去した版も出す
        clean_dump = re.sub(r'<[^>]+>', ' ', dump)
        print(f"RAW: {dump}")
        print(f"CLEAN: {clean_dump}")

    # --- 3. JSONデータの断片を探す ---
    # FlightViewが裏側でJSONを持っている可能性
    json_blobs = re.findall(r'\{[^{}]*?"flight"[^{}]*?\}', content, re.IGNORECASE)
    if json_blobs:
        print(f"✅ JSON形式のフライトデータを {len(json_blobs)} 件発見しました！")
        print(f"SAMPLE: {json_blobs[0]}")

    # 集計処理（今回はデバッグ優先のため空）
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    result = {
        "stands": stands, "pool_preds": {k: 100 for k in stands},
        "total_pax": 0, "rows": [], "update_time": datetime.datetime.now().strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n2. 偵察完了。ログの【構造ダンプ】を解析に回します。")
    return result
