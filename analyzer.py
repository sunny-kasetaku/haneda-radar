import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v7.0: 原点回帰・実測版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        content = f.read()

    # スタイルとスクリプトを消して、純粋なテキストにする
    text_only = re.sub(r'<[^>]+>', ' ', content) # HTMLタグをスペースに置換
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # 都市名とキャリアのリスト
    all_cities = CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]
    carriers = ["JAL", "ANA", "SKY", "ADO", "SNA", "SFJ", "BC", "JL", "NH"]

    # 時刻を基準に周辺をスキャン
    for m in re.finditer(r'(\d{1,2})[:：](\d{2})', text_only):
        h, m_str = int(m.group(1)), int(m.group(2))
        if not (0 <= h <= 23 and 0 <= m_str <= 59): continue
        
        # ウィンドウ判定
        f_t = now.replace(hour=h, minute=m_str, second=0, microsecond=0)
        diff = (f_t - now).total_seconds() / 60
        if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]): continue

        # 周辺100文字にキャリアや都市があるか
        chunk = text_only[max(0, m.start()-100) : m.end()+150]
        
        carrier = "不明"
        for c in carriers:
            if c in chunk.upper(): carrier = c; break
        
        origin = "不明"
        for city in all_cities:
            if city in chunk: origin = city; break

        if carrier != "不明" or origin != "不明":
            # 集計（簡易）
            pax = 180 if "777" in chunk or "787" in chunk else 120
            s_key = "P5"
            if "JAL" in carrier or "JL" in carrier:
                s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
            elif "ANA" in carrier or "NH" in carrier:
                s_key = "P3"
            
            flight_rows.append({
                "time": f"{h:02d}:{m_str:02d}", "flight": carrier, 
                "origin": origin[:6], "pax": pax, "s_key": s_key
            })

    # 重複削除
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
