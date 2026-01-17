from api_handler_v2 import fetch_flights_v2
from analyzer import analyze_demand # これは既存のものを流用（安全）
from renderer_new import generate_html_new

def main():
    print("--------------------------------------------------")
    print("📡 [TEST] 羽田需要レーダー v2 プロトタイプ起動")
    print("--------------------------------------------------")
    
    # 💡 3ページ（300件）取得を試みる
    flights = fetch_flights_v2(pages=3)
    
    if flights:
        print(f"📊 {len(flights)}件のフライト情報を解析中...")
        
        # 既存のロジックで需要計算
        results = analyze_demand(flights)
        
        # 新しいデザインでHTML出力
        generate_html_new(results, flights)
        
        print("\n✨ テスト完了！")
        print("同フォルダ内の 'index_test.html' をブラウザで開いてください。")
    else:
        print("❌ データの取得に失敗しました。")
    
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()