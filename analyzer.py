import os
import json
import re
from datetime import datetime
from config import CONFIG

def run_analyze():
    raw_file = CONFIG.get("DATA_FILE", "haneda_raw.html")
    result_file = CONFIG.get("RESULT_FILE", "analysis_result.json")
    
    print(f"--- KASETACK Analyzer v18.0: 本物抽出版 ---")
    
    if not os.path.exists(raw_file):
        print("❌ 生データファイルが見つかりません。")
        return {"flights": [], "count": 0, "total_pax": 0}

    with open(raw_file, "r", encoding="utf-8") as f:
        html = f.read()

    # 国内線の航空会社コード
    airlines = {"JL": "日本航空", "NH": "全日本空輸", "HD": "エア・ドゥ", 
                "BC": "スカイマーク", "7G": "スターフライヤー", "6J": "ソラシドエア"}

    results = []
    seen = set()
    
    # 【本物の抽出ロジック】生データから航空会社コード+数字のパターンを抽出
    # "JL123" や >NH456< などの形式を網羅します
    patterns = [r'([A-Z]{2})(\d{3,4})', r'"([A-Z]{2})(\d{3,4})"', r'>([A-Z]{2})(\d{3,4})<']
    
    for pattern in patterns:
        matches = re.findall(pattern, html)
        for code, num in matches:
            if code in airlines:
                flight = f"{code}{num}"
                if flight not in seen:
                    results.append({
                        "time": "捕捉", 
                        "flight_no": flight,
                        "airline": airlines[code],
                        "status": "生データより抽出"
                    })
                    seen.add(flight)

    # Rendererが欲しがっている項目を網羅して保存
    output = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "flights": results[:30],
        "total_pax": 0, # KeyError防止
        "count": len(results),
        "status": "success"
    }

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print(f"✅ 解析完了: {len(results)} 件の本物データを抽出しました。")
    return output

if __name__ == "__main__":
    run_analyze()
