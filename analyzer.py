import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v7.4: 深夜ラッシュ対応版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        content = f.read()

    # 都市名マッピング
    city_map = {
        "SAPPORO": "札幌", "CHITOSE": "札幌", "FUKUOKA": "福岡", 
        "OKINAWA": "那覇", "NAHA": "那覇", "OSAKA": "大阪", "ITAMI": "伊丹",
        "KANSAI": "関空", "HIROSHIMA": "広島", "KAGOSHIMA": "鹿児島",
        "KUMAMOTO": "熊本", "NAGASAKI": "長崎", "MATSUYAMA": "松山"
    }
    
    # HTMLタグを除去し、解析しやすく整形
    clean_text = re.sub(r'<[^>]+>', ' ', content)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # 時刻パターン: 22:50, 10:50 PM, 11:05p 等
    time_pat = r'(\d{1,2})[:：.](\d{2})\s*([APap][Mm]?)?'
    
    print("1. 5.7MBのデータを深夜モードで解析中...")
    debug_samples = []

    for m in re.finditer(time_pat, clean_text):
        try:
            h = int(m.group(1))
            m_val = int(m.group(2))
            ampm = m.group(3)
            
            if not (0 <= h <= 23 and 0 <= m_val <= 59): continue
            
            # AM/PM 変換
            if ampm:
                ampm = ampm.upper()
                if "P" in ampm and h < 12: h += 12
                if "A" in ampm and h == 12: h = 0
            
            # 日付またぎの補正
            f_t = now.replace(hour=h % 24, minute=m_val, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            
            # もし現在22-23時で、便が0-2時なら、それは「明日」の便
            if diff < -1000 and now.hour >= 21:
                f_t += datetime.timedelta(days=1)
                diff = (f_t - now).total_seconds() / 60

            # 常に上位5件の時刻周辺をデバッグ用にメモ
            if len(debug_samples) < 5:
                debug_samples.append(f"{h:02d}:{m_val:02d} around: {clean_text[m.start():m.start()+100]}")

            # 解析ウィンドウ判定
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            chunk = clean_text[max(0, m.start()-150) : m.end()+300].upper()
            
            # キャリア特定 (航空会社名フルネームにも対応)
            carrier = "不明"
            if "JAL" in chunk or "JL" in chunk or "JAPAN AIRLINES" in chunk: carrier = "JAL"
            elif "ANA" in chunk or "NH" in chunk or "ALL NIPPON" in chunk: carrier = "ANA"
            elif "SKY" in chunk or "BC" in chunk or "SKYMARK" in chunk: carrier = "SKY"
            elif "ADO" in chunk or "AIR DO" in chunk: carrier = "ADO"
            elif "SNA" in chunk or "SOLASEED" in chunk: carrier = "SNA"
            elif "SFJ" in chunk or "STARFLYER" in chunk: carrier = "SFJ"
            
            # 都市の特定
            origin = "不明"
            for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
                if city in chunk: origin = city; break
            if origin == "不明":
                for eng, jap in city_map.items():
                    if eng in chunk: origin = jap; break
            
            if carrier != "不明" or origin != "不明":
                pax = 180 if any(x in chunk for x in ["777", "787", "350", "767"]) else 120
                s_key = "P5"
                if carrier == "JAL":
                    s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
                elif carrier == "ANA": s_key = "P3"
                elif carrier == "SKY": s_key = "P1"
                elif carrier in ["ADO", "SNA", "SFJ"]: s_key = "P4"
                
                flight_rows.append({
                    "time": f_t.strftime("%H:%M"), "flight": carrier, 
                    "origin": origin, "pax": pax, "s_key": s_key
                })
        except: continue

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

    if not unique_rows:
        print("⚠️ 有効便が0件です。抽出された時刻のサンプルを確認してください:")
        for s in debug_samples: print(f" - {s}")

    print(f"2. 解析完了。有効便数: {len(unique_rows)}")
    return result
