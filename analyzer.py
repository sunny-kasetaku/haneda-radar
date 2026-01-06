import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- Analyzer v4.0: 洗浄 ＆ プール予測版開始 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8") as f:
        raw_content = f.read()

    # --- 足し算：HTMLノイズの徹底洗浄 ---
    # <style>タグとその中身、およびCSS変数（--font等）を事前に削除
    clean_content = re.sub(r'<style.*?>.*?</style>', '', raw_content, flags=re.DOTALL)
    clean_content = re.sub(r'--[a-zA-Z0-9-]+:.*?;', '', clean_content)
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    time_matches = list(re.finditer(r'(\d{1,2}):(\d{2})\s?([AP]M)?', clean_content, re.IGNORECASE))
    print(f"1. 30/30ウィンドウに基づき、{len(time_matches)}地点を調査します")

    for m in time_matches:
        try:
            h_str, m_str, ampm = m.groups()
            f_h, f_m = int(h_str), int(m_str)
            if ampm and ampm.upper() == "PM" and f_h < 12: f_h += 12
            elif ampm and ampm.upper() == "AM" and f_h == 12: f_h = 0
            
            f_t = now.replace(hour=f_h % 24, minute=f_m, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            # 前方の探索範囲を広げ、キャリアコード(JL/NH等)を確実に捕まえる
            start = max(0, m.start() - 250) 
            chunk = clean_content[start : m.start() + 400]
            
            # 便名検索：[A-Z]を必須にすることで 102 等の数字単体を排除
            flight_m = re.search(r'([A-Z]{2,3})\s?(\d{1,4})', chunk)
            if flight_m:
                carrier, fnum = flight_m.groups()
                carrier = carrier.upper()

                # 出身地の抽出：洗浄済みテキストから都市名を探す
                origin = "不明"
                origin_m = re.search(r'<td>(.*?)</td>', chunk, re.DOTALL)
                if origin_m:
                    origin = re.sub(r'<.*?>', '', origin_m.group(1)).strip()
                    if not origin or len(origin) < 2 or "--" in origin: # ゴミなら再探索
                        alt_m = re.search(r'>([ぁ-んァ-ヶー一-龠]{2,10})<', chunk)
                        origin = alt_m.group(1) if alt_m else "不明"

                # 機材・キャパ判定
                cap = CONFIG["CAPACITY"]["SMALL"]
                is_big = any(x in chunk for x in ["777", "787", "350", "767", "A330"])
                if is_big or int(fnum) < 1000:
                    cap = CONFIG["CAPACITY"]["BIG"]
                if carrier not in ["JL", "NH", "BC", "7G", "6J", "ADO", "SNA", "SFJ"]:
                    cap = CONFIG["CAPACITY"]["INTL"]

                rate = CONFIG["LOAD_FACTORS"]["NORMAL"]
                if 22 <= now.hour or now.hour <= 2: rate = CONFIG["LOAD_FACTORS"]["MIDNIGHT"]
                elif 7 <= now.hour <= 9 or 17 <= now.hour <= 20: rate = CONFIG["LOAD_FACTORS"]["RUSH"]

                pax = int(cap * rate)
                
                s_key = "P5"
                if "JL" in carrier:
                    if any(city in origin for city in CONFIG["SOUTH_CITIES"]): s_key = "P1"
                    elif any(city in origin for city in CONFIG["NORTH_CITIES"]): s_key = "P2"
                    else: s_key = "P1"
                elif "BC" in carrier: s_key = "P1"
                elif "NH" in carrier: s_key = "P3"
                elif any(c in carrier for c in ["ADO", "SNA", "SFJ", "7G"]): s_key = "P4"
                
                print(f" ✅ 検知: {f_h:02d}:{f_m:02d} {carrier}{fnum} ({origin})")
                flight_rows.append({"time": f"{f_h:02d}:{f_m:02d}", "flight": f"{carrier}{fnum}", "origin": origin[:6], "pax": pax, "s_key": s_key})

        except Exception: continue

    # 重複削除
    seen = set()
    unique_rows = []
    for r in flight_rows:
        id_str = f"{r['time']}-{r['origin']}" 
        if id_str not in seen:
            seen.add(id_str)
            unique_rows.append(r)

    # 最終集計と「プール予想」の計算
    for k in stands: stands[k] = 0
    for r in unique_rows:
        stands[r['s_key']] += r['pax']

    # --- 足し算：プール台数予想ロジック (暫定係数) ---
    pool_preds = {}
    base_cars = {"P1": 100, "P2": 100, "P3": 120, "P4": 80, "P5": 150}
    for k, p_pax in stands.items():
        # 需要10人につき1台減ると仮定
        est = base_cars[k] - int(p_pax / 10)
        pool_preds[k] = max(0, est) # 0以下にはならない

    total_pax = sum(r['pax'] for r in unique_rows)
    result = {
        "stands": stands, 
        "pool_preds": pool_preds, # 足し算
        "total_pax": total_pax, 
        "rows": unique_rows, 
        "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"2. 解析完了。有効な便数: {len(unique_rows)} / 総需要: {total_pax}人")
    return result
