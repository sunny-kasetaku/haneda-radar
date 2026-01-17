import os
import json
import requests
from datetime import datetime

# ★ここでさっき完成した2つのファイルを読み込みます
import analyzer_v2 as analyzer
import renderer_new as renderer

# ==========================================
# 設定エリア (22日にここを書き換えるだけでOK)
# ==========================================
API_KEY = "YOUR_FREE_API_KEY" # まだ無料版
BASE_URL = "http://api.aviationstack.com/v1/flights" # 例

def get_flight_data():
    """
    フライトデータを取得する関数
    現在はテスト用ロジック（または無料API）
    """
    # ---------------------------------------------------
    # 【A】テスト用：ダミーデータを返す（今の状態）
    # ※本番ではここをコメントアウトし、【B】を有効化する
    # ---------------------------------------------------
    print("LOG: テストデータを生成中...")
    
    # テストデータ（わざと時間をずらしてロジック確認用にするもよし）
    # ここではAnalyzerが「時間外」として弾くか確認するため、あえて固定データを入れています
    mock_data = [
        {"arrival_time": "2023-10-27T16:55:00+09:00", "airline": "JAL", "flight_iata": "JL496", "origin": "KCZ", "terminal": "1"},
        {"arrival_time": "2023-10-27T16:51:00+09:00", "airline": "Air China", "flight_iata": "CA6705", "origin": "SHA", "terminal": "3"},
        # 必要ならここに「現在の時間」に合わせたデータを手動で入れてテストも可能
    ]
    return mock_data

    # ---------------------------------------------------
    # 【B】本番用：有料APIから取得（22日以降）
    # ---------------------------------------------------
    # params = {
    #    'access_key': API_KEY,
    #    'arr_iata': 'HND',
    #    'limit': 100
    # }
    # response = requests.get(BASE_URL, params=params)
    # api_result = response.json()
    # return api_result.get('data', [])

def main():
    print(f"START: {datetime.now()}")

    # 1. データ取得（Get）
    flights = get_flight_data()
    print(f"LOG: 取得データ数 = {len(flights)}件")

    # 2. 分析（Analyze）
    # analyzer_v2.py の analyze_demand 関数を使う
    results = analyzer.analyze_demand(flights)
    print(f"LOG: 有効需要数(フィルタ後) = {results.get('unique_count')}機")

    # 3. 描画（Render）
    # renderer_new.py の generate_html_new 関数を使う
    # ※ファイル名は index.html で保存される
    renderer.generate_html_new(results, "dummy_prev_data")
    
    print("SUCCESS: index_test.html (またはindex.html) を更新しました")

if __name__ == "__main__":
    main()