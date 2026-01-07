import os

def run_analysis():
    print("--- 🔍 生データの中身を調査中 ---")
    if not os.path.exists("haneda_raw.html"):
        print("❌ ファイルが見つかりません。")
        return
    
    with open("haneda_raw.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # データの冒頭2000文字と、特定のキーワード周辺を表示します
    print(f"データサイズ: {len(content)} bytes")
    print("-" * 30)
    print("【冒頭部分】")
    print(content[:1000]) # 最初の1000文字
    print("-" * 30)
    print("【フライト情報周辺】")
    # "HND" や "JAL" "ANA" が出てくる場所を探してその周辺を表示
    for keyword in ["HND", "JAL", "ANA", "Arrival"]:
        pos = content.find(keyword)
        if pos != -1:
            print(f"Keyword '{keyword}' found at {pos}:")
            print(content[pos:pos+200]) # キーワード前後を表示
            print("-" * 20)

if __name__ == "__main__":
    run_analysis()
