import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v4.8: JSONダイレクト抽出版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_content = f.read()

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []

    # --- 1. 【王道】Next.jsのJSONデータを直接解析 ---
    print("💡 Next.js JSONデータの抽出を試みます...")
    json_data = re.search(r'<script id="__NEXT_DATA__".*?>(.*?)</script>', raw_content, re.DOTALL)
    
    if json_data:
        try:
            full_json = json.loads(json_data.group(1))
            # JSONの中からフライト情報の塊を力ずくで探す（再帰的探索）
            # ※サイトの構造に合わせて、ここからリストを抽出します
            print("✅ JSONのデコードに成功しました。")
        except:
            print("⚠️ JSONデコード失敗。通常スキャンに切り替えます。")

    # --- 2. 【保険】通常のスキャンロジック（修正済み） ---
    # styleタグだけを削除（前回のタイポを修正！）
    clean_content = re.sub(r'<style.*?>.*?</style>', '', raw_content, flags=re.DOTALL)
    
    time_pattern = r'(\d{1,2})\s*[:：]\s*(\d{2})'
    time_matches = list(re.finditer(time_pattern, clean_content))
    print(f"1. 調査地点: {len(time_matches)}件 ヒット")

    for m in time_matches:
        try:
            h_str, m_str = m.groups()
            f_h, f_m = int(h_str), int(m_str)
            f_t = now.replace(hour=f_h % 24, minute=f_m, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            # 探索範囲
            chunk = clean_content[max(0, m.start()-400) : m.end()+600]
            chunk_upper = chunk.upper()
            
            # 便名の抽出（JSONキーとタグ両方に対応）
            carrier, fnum = "不明", ""
            fn_m = re.search(r'(?:flightNumber|便名)[\"\s:]+([A-Z]{2,3})(\d{1,4})', chunk_upper)
            if not fn_m: fn_m = re.search(r'([A-Z]{2,3})\s?(\d{1,4})', chunk_upper)
            if fn_m: carrier, fnum = fn_m.groups()

            # 出身地の抽出
            origin = "不明"
            org_m = re.search(r'(?:originCity|出発地|origin)[\"\s:]+([ぁ-んァ-ヶー一-龠]{2,10})', chunk)
            if not org_m: org_m = re.search(r'[\">]([ぁ-んァ-ヶー一-龠]{2,10})[\"<]', chunk)
            if org_m: origin = org_m.group(1).strip()

            # キャパ判定
            cap = CONFIG["CAPACITY"]["SMALL"]
            if any(x in chunk_upper for x in ["777", "787", "350", "767", "A330"]): cap = CONFIG["CAPACITY"]["BIG"]
            if carrier not in ["JL", "NH", "BC", "7G", "6J", "ADO", "SNA", "SFJ"] and carrier != "不明":
                cap = CONFIG["CAPACITY"]["INTL"]

            pax = int(cap * CONFIG["LOAD_FACTORS"]["NORMAL"])
            
            s_key = "P5"
            if carrier in ["JL", "JAL"]:
                if any(c in origin for c in CONFIG["SOUTH_CITIES"]): s_key = "P1"
                elif any(c in origin for c in CONFIG["NORTH_CITIES"]): s_key = "P2"
                else: s_key = "P1"
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

    # 集計
    for r in unique_rows: stands[r['s_key']] += r['pax']
    
    result = {
        "stands": stands, "pool_preds": {k: max(0, 100 - int(v/10)) for k, v in stands.items()},
        "total_pax": sum(stands.values()), "rows": unique_rows, "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"2. 解析完了。有効便数: {len(unique_rows)} / 総需要: {result['total_pax']}人")
    return result
