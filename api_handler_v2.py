import requests
import time

def fetch_flight_data(api_key):
    base_url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': api_key,
        'arr_iata': 'HND',
        'limit': 100,
        'offset': 0
    }
    
    all_flights = []
    for i in range(3): # 300件取得
        params['offset'] = i * 100
        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            raw_data = data.get('data', [])
            if not raw_data: break
            
            for f in raw_data:
                info = extract_flight_info(f)
                if info: all_flights.append(info)
            if len(raw_data) < 100: break
        except: break
        time.sleep(0.1)
    return all_flights

def extract_flight_info(flight):
    arr = flight.get('arrival', {})
    airline = flight.get('airline', {})
    flight_data = flight.get('flight', {})
    dep = flight.get('departure', {})
    
    arrival_time = arr.get('estimated') or arr.get('actual') or arr.get('scheduled')
    if not arrival_time: return None

    # --- ターミナル判定ロジックの改善 ---
    term = arr.get('terminal')
    f_num_str = str(flight_data.get('number', ''))
    
    # ターミナルが不明な場合、便名の桁数で推測（国内線は通常4桁、国際線は3桁以下が多い）
    if term is None:
        if len(f_num_str) >= 4:
            term = "1" # 仮で1（Analyzerで1, 2に振り分けられる）
        else:
            term = "3" # 国際線

    return {
        "flight_number": f"{airline.get('iata', '??')}{f_num_str}",
        "airline": airline.get('name', 'Unknown'),
        "origin": dep.get('airport', 'Unknown'),
        "origin_iata": dep.get('iata', 'UNK'),
        "terminal": str(term),
        "arrival_time": arrival_time,
        "status": flight.get('flight_status', 'unknown')
    }
