import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v6.0: 埋蔵金発掘版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_content = f.read()

    # --- 1. スタイルタグを事前に除去（ノイズ削減） ---
    clean_content = re.sub(r'<style.*?>.*?</style>', ' ', raw_content, flags=re.DOTALL)
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    
    # --- 2. 埋蔵金捜索：キャリアや機材の「目印」を直接探す ---
    # 単なる ANA ではなく、amazon などを避けるために境界を意識
    targets = ["JAL", "ANA", "SKY", "777", "787", "A350"]
    
    found_count = 0
    print("--- 🔍 埋蔵金発掘ログ ---")

    for target in targets:
        # ファイル全体から目印を探す
        for m in re.finditer(target, clean_content.upper()):
            pos = m.start()
            # 目印の前後300文字を切り出す
            chunk = clean_content[max(0, pos-150) : pos+450]
            
            # --- ここで「時刻」らしいものを探す ---
            time_m = re.search(r'(\d{1,2})[:：](\d{2})', chunk)
            if time_m:
                f_h, f_m = int(time_m.group(1)), int(time_m.group(2))
                if 0 <= f_h <= 23 and 0 <= f_m <= 59:
                    
                    # 出身地
                    origin = "不明"
                    for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
                        if city in chunk:
                            origin = city; break
                    
                    # 便名（目印の周辺の数字）
                    fnum_m = re.search(r'\d{3,4}', chunk)
                    fnum = fnum_m.group(0) if fnum_m else ""
                    
                    print(f"✨ 発掘成功! [{f_h:02d}:{f_m:02d}] {target}{fnum} 出身:{origin}")
                    
                    # 時間ウィンドウ判定（最終的な集計用）
                    f_t = now.replace(hour=f_h, minute=f_m, second=0, microsecond=0)
                    diff = (f_t - now).total_seconds() / 60
                    
                    if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
                        s_key = "P5"
                        if target in ["JAL"]:
                            s_key = "P2" if origin in CONFIG["NORTH_CITIES"] else "P1"
                        elif target in ["ANA"]: s_key = "P3"
                        elif target in ["SKY"]: s_key = "P1"
                        
                        flight_rows.append({
                            "time": f"{f_h:02d}:{f_m:02d}", "flight": f"{target}{fnum}", 
                            "origin": origin[:6], "pax": 150, "s_key": s_key
                        })
                        found_count += 1

            if found_count > 20: break # 出しすぎ防止

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
    
    # 全く見つからない場合の最終デバッグ
    if not unique_rows:
        print("🚨 まだ何も見つかりません。JALの文字がある場所の周辺100文字を強制表示します:")
        jal_pos = clean_content.upper().find("JAL")
        if jal_pos != -1:
            print(f"CONTEXT: {clean_content[jal_pos:jal_pos+200]}")

    print(f"2. 解析完了。有効便数: {len(unique_rows)}")
    return result
