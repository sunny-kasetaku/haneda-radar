import re, datetime, json, os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v8.2: 全方位マイニング版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]): return None
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8") as f:
        content = f.read()

    # 広告やスクリプトを徹底排除
    content = re.sub(r'<(style|script|iframe)[^>]*>.*?</\1>', ' ', content, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'\s+', ' ', text).upper()

    flight_rows = []
    # 便名を探す (JL123, NH 456, ANA789 等)
    patterns = [r'(JL|NH|JAL|ANA|SKY|BC|ADO|SNA|SFJ)\s*(\d{1,4})']
    
    print("1. 広域マイニング開始...")
    for pat in patterns:
        for m in re.finditer(pat, text):
            chunk = text[max(0, m.start()-200) : m.end()+200]
            # 時刻を探す
            time_m = re.search(r'(\d{1,2})[:：](\d{2})', chunk)
            if time_m:
                flight_rows.append({
                    "time": f"{time_m.group(1)}:{time_m.group(2)}",
                    "flight": f"{m.group(1)}{m.group(2)}",
                    "origin": "羽田着", "pax": 150, "s_key": "P1"
                })

    # 結果を保存
    result = {"stands": {"P1": len(flight_rows)*150}, "total_pax": len(flight_rows)*150, "rows": flight_rows, "update_time": "更新中"}
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"2. 完了。有効便数: {len(flight_rows)}")
    return result
