import requests
import time

def fetch_flight_data(api_key):
    base_url = "http://api.aviationstack.com/v1/flights"
    
    # 明示的に「active(飛行中)」と「landed(到着)」を指定して取得
    # これをしないと「scheduled(明日の予定)」ばかり取れてしまう
    target_statuses = ['active', 'landed']
    
    all_flights = []
    
    for status in target_statuses:
        params = {
            'access_key': api_key,
            'arr_iata': 'HND',
            'limit': 100,
            'flight_status': status
        }
        
        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            raw_data = data.get('data', [])
            
            for f in raw_data:
                info = extract_flight_info(f)
                if info:
                    all_flights.append(info)
            
            # APIへの負荷軽減
            time.sleep(0.1)
            
        except Exception:
            pass

    return all_flights

def extract_flight_info(flight):
    arr = flight.get('arrival', {})
    airline = flight.get('airline', {})
    flight_data = flight.get('flight', {})
    dep = flight.get('departure', {})
    
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
