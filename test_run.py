# ==========================================
# Project: KASETACK - test_run_v2.py (Final Commander)
# ==========================================
import os
import webbrowser
from api_handler_v2 import fetch_flights_v2
from analyzer_v2 import analyze_demand
from renderer_new import generate_html_new

def main():
    print("--------------------------------------------------")
    print("📡 [V2 FINAL TEST] 羽田需要レーダー 起動中...")
    print("--------------------------------------------------")
    
    # 1. データ取得（おかわり300件モード）
    # api_handler_v2.py の fetch_flights_v2 を使用
    print("📥 航空データを取得しています（最大300件）...")
    flights = fetch_flights_v2(pages=3)
    
    if not flights:
        print("❌ データの取得に失敗しました。APIキーや通信環境を確認してください。")
        return

    print(f"📊 {len(flights)}件の有効なフライトを検出しました。")

    # 2. 需要分析（復元したv7.7ロジック + 期待値150人）
    # analyzer_v2.py の analyze_demand を使用
    print("🧠 Tさんの統計比率に基づき、期待値を計算中...")
    results = analyze_demand(flights)
    
    # 3. HTML生成（売れるデザイン + v7.7便利機能）
    # renderer_new.py の generate_html_new を使用
    print("🎨 最新デザインのHTMLを生成しています...")
    generate_html_new(results, flights)
    
    # 4. ブラウザ自動オープン
    print("✨ 工程完了。ブラウザを起動します。")
    print("--------------------------------------------------")
    
    # 生成されたファイルの絶対パスを取得して開く
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_file = os.path.join(current_dir, "index_test.html")
    
    if os.path.exists(target_file):
        webbrowser.open(f"file://{target_file}")
        print(f"✅ 成功！ 'index_test.html' を表示しました。")
    else:
        print("⚠️ エラー: HTMLファイルが見つかりません。")

if __name__ == "__main__":
    main()