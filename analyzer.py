import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v4.3.1: 構文エラー修正版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8") as f:
        raw_content = f.read()

    # --- 洗浄ロジック ---
    clean_content = re.sub(r'<style.*?>.*?</style>', '', raw_content, flags=re.DOTALL)
    clean_content = re.sub(r'<script.*?>.*?</script>', '', clean_content, flags=re.DOTALL)
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # 時刻検索正規表現（タグ考慮版）
    time_pattern = r'(\d{1,2})\s*(?:<[^>]+>)*\s*[:：]\s*(?:<[^>]+>)*\s*(\d{2})'
    time_matches = list(re.finditer(time_pattern, clean_content))
    
    print(f"1. 調査地点: {len(time_matches)}件 見つかりました")

    # 調査地点0件時のディープ・デバッグ（エラー修正箇所）
    if len(time_matches) == 0:
        print("⚠️ 時刻未検知。JAL/ANA周辺の構造を解析します...")
        for key in ["JAL", "JL", "ANA", "NH"]:
            pos = clean_content.find(key)
            if pos != -1:
                # バックスラッシュ問題を回避するため、一度変数に入れてから出力
                debug_text = clean_content[max(0,pos-100):pos+200].replace('\n',' ')
                print(f"[{key}] 周辺データ: {debug_text}")
                break

    for m in time_matches:
        try:
            h_str, m_str = m.groups()
            f_h, f_m = int(h_str), int(m_str)
            
            ampm_chunk = clean_content[m.end() : m.end() + 30].upper()
            if "PM" in ampm_chunk and f_h < 12: f_h += 12
            elif "AM" in ampm_chunk and f_h == 12: f_h = 0
            
            f_t = now.replace(hour=f_h % 24, minute=f_m, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            start = max(0, m.start() - 350) 
            chunk = clean_content[start : m.start() + 550]
            
            # 便名検索
            flight_m = re.search(r'([A-Z]{2,3})\s?(?:<[^>]+>)*\s?(\d{1,4})', chunk)
            if flight_m:
                carrier, fnum = flight_m.groups()
                carrier = carrier.upper()

                # 出身地の抽出
                origin = "不明"
                origin_m = re.search(r'<td>(.*?)</td>', chunk, re.DOTALL)
                if origin_m:
                    origin = re.sub(r'<.*?>', '', origin_m.group(1)).strip()
                    if not origin or len(origin) < 2 or "--" in origin:
                        alt_m = re.search(r'>([ぁ-んァ-ヶー一-龠]{2,10})<', chunk)
                        origin = alt_m.group(1) if alt_m else "不明"

                # 機材判定
                cap = CONFIG["CAPACITY"]["SMALL"]
                is_big = any(x in chunk for x in ["777", "787", "350", "767", "A330"])
                if is_big or int(fnum) < 1000:
                    cap = CONFIG["CAPACITY"]["BIG"]
                
                if carrier not in ["JL", "NH", "BC", "7G", "6J", "ADO", "SNA", "SFJ"]:
                    cap = CONFIG["CAPACITY"]["INTL"]

                pax = int(cap * CONFIG["LOAD_FACTORS"]["NORMAL"]) 
                
                s_key = "P5"
                if "JL" in carrier:
                    if any(city in origin for city in CONFIG["SOUTH_CITIES"]): s_key = "P1"
                    elif any(city in origin for city in CONFIG["NORTH_CITIES"]): s_key = "P2"
                    else: s_key = "P1"
                elif "BC" in carrier: s_key = "P1"
                elif "NH" in carrier: s_key = "P3"
                elif any(c in carrier for c in ["ADO", "SNA", "SFJ", "7G"]): s_key = "P4"
                
                flight_rows.append({
                    "time": f"{f_h:02d}:{f_m:02d}", "flight": f"{carrier}{fnum}", 
                    "origin": origin[:6], "pax": pax, "s_key": s_key
                })

        except Exception: continue

    seen = set()
    unique_rows = []
    for r in flight_rows:
        id_str = f"{r['time']}-{r['flight']}-{r['origin']}" 
        if id_str not in seen:
            seen.add(id_str)
            unique_rows.append(r)

    for k in stands: stands[k] = 0
    for r in unique_rows: stands[r['s_key']] += r['pax']

    pool_preds = {}
    base_cars = {"P1": 100, "P2": 100, "P3": 120, "P4": 80, "P5": 150}
    for k, p_pax in stands.items():
        pool_preds[k] = max(0, base_cars[k] - int(p_pax / 10))

    total_pax = sum(r['pax'] for r in unique_rows)
    result = {
        "stands": stands, "pool_preds": pool_preds, "total_pax": total_pax, 
        "rows": unique_rows, "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"2. 解析完了。有効便数: {len(unique_rows)} / 総需要: {total_pax}人")
    return result
