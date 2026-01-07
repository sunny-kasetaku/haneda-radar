import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v4.6: 隠しデータ発掘版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_content = f.read()

    # --- 1. 生データ内の「真」のキーワード捜索（誤検知回避） ---
    # 単なる ana ではなく、"ANA" や航空会社コードとして存在するものを探す
    print("--- 🔍 構造解析：深層スキャン ---")
    keys = [r'"ANA"', r'>ANA<', r'"JAL"', r'>JAL<', r'"JL"', r'"NH"']
    found_any = False
    for k_pat in keys:
        m = re.search(k_pat, raw_content)
        if m:
            snippet = raw_content[max(0, m.start()-50):m.end()+150].replace('\n',' ')
            print(f"✅ 発見 [{k_pat}]: ...{snippet}...")
            found_any = True
            break
    
    # --- 2. 隠しデータ (Next.js JSON) の直接抽出試行 ---
    next_data = re.search(r'<script id="__NEXT_DATA__".*?>(.*?)</script>', raw_content, re.DOTALL)
    if next_data:
        print("💡 隠しJSONデータを発見しました。ここから直接データを抜きます。")
        # ここにJSON解析を入れる余地あり

    # --- 3. 時刻検索の超・広域化 ---
    # パターン1: 19:05 / 19時05分 / 1905 (4桁数字)
    time_patterns = [
        r'(\d{1,2})\s*[:：]\s*(\d{2})',           # 19:05
        r'(\d{1,2})時\s*(\d{2})分',                # 19時05分
        r'\"arrivalTime\"\s*:\s*\"(\d{2})(\d{2})\"' # JSON内の "1905"
    ]
    
    flight_rows = []
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}

    for pat in time_patterns:
        time_matches = list(re.finditer(pat, raw_content))
        if time_matches:
            print(f"🎯 パターン [{pat}] で {len(time_matches)}件 ヒット")
            for m in time_matches:
                try:
                    h_str, m_str = m.groups()
                    f_h, f_m = int(h_str), int(m_str)
                    
                    f_t = now.replace(hour=f_h % 24, minute=f_m, second=0, microsecond=0)
                    diff = (f_t - now).total_seconds() / 60
                    
                    if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                        continue

                    chunk = raw_content[max(0, m.start()-300) : m.end()+500].upper()
                    
                    # 便名と出身地を力ずくで探す
                    carrier = "不明"
                    for c in ["JAL", "JL", "ANA", "NH", "BC", "SKY", "ADO", "SNA", "SFJ"]:
                        if c in chunk:
                            carrier = c
                            break
                    
                    origin = "不明"
                    # 漢字・カタカナの塊を都市名として推測
                    cities = re.findall(r'[ァ-ヶー一-龠]{2,6}', chunk)
                    for c_candidate in cities:
                        if any(c_candidate in city for city in CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
                            origin = c_candidate
                            break

                    cap = CONFIG["CAPACITY"]["SMALL"]
                    if any(x in chunk for x in ["777", "787", "350", "767", "A330"]): cap = CONFIG["CAPACITY"]["BIG"]
                    
                    pax = int(cap * CONFIG["LOAD_FACTORS"]["NORMAL"])
                    
                    s_key = "P5"
                    if carrier in ["JAL", "JL"]:
                        if any(c in origin for c in CONFIG["SOUTH_CITIES"]): s_key = "P1"
                        elif any(c in origin for c in CONFIG["NORTH_CITIES"]): s_key = "P2"
                        else: s_key = "P1"
                    elif carrier in ["NH", "ANA"]: s_key = "P3"
                    elif carrier in ["BC", "SKY"]: s_key = "P1"
                    elif any(c in carrier for c in ["ADO", "SNA", "SFJ"]): s_key = "P4"

                    flight_rows.append({"time": f"{f_h:02d}:{f_m:02d}", "flight": f"{carrier}", "origin": origin, "pax": pax, "s_key": s_key})
                except: continue
        
    # 重複削除
    unique_rows = []
    seen = set()
    for r in flight_rows:
        id_str = f"{r['time']}-{r['flight']}-{r['origin']}"
        if id_str not in seen:
            seen.add(id_str); unique_rows.append(r)

    # 集計
    for r in unique_rows: stands[r['s_key']] += r['pax']
    
    # 最終デバッグ：何も見つからない場合はテキストだけ出す
    if not unique_rows:
        print("🚨 有効なデータが見つかりません。HTMLタグを剥がして文字を調査します:")
        plain_text = re.sub(r'<[^>]+>', ' ', raw_content)
        print(plain_text[1000:2000].replace('\n', ' '))

    result = {
        "stands": stands, "pool_preds": {k: max(0, 100 - int(v/10)) for k, v in stands.items()},
        "total_pax": sum(stands.values()), "rows": unique_rows, "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"2. 解析完了。有効便数: {len(unique_rows)} / 総需要: {result['total_pax']}人")
    return result
