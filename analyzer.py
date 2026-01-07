import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v4.5: 全方位レーダー・救済版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    # ファイル読み込み（エラー回避のため errors='ignore' を追加）
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_content = f.read()

    # --- 1. 洗浄前の「生」の状態でキーワードを徹底捜索 ---
    raw_upper = raw_content.upper()
    print("--- 🔍 内部構造デバッグ ---")
    found_any = False
    for key in ["JAL", "JL", "ANA", "NH", "777", "787"]:
        pos = raw_upper.find(key)
        if pos != -1:
            # 見つけた場所の前後を表示（バックスラッシュ回避済み）
            snippet = raw_content[max(0, pos-100):pos+200].replace('\n', ' ').replace('\r', ' ')
            print(f"✅ 発見 [{key}]: ... {snippet} ...")
            found_any = True
            break
    if not found_any:
        print("⚠️ 警告: Analyzerにはキーワードが見えません（Fetcherとの乖離）")

    # --- 2. 洗浄（最小限） ---
    clean_content = re.sub(r'<style.*?>.*?</style>', '', raw_content, flags=re.DOTALL)
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # --- 3. 時刻検索（最も成功率の高いシンプルパターン） ---
    # 数字2桁 : 数字2桁 をとにかく探す
    time_matches = list(re.finditer(r'(\d{1,2})\s*[:：]\s*(\d{2})', clean_content))
    print(f"1. 調査地点: {len(time_matches)}件 ヒット")

    if len(time_matches) == 0:
        print("🚨 時刻パターンが全滅。データの時間表記が '1905' や '19時' の可能性があります。")
        print("データ冒頭300文字:", clean_content[:300])

    for m in time_matches:
        try:
            h_str, m_str = m.groups()
            f_h, f_m = int(h_str), int(m_str)
            
            # AM/PM判定
            ampm_chunk = clean_content[m.end() : m.end() + 30].upper()
            if "PM" in ampm_chunk and f_h < 12: f_h += 12
            elif "AM" in ampm_chunk and f_h == 12: f_h = 0
            
            f_t = now.replace(hour=f_h % 24, minute=f_m, second=0, microsecond=0)
            diff = (f_t - now).total_seconds() / 60
            
            # 統計的なウィンドウ判定
            if not (CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]):
                continue

            # 探索範囲を拡大（出身地や便名が離れているケースに対応）
            chunk = clean_content[max(0, m.start()-400) : m.end()+600]
            chunk_upper = chunk.upper()
            
            # 便名検索（JSON形式 "flightNumber":"JL501" 等も考慮）
            carrier = "不明"
            fnum = "000"
            flight_m = re.search(r'([A-Z]{2,3})\s*(?:<[^>]+>|[\"\s])*(\d{1,4})', chunk_upper)
            if flight_m:
                carrier, fnum = flight_m.groups()

                # 出身地の抽出
                origin = "不明"
                # 日本語（漢字・ひらがな）の塊を探す
                origin_m = re.search(r'>\s*([ぁ-んァ-ヶー一-龠]{2,10})\s*<', chunk)
                if not origin_m:
                    origin_m = re.search(r'[\":]([ぁ-んァ-ヶー一-龠]{2,10})[\"]', chunk)
                
                if origin_m:
                    origin = origin_m.group(1).strip()

                # キャパ判定
                cap = CONFIG["CAPACITY"]["SMALL"]
                if any(x in chunk_upper for x in ["777", "787", "350", "767", "A330", "B7"]):
                    cap = CONFIG["CAPACITY"]["BIG"]
                if carrier not in ["JL", "NH", "BC", "7G", "6J", "ADO", "SNA", "SFJ"]:
                    cap = CONFIG["CAPACITY"]["INTL"]

                pax = int(cap * CONFIG["LOAD_FACTORS"]["NORMAL"]) 
                
                # 乗り場判定
                s_key = "P5"
                if "JL" in carrier:
                    if any(c in origin for c in CONFIG["SOUTH_CITIES"]): s_key = "P1"
                    elif any(c in origin for c in CONFIG["NORTH_CITIES"]): s_key = "P2"
                    else: s_key = "P1"
                elif "BC" in carrier: s_key = "P1"
                elif "NH" in carrier: s_key = "P3"
                elif any(c in carrier for c in ["ADO", "SNA", "SFJ", "7G"]): s_key = "P4"
                
                flight_rows.append({
                    "time": f"{f_h:02d}:{f_m:02d}", "flight": f"{carrier}{fnum}", 
                    "origin": origin[:6], "pax": pax, "s_key": s_key
                })

        except Exception: continue

    # 重複削除
    seen = set()
    unique_rows = []
    for r in flight_rows:
        id_str = f"{r['time']}-{r['flight']}-{r['origin']}" 
        if id_str not in seen:
            seen.add(id_str)
            unique_rows.append(r)

    # 集計
    for k in stands: stands[k] = 0
    for r in unique_rows: stands[r['s_key']] += r['pax']

    # プール予測
    pool_preds = {}
    for k, p_pax in stands.items():
        base = {"P1":100, "P2":100, "P3":120, "P4":80, "P5":150}.get(k, 100)
        pool_preds[k] = max(0, base - int(p_pax / 10))

    result = {
        "stands": stands, "pool_preds": pool_preds, "total_pax": sum(stands.values()), 
        "rows": unique_rows, "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"2. 解析完了。有効便数: {len(unique_rows)} / 総需要: {result['total_pax']}人")
    return result
