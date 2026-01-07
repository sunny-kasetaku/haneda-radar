import re
import datetime
import json
import os
import unicodedata
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v10.0: 二段構え・安心運用版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_content = f.read()

    # 文字の正規化とタグ除去
    content = unicodedata.normalize('NFKC', raw_content)
    text_content = re.sub(r'<[^>]+>', ' ', content)
    text_content = re.sub(r'\s+', ' ', text_content)

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    active_rows = []
    all_flights_count = 0  # 【生存確認用】

    # 航空会社判定パターン
    carrier_pat = r'(JAL|ANA|SKY|ADO|SNA|SFJ|JL|NH|BC|6J|7G)\s*(\d+)'
    
    # 時刻を起点にスキャン
    for m in re.finditer(r'(\d{1,2}:\d{2})', text_content):
        time_str = m.group(1)
        if len(time_str) == 4: time_str = "0" + time_str
        h, m_val = map(int, time_str.split(':'))
        
        chunk = text_content[max(0, m.start()-100) : m.start() + 250]
        c_match = re.search(carrier_pat, chunk.upper())
        
        if c_match:
            all_flights_count += 1 # 窓に関係なくカウント
            
            carrier = c_match.group(1)
            f_num = c_match.group(2)
            
            # 都市名探し
            origin = "不明"
            for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
                if city in chunk:
                    origin = city; break

            # 時刻計算
            f_t = now.replace(hour=h, minute=m_val, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            
            # 日付またぎ補正
            if diff < -720: f_t += datetime.timedelta(days=1); diff += 1440
            elif diff > 720: f_t -= datetime.timedelta(days=1); diff -= 1440

            # 需要対象（窓内）の判定
            if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
                real_c = carrier
                if carrier == "NH": real_c = "ANA"
                if carrier == "JL": real_c = "JAL"
                if carrier == "BC": real_c = "SKY"
                
                s_key = "P5"
                if real_c == "JAL":
                    s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
                elif real_c == "ANA": s_key = "P3"
                elif real_c == "SKY": s_key = "P1"
                elif real_c in ["ADO", "SNA", "SFJ"]: s_key = "P4"

                pax = int(CONFIG["CAPACITY"]["SMALL"] * 0.85)
                if origin in ["札幌", "福岡", "那覇", "伊丹"]:
                    pax = int(CONFIG["CAPACITY"]["BIG"] * 0.85)

                active_rows.append({
                    "time": time_str, "flight": f"{real_c}{f_num}", 
                    "origin": origin, "pax": pax, "s_key": s_key
                })
                stands[s_key] += pax

    # 結果JSON
    result = {
        "stands": stands, "total_pax": sum(stands.values()), "rows": active_rows, 
        "total_flights_on_page": all_flights_count, "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"--- 📊 KASETACK 運用状況 ---")
    print(f"✅ 取得成功: ページ内に計 {all_flights_count} 便のデータを捕捉中")
    print(f"🎯 需要対象: {len(active_rows)} 便 (現在の窓内)")
    print(f"--------------------------")
    
    return result
