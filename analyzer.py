import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v7.1: 精密選別版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        content = f.read()

    # --- 1. 不要な空白や特殊記号を整理 ---
    # 改行やタブをスペース1つにまとめ、解析しやすくする
    clean_text = re.sub(r'\s+', ' ', content)
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # --- 2. 検索パターンの定義 ---
    # 時刻パターン: 22:50 または 10:50 PM (または AM)
    time_pat = r'(\d{1,2})[:：](\d{2})\s*(AM|PM|am|pm)?'
    
    all_cities = CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]
    # キャリア検索を強化
    carrier_map = {
        "JAL": "JAL", "JL": "JAL", "ANA": "ANA", "NH": "ANA", 
        "SKY": "SKY", "BC": "SKY", "ADO": "ADO", "SNA": "SNA", "SFJ": "SFJ"
    }

    print("1. 抽出シミュレーション開始...")
    
    # 時刻を起点に周囲をスキャン
    for m in re.finditer(time_pat, clean_text):
        h = int(m.group(1))
        m_val = int(m.group(2))
        ampm = m.group(3)
        
        # 12時間制を24時間制に変換
        if ampm:
            ampm = ampm.upper()
            if ampm == "PM" and h < 12: h += 12
            if ampm == "AM" and h == 12: h = 0
            
        # 解析ウィンドウ判定（現在時刻の周辺 75分）
        f_t = now.replace(hour=h % 24, minute=m_val, second=0, microsecond=0)
        diff = (f_t - now).total_seconds() / 60
        if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
            continue

        # 周辺をスキャンして便名と都市を探す
        chunk = clean_text[max(0, m.start()-150) : m.end()+250]
        
        # 都市の特定
        origin = "不明"
        for city in all_cities:
            if city in chunk:
                origin = city
                break
        
        # キャリアの特定
        carrier = "不明"
        for code, name in carrier_map.items():
            if code in chunk.upper():
                carrier = name
                break
        
        # もしキャリアか都市のどちらかが見つかれば、それはフライトデータ
        if carrier != "不明" or origin != "不明":
            # 機材による人数判定
            cap = CONFIG["CAPACITY"]["SMALL"]
            if any(x in chunk for x in ["777", "787", "350", "767"]):
                cap = CONFIG["CAPACITY"]["BIG"]
            
            pax = int(cap * CONFIG["LOAD_FACTORS"]["NORMAL"])
            
            # 乗り場判定
            s_key = "P5"
            if carrier == "JAL":
                s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
            elif carrier == "ANA":
                s_key = "P3"
            elif carrier == "SKY":
                s_key = "P1"
            elif carrier in ["ADO", "SNA", "SFJ"]:
                s_key = "P4"
            
            flight_rows.append({
                "time": f"{h:02d}:{m_val:02d}", "flight": carrier, 
                "origin": origin[:6], "pax": pax, "s_key": s_key
            })

    # 重複削除
    unique_rows = []
    seen = set()
    for r in flight_rows:
        id_str = f"{r['time']}-{r['flight']}-{r['origin']}"
        if id_str not in seen:
            seen.add(id_str); unique_rows.append(r)

    for r in unique_rows:
        stands[r['s_key']] += r['pax']
    
    result = {
        "stands": stands, "pool_preds": {k: max(0, 100 - int(v/10)) for k, v in stands.items()},
        "total_pax": sum(stands.values()), "rows": unique_rows, "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"2. 解析完了。有効便数: {len(unique_rows)} / 総需要: {result['total_pax']}人")
    return result
