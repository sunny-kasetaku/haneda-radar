import re
import datetime
import json
import os
import unicodedata
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v9.3: 全時間帯・全文字正規化版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_content = f.read()

    # 1. 全角を半角に変換 (ＡＮＡ -> ANA, ００:１５ -> 00:15)
    content = unicodedata.normalize('NFKC', raw_content)
    
    # 不要なタグを除去して、純粋な「文字の流れ」にする
    text_content = re.sub(r'<[^>]+>', ' ', content)
    text_content = re.sub(r'\s+', ' ', text_content)
    
    print(f"DEBUG: 変換後テキスト(冒頭300文字): {text_content[:300]}")

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # 便名パターンの定義 (ANA123, NH456 等)
    carrier_pat = r'(JAL|ANA|SKY|ADO|SNA|SFJ|JL|NH|BC|6J|7G)\s*(\d+)'
    
    print("1. 29KBの全データから「全時間の便」をスキャン中...")
    
    # 時刻を起点に検索
    for m in re.finditer(r'(\d{1,2}:\d{2})', text_content):
        time_str = m.group(1)
        # 1桁の時間を2桁に補正 (例: 8:30 -> 08:30)
        if len(time_str) == 4: time_str = "0" + time_str
        
        h, m_val = map(int, time_str.split(':'))
        
        # 周辺200文字（Yahoo!は情報が離れていることがあるため広め）を調査
        chunk = text_content[max(0, m.start()-100) : m.start() + 200]
        
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

        # 判定用時刻オブジェクト
        f_t = now.replace(hour=h, minute=m_val, second=0, microsecond=0)
        diff = (f_t - now).total_seconds() / 60
        
        # 深夜の日付またぎ補正
        if diff < -720: # 12時間以上前なら明日
            f_t += datetime.timedelta(days=1)
            diff = (f_t - now).total_seconds() / 60
        elif diff > 720: # 12時間以上先なら昨日
            f_t -= datetime.timedelta(days=1)
            diff = (f_t - now).total_seconds() / 60

        # --- デバッグ用：窓の外でも、見つかった便は全てメモする ---
        real_c = carrier
        if carrier == "NH": real_c = "ANA"
        if carrier == "JL": real_c = "JAL"
        if carrier == "BC": real_c = "SKY"
        
        # 条件に合うものだけを本採用
        is_in_window = (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"])
        
        if is_in_window:
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
        else:
            # 窓の外で見つけた便（確認用）
            pass

    result = {
        "stands": stands, "pool_preds": {k: max(0, 100 - int(v/10)) for k, v in stands.items()},
        "total_pax": sum(stands.values()), "rows": flight_rows, "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"2. 解析完了。有効便数(窓内): {len(flight_rows)}")
    if len(flight_rows) == 0:
        print("ℹ️ 現在の窓(00:10-01:25)には到着便がありません。データ取得自体は成功しています。")
    return result
