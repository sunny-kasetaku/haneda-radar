import os
import json
import re
from datetime import datetime
from config import CONFIG

def run_analyze():
    raw_file = CONFIG.get("DATA_FILE", "haneda_raw.html")
    print(f"--- KASETACK Analyzer v21.0: APIデータ対応版 ---")
    
    if not os.path.exists(raw_file):
        return {"flights": [], "update_time": "--:--", "count": 0}

    # API版ではJSONとして読み込む
    try:
        with open(raw_file, "r", encoding="utf-8") as f:
            # --- [残存（コメントアウト）: Regex解析ロジック] ---
            # html = f.read()
            # patterns = [...]
            # for pattern in patterns:
            #     matches = re.findall(pattern, html)
            # ----------------------------------------------
            
            # APIから渡された構造化データを直接処理
            flights_data = json.load(f)
            
        results = flights_data # api_handlerで既に整形済み

    except json.JSONDecodeError:
        print("⚠️ HTML形式の旧データを検知しました。解析をスキップします。")
        return None

    output = {
        "update_time": datetime.now().strftime("%H:%M"),
        "flights": sorted(results, key=lambda x: x['flight_no'])[:40],
        "count": len(results),
        "total_pax": sum(f['pax'] for f in results) # 期待値の合計
    }

    with open(CONFIG["RESULT_FILE"], "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    
    print(f"✅ 解析完了: 合計期待値 {output['total_pax']} 名の需要を算出しました。")
    return output
