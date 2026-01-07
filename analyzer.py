import os
import json
import re
from datetime import datetime
from config import CONFIG

def run_analyze():
    raw_file = CONFIG.get("DATA_FILE", "haneda_raw.html")
    print(f"--- KASETACK Analyzer v20.0: 深層解析版 ---")
    
    if not os.path.exists(raw_file):
        return {"flights": [], "update_time": "--:--", "count": 0}

    with open(raw_file, "r", encoding="utf-8") as f:
        html = f.read()

    # 国内航空会社マッピング
    airlines = {"JL": "日本航空", "NH": "全日本空輸", "HD": "エア・ドゥ", 
                "BC": "スカイマーク", "7G": "スターフライヤー", "6J": "ソラシドエア"}

    results = []
    seen = set()

    # 戦略：HTML内の JSON 構造体 ("identification":{"number":{"default":"BC77"}}) を狙う
    # 便名（例: BC77, JL123）の抽出精度を極限まで高めます
    patterns = [
        r'"default":"([A-Z]{2}\d{2,4})"',  # JSON内の便名
        r'flight-number">([A-Z]{2}\d{2,4})', # HTMLタグ内の便名
        r'([A-Z]{2})(\d{2,4})'            # 生の航空コード+数字
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html)
        for m in matches:
            # 抽出結果が1つの場合と2つの場合(code, num)に対応
            flight = "".join(m).upper() if isinstance(m, tuple) else m.upper()
            code = flight[:2]
            if code in airlines and flight not in seen:
                results.append({
                    "time": "捕捉済", # 時刻は次のステップで精密化
                    "flight_no": flight,
                    "airline": airlines[code],
                    "pax": 150 # 現場判断用の初期推計値
                })
                seen.add(flight)

    # 現場の仕様に合わせたデータ構造で出力
    output = {
        "update_time": datetime.now().strftime("%H:%M"),
        "flights": sorted(results, key=lambda x: x['flight_no'])[:40],
        "count": len(results),
        "total_pax": len(results) * 150
    }

    with open(CONFIG["RESULT_FILE"], "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    
    print(f"✅ 解析完了: {len(results)} 件のフライトを情報の海から救出しました。")
    return output

if __name__ == "__main__":
    run_analyze()
