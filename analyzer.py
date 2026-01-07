import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v5.8: 強制剥離・全方位スキャン版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_content = f.read()

    # --- 1. 【絶対露出】データの正体を暴くための強制出力 ---
    print(f"DEBUG: データ総長: {len(raw_content)} bytes")
    # 最初の1000文字を出す（ここを見れば構造が一発でわかります）
    sample = raw_content[:1000].replace('\n', ' ').replace('\r', ' ')
    print(f"🔍 [RAW SAMPLE]: {sample}")

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # --- 2. 複数の時刻形式でアタック ---
    # 形式1: "22:10" / 形式2: "2210" (JSON) / 形式3: "22時10分"
    time_patterns = [
        r'(\d{1,2})[:：](\d{2})', 
        r'\"(\d{2})(\d{2})\"', # JSON内の4桁
        r'(\d{1,2})時(\d{2})分'
    ]
    
    found_times = []
    for pat in time_patterns:
        for m in re.finditer(pat, raw_content):
            h, m_str = m.groups()
            found_times.append((int(h), int(m_str), m.start()))

    print(f"1. 時刻候補の発見数: {len(found_times)}件")

    all_cities = CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]
    carriers = ["JAL", "JL", "ANA", "NH", "BC", "SKY", "ADO", "SNA", "SFJ", "7G", "6J"]

    for f_h, f_m, pos in found_times:
        try:
            # 時刻の妥当性
            if not (0 <= f_h <= 23 and 0 <= f_m <= 59): continue
            
            f_t = now.replace(hour=f_h, minute=f_m, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            
            # 解析ウィンドウ (-30〜+45分)
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            # 周辺を広めにスキャン
            chunk = raw_content[max(0, pos-600) : pos+600]
            chunk_upper = chunk.upper()

            # --- 便名とキャリアを特定 ---
            carrier, fnum = "不明", ""
            for c_code in carriers:
                if c_code in chunk_upper:
                    carrier = c_code
                    # 直後の数字
                    fnum_m = re.search(carrier + r'[^0-9]{0,15}(\d{1,4})', chunk_upper)
                    fnum = fnum_m.group(1) if fnum_m else ""
                    break
            
            # --- 出身地を特定 ---
            origin = "不明"
            for city in all_cities:
                if city in chunk:
                    origin = city
                    break
            
            # キャリアすら不明な「ただの時間」は無視
            if carrier == "不明": continue

            # --- 集計 ---
            cap = CONFIG["CAPACITY"]["SMALL"]
            if any(x in chunk_upper for x in ["777", "787", "350", "767", "A330"]): cap = CONFIG["CAPACITY"]["BIG"]
            pax = int(cap * CONFIG["LOAD_FACTORS"]["NORMAL"])
            
            s_key = "P5" 
            if carrier in ["JAL", "JL"]:
                s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
            elif carrier in ["NH", "ANA"]: s_key = "P3"
            elif carrier in ["BC", "SKY"]: s_key = "P1"
            elif any(c in carrier for c in ["ADO", "SNA", "SFJ"]): s_key = "P4"
            
            flight_rows.append({
                "time": f"{f_h:02d}:{f_m:02d}", "flight": f"{carrier}{fnum}", 
                "origin": origin[:6], "pax": pax, "s_key": s_key
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
    
    print(f"2. 解析完了。有効便数: {len(unique_rows)}")
    return result
