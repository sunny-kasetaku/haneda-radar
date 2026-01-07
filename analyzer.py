import os
import json
import re
from datetime import datetime
from config import CONFIG

def run_analyze():
    raw_file = CONFIG.get("DATA_FILE", "haneda_raw.html")
    result_file = CONFIG.get("RESULT_FILE", "analysis_result.json")
    
    print(f"--- KASETACK Analyzer v19.0: 名前一致版 ---")
    
    if not os.path.exists(raw_file):
        return {"flights": [], "update_time": "--:--", "total_pax": 0}

    with open(raw_file, "r", encoding="utf-8") as f:
        html = f.read()

    airlines = {"JL": "日本航空", "NH": "全日本空輸", "HD": "エア・ドゥ", 
                "BC": "スカイマーク", "7G": "スターフライヤー", "6J": "ソラシドエア"}

    results = []
    seen = set()
    # 広範囲な便名抽出（大文字小文字問わず）
    matches = re.findall(r'([A-Z]{2})\s?(\d{2,4})', html, re.IGNORECASE)
    
    for code, num in matches:
        code = code.upper()
        if code in airlines:
            flight = f"{code}{num}"
            if flight not in seen:
                results.append({"time": "捕捉", "flight_no": flight, "airline": airlines[code], "status": "生データ抽出"})
                seen.add(flight)

    # ❗ haneda_radar.py が欲しがっている名前（update_time）に修正
    output = {
        "update_time": datetime.now().strftime("%H:%M:%S"), # 👈 名前を修正
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "flights": results[:30],
        "total_pax": 0,
        "count": len(results)
    }

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print(f"✅ 解析完了: {len(results)} 件の本物データを抽出")
    return output

if __name__ == "__main__":
    run_analyze()
