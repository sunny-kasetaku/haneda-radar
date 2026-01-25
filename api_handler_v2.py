import requests
import time
import sys

def fetch_flight_data(api_key, date_str=None):
    """
    AviationStackからデータを取得する。
    date_str が指定されていればその日付のデータを、なければ当日のデータを取得。
    """
    base_url = "http://api.aviationstack.com/v1/flights"
    
    # 明示的に「active(飛行中)」と「landed(到着)」を指定して取得
    target_statuses = ['active', 'landed']
    
    all_flights = []
    
    for status in target_statuses:
        params = {
            'access_key': api_key,
            'arr_iata': 'HND',
            'limit': 100,
            'flight_status': status
        }
        
        # 【追加】日付指定がある場合はパラメータに追加 (例: '2026-01-24')
        # これがないと、深夜に「昨日の出発便」が取れません
        if date_str:
            params['flight_date'] = date_str
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()
            raw_data = data.get('data', [])
            
            # 生データをそのまま返さず、必ず整形関数を通す
            for f in raw_data:
                info = extract_flight_info(f)
                if info:
                    all_flights.append(info)
            
            # APIへの負荷軽減
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error fetching {status} flights: {e}", file=sys.stderr)
            pass

    return all_flights

def extract_flight_info(flight):
    """
    APIの生データから必要な情報を抽出し、ターミナル判定を行う関数
    （変更なし・維持）
    """
    arr = flight.get('arrival', {})
    airline = flight.get('airline', {})
    flight_data = flight.get('flight', {})
    dep = flight.get('departure', {})
    
    arrival_time = arr.get('estimated') or arr.get('actual') or arr.get('scheduled')
    if not arrival_time: return None

    # ターミナル判定ロジック
    term = arr.get('terminal')
    f_num_str = str(flight_data.get('number', ''))
    
    # ターミナル情報がない場合の推測ロジック（重要）
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
