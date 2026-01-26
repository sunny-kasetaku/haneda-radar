import requests
import time
import sys
from datetime import datetime, timedelta

def fetch_flight_data(api_key, date_str=None):
    """
    AviationStackからデータを取得する（ページネーション版）。
    """
    base_url = "http://api.aviationstack.com/v1/flights"
    all_flights = []
    offset = 0
    limit = 100 

    while True:
        params = {
            'access_key': api_key,
            'arr_iata': 'HND',
            'limit': limit,
            'offset': offset
        }
        if date_str:
            params['flight_date'] = date_str
        
        try:
            print(f"DEBUG: Fetching offset {offset}...", file=sys.stderr)
            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()
            raw_data = data.get('data', [])
            
            if not raw_data:
                break
            
            for f in raw_data:
                info = extract_flight_info(f)
                if info:
                    all_flights.append(info)
            
            offset += limit
            if offset >= 1000:
                break
            time.sleep(0.1)
        except Exception as e:
            print(f"Error fetching flights: {e}", file=sys.stderr)
            break
            
    return all_flights

def extract_flight_info(flight):
    arr = flight.get('arrival', {})
    airline = flight.get('airline', {})
    flight_data = flight.get('flight', {})
    dep = flight.get('departure', {})
    
    arrival_time_raw = arr.get('estimated') or arr.get('actual') or arr.get('scheduled')
    if not arrival_time_raw: return None

    # --- 【重要】ここが「時刻のズレ」を直す心臓部です ---
    try:
        # APIのUTC時刻(例: 08:00)をパースして +9時間(17:00)にする
        dt_utc = datetime.strptime(arrival_time_raw[:19], '%Y-%m-%dT%H:%M:%S')
        dt_jst = dt_utc + timedelta(hours=9)
        arrival_time_jst = dt_jst.strftime('%Y-%m-%dT%H:%M:%S')
    except:
        arrival_time_jst = arrival_time_raw # 失敗したら元の値を維持

    term = arr.get('terminal')
    f_num_str = str(flight_data.get('number', ''))
    
    if term is None:
        if len(f_num_str) >= 4: term = "1"
        else: term = "3"

    return {
        "flight_number": f"{airline.get('iata', '??')}{f_num_str}",
        "airline": airline.get('name', 'Unknown'),
        "origin": dep.get('airport', 'Unknown'),
        "origin_iata": dep.get('iata', 'UNK'),
        "terminal": str(term),
        "arrival_time": arrival_time_jst, # 日本時間に変換済みの時刻を渡す
        "status": flight.get('flight_status', 'unknown')
    }