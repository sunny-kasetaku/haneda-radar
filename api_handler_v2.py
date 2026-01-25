import requests
import time
import sys

def fetch_flight_data(api_key, date_str=None):
    """
    AviationStackからデータを取得する（ページネーション復元版）。
    勝手に削除していた「複数ページ取得（ループ処理）」を復活させました。
    100件制限を超えて、その日のデータを奥底まで取りに行きます。
    """
    base_url = "http://api.aviationstack.com/v1/flights"
    
    all_flights = []
    offset = 0
    limit = 100  # APIの1回あたりの最大取得数
    
    # プロデューサーの指示通り、データを取り切るまで回します
    # (通常3〜5回程度で全便取得完了します)
    while True:
        params = {
            'access_key': api_key,
            'arr_iata': 'HND',
            'limit': limit,
            'offset': offset
        }
        
        # main_v8からの日付指定を反映
        if date_str:
            params['flight_date'] = date_str
        
        try:
            # 進行状況をログに出します
            print(f"DEBUG: Fetching offset {offset}...", file=sys.stderr)
            
            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()
            
            raw_data = data.get('data', [])
            
            # データが空っぽ（最後のページまで行った）なら終了
            if not raw_data:
                break
            
            # 取得したデータをリストに追加
            for f in raw_data:
                info = extract_flight_info(f)
                if info:
                    all_flights.append(info)
            
            # 次のページ（100件後）へ
            offset += limit
            
            # 安全装置: 無限ループ防止（最大1000件=10回あれば十分カバー可能）
            if offset >= 1000:
                break
                
            # APIへの連続アクセス負荷を避けるため一瞬待つ
            time.sleep(0.1)

        except Exception as e:
            print(f"Error fetching flights: {e}", file=sys.stderr)
            # エラーが出ても、そこまで取れた分は返す
            break
            
    return all_flights

def extract_flight_info(flight):
    arr = flight.get('arrival', {})
    airline = flight.get('airline', {})
    flight_data = flight.get('flight', {})
    dep = flight.get('departure', {})
    
    # 到着時刻の特定
    arrival_time = arr.get('estimated') or arr.get('actual') or arr.get('scheduled')
    if not arrival_time: return None

    # ターミナル判定
    term = arr.get('terminal')
    f_num_str = str(flight_data.get('number', ''))
    
    if term is None:
        if len(f_num_str) >= 4:
            term = "1"
        else:
            term = "3"

    return {
        "flight_number": f"{airline.get('iata', '??')}{f_num_str}",
        "airline": airline.get('name', 'Unknown'),
        "origin": dep.get('airport', 'Unknown'),
        "origin_iata": dep.get('iata', 'UNK'),
        "terminal": str(term),
        "arrival_time": arrival_time,
        "status": flight.get('flight_status', 'unknown')
    }
