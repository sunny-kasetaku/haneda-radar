import re, datetime, json, os, unicodedata
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v13.0: 逆転のアンカー発掘版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]): return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        content = f.read()

    # 1. ノイズ除去と正規化
    content = unicodedata.normalize('NFKC', content)
    # タグを消す際、情報の区切りを消さないようスペースに置換
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'\s+', ' ', text)

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    active_rows = []
    
    # 【逆転の発想】まず「便名」を探す。これはページ上部に存在しない「アンカー（錨）」です。
    carrier_pat = r'(JAL|ANA|SKY|ADO|SNA|SFJ|JL|NH|BC|6J|7G)\s*(\d+)'
    
    print("1. 便名をアンカーにして、周囲の時刻と出身地をサルベージ中...")
    
    # ページ内の全ての「便名」を抽出
    all_flight_matches = list(re.finditer(carrier_pat, text.upper()))
    total_found = len(all_flight_matches)

    for m in all_flight_matches:
        carrier = m.group(1)
        f_num = m.group(2)
        
        # 便名の前後300文字を「捜索範囲」とする
        search_range = text[max(0, m.start()-150) : m.end()+150]
        
        # 時刻(HH:MM)を探す
        time_m = re.search(r'(\d{1,2}:\d{2})', search_range)
        if not time_m: continue
        
        time_str = time_m.group(1)
        if len(time_str) == 4: time_str = "0" + time_str
        h, m_val = map(int, time_str.split(':'))
        
        # 出身地を探す
        origin = "不明"
        for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
            if city in search_range:
                origin = city; break
        
        # 判定用時刻
        f_t = now.replace(hour=h, minute=m_val, second=0, microsecond=0)
        diff = (f_t - now).total_seconds() / 60
        if diff < -720: f_t += datetime.timedelta(days=1); diff += 1440
        elif diff > 720: f_t -= datetime.timedelta(days=1); diff -= 1440

        # 需要対象（窓内）の判定
        if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
            real_c = carrier
            if carrier == "NH": real_c = "ANA"
            if carrier == "JL": real_c = "JAL"
            
            s_key = "P5"
            if real_c == "JAL":
                s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
            elif real_c == "ANA": s_key = "P3"
            elif real_c == "SKY": s_key = "P1"
            elif real_c in ["ADO", "SNA", "SFJ"]: s_key = "P4"

            pax = int(CONFIG["CAPACITY"]["SMALL"] * 0.8)
            if origin in ["札幌", "福岡", "那覇", "伊丹"]:
                pax = int(CONFIG["CAPACITY"]["BIG"] * 0.8)

            active_rows.append({"time": time_str, "flight": f"{real_c}{f_num}", "origin": origin, "pax": pax, "s_key": s_key})
            stands[s_key] += pax

    result = {
        "stands": stands, "total_pax": sum(stands.values()), "rows": active_rows, 
        "total_flights_on_page": total_found, "update_time": now.strftime("%H:%M")
    }
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"--- 📊 KASETACK 最終報告 (v13.0) ---")
    print(f"✅ 発掘成功: {total_found} 便のアンカーを特定")
    print(f"🎯 有効需要: {len(active_rows)} 便")
    return result
