import os
from config import CONFIG # configから正確なファイル名を読み込みます

def run_analyze():
    # config.py で定義されているファイル名（例: haneda_raw.html）を使用
    raw_file = CONFIG.get("DATA_FILE", "haneda_raw.html")
    
    print(f"--- 🔍 生データの中身を調査中 (対象: {raw_file}) ---")
    
    if not os.path.exists(raw_file):
        # 万が一のために、今そこにあるファイルを表示して原因を探ります
        print(f"❌ {raw_file} が見つかりません。")
        print(f"📂 現在のフォルダにあるファイル: {os.listdir('.')}")
        return
    
    with open(raw_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    print(f"✅ ファイル読み込み完了: {len(content)} bytes")
    print("-" * 30)
    
    # Flightradar24のデータ構造を特定するための重要単語
    keywords = ["flight", "arrival", "HND", "JAL", "ANA", "scheduled", "status"]
    
    print("【フライト情報周辺の抜粋】")
    for keyword in keywords:
        # 大文字小文字を無視して検索
        pos = content.lower().find(keyword.lower())
        if pos != -1:
            print(f"Keyword '{keyword}' found at {pos}:")
            # 前後150文字を抜き出し、改行を整理して表示
            excerpt = content[max(0, pos-30):pos+150].replace('\n', ' ')
            print(f"...{excerpt}...")
            print("-" * 20)

if __name__ == "__main__":
    run_analyze()
