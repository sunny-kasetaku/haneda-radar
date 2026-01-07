import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v5.3: 原点回帰・スマートフィルター版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_content = f.read()

    # --- 1. 都市リストの読み込み（偽物判定の生命線） ---
    all_cities = CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # --- 2. 時刻検索（v5.0で成功した生データ検索） ---
    time_pattern = r'(\d{1,2})\s*[:：]\s*(\d{2})'
    time_matches = list(re.finditer(time_pattern, raw_content))
    print(f"1. 調査地点: {len(time_matches)}件 ヒット（生データから抽出）")

    for m in time_matches:
        try:
            h_str, m_str = m.groups()
            f_h, f_m = int(h_str), int(m_str)
            f_t = now.replace(hour=f_h % 24, minute=f_m, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            
            # タイムウィンドウ内か
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            # 周辺 1000文字をスキャン（JSON構造を考慮して広めに）
            chunk = raw_content[max(0, m.start()-500) : m.end()+500]
            chunk_upper = chunk.upper()
            
            # --- 【スマートフィルター】都市名が周辺にあるか？ ---
            # プログラムコードには都市名が入らないことを利用する
            origin = "不明"
            is_real_flight = False
            for city in all_cities:
                if city in chunk:
                    origin = city
                    is_real_flight = True
                    break
            
            # 都市名が見つからない場合は、この地点は「コードのゴミ」とみなして捨てる
            if not is_real_flight:
                continue

            # --- 便名の抽出（数字を伴うものを優先） ---
            carrier = "不明"
            fnum = ""
            carriers = ["JAL", "JL", "ANA", "NH", "BC", "SKY", "ADO", "SNA", "SFJ", "7G", "6J"]
            for c_code in carriers:
                # airline": "ANA" 形式か、タグ内の >ANA< 形式、または単語境界を狙う
                c_pat = r'[\"\' >](' + c_code + r')[\"\' <:]'
                if re.search(c_pat, chunk_upper):
                    carrier = c_code
                    # 直後の数字（便名）を探す
                    fnum_m = re.search(carrier + r'[\"\s>:]*(\d{1,4})', chunk_upper)
                    fnum = fnum_m.group(1) if fnum_m else ""
                    break

            # --- 人数・乗り場判定 ---
            cap = CONFIG["CAPACITY"]["SMALL"]
            if any(x in chunk_upper for x in ["777", "787", "350", "767", "A330", "B7"]):
                cap = CONFIG["CAPACITY"]["BIG"]
            
            pax = int(cap * CONFIG["LOAD_FACTORS"]["NORMAL"])
            
            s_key = "P5"
            if carrier in ["JAL", "JL"]:
                if origin in CONFIG["SOUTH_CITIES"]: s_key = "P1"
                elif origin in CONFIG["NORTH_CITIES"]: s_key = "P2"
                else: s_key = "P1"
            elif carrier in ["NH", "ANA"]: s_key = "P3"
            elif carrier in ["BC", "SKY"]: s_key = "P1"
            elif any(c in carrier for c in ["ADO", "SNA", "SFJ", "7G", "6J"]): s_key = "P4"
            
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
    
    print(f"2. 解析完了。有効便数: {len(unique_rows)} / 総需要: {result['total_pax']}人")
    return result
