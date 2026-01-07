import re, datetime, json, os, unicodedata
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v11.0: 超・広域マイニング版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]): return None
    
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8") as f:
        raw_content = f.read()

    # 正規化と全角・半角の統一
    content = unicodedata.normalize('NFKC', raw_content)
    text_content = re.sub(r'<[^>]+>', ' ', content)
    text_content = re.sub(r'\s+', ' ', text_content)

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    active_rows = []
    all_flights_count = 0

    # 航空会社のパターンを大幅強化 (日本航空, 全日空 等にも対応)
    carrier_map = {
        "JAL": "JAL", "JL": "JAL", "日本航空": "JAL",
        "ANA": "ANA", "NH": "ANA", "全日空": "ANA",
        "SKY": "SKY", "BC": "SKY", "スカイマーク": "SKY",
        "ADO": "ADO", "AIR DO": "ADO",
        "SNA": "SNA", "ソラシド": "SNA",
        "SFJ": "SFJ", "スターフライヤー": "SFJ"
    }

    print("1. 30KBの深層からデータを一本釣り中...")

    # 時刻(HH:MM)をすべて見つけ、その周辺400文字を徹底捜査
    for m in re.finditer(r'(\d{1,2}:\d{2})', text_content):
        time_str = m.group(1)
        if len(time_str) == 4: time_str = "0" + time_str
        h, m_val = map(int, time_str.split(':'))
        
        # 時刻の前後200文字（計400文字）を切り出し
        chunk = text_content[max(0, m.start()-200) : m.start() + 200].upper()
        
        # キャリア判定
        carrier = "不明"
        for key, val in carrier_map.items():
            if key in chunk:
                carrier = val; break
        
        if carrier != "不明":
            all_flights_count += 1
            
            # 都市名
            origin = "不明"
            for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
                if city in chunk:
                    origin = city; break

            f_t = now.replace(hour=h, minute=m_val, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            if diff < -720: f_t += datetime.timedelta(days=1); diff += 1440
            elif diff > 720: f_t -= datetime.timedelta(days=1); diff -= 1440

            if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
                s_key = "P5"
                if carrier == "JAL":
                    s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
                elif carrier == "ANA": s_key = "P3"
                elif carrier == "SKY": s_key = "P1"
                elif carrier in ["ADO", "SNA", "SFJ"]: s_key = "P4"

                pax = int(CONFIG["CAPACITY"]["SMALL"] * 0.8) # 深夜想定
                active_rows.append({"time": time_str, "flight": carrier, "origin": origin, "pax": pax, "s_key": s_key})
                stands[s_key] += pax

    result = {
        "stands": stands, "total_pax": sum(stands.values()), "rows": active_rows, 
        "total_flights_on_page": all_flights_count, "update_time": now.strftime("%H:%M")
    }
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"--- 📊 最終報告 ---")
    print(f"✅ 生存確認: {all_flights_count} 便を検出")
    print(f"🎯 需要対象: {len(active_rows)} 便")
    return result
