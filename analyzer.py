import os
import json
from datetime import datetime
from config import CONFIG

def get_recommended_stand():
    """[T氏セオリー] 推奨乗り場判定ロジック"""
    now = datetime.now()
    hour = now.hour
    if 6 <= hour < 16: return "3号"
    elif 16 <= hour < 18: return "4号"
    elif 18 <= hour < 21: return "3号"
    elif 21 <= hour < 22: return "1号または2号"
    else: return "3号"

def run_analyze():
    raw_file = CONFIG.get("DATA_FILE", "haneda_raw.json")
    print(f"--- KASETACK Analyzer v23.0: ログ出力強化版 ---")
    
    if not os.path.exists(raw_file):
        return None

    with open(raw_file, "r", encoding="utf-8") as f:
        # --- [残存（コメントアウト）: Regex解析] ---
        # html = f.read()
        # matches = re.findall(pattern, html)
        # ----------------------------------------
        results = json.load(f)

    recommended = get_recommended_stand()
    total_pax = sum(f['pax'] for f in results)

    # 【検証用ログ出力】
    print("\n" + "="*40)
    print(f"🔍 [ロジック検証ログ]")
    for f in results[:5]: # 最初の5件をサンプル表示
        print(f"✈️  便名: {f['flight_no']} | 機種: {f['aircraft']} -> 推計期待値: {f['pax']}名")
    print(f"📊 合計期待値(total_pax): {total_pax}名")
    print(f"🎯 推奨乗り場(T氏セオリー): {recommended}")
    print("="*40 + "\n")

    output = {
        "update_time": datetime.now().strftime("%H:%M"),
        "recommended_stand": recommended,
        "flights": sorted(results, key=lambda x: x['flight_no'])[:40],
        "count": len(results),
        "total_pax": total_pax
    }

    with open(CONFIG["RESULT_FILE"], "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    
    return output
