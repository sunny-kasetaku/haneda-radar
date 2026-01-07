import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v5.0: 大台突破・連結極限版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_content = f.read()

    # --- 1. 【絶対律】生データの生存確認ログ ---
    raw_upper = raw_content.upper()
    for key in ["JAL", "ANA", "JL", "NH"]:
        pos = raw_upper.find(key)
        if pos != -1:
            snippet = raw_content[max(0, pos-50):pos+150].replace('\n', ' ')
            print(f"✅ 連結ターゲット確認 [{key}]: ...{snippet}...")
            break

    # --- 2. 解析（無洗浄・フルパワー・スキャン） ---
    # あえてタグ除去を行わず、生データからパターンを抽出
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # 時刻検索
    time_pattern = r'(\d{1,2})\s*[:：]\s*(\d{2})'
    time_matches = list(re.finditer(time_pattern, raw_content))
    print(f"1. 時刻候補: {len(time_matches)}件 ヒット")

    for m in time_matches:
        try:
            h_str, m_str = m.groups()
            f_h, f_m = int(h_str), int(m_str)
            f_t = now.replace(hour=f_h % 24, minute=f_m, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            
            # 時間ウィンドウ判定 (-30分 〜 +45分)
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            # 探索範囲を大幅拡大（800文字）
            chunk = raw_content[max(0, m.start()-400) : m.end()+400]
            chunk_upper = chunk.upper()
            
            # --- 便名の抽出（JSON/HTML両対応・超強力版） ---
            carrier = "不明"
            fnum = ""
            # あらゆるキャリアコードを巡回
            for c_code in ["JAL", "JL", "ANA", "NH", "BC", "SKY", "ADO", "SNA", "SFJ", "7G", "6J"]:
                if c_code in chunk_upper:
                    # コードの直後の数字を捕まえる
                    fnum_m = re.search(c_code + r'[\"\s>:]*(\d{1,4})', chunk_upper)
                    carrier = c_code
                    fnum = fnum_m.group(1) if fnum_m else ""
                    break

            # --- 出身地の抽出（正規表現の多重化） ---
            origin = "不明"
            # パターン1: >札幌<
            org_m = re.search(r'>\s*([ぁ-んァ-ヶー一-龠]{2,10})\s*<', chunk)
            # パターン2: "札幌"
            if not org_m: org_m = re.search(r'[\":]([ぁ-んァ-ヶー一-龠]{2,10})[\"]', chunk)
            
            if org_m:
                origin = org_m.group(1).strip()

            # --- 人数・乗り場判定 ---
            cap = CONFIG["CAPACITY"]["SMALL"]
            if any(x in chunk_upper for x in ["777", "787", "350", "767", "A330", "B7"]): cap = CONFIG["CAPACITY"]["BIG"]
            
            # 国際線キャリア判定
            if carrier not in ["JAL", "JL", "ANA", "NH", "BC", "SKY", "7G", "6J", "ADO", "SNA", "SFJ", "不明"]:
                cap = CONFIG["CAPACITY"]["INTL"]

            pax = int(cap * CONFIG["LOAD_FACTORS"]["NORMAL"])
            
            s_key = "P5"
            if carrier in ["JAL", "JL"]:
                if any(c in origin for c in CONFIG["SOUTH_CITIES"]): s_key = "P1"
                elif any(c in origin for c in CONFIG["NORTH_CITIES"]): s_key = "P2"
                else: s_key = "P1"
            elif carrier in ["NH", "ANA"]: s_key = "P3"
            elif carrier in ["BC", "SKY"]: s_key = "P1"
            elif any(c in carrier for c in ["ADO", "SNA", "SFJ", "7G", "6J"]): s_key = "P4"
            
            flight_rows.append({
                "time": f"{f_h:02d}:{f_m:02d}", "flight": f"{carrier}{fnum}", 
                "origin": origin[:6], "pax": pax, "s_key": s_key
            })

        except: continue

    # 重複削除（精度重視）
    unique_rows = []
    seen = set()
    for r in flight_rows:
        id_str = f"{r['time']}-{r['flight']}-{r['origin']}"
        if id_str not in seen:
            seen.add(id_str); unique_rows.append(r)

    # 集計
    for r in unique_rows: stands[r['s_key']] += r['pax']
    
    result = {
        "stands": stands, "pool_preds": {k: max(0, 100 - int(v/10)) for k, v in stands.items()},
        "total_pax": sum(stands.values()), "rows": unique_rows, "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"2. 解析完了。有効便数: {len(unique_rows)} / 総需要: {result['total_pax']}人")
    return result
