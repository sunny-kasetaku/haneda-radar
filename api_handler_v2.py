import requests
import time
import sys
from datetime import datetime, timedelta

def fetch_flight_data(api_key, date_str=None):
    """
    【v18 最終修正版】深掘り全取得 ＋ タイムアウト対策(30秒)
    ・APIリクエストは7回深掘り（Active×2, Landed×2, Scheduled×2, Yesterday×1）
    ・タイムアウトを30秒に設定し、通信エラーを防ぐ
    ・重複排除を「時刻・ターミナル・出発地」のトリプルチェックに改善
    """
    base_url = "http://api.aviationstack.com/v1/flights"
    
    all_flights = []
    
    # 時間計算
    now_jst = datetime.utcnow() + timedelta(hours=9)
    yesterday_jst = now_jst - timedelta(days=1)
    yesterday_str = yesterday_jst.strftime('%Y-%m-%d')
    
    # 🦁 修正: 日付指定がない場合は今日とする
    target_date = date_str if date_str else now_jst.strftime('%Y-%m-%d')

    # 🦁 追加: 午後は「降順」で夜の便を優先確保
    if now_jst.hour >= 12:
        sched_sort = 'scheduled_arrival.desc'
    else:
        sched_sort = 'scheduled_arrival'

    # バージョン表示を v18 に修正
    print(f"DEBUG: Start API Fetch v18. Strategy: Deep Dive & Triple Check", file=sys.stderr)

    strategies = [
        # 1. Active: 未来の便 (200件まで深掘り)
        # 🦁 修正: flight_dateを指定して去年のゴミデータを排除
        {'desc': '1. Active', 'params': {'flight_status': 'active', 'sort': 'scheduled_arrival', 'flight_date': target_date}, 'max_depth': 200},
        # 2. Landed: 過去の便 (200件まで深掘り -> これで消えた国内線を全カバー)
        # 🦁 修正: flight_dateを指定して「今日の」新しい順にすることで、23時台の到着漏れを防ぐ
        {'desc': '2. Landed', 'params': {'flight_status': 'landed', 'sort': 'scheduled_arrival.desc', 'flight_date': target_date}, 'max_depth': 400},
        # 🦁 追加: 3. Scheduled: 予定の便 (200件まで深掘り) ★ここを追加
        {'desc': '3. Scheduled', 'params': {'flight_status': 'scheduled', 'sort': sched_sort, 'flight_date': target_date}, 'max_depth': 300},
        # 4. Yesterday: 昨日出発の長距離便 (100件)
        {'desc': '4. Yesterday', 'params': {'flight_date': yesterday_str, 'sort': 'scheduled_arrival.desc'}, 'max_depth': 100}
    ]

    for strat in strategies:
        current_offset = 0
        fetched_count = 0
        target_depth = strat['max_depth']
        
        while fetched_count < target_depth:
            params = {
                'access_key': api_key,
                'arr_iata': 'HND',
                'limit': 100, 
                'offset': current_offset
            }
            params.update(strat['params'])
            
            try:
                print(f"DEBUG: Fetching [{strat['desc']}] offset={current_offset}...", file=sys.stderr)
                
                # 【修正】タイムアウトを30秒に延長
                response = requests.get(base_url, params=params, timeout=30)
                data = response.json()
                raw_data = data.get('data', [])
                
                if not raw_data:
                    break
                
                for f in raw_data:
                    info = extract_flight_info(f)
                    if info:
                        # --- 重複排除 (1) 同一便名チェック ---
                        same_flight_index = -1
                        for i, existing in enumerate(all_flights):
                            if existing['flight_number'] == info['flight_number']:
                                same_flight_index = i
                                break
                        
                        if same_flight_index != -1:
                            all_flights[same_flight_index] = info
                            continue

                        # --- 重複排除 (2) コードシェア便トリプルチェック ---
                        # 同時刻・同ターミナル・同出発地の場合のみ「同じ1機」とみなす
                        duplicate_index = -1
                        for i, existing in enumerate(all_flights):
                            if (existing['arrival_time'] == info['arrival_time'] and 
                                existing['terminal'] == info['terminal'] and 
                                existing['origin_iata'] == info['origin_iata']):
                                duplicate_index = i
                                break
                        
                        if duplicate_index != -1:
                            # 既にJALやANAが入っているなら、海外便名は追加せずに捨てる
                            existing_flight = all_flights[duplicate_index]
                            is_new_japanese = info['flight_number'].startswith(('JL', 'NH'))
                            is_existing_japanese = existing_flight['flight_number'].startswith(('JL', 'NH'))
                            
                            if is_new_japanese and not is_existing_japanese:
                                all_flights[duplicate_index] = info
                            continue

                        # 全部追加
                        all_flights.append(info)
                
                got_num = len(raw_data)
                current_offset += got_num
                fetched_count += got_num
                
                if got_num < 100:
                    break
                
                # 【修正】少し休憩時間を増やす
                time.sleep(0.5)

            except Exception as e:
                print(f"Error fetching flights: {e}", file=sys.stderr)
                break
            
    return all_flights

# 🦁 ここから下が消えていたので、MAX時刻ロジックを含めて完全復元しました
def extract_flight_info(flight):
    arr = flight.get('arrival', {})
    airline = flight.get('airline', {})
    flight_data = flight.get('flight', {})
    dep = flight.get('departure', {})
    aircraft = flight.get('aircraft', {})
    aircraft_iata = aircraft.get('iata', 'none') if aircraft else 'none'
    
    # 🦁 修正：遅延を絶対に逃さない「MAX時刻採用ロジック」
    s_time = arr.get('scheduled')
    e_time = arr.get('estimated')
    a_time = arr.get('actual')
    
    time_candidates = [t for t in [s_time, e_time, a_time] if t]
    if not time_candidates: return None
    
    # 全候補の中で最も遅い時刻を到着とする。
    arrival_time = max(time_candidates)
    scheduled_time = s_time 
    
    term = arr.get('terminal')
    f_num_str = str(flight_data.get('number', ''))
    airline_iata = airline.get('iata', '??')
    origin_iata = dep.get('iata', 'UNK')

    if term in ["I", "INT", "i", "int"]:
        term = "3"

    if term is None or term == "" or term == "None":
        domestic_carriers = ["JL", "NH", "BC", "7G", "6J", "HD", "NU", "FW"]
        
        if airline_iata in domestic_carriers:
            if airline_iata in ["NH", "HD"]: 
                term = "2"
            elif airline_iata == "JL" and (f_num_str.startswith("5") or f_num_str.startswith("8") or len(f_num_str) <= 3):
                term = "3"
            else: 
                term = "1"
        else:
            term = "3"

    return {
        "flight_number": f"{airline_iata}{f_num_str}",
        "airline": airline.get('name', 'Unknown'),
        "origin": dep.get('airport', 'Unknown'),
        "origin_iata": origin_iata,
        "terminal": str(term),
        "arrival_time": arrival_time,
        "scheduled_time": scheduled_time,
        "status": flight.get('flight_status', 'unknown'),
        "aircraft": aircraft_iata
    }