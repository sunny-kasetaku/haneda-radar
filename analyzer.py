import os
import json
import re
from datetime import datetime
from config import CONFIG

def run_analyze():
    raw_file = CONFIG.get("DATA_FILE", "haneda_raw.html")
    result_file = CONFIG.get("RESULT_FILE", "analysis_result.json")
    
    print(f"--- KASETACK Analyzer v19.2: 完遂版 ---")
    
    # ファイルがない場合の空データ（KeyError防止用）
    empty_data = {
        "update_time": datetime.now().strftime("%H:%M"),
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "flights": [],
        "total_pax": 0,
        "total_flights": 0,
        "count": 0
    }

    if not os.path.exists(raw_file):
        return empty_data

    with open(raw_file, "r", encoding="utf-8") as f:
        html = f.read()

    airlines = {"JL": "日本航空", "NH": "全日本空輸", "HD": "エア・ドゥ", 
                "BC": "スカイマーク", "7G": "スターフライヤー", "6J": "ソラシドエア"}

    results = []
    seen = set()
    # あらゆる形式の便名を抽出 (JL123, NH 456, "JL123"など)
    matches = re.findall(r'([A-Z]{2})\s?(\d{2,4})', html, re.IGNORECASE)
    
    for code, num in matches:
        c = code.upper()
        if c in airlines:
            flight = f"{c}{num}"
            if flight not in seen:
                results.append({"time": "捕捉", "flight_no": flight, "airline": airlines[c], "status": "本物抽出"})
                seen.add(flight)

    output = {
        "update_time": datetime.now().strftime("%H:%M:%S"),
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "flights": results[:30],
        "total_pax": 0,
        "total_flights": len(results),
        "count": len(results)
    }

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print(f"✅ 解析完了: {len(results)} 件の本物データを捕捉しました。")
    return output

if __name__ == "__main__":
    run_analyze()
