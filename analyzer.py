import os
import json
import re
from datetime import datetime
from config import CONFIG

def run_analyze():
    raw_file = CONFIG.get("DATA_FILE", "haneda_raw.html")
    result_file = CONFIG.get("RESULT_FILE", "analysis_result.json")
    
    print(f"--- KASETACK Analyzer v17.1: Flightradar24 安定版 ---")
    
    if not os.path.exists(raw_file):
        print(f"❌ 解析対象の {raw_file} が見つかりません。")
        return {"flights": [], "count": 0}

    with open(raw_file, "r", encoding="utf-8") as f:
        html = f.read()

    # 国内線の航空会社コード
    airlines = {
        "JL": "日本航空", "NH": "全日本空輸", "HD": "エア・ドゥ",
        "BC": "スカイマーク", "7G": "スターフライヤー", "6J": "ソラシドエア"
    }

    # 便名（例: JL123, NH456）を抽出する正規表現
    flight_matches = re.findall(r'([A-Z]{2}\d{3,4})', html)
    
    results = []
    seen = set()
    
    for flight in flight_matches:
        code = flight[:2]
        if code in airlines and flight not in seen:
            results.append({
                "time": "確認中",
                "flight_no": flight,
                "airline": airlines[code],
                "status": "捕捉成功"
            })
            seen.add(flight)

    # 保存用データ構造
    output = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "flights": results[:30], # 上位30件
        "count": len(results),
        "status": "success"
    }

    # JSON保存
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print(f"✅ 解析完了: {len(results)} 件の国内線を捕捉しました。")
    return output

if __name__ == "__main__":
    run_analyze()
