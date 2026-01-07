import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v5.6: ノイズフィルタリング版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_content = f.read()

    # --- 1. 【ノイズ除去】CSSを完全に焼き払う ---
    # デバッグで判明した「CSS変数の誤検知」を根絶します
    clean_content = re.sub(r'<style.*?>.*?</style>', ' ', raw_content, flags=re.DOTALL)
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # 2. 時刻検索（境界線を意識してノイズを回避）
    # 引用符の中 "20:15" や タグの中 >20:15< などを狙い撃つ
    time_pattern = r'[\">]?(\d{1,2})[:：](\d{2})[\" <]?'
    time_matches = list(re.finditer(time_pattern, clean_content))
    
    valid_time_count = 0
    debug_done = False

    for m in time_matches:
        try:
            h_str, m_str = m.groups()
            f_h, f_m = int(h_str), int(m_str)
            
            # 時間としての妥当性チェック
            if not (0 <= f_h <= 23 and 0 <= f_m <= 59):
                continue
            
            f_t = now.replace(hour=f_h, minute=f_m, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            
            # 範囲外ならスキップ
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            valid_time_count += 1
            chunk = clean_content[max(0, m.start()-500) : m.end()+500]
            chunk_upper = chunk.upper()
            
            if not debug_done:
                # 本物のデータらしき場所のデバッグ
                debug_chunk = chunk[:200].replace('\n', ' ').replace('\r', ' ')
                print(f"🎯 有効候補発見 ({f_h:02d}:{f_m:02d}): {debug_chunk}")
                debug_done = True

            # --- 便名の抽出 ---
            carrier = "不明"
            fnum = ""
            carriers = ["JAL", "JL", "ANA", "NH", "BC", "SKY", "ADO", "SNA", "SFJ", "7G", "6J"]
            for c_code in carriers:
                if c_code in chunk_upper:
                    carrier = c_code
                    fnum_m = re.search(carrier + r'[^0-9]{0,10}(\d{1,4})', chunk_upper)
                    fnum = fnum_m.group(1) if fnum_m else ""
                    break

            if carrier == "不明":
                continue

            # --- 出身地の抽出 ---
            origin = "不明"
            all_cities = CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]
            for city in all_cities:
                if city in chunk:
                    origin = city
                    break
            
            if origin == "不明":
                org_m = re.search(r'[\">]([ぁ-んァ-ヶー一-龠]{2,10})[\"<]', chunk)
                if org_m: origin = org_m.group(1).strip()

            # --- 計算と集計 ---
            cap = CONFIG["CAPACITY"]["SMALL"]
            if any(x in chunk_upper for x in ["777", "787", "350", "767", "A330"]):
                cap = CONFIG["CAPACITY"]["BIG"]
            pax = int(cap * CONFIG["LOAD_FACTORS"]["NORMAL"])
            
            s_key = "P5" 
            if carrier in ["JAL", "JL"]:
                s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
            elif carrier in ["NH", "ANA"]: s_key = "P3"
            elif carrier in ["BC", "SKY"]: s_key = "P1"
            elif any(c in carrier for c in ["ADO", "SNA", "SFJ", "7G", "6J"]): s_key = "P4"
            
            flight_rows.append({
                "time": f"{f_h:02d}:{f_m:02d}", "flight": f"{carrier}{fnum}", 
                "origin": origin[:6], "pax": pax, "s_key": s_key
            })

        except: continue

    print(f"1. 有効な時刻候補: {valid_time_count}件 (ノイズ除去後)")

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
