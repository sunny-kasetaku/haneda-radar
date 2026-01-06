import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- Analyzer 最終・総当たり解析開始 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8") as f:
        content = f.read()

    # 🕵️ デバッグ：最初の500文字を表示して構造を確認する
    print(f"DEBUG: 受信データの先頭500文字:\n{content[:500]}")

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    total_pax = 0

    # 🚀 タグを無視！「時刻っぽい文字列」をすべて探し、その周辺を解析する
    # パターン: 12:34 AM/PM または 12:34
    time_matches = list(re.finditer(r'(\d{1,2}):(\d{2})\s?([AP]M)?', content, re.IGNORECASE))
    print(f"1. 時刻っぽい文字列を {len(time_matches)} 個発見しました")

    for m in time_matches:
        # 時刻が見つかった場所から、後ろに続く300文字を「便情報の塊」として抽出
        start = m.start()
        chunk = content[start : start + 300]
        
        # この塊の中に「便名」が含まれているか確認
        # 航空会社(2-3文字) + 便名(1-4桁)
        flight_m = re.search(r'([A-Z0-9]{2,3})\s?(\d{1,4})', chunk)
        
        if flight_m:
            h, minute, ampm = m.groups()
            carrier, fnum = flight_m.groups()
            carrier = carrier.upper()
            
            # --- 時間計算 ---
            f_h = int(h)
            if ampm and ampm.upper() == "PM" and f_h < 12: f_h += 12
            elif ampm and ampm.upper() == "AM" and f_h == 12: f_h = 0
            
            f_t = now.replace(hour=f_h % 24, minute=int(minute), second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            
            # 指定の時間枠（-30〜+30）に合致するか
            if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
                # 出身地も塊の中から探す（<td>～</td>の中身を狙う）
                origin_m = re.search(r'<td>(.*?)</td>', chunk, re.DOTALL | re.IGNORECASE)
                origin = origin_m.group(1).strip() if origin_m else "不明"

                # 搭乗計算（サニーさんロジック）
                rate = CONFIG["LOAD_FACTORS"]["NORMAL"]
                if 22 <= now.hour or now.hour <= 2: rate = CONFIG["LOAD_FACTORS"]["MIDNIGHT"]
                elif 7 <= now.hour <= 9 or 17 <= now.hour <= 20: rate = CONFIG["LOAD_FACTORS"]["RUSH"]

                cap = CONFIG["CAPACITY"]["BIG"] if int(fnum) < 1000 else CONFIG["CAPACITY"]["SMALL"]
                if carrier not in ["JL", "NH", "BC", "7G", "6J", "ADO", "SNA", "SFJ"]:
                    cap = CONFIG["CAPACITY"]["INTL"]
                
                pax = int(cap * rate)
                total_pax += pax
                
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
                flight_rows.append({"time": f"{f_h:02d}:{minute}", "flight": f"{carrier}{fnum}", "origin": origin[:6], "pax": pax})

    # 重複を削除（同じ便が複数回マッチすることがあるため）
    seen = set()
    unique_rows = []
    for r in flight_rows:
        id_str = f"{r['time']}-{r['flight']}"
        if id_str not in seen:
            seen.add(id_str)
            unique_rows.append(r)

    print(f"2. 解析完了。有効な便数: {len(unique_rows)} 便 / 合計: {total_pax}人")

    result = {
        "stands": stands, "total_pax": total_pax, "rows": unique_rows, "update_time": now.strftime("%H:%M")
    }
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result
