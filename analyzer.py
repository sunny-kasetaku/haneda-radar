import re, datetime, json, os, unicodedata
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v13.0: 逆転のアンカー発掘版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]): return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        content = f.read()

    # 1. 徹底的なノイズ除去と正規化
    content = unicodedata.normalize('NFKC', content)
    # タグをスペースに置換して情報の癒着を防ぐ
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'\s+', ' ', text)

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    active_rows = []
    
    # 2. 【逆転のアンカー】まず「便名」をページ全体から探し出す
    # 航空会社コード + 数字 (例: ANA123, JL500)
    carrier_pat = r'(JAL|ANA|SKY|ADO|SNA|SFJ|JL|NH|BC|6J|7G)\s*(\d+)'
    
    print("1. 便名をアンカーにして、周囲の時刻と出身地を救出中...")
    
    # 全ての便名マッチをリスト化
    all_flight_matches = list(re.finditer(carrier_pat, text.upper()))
    total_found = len(all_flight_matches)

    for m in all_flight_matches:
        carrier_code = m.group(1)
        f_num = m.group(2)
        
        # 便名が見つかった場所の「前後250文字」を捜索範囲とする
        # これにより、ページ上部の更新時刻などに惑わされることがなくなります
        search_area = text[max(0, m.start()-150) : m.end()+150]
        
        # 捜索範囲内から「時刻(HH:MM)」を探す
        time_m = re.search(r'(\d{1,2}:\d{2})', search_area)
        if not time_m: continue
        
        time_str = time_m.group(1)
        if len(time_str) == 4: time_str = "0" + time_str
        h, m_val = map(int, time_str.split(':'))
        
        # 捜索範囲内から「出身地」を探す
        origin = "不明"
        for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
            if city in search_area:
                origin = city; break
        
        # 時刻計算（日付またぎ補正）
        f_t = now.replace(hour=h, minute=m_val, second=0, microsecond=0)
        diff = (f_t - now).total_seconds() / 60
        if diff < -720: f_t += datetime.timedelta(days=1); diff += 1440
        elif diff > 720: f_t -= datetime.timedelta(days=1); diff -= 1440

        # 需要対象（窓内）の判定
        if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
            real_c = carrier_code
            if carrier_code == "NH": real_c = "ANA"
            if carrier_code == "JL": real_c = "JAL"
            
            s_key = "P5"
            if real_c == "JAL":
                s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
            elif real_c == "ANA": s_key = "P3"
            elif real_c == "SKY": s_key = "P1"
            elif real_c in ["ADO", "SNA", "SFJ"]: s_key = "P4"

            # 推計人数 (深夜帯のコンサバ設定)
            cap = CONFIG["CAPACITY"]["BIG"] if origin in ["札幌", "福岡", "那覇", "伊丹"] else CONFIG["CAPACITY"]["SMALL"]
            pax = int(cap * 0.8)

            active_rows.append({
                "time": time_str, 
                "flight": f"{real_c}{f_num}", 
                "origin": origin, 
                "pax": pax, 
                "s_key": s_key
            })
            stands[s_key] += pax

    result = {
        "stands": stands, 
        "total_pax": sum(stands.values()), 
        "rows": active_rows, 
        "total_flights_on_page": total_found, 
        "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"--- 📊 KASETACK 逆転発掘レポート ---")
    print(f"✅ 全 {total_found} 便のアンカーを特定")
    print(f"🎯 有効需要: {len(active_rows)} 便")
    return result
