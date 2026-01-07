import os
import json
import re
from datetime import datetime
from config import CONFIG

def run_analyze():
    raw_file = CONFIG.get("DATA_FILE", "haneda_raw.html")
    print(f"--- KASETACK Analyzer v17.0: Flightradar24 特化型 ---")
    
    if not os.path.exists(raw_file):
        print("❌ 解析対象のファイルが見つかりません。")
        return

    with open(raw_file, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. 国内線の航空会社コードを定義 (JAL, ANA, ADO, SNA, SFJ, SKY)
    airlines = {
        "JL": "日本航空", "NH": "全日本空輸", "HD": "エア・ドゥ",
        "BC": "スカイマーク", "7G": "スターフライヤー", "6J": "ソラシドエア"
    }

    # 2. 便名と時間を抜き出すための「網（正規表現）」
    # Flightradar24のHTML内にあるフライト番号（例: JL123, NH456）を抽出
    # ※217KBの中には JSON形式のデータが含まれている可能性が高いので広めに探します
    flight_matches = re.findall(r'([A-Z0-9]{2}\d{3,4})', html)
    
    # 3. データの整形
    results = []
    seen = set() # 重複除外用
    
    for flight in flight_matches:
        code = flight[:2]
        if code in airlines and flight not in seen:
            # 現場で使いやすい形式に整形
            name = airlines[code]
            results.append({
                "time": "確認中", # 時刻の抽出は次のステップで精密化
                "flight_no": flight,
                "airline": name,
                "status": "取得済み"
            })
            seen.add(flight)

    # 4. 結果の保存
    output = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "flights": results[:20], # 直近20件
        "raw_size": len(html)
    }

    with open(CONFIG["RESULT_FILE"], "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print(f"✅ 解析完了: {len(results)} 件の国内線候補を検知しました！")
    
    # ログに少しだけ中身を表示
    for f in results[:5]:
        print(f"✈️  {f['airline']} ({f['flight_no']}) を捕捉")

if __name__ == "__main__":
    run_analyze()
