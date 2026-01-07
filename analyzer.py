import re, datetime, json, os, unicodedata
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v16.1: 現場語彙・完全一致版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]): return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_html = f.read()

    # 前処理：正規化
    content = unicodedata.normalize('NFKC', raw_html)
    text = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    # 🔎 【証拠開示】冒頭のテキストを表示
    print(f"\n--- 📋 取得データ断片 (JAL/ANA/エアドゥを探せ！) ---")
    print(text[text.find("到着"):text.find("到着")+1000]) # 「到着」という文字周辺を表示
    print(f"-----------------------------------\n")

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    active_rows = []
    found_all_list = []

    # 🌟 プロデューサーの目視情報を辞書に完全反映
    carrier_map = {
        "ANA": ["全日本空輸", "ANA", "全日空"],
        "JAL": ["日本航空", "JAL", "JL"],
        "ADO": ["エアドゥ", "AIRDO", "AIR DO"],
        "SNA": ["ソラシド エア", "ソラシド", "SNJ"],
        "SKY": ["スカイマーク", "SKY", "BC"]
    }

    time_matches = list(re.finditer(r'(\d{1,2}:\d{2})', text))
    print(f"1. ページ内に {len(time_matches)} 個の時刻ポイントを確認。精査開始...")

    for m in time_matches:
        time_str = m.group(1)
        chunk = text[m.start() : m.start() + 300].upper()
        
        found_c = None
        for code, keywords in carrier_map.items():
            if any(kw.upper() in chunk for kw in keywords):
                found_c = code; break
        
        if not found_c: continue
        
        origin = "不明"
        for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
            if city in chunk:
                origin = city; break

        found_all_list.append(f"[{time_str} {found_c} ({origin})]")

        # 需要窓判定 (T-30 〜 T+45)
        h, m_val = map(int, time_str.split(':'))
        f_t = now.replace(hour=h, minute=m_val, second=0, microsecond=0)
        diff = (f_t - now).total_seconds() / 60
        if diff < -720: f_t += datetime.timedelta(days=1); diff += 1440
        elif diff > 720: f_t -= datetime.timedelta(days=1); diff -= 1440

        if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
            active_rows.append({"time": time_str, "flight": found_c, "origin": origin, "pax": 150, "s_key": "P1"})

    print(f"--- 📊 最終監査報告 ---")
    if found_all_list:
        print(f"✅ 発掘成功！ 計 {len(found_all_list)} 件を確認。")
        print(f"サンプル: {', '.join(found_all_list[:5])}")
    else:
        print(f"❌ 依然として有効な便が見当たりません。")
    print(f"----------------------")

    result = {"stands": stands, "total_pax": len(active_rows)*150, "rows": active_rows, "total_flights_on_page": len(found_all_list), "update_time": now.strftime("%H:%M")}
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result
