import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v9.1: Yahoo!空路情報・完全攻略版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        content = f.read()

    # 1. データのゴミ（スクリプト等）を排除
    content = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', content, flags=re.DOTALL | re.IGNORECASE)
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # 2. Yahoo!空路情報のテーブル構造を狙い撃つ
    # <td>12:34</td> ... <td>JAL123</td> ... <td>札幌(新千歳)</td>
    # このパターンで便を抽出
    pattern = r'<td>(\d{2}:\d{2})</td>.*?<td>([A-Z]{2,3})\d+.*?</td>.*?<td>(.*?)</td>'
    
    print("1. Yahoo!の構造からフライトを抽出中...")
    
    # re.findall よりも精密に、各行を処理
    # <td>(\d{2}:\d{2})</td> ... <td>([^<]+)</td> ... <td>([^<]+)</td>
    # 状況（定刻・着陸など）も含む広範なキャプチャ
    matches = re.findall(r'<td>(\d{2}:\d{2})</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>', content)

    for time_str, flight_raw, origin_raw in matches:
        try:
            h, m = map(int, time_str.split(':'))
            
            # 日付またぎ補正
            f_t = now.replace(hour=h, minute=m, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            if diff < -1000: f_t += datetime.timedelta(days=1); diff += 1440
            
            # ウィンドウ判定 (T-30 〜 T+45)
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            # キャリア特定
            carrier = "不明"
            flight_upper = flight_raw.upper()
            if "JAL" in flight_upper or "JL" in flight_upper: carrier = "JAL"
            elif "ANA" in flight_upper or "NH" in flight_upper: carrier = "ANA"
            elif "SKY" in flight_upper or "BC" in flight_upper: carrier = "SKY"
            elif "ADO" in flight_upper: carrier = "ADO"
            elif "SNA" in flight_upper: carrier = "SNA"
            elif "SFJ" in flight_upper: carrier = "SFJ"

            # 都市特定
            origin = origin_raw.split('(')[0] # "札幌(新千歳)" -> "札幌"
            
            # 乗り場判定
            s_key = "P5" # デフォルト
            if carrier == "JAL":
                s_key = "P2" if any(c in origin for c in CONFIG["NORTH_CITIES"]) else "P1"
            elif carrier == "ANA":
                s_key = "P3"
            elif carrier == "SKY":
                s_key = "P1"
            elif carrier in ["ADO", "SNA", "SFJ"]:
                s_key = "P4"

            # 人数算出（深夜係数 0.85）
            cap = CONFIG["CAPACITY"]["BIG"] if any(x in origin for x in ["札幌", "福岡", "那覇", "伊丹"]) else CONFIG["CAPACITY"]["SMALL"]
            pax = int(cap * CONFIG["LOAD_FACTORS"]["MIDNIGHT"])

            flight_rows.append({
                "time": time_str, "flight": flight_raw, 
                "origin": origin, "pax": pax, "s_key": s_key
            })
            stands[s_key] += pax

        except Exception as e:
            continue

    result = {
        "stands": stands, "pool_preds": {k: max(0, 100 - int(v/10)) for k, v in stands.items()},
        "total_pax": sum(stands.values()), "rows": flight_rows, "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"2. 解析完了。有効便数: {len(flight_rows)} / 総予測人数: {result['total_pax']}名")
    return result
