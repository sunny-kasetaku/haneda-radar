import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v7.3: バイリンガル選別版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        content = f.read()

    # --- 1. 都市名の日英マッピング（翻訳機） ---
    city_map = {
        "SAPPORO": "札幌", "NEW CHITOSE": "札幌", "CHITOSE": "札幌",
        "FUKUOKA": "福岡", "OKINAWA": "那覇", "NAHA": "那覇",
        "OSAKA": "大阪", "ITAMI": "伊丹", "KANSAI": "関空",
        "HIROSHIMA": "広島", "KAGOSHIMA": "鹿児島", "KUMAMOTO": "熊本",
        "NAGASAKI": "長崎", "MATSUYAMA": "松山", "TAKAMATSU": "高松"
    }
    
    # HTMLタグを除去して純粋なテキストの並びにする
    clean_text = re.sub(r'<[^>]+>', ' ', content)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # 時刻パターン: 22:50 または 10:50 PM
    time_pat = r'(\d{1,2})[:：](\d{2})\s*(AM|PM|am|pm)?'
    
    print("1. 5.7MBの英文データから翻訳・抽出中...")
    
    for m in re.finditer(time_pat, clean_text):
        try:
            h, m_val = int(m.group(1)), int(m.group(2))
            ampm = m.group(3)
            
            if not (0 <= h <= 23 and 0 <= m_val <= 59): continue
            if ampm:
                ampm = ampm.upper()
                if ampm == "PM" and h < 12: h += 12
                if ampm == "AM" and h == 12: h = 0
                
            f_t = now.replace(hour=h % 24, minute=m_val, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            # 前後300文字を調査
            chunk = clean_text[max(0, m.start()-150) : m.end()+300].upper()
            
            # --- 都市の特定（日英両対応） ---
            origin = "不明"
            # 日本語で探す
            for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
                if city in chunk:
                    origin = city; break
            # 見つからなければ英語で探して翻訳する
            if origin == "不明":
                for eng, jap in city_map.items():
                    if eng in chunk:
                        origin = jap; break
            
            # --- キャリアの特定 ---
            carrier = "不明"
            if "JAL" in chunk or "JL" in chunk: carrier = "JAL"
            elif "ANA" in chunk or "NH" in chunk: carrier = "ANA"
            elif "SKY" in chunk or "BC" in chunk: carrier = "SKY"
            elif "ADO" in chunk: carrier = "ADO"
            elif "SNA" in chunk: carrier = "SNA"
            elif "SFJ" in chunk: carrier = "SFJ"
            
            if carrier != "不明" or origin != "不明":
                pax = 180 if any(x in chunk for x in ["777", "787", "350", "767"]) else 120
                s_key = "P5"
                if carrier == "JAL":
                    s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
                elif carrier == "ANA": s_key = "P3"
                elif carrier == "SKY": s_key = "P1"
                elif carrier in ["ADO", "SNA", "SFJ"]: s_key = "P4"
                
                flight_rows.append({
                    "time": f"{h:02d}:{m_val:02d}", "flight": carrier, 
                    "origin": origin, "pax": pax, "s_key": s_key
                })
        except: continue

    # 重複削除
    unique_rows = []
    seen = set()
    for r in flight_rows:
        id_str = f"{r['time']}-{r['flight']}-{r['origin']}"
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
