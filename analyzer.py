import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v6.1: 生存確認・最終スキャン ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt がありません")
        return None

    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_content = f.read()

    print(f"DEBUG: ファイル総量 {len(raw_content)} bytes")
    
    # --- 1. 都市名による「実需データ」の存在確認 ---
    print("--- 🔍 実需データ生存確認 ---")
    all_cities = CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]
    found_cities = []
    for city in all_cities:
        if city in raw_content:
            found_cities.append(city)
    
    if found_cities:
        print(f"✅ 都市名を発見しました！: {found_cities[:5]}... (本物のデータの可能性アリ)")
    else:
        print("🚨 警告: ファイル内に都市名（札幌・福岡など）が1つも見つかりません。")
        print("➡ これは、Fetcherが「中身のない抜け殻」を取得している決定的証拠です。")

    # --- 2. 偽物（コード）と本物の判別 ---
    for target in ["JAL", "ANA", "JL", "NH"]:
        pos = raw_content.upper().find(target)
        if pos != -1:
            chunk = raw_content[max(0, pos-50):pos+150].replace('\n', ' ')
            if "google" in chunk.lower() or "gtm" in chunk.lower():
                print(f"⚠️ 偽物の[{target}]を検出 (解析用コード内): ...{chunk[:100]}...")
            else:
                print(f"✨ 本物候補の[{target}]を検出!: ...{chunk[:100]}...")

    # --- 3. 解析処理（簡易版） ---
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    
    # 暫定的に結果を保存
    result = {
        "stands": stands, "pool_preds": {k: 100 for k in stands},
        "total_pax": 0, "rows": [], "update_time": datetime.datetime.now().strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"2. 解析完了。有効便数: 0")
    if not found_cities:
        print("\n💡 【プロデューサーへの進言】")
        print("もし都市名が0件なら、今のFetcher（URL取得）ではこれ以上進めません。")
        print("『Playwright（自動操作）』を導入して、人間と同じように画面を開く方式に切り替えることを推奨します。")
        
    return result
