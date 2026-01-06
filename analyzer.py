import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- Analyzer 最終・バリデーション版開始 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8") as f:
        content = f.read()

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    total_pax = 0

    # 時刻パターンの抽出
    time_matches = list(re.finditer(r'(\d{1,2}):(\d{2})\s?([AP]M)?', content, re.IGNORECASE))
    print(f"1. 解析候補: {len(time_matches)} 個の文字列をチェックします")

    for m in time_matches:
        try:
            h_str, m_str, ampm = m.groups()
            f_h = int(h_str)
            f_m = int(m_str)

            # 🛑 バリデーション: 時刻として正しくない数値はスキップ
            if not (0 <= f_h <= 23 and 0 <= f_m <= 59):
                continue

            # 周辺300文字を調査
            start = m.start()
            chunk = content[start : start + 300]
            
            # 便名(2-3文字 + 1-4桁)を検索
            flight_m = re.search(r'([A-Z0-9]{2,3})\s?(\d{1,4})', chunk)
            
            if flight_m:
                carrier, fnum = flight_m.groups()
                carrier = carrier.upper()
                
                # PM/AM 補正
                if ampm and ampm.upper() == "PM" and f_h < 12: f_h += 12
                elif ampm and ampm.upper() == "AM" and f_h == 12: f_h = 0
                
                f_t = now.replace(hour=f_h % 24, minute=f_m, second=0, microsecond=0)
                diff = (f_t - now).total_seconds() / 60
                
                # ターゲット時間枠（-30分〜+30分）
                if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
                    origin_m = re.search(r'<td>(.*?)</td>', chunk, re.DOTALL | re.IGNORECASE)
                    origin = origin_m.group(1).strip() if origin_m else "不明"

                    # 搭乗数計算
                    rate = CONFIG["LOAD_FACTORS"]["NORMAL"]
                    if 22 <= now.hour or now.hour <= 2: rate = CONFIG["LOAD_FACTORS"]["MIDNIGHT"]
                    elif 7 <= now.hour <= 9 or 17 <= now.hour <= 20: rate = CONFIG["LOAD_FACTORS"]["RUSH"]

                    cap = CONFIG["CAPACITY"]["BIG"] if int(fnum) < 1000 else CONFIG["CAPACITY"]["SMALL"]
                    if carrier not in ["JL", "NH", "BC", "7G", "6J", "ADO", "SNA", "SFJ"]:
                        cap = CONFIG["CAPACITY"]["INTL"]
                    
                    pax = int(cap * rate)
                    
                    # 振り分け
                    s_key = "P5"
                    if "JL" in carrier:
                        if any(city in origin for city in CONFIG["SOUTH_CITIES"]): s_key = "P1"
                        elif any(city in origin for city in CONFIG["NORTH_CITIES"]): s_key = "P2"
                        else: s_key = "P1"
                    elif "BC" in carrier: s_key = "P1"
                    elif "NH" in carrier: s_key = "P3"
                    elif any(c in carrier for c in ["ADO", "SNA", "SFJ", "7G"]): s_key = "P4"
                    
                    stands[s_key] += pax
                    total_pax += pax
                    flight_rows.append({"time": f"{f_h:02d}:{f_m:02d}", "flight": f"{carrier}{fnum}", "origin": origin[:6], "pax": pax})

        except Exception:
            continue # 不正なデータは無視して次へ

    # 重複削除
    seen = set()
    unique_rows = []
    for r in flight_rows:
        id_str = f"{r['time']}-{r['flight']}"
        if id_str not in seen:
            seen.add(id_str)
            unique_rows.append(r)

    print(f"2. 解析完了。有効な便数: {len(unique_rows)} 便 / 合計需要: {total_pax}人")

    result = {
        "stands": stands, "total_pax": total_pax, "rows": unique_rows, "update_time": now.strftime("%H:%M")
    }
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result
