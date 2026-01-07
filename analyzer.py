import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v7.6: 真実の全貌ダンプ版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_html = f.read()

    # --- 1. 瓦礫（CSS/JS）を徹底排除して「意味のある文字」だけにする ---
    clean_html = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', raw_html, flags=re.DOTALL | re.IGNORECASE)
    # タグを消し、連続する空白を整理
    text_content = re.sub(r'<[^>]+>', ' ', clean_html)
    text_content = re.sub(r'\s+', ' ', text_content)

    # --- 2. 構造の「強制露出」 ---
    # JAL か ANA が見つかった場所の構造を 1 回だけ晒す
    for target in ["JAL", "ANA"]:
        pos = text_content.upper().find(target)
        if pos != -1:
            print(f"🔍 [構造ダンプ ({target}周辺)]: {text_content[max(0, pos-200):pos+800]}")
            break

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    city_map = {
        "SAPPORO": "札幌", "CHITOSE": "札幌", "FUKUOKA": "福岡", 
        "OKINAWA": "那覇", "NAHA": "那覇", "OSAKA": "大阪", "ITAMI": "伊丹"
    }
    
    # 3. 時刻とキャリアを広範囲で結びつける
    time_pat = r'(\d{1,2})[:：](\d{2})\s*([APap][Mm])?'
    
    print("1. 広域スキャン（1000文字レンジ）を開始...")

    for m in re.finditer(time_pat, text_content):
        try:
            h, m_val = int(m.group(1)), int(m.group(2))
            ampm = m.group(3)
            
            # AM/PM 補正
            if ampm:
                ampm = ampm.upper()
                if "PM" in ampm and h < 12: h += 12
                if "AM" in ampm and h == 12: h = 0
            
            # 探索範囲を前後に 500文字（計1000文字）に大幅拡大
            chunk = text_content[max(0, m.start()-500) : m.end()+500].upper()
            
            # キャリア特定
            carrier = "不明"
            if "JAL" in chunk or "JL" in chunk: carrier = "JAL"
            elif "ANA" in chunk or "NH" in chunk: carrier = "ANA"
            elif "SKY" in chunk or "BC" in chunk: carrier = "SKY"
            
            if carrier == "不明": continue

            # 都市特定
            origin = "不明"
            for eng, jap in city_map.items():
                if eng in chunk: origin = jap; break
            
            # 時間ウィンドウ（判定は最後に行う）
            f_t = now.replace(hour=h % 24, minute=m_val, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            if diff < -1000: f_t += datetime.timedelta(days=1); diff += 1440
            
            if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
                flight_rows.append({
                    "time": f_t.strftime("%H:%M"), "flight": carrier, 
                    "origin": origin, "pax": 150, "s_key": "P5" # 暫定
                })
        except: continue

    # 重複削除
    unique_rows = []
    seen = set()
    for r in flight_rows:
        id_str = f"{r['time']}-{r['flight']}-{r['origin']}"
        if id_str not in seen:
            seen.add(id_str); unique_rows.append(r)

    result = {
        "stands": stands, "pool_preds": {k: 100 for k in stands},
        "total_pax": len(unique_rows) * 150, "rows": unique_rows, "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"2. 解析完了。有効便数: {len(unique_rows)}")
    return result
