import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- Analyzer 執念の解析開始 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: 生データが見つかりません。")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 大文字小文字を無視し、改行も考慮して「行(tr)」を抽出
    # <tr ...> ～ </tr> を、大文字小文字問わずに抜き出す
    rows = re.findall(r'<tr.*?>.*?</tr>', content, re.IGNORECASE | re.DOTALL)
    print(f"1. ファイル読み込み完了 (サイズ: {len(content)} bytes)")
    print(f"2. 抽出された候補行数: {len(rows)} 行")

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    total_pax = 0
    
    # 判定用の時間帯レート
    rate = CONFIG["LOAD_FACTORS"]["NORMAL"]
    if 22 <= now.hour or now.hour <= 2: rate = CONFIG["LOAD_FACTORS"]["MIDNIGHT"]
    elif 7 <= now.hour <= 9 or 17 <= now.hour <= 20: rate = CONFIG["LOAD_FACTORS"]["RUSH"]

    # 便情報を抜くための正規表現（よりタフな書き方に変更）
    # 時間(hh:mm AM/PM)、航空会社(2-3文字)、便名(1-4桁) を狙い撃ち
    pattern = re.compile(r'(\d{1,2}):(\d{2})\s?([AP]M)?.*?([A-Z0-9]{2,3})\s?(\d{1,4})', re.IGNORECASE | re.DOTALL)

    for row in rows:
        match = pattern.search(row)
        if match:
            h, m, ampm, carrier, fnum = match.groups()
            carrier = carrier.upper()
            
            # --- 時間計算 ---
            f_h = int(h)
            if ampm and ampm.upper() == "PM" and f_h < 12: f_h += 12
            elif ampm and ampm.upper() == "AM" and f_h == 12: f_h = 0
            
            f_t = now.replace(hour=f_h % 24, minute=int(m), second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            
            # 設定された時間枠内か判定
            if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
                # 出身地(Origin)を別途抽出
                origin_match = re.search(r'<td>(.*?)</td>\s*$', row, re.DOTALL)
                origin = origin_match.group(1).strip() if origin_match else "不明"

                # 搭乗数計算
                cap = CONFIG["CAPACITY"]["BIG"] if int(fnum) < 1000 else CONFIG["CAPACITY"]["SMALL"]
                if carrier not in ["JL", "NH", "BC", "7G", "6J", "ADO", "SNA", "SFJ"]:
                    cap = CONFIG["CAPACITY"]["INTL"]
                
                pax = int(cap * rate)
                total_pax += pax
                
                # 振り分け
                s_key = "P5"
                if "JL" in carrier:
                    if any(city in origin for city in CONFIG["SOUTH_CITIES"]): s_key = "P1"
                    elif any(city in origin for city in CONFIG["NORTH_CITIES"]): s_key = "P2"
                    else: s_key = "P1"
                elif "BC" in carrier: s_key = "P1"
                elif "NH" in carrier: s_key = "P3"
                elif any(c in carrier for c in ["ADO", "SNA", "SFJ", "7G"]): s_key = "P4"
                
                stands[s_key] += pax
                flight_rows.append({"time": f"{f_h:02d}:{m}", "flight": f"{carrier}{fnum}", "origin": origin[:6], "pax": pax})

    print(f"3. 解析完了。該当便数: {len(flight_rows)} 便 / 推計合計: {total_pax}人")

    result = {
        "stands": stands, "total_pax": total_pax, "rows": flight_rows, "update_time": now.strftime("%H:%M")
    }
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("--- Analyzer 成功終了 ---")
    return result
