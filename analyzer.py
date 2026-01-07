import re, datetime, json, os, unicodedata
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v14.0: 執念の絨毯爆撃版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]): return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_html = f.read()

    # 1. 徹底クリーニング（タグを消して情報の密度を上げる）
    content = unicodedata.normalize('NFKC', raw_html)
    # スクリプトとスタイルを物理除去
    clean_html = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', content, flags=re.DOTALL | re.IGNORECASE)
    # タグを1つのスペースに置換
    text = re.sub(r'<[^>]+>', ' ', clean_html)
    text = re.sub(r'\s+', ' ', text)

    # 🔍 【重要】ページ冒頭のノイズ（現在時刻など）をカット
    # "便名" または "出発地" という文字以降が本番の表
    start_marker = text.find("便名")
    if start_marker == -1: start_marker = text.find("出発地")
    search_text = text[start_marker:] if start_marker != -1 else text

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    active_rows = []
    
    # 2. 航空会社判定用辞書
    carrier_map = {
        "JAL": ["JAL", "JL", "日本航空"],
        "ANA": ["ANA", "NH", "全日空"],
        "SKY": ["SKY", "BC", "スカイマーク"],
        "ADO": ["ADO", "エア・ドゥ", "AIR DO"],
        "SNA": ["SNA", "ソラシド"],
        "SFJ": ["SFJ", "スターフライヤー"]
    }

    # 3. 絨毯爆撃開始：ページ内のすべての時刻「HH:MM」を探す
    time_matches = list(re.finditer(r'(\d{1,2}:\d{2})', search_text))
    total_found = 0

    print(f"1. 検出された {len(time_matches)} 個の時刻周辺を絨毯爆撃中...")

    for i in range(len(time_matches)):
        m = time_matches[i]
        time_str = m.group(1)
        
        # 次の時刻までの間、あるいは200文字以内を「1便のデータ塊」とする
        end_pos = time_matches[i+1].start() if i+1 < len(time_matches) else m.start() + 200
        chunk = search_text[m.start() : end_pos].upper()
        
        # 航空会社特定（日本語名も逃さない）
        found_c = None
        for code, keywords in carrier_map.items():
            if any(kw in chunk for kw in keywords):
                found_c = code; break
        
        if not found_c: continue # 航空会社がいない時刻はゴミ
        
        total_found += 1
        
        # 出身地特定
        origin = "不明"
        for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
            if city in chunk:
                origin = city; break

        # 時刻計算と日付またぎ
        h, m_val = map(int, time_str.split(':'))
        f_t = now.replace(hour=h, minute=m_val, second=0, microsecond=0)
        diff = (f_t - now).total_seconds() / 60
        if diff < -720: f_t += datetime.timedelta(days=1); diff += 1440
        elif diff > 720: f_t -= datetime.timedelta(days=1); diff -= 1440

        # 実戦窓判定
        if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
            s_key = "P5"
            if found_c == "JAL":
                s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
            elif found_c == "ANA": s_key = "P3"
            elif found_c == "SKY": s_key = "P1"
            elif found_c in ["ADO", "SNA", "SFJ"]: s_key = "P4"

            cap = CONFIG["CAPACITY"]["BIG"] if origin in ["札幌", "福岡", "那覇", "伊丹"] else CONFIG["CAPACITY"]["SMALL"]
            pax = int(cap * 0.85)

            active_rows.append({
                "time": time_str, "flight": found_c, "origin": origin, "pax": pax, "s_key": s_key
            })
            stands[s_key] += pax

    result = {
        "stands": stands, "total_pax": sum(stands.values()), "rows": active_rows, 
        "total_flights_on_page": total_found, "update_time": now.strftime("%H:%M")
    }
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"--- 📊 絨毯爆撃結果 ---")
    print(f"✅ 全 {total_found} 便をサルベージしました！")
    print(f"🎯 有効需要: {len(active_rows)} 便")
    return result
