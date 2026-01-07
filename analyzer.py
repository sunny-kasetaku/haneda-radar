import re
import datetime
import json
import os
import unicodedata
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v12.1: 構造突破版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_content = f.read()

    # 1. 全角半角の正規化
    content = unicodedata.normalize('NFKC', raw_content)
    
    # 2. 【必殺】フライトリストの開始地点を特定
    # ページの冒頭にある「更新時刻」を避けるため、「便名」という文字より後だけを解析対象にします
    start_pos = content.find("便名")
    if start_pos == -1: start_pos = 0
    target_html = content[start_pos:]
    
    # 3. タグを除去してテキスト化
    text = re.sub(r'<[^>]+>', ' ', target_html)
    text = re.sub(r'\s+', ' ', text)
    
    print(f"DEBUG: 解析対象テキスト(冒頭200文字): {text[:200]}")

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    active_rows = []
    total_found = 0

    # 4. パターン： 時刻(HH:MM) の後に 便名 と 都市名 が並ぶ
    carrier_pat = r'(JAL|ANA|SKY|ADO|SNA|SFJ|JL|NH|BC|6J|7G)\s*(\d+)'
    
    print("1. フライト表を一本釣り中...")
    
    for m in re.finditer(r'(\d{1,2}:\d{2})', text):
        time_str = m.group(1)
        h, m_val = map(int, time_str.split(':'))
        
        # 時刻の見つかった場所から、後方250文字を「1便のデータ塊」として調査
        chunk = text[m.start() : m.start() + 250]
        
        # キャリア判定
        c_match = re.search(carrier_pat, chunk.upper())
        if not c_match: continue
        
        total_found += 1
        carrier_code = c_match.group(1)
        f_num = c_match.group(2)
        
        # 出身地探し
        origin = "不明"
        for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
            if city in chunk:
                origin = city; break
        
        # 時刻計算と補正
        f_t = now.replace(hour=h, minute=m_val, second=0, microsecond=0)
        diff = (f_t - now).total_seconds() / 60
        if diff < -720: f_t += datetime.timedelta(days=1); diff += 1440
        elif diff > 720: f_t -= datetime.timedelta(days=1); diff -= 1440

        # 需要対象判定 (T-30 〜 T+45)
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

            # 推計人数
            cap = CONFIG["CAPACITY"]["BIG"] if origin in ["札幌", "福岡", "那覇", "伊丹"] else CONFIG["CAPACITY"]["SMALL"]
            pax = int(cap * 0.8) # 深夜帯

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

    print(f"--- 📊 最終報告 ---")
    print(f"✅ 解析成功: {total_found} 便のデータを捉えました。")
    print(f"🎯 需要対象: {len(active_rows)} 便")
    return result
