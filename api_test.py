import requests
from datetime import datetime, timedelta

# サニーさんのAPIキー
API_KEY = "dd32199bfacf0d3d6f8d538b4511d29b"

def check_airport(iata_code, airport_name, target_date=None):
    """
    指定した空港の到着便データを取得して表示する関数
    target_dateがNoneの場合は日付指定なし（最新順）で取得
    """
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': API_KEY,
        'arr_iata': iata_code,
        'limit': 5
    }
    
    # 日付指定がある場合はパラメータに追加
    if target_date:
        params['flight_date'] = target_date
        display_name = f"{airport_name}({iata_code}) [{target_date}指定]"
    else:
        display_name = f"{airport_name}({iata_code}) [日付指定なし]"

    print(f"\n--- {display_name} の状況を確認中 ---")
    
    try:
        # タイムアウトを少し長めに設定
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        flights = data.get('data', [])
        total = data.get('pagination', {}).get('total', 0)
        print(f"結果: 総件数 {total}件中、上位 {len(flights)}件を表示します。")
        
        if len(flights) > 0:
            for i, f in enumerate(flights, 1):
                flight_num = f.get('flight', {}).get('iata', '不明')
                dep_airport = f.get('departure', {}).get('airport', '不明')
                s_arr = f.get('arrival', {}).get('scheduled', '不明')
                # 取得できたデータの実際の日付を確認しやすく表示
                print(f"  {i}. 便名: {flight_num}, 出発地: {dep_airport}, 到着予定: {s_arr}")
        else:
            print(f"  警告: データは「0件」でした。")
            
    except Exception as e:
        print(f"  エラーが発生しました: {e}")

# メイン処理
if __name__ == "__main__":
    print("【API 詳細検証プログラム実行】")
    
    # 今日の日付と昨日の日付を取得（JSTベース）
    # UTCとの兼ね合いを考え、文字列で指定
    today_str = "2026-05-02"
    yesterday_str = "2026-05-01"
    
    # 1. 羽田の「今日」を確認（おそらくこれが0件になる原因）
    check_airport('HND', '羽田空港', target_date=today_str)
    
    # 2. 羽田の「昨日（5/1）」を確認（これが前回のログで出ていたもの）
    check_airport('HND', '羽田空港', target_date=yesterday_str)
    
    # 3. 比較用の成田も「今日」で確認
    check_airport('NRT', '成田空港', target_date=today_str)

    print("\n-------------------------------------------")
    print("検証が完了しました。")
    print(f"もし '{today_str}' 指定で0件になり、'{yesterday_str}' 指定でデータが出るなら、")
    print("API側が『今日のデータ』をまだ配信できていないことが確定します。")
