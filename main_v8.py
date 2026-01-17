# main_v8.py
# ---------------------------------------------------------
# 羽田空港タクシー需要予測システム v8.0 Main Controller
# ---------------------------------------------------------
import os
import json
import requests
from datetime import datetime

# 完成した2つのモジュールを読み込む
import analyzer_v2 as analyzer
import renderer_new as renderer

# ==========================================
# 設定エリア (22日にここを書き換える)
# ==========================================
# 有料版APIキーが来たらここに貼り付ける
API_KEY = "YOUR_API_KEY_HERE" 
BASE_URL = "http://api.aviationstack.com/v1/flights"

def get_flight_data():
    """
    フライトデータを取得する関数
    """
    # ---------------------------------------------------
    # 【A】テストモード（現在はこれが動く）
    # 無料版やテスト時は、ここにおかしな時間のデータが入っている想定
    # ---------------------------------------------------
    print("LOG: [Test Mode] ダミーデータを生成します...")
    mock_data = [
        # わざと「16:55」などの過去データを入れて、弾かれるかテスト
        {"arrival_time": "2023-10-27T16:55:00+09:00", "airline": "JAL", "flight_iata": "JL496", "origin": "KCZ", "terminal": "1"},
        {"arrival_time": "2023-10-27T16:51:00+09:00", "airline": "Air China", "flight_iata": "CA6705", "origin": "SHA", "terminal": "3"},
        {"arrival_time": "2023-10-27T17:16:00+09:00", "airline": "JAL", "flight_iata": "JL320", "origin": "FUK", "terminal": "1"},
    ]
    return mock_data

    # ---------------------------------------------------
    # 【B】本番モード（22日以降、ここを有効化する）
    # ---------------------------------------------------
    # try:
    #     print("LOG: [Live Mode] APIからデータを取得します...")
    #     params = {
    #        'access_key': API_KEY,
    #        'arr_iata': 'HND',
    #        'limit': 100
    #     }
    #     # requestsライブラリがない場合は pip install requests が必要
    #     # response = requests.get(BASE_URL, params=params)
    #     # api_result = response.json()
    #     # return api_result.get('data', [])
    # except Exception as e:
    #     print(f"ERROR: API取得エラー {e}")
    #     return []

def main():
    start_time = datetime.now()
    print(f"START: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. データ取得
    flights = get_flight_data()
    print(f"LOG: 取得データ数 = {len(flights)}件")

    # 2. 分析 (Analyzer)
    # ここで「時間外のデータ」は弾かれるはず
    results = analyzer.analyze_demand(flights)
    print(f"LOG: 有効需要数(フィルタ後) = {results.get('unique_count')}機")

    # 3. 描画 (Renderer)
    # index.html を生成する
    renderer.generate_html_new(results, "dummy_prev_data")
    
    print("SUCCESS: index_test.html (本番用ファイル名に変更可) を更新しました")
    print("END")

if __name__ == "__main__":
    main()