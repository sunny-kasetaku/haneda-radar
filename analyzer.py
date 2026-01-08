# ==========================================
# Project: KASETACK - analyzer.py (Audit Table RESTORED)
# ==========================================
import os
import json
from datetime import datetime, timezone, timedelta
from config import CONFIG

def get_recommended_stand():
    """T氏セオリー判定 (JST同期)"""
    jst = timezone(timedelta(hours=9))
    hour = datetime.now(jst).hour
    if 6 <= hour < 16: return "3号"
    elif 16 <= hour < 18: return "4号"
    elif 18 <= hour < 21: return "3号"
    elif 21 <= hour < 22: return "1号または2号"
    else: return "3号"

def run_analyze():
    raw_file = CONFIG.get("DATA_FILE")
    if not os.path.exists(raw_file):
        print("❌ 解析対象データが見つかりません")
        return None

    with open(raw_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    jst = timezone(timedelta(hours=9))
    # 監査レポート用の詳細時刻
    audit_time = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    update_time_short = datetime.now(jst).strftime("%H:%M")
    recommended = get_recommended_stand()
    total_pax = sum(f['pax'] for f in results)

    # ==========================================
    # 🕵️ 監査用ターミナル出力（引かずに足す：復旧箇所）
    # ==========================================
    print(f"\n{'='*85}")
    print(f"【KASETACK 監査レポート】 実行時刻(JST): {audit_time}")
    print(f"{'='*85}")
    
    # ヘッダー
    header = f"{'便名':<8} | {'出身':<5} | {'到着予定(JST)':<20} | {'遅延':<5} | {'ステータス':<10} | {'期待値'}"
    print(header)
    print(f"{'-'*85}")

    for f in results:
        # 時刻文字列の整形 (T15:30:00+00:00 -> 15:30)
        time_str = f.get('time', '---')
        if "T" in time_str:
            time_str = time_str.split("T")[1][:5]
        
        row = f"{f.get('flight_no', 'N/A'):<8} | {f.get('origin', 'UNK'):<5} | {time_str:<20} | {f.get('delay', 0):>3}分 | {f.get('status', 'unknown'):<10} | {f.get('pax', 0):>3}名"
        print(row)

    print(f"{'-'*85}")
    print(f"📊 総期待値: {total_pax}名")
    print(f"🎯 推奨乗り場: {recommended}")
    print(f"{'='*85}\n")

    output = {
        "update_time": update_time_short,
        "recommended_stand": recommended,
        "flights": sorted(results, key=lambda x: x['flight_no']),
        "total_pax": total_pax
    }

    with open(CONFIG["RESULT_FILE"], "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    
    return output
