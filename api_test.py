import requests

# サニーさんのAPIキー
API_KEY = "dd32199bfacf0d3d6f8d538b4511d29b"

def check_airport(iata_code, airport_name):
    """
    指定した空港の到着便データを取得して表示する関数
    """
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': API_KEY,
        'arr_iata': iata_code,
        'limit': 5
    }
    
    print(f"\n--- {airport_name}({iata_code}) の状況を確認中 ---")
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        flights = data.get('data', [])
        print(f"結果: {len(flights)}件のデータを取得しました。")
        
        if len(flights) > 0:
            for i, f in enumerate(flights, 1):
                flight_num = f.get('flight', {}).get('iata', '不明')
                dep_airport = f.get('departure', {}).get('airport', '不明')
                s_arr = f.get('arrival', {}).get('scheduled', '不明')
                print(f"  {i}. 便名: {flight_num}, 出発地: {dep_airport}, 到着予定: {s_arr}")
        else:
            print(f"  警告: {airport_name}のデータは「0件」でした。")
            
    except Exception as e:
        print(f"  エラーが発生しました: {e}")

# メイン処理
if __name__ == "__main__":
    print("【API 比較検証プログラム実行】")
    
    # 1. 本命の羽田を確認
    check_airport('HND', '羽田空港')
    
    # 2. 比較用の成田を確認
    check_airport('NRT', '成田空港')

    print("\n-------------------------------------------")
    print("検証が完了しました。")
    print("もし成田が取れて羽田が0件なら、API側の羽田限定の障害です。")
    print("両方とも0件なら、API全体のシステムトラブルかプランの問題です。")
