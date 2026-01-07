import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v9.2: Yahoo!一網打尽版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        content = f.read()

    # 1. 余計なタグを除去して、純粋な「文字の流れ」にする
    # タグをすべてスペースに置換
    text_content = re.sub(r'<[^>]+>', ' ', content)
    # 連続する空白を1つにまとめる
    text_content = re.sub(r'\s+', ' ', text_content)
    
    print(f"DEBUG: 抽出テキスト(冒頭500文字): {text_content[:500]}")

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # 時刻を起点に、その後の100文字以内に便名と都市があるか探す
    # パターン: HH:MM の後に 便名(ANA123等) と 都市名
    time_pat = r'(\d{2}:\d{2})'
    carrier_pat = r'(JAL|ANA|SKY|ADO|SNA|SFJ|JL|NH|BC|6J|7G)\s*(\d+)'
    
    print("1. 29KBのテキストから全便を抽出中...")
    
    # 全ての時刻を検索
    for m in re.finditer(time_pat, text_content):
        time_str = m.group(1)
        h, m_val = map(int, time_str.split(':'))
        
        # 周辺150文字を調査
        chunk = text_content[m.start() : m.start() + 150]
        
        # 便名探し
        c_match = re.search(carrier_pat, chunk.upper())
        if not c_match: continue
        
        carrier = c_match.group(1)
        f_num = c_match.group(2)
        
        # 都市名探し
        origin = "不明"
        for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
            if city in chunk:
                origin = city; break

        # 日付またぎ補正
        f_t = now.replace(hour=h, minute=m_val, second=0, microsecond=0)
        diff = (f_t - now).total_seconds() / 60
        if diff < -1000: f_t += datetime.timedelta(days=1); diff += 1440
        
        # 判定ウィンドウ (T-30 〜 T+45)
        if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
            continue

        # 乗り場判定
        real_c = carrier
        if carrier == "NH": real_c = "ANA"
        if carrier == "JL": real_c = "JAL"
        if carrier == "BC": real_c = "SKY"
        
        s_key = "P5"
        if real_c == "JAL":
            s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
        elif real_c == "ANA": s_key = "P3"
        elif real_c == "SKY": s_key = "P1"
        elif real_c in ["ADO", "SNA", "SFJ"]: s_key = "P4"

        pax = int(CONFIG["CAPACITY"]["SMALL"] * CONFIG["LOAD_FACTORS"]["MIDNIGHT"])
        if origin in ["札幌", "福岡", "那覇", "伊丹"]:
            pax = int(CONFIG["CAPACITY"]["BIG"] * CONFIG["LOAD_FACTORS"]["MIDNIGHT"])

        flight_rows.append({
            "time": time_str, "flight": f"{real_c}{f_num}", 
            "origin": origin, "pax": pax, "s_key": s_key
        })
        stands[s_key] += pax

    result = {
        "stands": stands, "pool_preds": {k: max(0, 100 - int(v/10)) for k, v in stands.items()},
        "total_pax": sum(stands.values()), "rows": flight_rows, "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"2. 解析完了。有効便数: {len(flight_rows)} / 総予測人数: {result['total_pax']}名")
    return result
