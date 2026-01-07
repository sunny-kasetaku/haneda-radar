import re
import datetime
import json
import os
import unicodedata
from config import CONFIG

def run_analyze():
    print("--- KASETACK Analyzer v16.0: 国内線・徹底監査版 ---")
    if not os.path.exists(CONFIG["DATA_FILE"]):
        print("❌ エラー: raw_flight.txt が存在しません")
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8", errors='ignore') as f:
        raw_html = f.read()

    # 1. 前処理：正規化とHTMLタグの除去
    content = unicodedata.normalize('NFKC', raw_html)
    # スクリプトとスタイルシートの中身を物理的に消去
    clean_html = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', content, flags=re.DOTALL | re.IGNORECASE)
    # タグをスペースに変換
    text = re.sub(r'<[^>]+>', ' ', clean_html)
    # 連続する空白を1つに
    text = re.sub(r'\s+', ' ', text)

    # 🔍 【証拠開示】テキストの冒頭1200文字を直接表示。ここで「便名」や「時刻」が見えるか確認
    print(f"\n--- 📋 生データ断片（目視確認用） ---")
    print(text[300:1500])
    print(f"-----------------------------------\n")

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    active_rows = []
    found_all_list = [] # 窓に関係なく見つかった全フライト用

    # 2. 航空会社判定キーワード
    carrier_map = {
        "JAL": ["JAL", "JL", "日本航空"],
        "ANA": ["ANA", "NH", "全日空"],
        "SKY": ["SKY", "BC", "スカイマーク"],
        "ADO": ["ADO", "AIR DO"],
        "SNA": ["SNA", "ソラシド"],
        "SFJ": ["SFJ", "スターフライヤー"]
    }

    # 3. 解析：全ての時刻「HH:MM」を起点に周囲をスキャン
    time_matches = list(re.finditer(r'(\d{1,2}:\d{2})', text))
    print(f"1. ページ内に {len(time_matches)} 個の時刻表記を確認。精査を開始...")

    for m in time_matches:
        time_str = m.group(1)
        # 時刻の後方250文字をデータ塊として切り出し
        chunk = text[m.start() : m.start() + 250].upper()
        
        # 航空会社の特定
        found_c = None
        for code, keywords in carrier_map.items():
            if any(kw in chunk for kw in keywords):
                found_c = code; break
        
        if not found_c: continue # 航空会社が見つからない時刻はノイズ
        
        # 都市名の特定
        origin = "不明"
        for city in (CONFIG["SOUTH_CITIES"] + CONFIG["NORTH_CITIES"]):
            if city in chunk:
                origin = city; break

        # 【重要】監査用に全ての発見便をリストに蓄積
        found_all_list.append(f"[{time_str} {found_c} ({origin})]")

        # 4. 通常の需要窓判定 (T-30 〜 T+45)
        h, m_val = map(int, time_str.split(':'))
        f_t = now.replace(hour=h, minute=m_val, second=0, microsecond=0)
        diff = (f_t - now).total_seconds() / 60
        if diff < -720: f_t += datetime.timedelta(days=1); diff += 1440
        elif diff > 720: f_t -= datetime.timedelta(days=1); diff -= 1440

        if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
            active_rows.append({"time": time_str, "flight": found_c, "origin": origin, "pax": 150, "s_key": "P1"})

    # --- 📜 徹底監査レポート出力 ---
    print(f"--- 📊 監査報告結果 ---")
    if found_all_list:
        print(f"✅ 成功: ページ内から計 {len(found_all_list)} 件のフライト記述を発掘しました。")
        print(f"抽出サンプル: {', '.join(found_all_list[:10])} ...")
    else:
        print(f"❌ 失敗: 時刻はありましたが、有効なフライト記述（JAL/ANA等）が周囲にありませんでした。")
    print(f"🎯 需要窓内の有効便: {len(active_rows)} 便")
    print(f"----------------------")

    result = {
        "stands": stands, "total_pax": len(active_rows)*150, "rows": active_rows, 
        "total_flights_on_page": len(found_all_list), "update_time": now.strftime("%H:%M")
    }
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result
