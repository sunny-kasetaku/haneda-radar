import requests
import time
import sys

def fetch_flight_data(api_key, date_str=None):
    """
    AviationStackからデータを取得する（省エネ設定版）。
    1回につき100件取得 × 3回ループ = 最大300件取得。
    これでAPI消費を大幅に抑えつつ、直近の重要データは確保します。
    """
    base_url = "http://api.aviationstack.com/v1/flights"
    
    all_flights = []
    offset = 0
    limit = 100  # APIの1回あたりの最大取得数
    
    # ループ開始
    while True:
        params = {
            'access_key': api_key,
            'arr_iata': 'HND',
            'limit': limit,
            'offset': offset
        }
        
        # 日付指定があれば追加
        if date_str:
            params['flight_date'] = date_str
        
        try:
            print(f"DEBUG: Fetching offset {offset}...", file=sys.stderr)
            
            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()
            
            raw_data = data.get('data', [])
            
            # データが空っぽなら終了
            if not raw_data:
                break
            
            # 取得したデータをリストに追加
            for f in raw_data:
                info = extract_flight_info(f)
                if info:
                    all_flights.append(info)
            
            # 次のページへ進む準備
            offset += limit
            
            # 【重要修正】ここでブレーキをかけます！
            # 1000 -> 300 に変更しました。これで3回(30リクエスト)で止まります。
            if offset >= 300:
                print("DEBUG: Limit reached (300 records). Stopping fetch.", file=sys.stderr)
                break
                
            # APIへの負荷軽減
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
    
    # 【追加修正】機材情報の取得
    # これがないと、先ほど実装した「大型機判定」が動きません
    aircraft = flight.get('aircraft', {})
    aircraft_iata = aircraft.get('iata', 'none') if aircraft else 'none'
    
    # 到着時刻の特定
    arrival_time = arr.get('estimated') or arr.get('actual') or arr.get('scheduled')
    if not arrival_time: return None

    # ターミナル判定 (APIになければ便名で簡易推測)
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
        "aircraft": aircraft_iata  # ← これをanalyzerに渡します！
    }