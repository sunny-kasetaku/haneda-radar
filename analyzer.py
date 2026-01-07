import re
import datetime
import json
import os
import unicodedata
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v12.2: 真・一本釣り（ノイズフィルター版） ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_html = f.read()

    # 1. 【ノイズ粉砕】スクリプト、スタイル、JSON-LDを徹底削除
    clean_html = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', raw_html, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. 全角半角の正規化
    content = unicodedata.normalize('NFKC', clean_html)
    
    # 3. タグを除去してテキスト化
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'\s+', ' ', text)
    
    # デバッグ：ゴミが消えたか確認
    print(f"DEBUG: クリーンテキスト(冒頭200文字): {text[:200]}")

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    active_rows = []
    total_found = 0

    # 航空会社判定パターン
    carrier_pat = r'(JAL|ANA|SKY|ADO|SNA|SFJ|JL|NH|BC|6J|7G)\s*(\d+)'
    
    print("1. フライト表を再スキャン中...")
    
    # 時刻(HH:MM)を起点にスキャン
    for m in re.finditer(r'(\d{1,2}:\d{2})', text):
        time_str = m.group(1)
        h, m_val = map(int, time_str.split(':'))
        
        # 時刻の後方200文字（ここが1便のデータ塊）を調査
        chunk = text[m.start() : m.start() + 250]
        
        # 【重要】周辺に「便名」らしきものがない時刻（更新時刻など）は無視する
        c_match = re.search(carrier_pat, chunk.upper())
        if not c_match:
            continue
        
        total_found += 1
        carrier_code = c_match.group(1)
        f_num = c_match.group(2)
        
        # 出身地探し
        origin = "不明"
        for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
            if city in chunk:
                origin = city; break
        
        # 時刻計算
        f_t = now.replace(hour=h, minute=m_val, second=0, microsecond=0)
        diff = (f_t - now).total_seconds() / 60
        if diff < -720: f_t += datetime.timedelta(days=1); diff += 1440
        elif diff > 720: f_t -= datetime.timedelta(days=1); diff -= 1440

        # 需要対象判定
        if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
            # コード正規化
            real_c = carrier_code
            if carrier_code == "NH": real_c = "ANA"
            if carrier_code == "JL": real_c = "JAL"
            
            s_key = "P5"
            if real_c == "JAL":
                s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
            elif real_c == "ANA": s_key = "P3"
            elif real_c == "SKY": s_key = "P1"
            elif real_c in ["ADO", "SNA", "SFJ"]: s_key = "P4"

            cap = CONFIG["CAPACITY"]["BIG"] if origin in ["札幌", "福岡", "那覇", "伊丹"] else CONFIG["CAPACITY"]["SMALL"]
            pax = int(cap * 0.8)

            active_rows.append({
                "time": time_str, "flight": f"{real_c}{f_num}", 
                "origin": origin, "pax": pax, "s_key": s_key
            })
            stands[s_key] += pax

    result = {
        "stands": stands, "total_pax": sum(stands.values()), "rows": active_rows, 
        "total_flights_on_page": total_found, "update_time": now.strftime("%H:%M")
    }
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"--- 📊 KASETACK 最終解析結果 ---")
    print(f"✅ 全 {total_found} 便を捕捉。")
    print(f"🎯 有効便(窓内): {len(active_rows)} 便")
    return result
