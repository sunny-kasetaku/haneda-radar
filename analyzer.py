import os
import json
from datetime import datetime
from config import CONFIG

def get_recommended_stand():
    """
    [T氏セオリー] 推奨乗り場判定ロジック
    """
    now = datetime.now() # JST環境想定
    hour = now.hour
    
    if 6 <= hour < 16:
        return "3号"
    elif 16 <= hour < 18:
        return "4号"
    elif 18 <= hour < 21:
        return "3号"
    elif 21 <= hour < 22:
        return "1号または2号"
    else: # 22:00 - 05:59
        return "3号"

def run_analyze():
    raw_file = CONFIG.get("DATA_FILE", "haneda_raw.html")
    print(f"--- KASETACK Analyzer v22.0: セオリー統合版 ---")
    
    if not os.path.exists(raw_file):
        return {"flights": [], "update_time": "--:--", "count": 0}

    try:
        with open(raw_file, "r", encoding="utf-8") as f:
            results = json.load(f)
    except json.JSONDecodeError:
        print("⚠️ データ形式エラー")
        return None

    # 最新のセオリーに基づき推奨乗り場を決定
    recommended = get_recommended_stand()

    output = {
        "update_time": datetime.now().strftime("%H:%M"),
        "recommended_stand": recommended, # セオリーを追加
        "flights": sorted(results, key=lambda x: x['flight_no'])[:40],
        "count": len(results),
        "total_pax": sum(f['pax'] for f in results)
    }

    with open(CONFIG["RESULT_FILE"], "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    
    print(f"✅ 解析完了: 現在の推奨は 【{recommended}】 です。")
    return output
