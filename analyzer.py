# ==========================================
# Project: KASETACK - analyzer.py (JST Sync Version)
# ==========================================
import os
import json
from datetime import datetime, timezone, timedelta
from config import CONFIG

def get_recommended_stand():
    """
    [T氏セオリー] 推奨乗り場判定ロジック
    日本時間（JST）に基づき正確に判定します
    """
    # UTCから日本時間(JST)へ変換
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    hour = now.hour
    
    # 実行仕様書 v1.1 ロジック
    if 6 <= hour < 16:
        return "3号"
    elif 16 <= hour < 18:
        return "4号"
    elif 18 <= hour < 21:
        return "3号"
    elif 21 <= hour < 22:
        return "1号または2号"
    else: # 22:00以降
        return "3号"

def run_analyze():
    raw_file = CONFIG.get("DATA_FILE")
    print(f"--- KASETACK Analyzer: JST同期版 ---")
    
    if not os.path.exists(raw_file):
        print("❌ 解析対象データが見つかりません")
        return None

    with open(raw_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    # 日本時間での判定と集計
    jst = timezone(timedelta(hours=9))
    update_time = datetime.now(jst).strftime("%H:%M")
    recommended = get_recommended_stand()
    total_pax = sum(f['pax'] for f in results)

    # ログ出力（プロデューサー確認用）
    print(f"🕒 現在時刻(JST): {update_time}")
    print(f"🎯 セオリー判定: {recommended}")
    print(f"📊 総期待値: {total_pax}名")

    output = {
        "update_time": update_time,
        "recommended_stand": recommended,
        "flights": sorted(results, key=lambda x: x['flight_no']),
        "total_pax": total_pax
    }

    with open(CONFIG["RESULT_FILE"], "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    
    return output
