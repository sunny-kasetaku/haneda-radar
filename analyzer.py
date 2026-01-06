import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- Analyzer 出身地・機材 徹底特定版開始 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8") as f:
        content = f.read()

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # 1. 時刻パターンの抽出
    time_matches = list(re.finditer(r'(\d{1,2}):(\d{2})\s?([AP]M)?', content, re.IGNORECASE))
    print(f"1. 全 {len(time_matches)} 候補のうち、前後30分の便を精査します")

    for m in time_matches:
        try:
            h_str, m_str, ampm = m.groups()
            f_h, f_m = int(h_str), int(m_str)
            if ampm and ampm.upper() == "PM" and f_h < 12: f_h += 12
            elif ampm and ampm.upper() == "AM" and f_h == 12: f_h = 0
            
            f_t = now.replace(hour=f_h % 24, minute=f_m, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            
            # 【鉄の掟】30/30ウィンドウ（ここ以外は容赦なく捨てる）
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            # 周辺情報を取得
            start = max(0, m.start() - 150)
            chunk = content[start : start + 600]
            
            # 便名検索
            flight_m = re.search(r'([A-Z0-9]{2,3})\s?(\d{1,4})', chunk)
            if flight_m:
                carrier, fnum = flight_m.groups()
                carrier = carrier.upper()

                # --- 足し算：出身地（Origin）の徹底抽出 ---
                # パターンA: <td>内, パターンB: リンクテキスト内, パターンC: カッコ内
                origin = "不明"
                origin_patterns = [r'<td>(.*?)</td>', r'>(.*?)</a>', r'\((.*?)\)']
                for pat in origin_patterns:
                    om = re.search(pat, chunk, re.DOTALL)
                    if om:
                        tmp = re.sub(r'<.*?>', '', om.group(1)).strip()
                        if len(tmp) > 1 and "AM" not in tmp and "PM" not in tmp:
                            origin = tmp
                            break

                # --- 足し算：機材名によるキャパ判定 ---
                cap = CONFIG["CAPACITY"]["SMALL"]
                is_big = False
                if any(x in chunk for x in ["777", "787", "350", "767", "A330"]):
                    cap = CONFIG["CAPACITY"]["BIG"]
                    is_big = True
                elif int(fnum) < 1000: # 3桁便名は幹線（JAL/ANA想定）
                    cap = CONFIG["CAPACITY"]["BIG"]

                if carrier not in ["JL", "NH", "BC", "7G", "6J", "ADO", "SNA", "SFJ"]:
                    cap = CONFIG["CAPACITY"]["INTL"]

                rate = CONFIG["LOAD_FACTORS"]["NORMAL"]
                if 22 <= now.hour or now.hour <= 2: rate = CONFIG["LOAD_FACTORS"]["MIDNIGHT"]
                elif 7 <= now.hour <= 9 or 17 <= now.hour <= 20: rate = CONFIG["LOAD_FACTORS"]["RUSH"]

                pax = int(cap * rate)
                
                # 振り分けロジック
                s_key = "P5"
                if "JL" in carrier:
                    if any(city in origin for city in CONFIG["SOUTH_CITIES"]): s_key = "P1"
                    elif any(city in origin for city in CONFIG["NORTH_CITIES"]): s_key = "P2"
                    else: s_key = "P1"
                elif "BC" in carrier: s_key = "P1"
                elif "NH" in carrier: s_key = "P3"
                elif any(c in carrier for c in ["ADO", "SNA", "SFJ", "7G"]): s_key = "P4"
                
                # ログ出力（プロデューサーへの安心感）
                status = "大型" if is_big else "普通"
                print(f" ✅ 検知: {f_h:02d}:{f_m:02d} {carrier}{fnum} ({origin}) [{status}] -> {pax}人")

                flight_rows.append({"time": f"{f_h:02d}:{f_m:02d}", "flight": f"{carrier}{fnum}", "origin": origin[:6], "pax": pax, "s_key": s_key})

        except Exception: continue

    # 重複排除
    seen = set()
    unique_rows = []
    for r in flight_rows:
        id_str = f"{r['time']}-{r['origin']}" 
        if id_str not in seen:
            seen.add(id_str)
            unique_rows.append(r)

    # 最終集計
    total_pax = sum(r['pax'] for r in unique_rows)
    for k in stands: stands[k] = 0
    for r in unique_rows:
        stands[r['s_key']] += r['pax']

    result = {"stands": stands, "total_pax": total_pax, "rows": unique_rows, "update_time": now.strftime("%H:%M")}
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"2. 解析完了。有効な便数: {len(unique_rows)} 便 / 合計需要: {total_pax}人")
    return result
