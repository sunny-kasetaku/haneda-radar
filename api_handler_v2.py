import requests
import time
import sys
from datetime import datetime, timedelta

def fetch_flight_data(api_key, date_str=None):
    """
    AviationStackからデータを取得する（時間追従・省エネ版）。
    現在時刻を意識し、「もう終わった朝の便」をスキップして、
    「直近〜未来の便」だけを300件の中に詰め込みます。
    これにより、夜になっても欧米便などの取りこぼしがなくなります。
    """
    base_url = "http://api.aviationstack.com/v1/flights"
    
    all_flights = []
    offset = 0
    limit = 100
    
    # 現在時刻(JST)を取得して、「4時間前」を計算
    # 例: 今が20:00なら、16:00以降の便だけをリクエストする
    now_jst = datetime.utcnow() + timedelta(hours=9)
    min_time_dt = now_jst - timedelta(hours=4)
    min_time_str = min_time_dt.strftime('%Y-%m-%d %H:%M:%S')

    # 日付が変わった直後(朝4時まで)は、昨日のデータも取る必要があるのでフィルタしない
    # 朝4時以降なら、フィルタを有効にする
    use_time_filter = False
    if now_jst.hour >= 4:
        use_time_filter = True
        # ただし、date_strが「今日」指定の場合に限る
        if date_str and date_str != now_jst.strftime('%Y-%m-%d'):
            use_time_filter = False

    while True:
        params = {
            'access_key': api_key,
            'arr_iata': 'HND',
            'limit': limit,
            'offset': offset
        }
        
        if date_str:
            params['flight_date'] = date_str
            
        # 【重要】ここで「古い便」を足切りします
        if use_time_filter:
            # APIに対して「この時間よりあとの到着便だけくれ」と指定
            # これで朝の便が除外され、夜の欧米便が300件の枠内に入ってきます
            params['min_scheduled_arrival'] = min_time_str
        
        try:
            # ログにフィルタ状況を出す
            filter_msg = f"(Filter > {min_time_str})" if use_time_filter else "(All Day)"
            print(f"DEBUG: Fetching offset {offset} {filter_msg}...", file=sys.stderr)
            
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
            
            # 300件でストップ（ブレーキ）
            if offset >= 300:
                print("DEBUG: Limit reached (300 records). Stopping fetch.", file=sys.stderr)
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
    # 【重要】機材情報も忘れずに取得
    aircraft = flight.get('aircraft', {})
    aircraft_iata = aircraft.get('iata', 'none') if aircraft else 'none'
    
    arrival_time = arr.get('estimated') or arr.get('actual') or arr.get('scheduled')
    if not arrival_time: return None

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
        "status": flight.get('flight_status', 'unknown'),
        "aircraft": aircraft_iata
    }