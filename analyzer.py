# ==========================================
# Project: KASETACK - analyzer.py
# ==========================================
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
    raw_file = CONFIG.get("DATA_FILE")
    if not os.path.exists(raw_file):
        print("❌ 解析対象ファイルが存在しません")
        return None

    with open(raw_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    recommended = get_recommended_stand()
    total_pax = sum(f['pax'] for f in results)

    print(f"🔍 解析完了: 推奨乗り場={recommended} / 合計期待値={total_pax}名")

    output = {
        "update_time": datetime.now().strftime("%H:%M"),
        "recommended_stand": recommended,
        "flights": sorted(results, key=lambda x: x['flight_no']),
        "total_pax": total_pax
    }

    with open(CONFIG["RESULT_FILE"], "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    
    return output
