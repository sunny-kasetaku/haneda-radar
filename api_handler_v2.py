import requests
import time
import sys
from datetime import datetime, timedelta

def fetch_flight_data(api_key, date_str=None):
    """
    【修正版 v12】深掘り全取得ロジック（時間フィルタ撤廃）
    ・30分に1回のAPI実行で、可能な限り広く深くデータを収集する。
    ・Python側での「時間による削除」は一切行わない。
    """
    base_url = "http://api.aviationstack.com/v1/flights"
    
    all_flights = []
    
    # 時間計算
    now_jst = datetime.utcnow() + timedelta(hours=9)
    yesterday_jst = now_jst - timedelta(days=1)
    yesterday_str = yesterday_jst.strftime('%Y-%m-%d')

    print(f"DEBUG: Start API Fetch v12. Strategy: Deep Dive & Keep ALL", file=sys.stderr)

    strategies = [
        # 1. Active: 未来の便 (200件まで深掘り)
        {'desc': '1. Active', 'params': {'flight_status': 'active', 'sort': 'scheduled_arrival'}, 'max_depth': 200},
        # 2. Landed: 過去の便 (200件まで深掘り)
        {'desc': '2. Landed', 'params': {'flight_status': 'landed', 'sort': 'scheduled_arrival.desc'}, 'max_depth': 200},
        # 3. Yesterday: 昨日出発の長距離便 (100件)
        {'desc': '3. Yesterday', 'params': {'flight_date': yesterday_str, 'sort': 'scheduled_arrival.desc'}, 'max_depth': 100}
    ]

    for strat in strategies:
        current_offset = 0
        fetched_count = 0
        target_depth = strat['max_depth']
        
        while fetched_count < target_depth:
            params = {
                'access_key': api_key, 'arr_iata': 'HND',
                'limit': 100, 'offset': current_offset
            }
            params.update(strat['params'])
            
            try:
                print(f"DEBUG: Fetching [{strat['desc']}] offset={current_offset}...", file=sys.stderr)
                response = requests.get(base_url, params=params, timeout=10)
                data = response.json()
                raw_data = data.get('data', [])
                
                if not raw_data: break
                
                for f in raw_data:
                    info = extract_flight_info(f)
                    if info:
                        # 重複排除ロジック
                        same_flight_index = -1
                        for i, existing in enumerate(all_flights):
                            if existing['flight_number'] == info['flight_number']:
                                same_flight_index = i
                                break
                        if same_flight_index != -1:
                            all_flights[same_flight_index] = info
                            continue

                        duplicate_time_index = -1
                        for i, existing in enumerate(all_flights):
                            if existing['arrival_time'] == info['arrival_time']:
                                duplicate_time_index = i
                                break
                        if duplicate_time_index != -1:
                            existing_flight = all_flights[duplicate_time_index]
                            is_new_japanese = info['flight_number'].startswith(('JL', 'NH'))
                            is_existing_japanese = existing_flight['flight_number'].startswith(('JL', 'NH'))
                            if is_new_japanese and not is_existing_japanese:
                                all_flights[duplicate_time_index] = info
                            continue
                        
                        # 時間フィルタなしで全部追加
                        all_flights.append(info)
                
                got_num = len(raw_data)
                current_offset += got_num
                fetched_count += got_num
                if got_num < 100: break
                time.sleep(0.1)

            except Exception as e:
                print(f"Error fetching flights: {e}", file=sys.stderr)
                break
            
    return all_flights

def extract_flight_info(flight):
    # 変更なし（サニーさんの元のロジック維持）
    arr = flight.get('arrival', {})
    airline = flight.get('airline', {})
    flight_data = flight.get('flight', {})
    dep = flight.get('departure', {})
    aircraft = flight.get('aircraft', {})
    aircraft_iata = aircraft.get('iata', 'none') if aircraft else 'none'
    
    arrival_time = arr.get('estimated') or arr.get('actual') or arr.get('scheduled')
    if not arrival_time: return None

    term = arr.get('terminal')
    f_num_str = str(flight_data.get('number', ''))
    airline_iata = airline.get('iata', '??')
    origin_iata = dep.get('iata', 'UNK')

    if term in ["I", "INT", "i", "int"]: term = "3"

    if term is None or term == "" or term == "None":
        domestic_carriers = ["JL", "NH", "BC", "7G", "6J", "HD", "NU", "FW"]
        if airline_iata in domestic_carriers:
            if airline_iata in ["NH", "HD"]: term = "2"
            elif airline_iata == "JL" and (f_num_str.startswith("5") or f_num_str.startswith("8") or len(f_num_str) <= 3): term = "3"
            else: term = "1"
        else: term = "3"

    return {
        "flight_number": f"{airline_iata}{f_num_str}",
        "airline": airline.get('name', 'Unknown'),
        "origin": dep.get('airport', 'Unknown'),
        "origin_iata": origin_iata,
        "terminal": str(term),
        "arrival_time": arrival_time,
        "status": flight.get('flight_status', 'unknown'),
        "aircraft": aircraft_iata
    }