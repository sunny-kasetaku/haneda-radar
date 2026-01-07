import os, json, re
from datetime import datetime
from config import CONFIG

def run_analyze():
    raw_file = CONFIG.get("DATA_FILE", "haneda_raw.html")
    print(f"--- KASETACK Analyzer: 捕捉力強化版 ---")
    
    if not os.path.exists(raw_file):
        return {"flights": [], "update_time": "--:--"}

    with open(raw_file, "r", encoding="utf-8") as f:
        html = f.read()

    # 抽出ターゲットをさらに拡大 (BC/JL/NH/HD/7G/6J)
    airlines = {"JL": "日本航空", "NH": "全日本空輸", "HD": "エア・ドゥ", 
                "BC": "スカイマーク", "7G": "スターフライヤー", "6J": "ソラシドエア"}

    results = []
    seen = set()
    # "flight":"JL123" のようなJSON形式も、タグ形式もすべて網羅
    matches = re.findall(r'([A-Z]{2})\s?(\d{2,4})', html, re.IGNORECASE)
    
    for code, num in matches:
        c = code.upper()
        if c in airlines:
            flight = f"{c}{num}"
            if flight not in seen:
                results.append({"flight_no": flight, "airline": airlines[c]})
                seen.add(flight)

    output = {
        "update_time": datetime.now().strftime("%H:%M:%S"),
        "flights": results[:40],
        "count": len(results)
    }

    with open(CONFIG["RESULT_FILE"], "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    
    print(f"✅ 解析完了: {len(results)} 件捕捉")
    return output
