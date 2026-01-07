import os

def run_analyze(): # 👈 ここを run_analyze に直しました
    print("--- 🔍 生データの中身を調査中 ---")
    if not os.path.exists("haneda_raw.html"):
        print("❌ ファイルが見つかりません。")
        return
    
    with open("haneda_raw.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # データのサイズを表示
    print(f"データサイズ: {len(content)} bytes")
    print("-" * 30)
    
    # Flightradar24 のデータ構造を探るためのキーワード
    keywords = ["flight", "arrival", "HND", "JAL", "ANA", "scheduled"]
    
    print("【フライト情報周辺の抜粋】")
    for keyword in keywords:
        # 大文字小文字を区別せず検索
        pos = content.lower().find(keyword.lower())
        if pos != -1:
            print(f"Keyword '{keyword}' found at {pos}:")
            # その周辺150文字を表示
            print(content[pos:pos+150].replace('\n', ' ')) 
            print("-" * 20)

if __name__ == "__main__":
    run_analyze()
