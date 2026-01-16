import requests
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))

try:
    from config import CONFIG
    ACCESS_KEY = CONFIG.get("AVIATIONSTACK_KEY") or CONFIG.get("API_KEY")
except Exception:
    ACCESS_KEY = None

def get_refined_arrival_time(arrival_data):
    # 深夜は「実際に着いた時間(actual)」が何より重要です
    return arrival_data.get('actual') or arrival_data.get('estimated') or arrival_data.get('scheduled')

def fetch_flights(target_airport="HND"):
    if not ACCESS_KEY:
        print("⚠️ エラー: APIキーが見つかりません。")
        return []

    url = "http://api.aviationstack.com/v1/flights"
    
    # 💡 戦略：ステータスを 'landed'（着陸済み）に限定します。
    # これにより「これから来る朝の便」は無視され、
    # 「23時台、0時台に実際に着いた便」が100件分リストに並びます。
    params = {
        'access_key': ACCESS_KEY,
        'arr_iata': target_airport,
        'limit': 100,
        'flight_status': 'landed' 
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return []
            
        raw_data = response.json()
        if 'data' not in raw_data:
            return []

        processed_flights = []
        for flight in raw_data['data']:
            arrival = flight.get('arrival', {})
            arrival_time = get_refined_arrival_time(arrival)
            
            if not arrival_time: continue

            processed_flights.append({
                'flight_iata': flight.get('flight', {}).get('iata') or "??",
                'airline': flight.get('airline', {}).get('name') or "Unknown",
                'arrival_time': arrival_time,
                'terminal': arrival.get('terminal'),
                'status': flight.get('flight_status')
            })

        return processed_flights

    except Exception:
        return []