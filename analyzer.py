import os
import json
import re
from datetime import datetime
from config import CONFIG

def run_analyze():
    raw_file = CONFIG.get("DATA_FILE", "haneda_raw.html")
    result_file = CONFIG.get("RESULT_FILE", "analysis_result.json")
    
    print(f"--- KASETACK Analyzer v17.2: FR24深層解析版 ---")
    
    if not os.path.exists(raw_file):
        return {"flights": [], "count": 0}

    with open(raw_file, "r", encoding="utf-8") as f:
        html = f.read()

    # 国内線の航空会社コード
    airlines = {"JL": "日本航空", "NH": "全日本空輸", "HD": "エア・ドゥ", 
                "BC": "スカイマーク", "7G": "スターフライヤー", "6J": "ソラシドエア"}

    # Flightradar24のデータ構造（"identification":{"number":{"default":"JL123"}}など）から抽出
    # もっとも確実に「便名」が含まれるパターンを探します
    results = []
    seen = set()
    
    # パターン1: "JL123" のような引用符付き
    # パターン2: >JL123< のようなタグの間
    patterns = [r'"([A-Z]{2}\d{3,4})"', r'>([A-Z]{2}\d{3,4})<']
    
    for pattern in patterns:
        matches = re.findall(pattern, html)
        for flight in matches:
            code = flight[:2]
            if code in airlines and flight not in seen:
                results.append({
                    "time": datetime.now().strftime("%H:%M"), # 暫定
                    "flight_no": flight,
                    "airline": airlines[code],
                    "status": "捕捉成功"
                })
                seen.add(flight)

    output = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "flights": results[:30],
        "count": len(results)
    }

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print(f"✅ 解析完了: {len(results)} 件の国内線を捕捉しました！")
    return output

if __name__ == "__main__":
    run_analyze()
