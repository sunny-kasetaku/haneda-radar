import re
import datetime
import json
import os
import unicodedata
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v12.0: 精密「一本釣り」版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        content = f.read()

    # 文字の正規化
    content = unicodedata.normalize('NFKC', content)
    
    # 【重要】Yahoo!のフライトテーブル（行）を正規表現でダイレクトに抜く
    # <td>時刻</td> <td>便名</td> <td>出発地</td> <td>状況</td> という構造を狙い撃ち
    # 💡 タグを含めたまま検索することで、ヘッダーの「更新時刻」などのノイズを完全に無視します
    row_pat = re.compile(
        r'<td>(?P<time>\d{1,2}:\d{2})</td>'     # 時刻
        r'.*?<td>(?P<flight>.*?)</td>'           # 便名
        r'.*?<td>(?P<origin>.*?)</td>'           # 出発地
        r'.*?<td>(?P<status>.*?)</td>',          # 状況
        re.DOTALL | re.IGNORECASE
    )

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    active_rows = []
    total_count = 0

    print("1. Yahoo!のテーブル構造を精密スキャン中...")

    for m in row_pat.finditer(content):
        # 各項目からタグを除去して純粋なテキストに
        time_str = re.sub(r'<[^>]+>', '', m.group('time')).strip()
        flight_raw = re.sub(r'<[^>]+>', '', m.group('flight')).strip()
        origin_raw = re.sub(r'<[^>]+>', '', m.group('origin')).strip()
        
        if not flight_raw or "便名" in flight_raw: continue
        
        total_count += 1
        
        # 時刻補正 (例: 8:30 -> 08:30)
        if len(time_str) == 4: time_str = "0" + time_str
        h, m_val = map(int, time_str.split(':'))
        
        # 出身地の特定
        origin = "不明"
        for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
            if city in origin_raw:
                origin = city; break
        
        # キャリア判定
        carrier = "不明"
        if any(x in flight_raw.upper() for x in ["JAL", "JL"]): carrier = "JAL"
        elif any(x in flight_raw.upper() for x in ["ANA", "NH"]): carrier = "ANA"
        elif any(x in flight_raw.upper() for x in ["SKY", "BC"]): carrier = "SKY"
        elif "ADO" in flight_raw.upper(): carrier = "ADO"
        elif "SNA" in flight_raw.upper(): carrier = "SNA"
        elif "SFJ" in flight_raw.upper(): carrier = "SFJ"

        # 時刻計算と判定
        f_t = now.replace(hour=h, minute=m_val, second=0, microsecond=0)
        diff = (f_t - now).total_seconds() / 60
        if diff < -720: f_t += datetime.timedelta(days=1); diff += 1440
        elif diff > 720: f_t -= datetime.timedelta(days=1); diff -= 1440

        if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
            s_key = "P5"
            if carrier == "JAL":
                s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
            elif carrier == "ANA": s_key = "P3"
            elif carrier == "SKY": s_key = "P1"
            elif carrier in ["ADO", "SNA", "SFJ"]: s_key = "P4"

            # 予測人数
            cap = CONFIG["CAPACITY"]["BIG"] if origin in ["札幌", "福岡", "那覇", "伊丹"] else CONFIG["CAPACITY"]["SMALL"]
            pax = int(cap * 0.8) # 深夜帯

            active_rows.append({
                "time": time_str, "flight": flight_raw, 
                "origin": origin, "pax": pax, "s_key": s_key
            })
            stands[s_key] += pax

    result = {
        "stands": stands, "total_pax": sum(stands.values()), 
        "rows": active_rows, "total_flights_on_page": total_count,
        "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ 解析完了: ページ内に {total_count} 便を確認")
    print(f"🎯 有効便(窓内): {len(active_rows)} 便")
    return result
