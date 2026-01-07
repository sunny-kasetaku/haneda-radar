import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v8.0: 真贋鑑定・ゴーストバスター版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_html = f.read()

    # --- 1. 【ゴーストバスター】偽物のANA（Analytics）を完全に消去 ---
    # 大文字小文字問わず Analytics を消す
    clean_content = re.sub(r'analytics', ' ', raw_html, flags=re.IGNORECASE)
    # ついでにCSSやスクリプトも排除
    clean_content = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', clean_content, flags=re.DOTALL | re.IGNORECASE)
    text_content = re.sub(r'<[^>]+>', ' ', clean_content)
    text_content = re.sub(r'\s+', ' ', text_content)

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    city_map = {
        "SAPPORO": "札幌", "CHITOSE": "札幌", "FUKUOKA": "福岡", 
        "OKINAWA": "那覇", "NAHA": "那覇", "OSAKA": "大阪", "ITAMI": "伊丹"
    }
    
    # 2. 便名パターンを直接狙う (例: ANA 584, JAL92, NH 126)
    # \b は単語の境界を意味し、Analytics のような単語の一部を排除します
    flight_pat = r'\b(ANA|JAL|SKY|ADO|SNA|SFJ|NH|JL|BC)\s*(\d{1,4})\b'
    
    print("1. 偽物を排除し、本物の便名パターンをスキャン中...")

    for m in re.finditer(flight_pat, text_content.upper()):
        try:
            carrier_code = m.group(1)
            f_num = m.group(2)
            
            # 便名が見つかった周辺 300文字を調査
            chunk = text_content[max(0, m.start()-150) : m.end()+150]
            
            # 周辺から時刻を探す (10:50 PM 等)
            time_m = re.search(r'(\d{1,2})[:：](\d{2})\s*([APap][Mm])?', chunk)
            if not time_m: continue
            
            h = int(time_m.group(1))
            m_val = int(time_m.group(2))
            ampm = time_m.group(3)
            
            if ampm:
                ampm = ampm.upper()
                if "PM" in ampm and h < 12: h += 12
                if "AM" in ampm and h == 12: h = 0
            
            # 日付またぎ補正
            f_t = now.replace(hour=h % 24, minute=m_val, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            if diff < -1000: f_t += datetime.timedelta(days=1); diff += 1440
            
            # ウィンドウ判定
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            # 都市特定
            origin = "不明"
            for eng, jap in city_map.items():
                if eng in chunk.upper(): origin = jap; break
            
            # キャリア名の正規化
            real_carrier = carrier_code
            if carrier_code in ["NH"]: real_carrier = "ANA"
            if carrier_code in ["JL"]: real_carrier = "JAL"
            if carrier_code in ["BC"]: real_carrier = "SKY"

            pax = 180 if any(x in chunk for x in ["777", "787", "350", "767"]) else 120
            
            s_key = "P5"
            if real_carrier == "JAL":
                s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
            elif real_carrier == "ANA": s_key = "P3"
            elif real_carrier == "SKY": s_key = "P1"
            
            flight_rows.append({
                "time": f_t.strftime("%H:%M"), "flight": f"{real_carrier}{f_num}", 
                "origin": origin, "pax": pax, "s_key": s_key
            })
        except: continue

    # 重複削除
    unique_rows = []
    seen = set()
    for r in flight_rows:
        id_str = f"{r['time']}-{r['flight']}"
        if id_str not in seen:
            seen.add(id_str); unique_rows.append(r)

    for r in unique_rows: stands[r['s_key']] += r['pax']
    
    result = {
        "stands": stands, "pool_preds": {k: max(0, 100 - int(v/10)) for k, v in stands.items()},
        "total_pax": sum(stands.values()), "rows": unique_rows, "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"2. 解析完了。有効便数: {len(unique_rows)} / 総需要: {result['total_pax']}人")
    return result
