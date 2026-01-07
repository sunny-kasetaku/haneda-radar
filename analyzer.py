import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v5.9.1: 構文エラー修正・JSONターゲット版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_content = f.read()

    # --- 1. 【核心】Next.jsのJSONブロックを切り出す ---
    json_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', raw_content, re.DOTALL)
    
    target_content = ""
    if json_match:
        print("✅ 隠しJSONデータの抽出に成功しました。")
        target_content = json_match.group(1)
    else:
        print("⚠️ JSONタグが見つかりません。HTML全体からキャリアを起点に探します。")
        target_content = re.sub(r'<style.*?>.*?</style>', ' ', raw_content, flags=re.DOTALL)

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # --- 2. キャリアコード（JAL/ANA等）を起点に周囲を探索 ---
    carriers = ["JAL", "JL", "ANA", "NH", "BC", "SKY", "ADO", "SNA", "SFJ", "7G", "6J"]
    all_cities = CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]

    for c_code in carriers:
        for m in re.finditer(r'[\"\' >](' + c_code + r')[\"\' <:]', target_content.upper()):
            pos = m.start()
            chunk = target_content[max(0, pos-250) : pos+450]
            chunk_upper = chunk.upper()

            # 時刻を探す (HH:MM or HHMM)
            time_m = re.search(r'(\d{2})[:：]?(\d{2})', chunk)
            if not time_m: continue
            
            f_h, f_m = int(time_m.group(1)), int(time_m.group(2))
            if not (0 <= f_h <= 23 and 0 <= f_m <= 59): continue

            # 解析ウィンドウ判定
            f_t = now.replace(hour=f_h, minute=f_m, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            # 便名
            fnum_m = re.search(c_code + r'[^0-9]{0,10}(\d{1,4})', chunk_upper)
            fnum = fnum_m.group(1) if fnum_m else ""

            # 出身地
            origin = "不明"
            for city in all_cities:
                if city in chunk:
                    origin = city
                    break

            # 集計
            cap = CONFIG["CAPACITY"]["SMALL"]
            if any(x in chunk_upper for x in ["777", "787", "350", "767", "A330"]): cap = CONFIG["CAPACITY"]["BIG"]
            pax = int(cap * CONFIG["LOAD_FACTORS"]["NORMAL"])
            
            s_key = "P5" 
            if c_code in ["JAL", "JL"]:
                s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
            elif c_code in ["ANA", "NH"]: s_key = "P3"
            elif c_code in ["SKY", "BC"]: s_key = "P1"
            elif any(x in c_code for x in ["ADO", "SNA", "SFJ"]): s_key = "P4"
            
            flight_rows.append({
                "time": f"{f_h:02d}:{f_m:02d}", "flight": f"{c_code}{fnum}", 
                "origin": origin[:6], "pax": pax, "s_key": s_key
            })

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
        print("⚠️ 有効便がまだ0件です。データの後半（JSON領域）を調査します...")
        tail_sample = raw_content[-1500:].replace('\n', ' ').replace('\r', ' ')
        print(f"🔍 [TAIL SAMPLE]: {tail_sample}")

    print(f"2. 解析完了。有効便数: {len(unique_rows)}")
    return result
