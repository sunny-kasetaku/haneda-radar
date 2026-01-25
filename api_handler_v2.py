import requests
import time
import sys

def fetch_flight_data(api_key, date_str=None):
    """
    AviationStackからデータを取得する（超・省エネ版）。
    ステータスを指定せず、1回の通信で「active」「landed」「scheduled」すべてを一括取得する。
    """
    base_url = "http://api.aviationstack.com/v1/flights"
    
    # パラメータ設定
    # flight_statusを指定しない = APIの仕様ですべてのステータスが返ってくる
    # これにより 1回の通信で「到着済み」も「予定」も「飛行中」も全部取れます。
    params = {
        'access_key': api_key,
        'arr_iata': 'HND',  # 羽田到着
        'limit': 100        # 直近100件
    }
    
    if date_str:
        params['flight_date'] = date_str
    
    try:
        # ここでリクエスト（通信は1回だけ！）
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()
        raw_data = data.get('data', [])
        
        all_flights = []
        for f in raw_data:
            info = extract_flight_info(f)
            if info:
                all_flights.append(info)
        
        return all_flights

    except Exception as e:
        print(f"Error fetching flights: {e}", file=sys.stderr)
        return []

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
