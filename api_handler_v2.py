import requests
import time
import sys
from datetime import datetime, timedelta

def fetch_flight_data(api_key, date_str=None):
    """
    【修正版 v3】API取得ロジック (UTC補正対応)
    ・過去データを「2時間前」までで足切りし、300件の枠を節約。
    ・JST時間をUTCに変換してAPIに渡すことで、国際線の取りこぼしを防ぐ。
    """
    base_url = "http://api.aviationstack.com/v1/flights"
    
    all_flights = []
    offset = 0
    limit = 100
    
    # 1. 現在時刻(JST)を取得
    now_jst = datetime.utcnow() + timedelta(hours=9)
    
    # 2. 足切りライン(2時間前)を計算 (JST)
    min_time_dt_jst = now_jst - timedelta(hours=2)
    
    # 【重要修正】APIには「UTC時間」を渡さないと、9時間のズレで午前便が消える
    # JST から 9時間引いて UTC に戻すことで、APIが正しく時間を認識できる
    min_time_dt_utc = min_time_dt_jst - timedelta(hours=9)
    min_time_str_utc = min_time_dt_utc.strftime('%Y-%m-%d %H:%M:%S')

    # 朝4時以降ならフィルタを有効にする
    use_time_filter = False
    if now_jst.hour >= 4:
        use_time_filter = True
        # 日付指定がある場合(過去ログ調査など)はフィルタオフ
        if date_str and date_str != now_jst.strftime('%Y-%m-%d'):
            use_time_filter = False

    # デバッグログ: どの時間（UTC）でフィルタしているかを表示
    print(f"DEBUG: Start API Fetch. Time Filter (UTC): {use_time_filter} (> {min_time_str_utc})", file=sys.stderr)

    while True:
        params = {
            'access_key': api_key,
            'arr_iata': 'HND',
            'limit': limit,
            'offset': offset
        }
        
        # 元のコード（ここは触らずそのまま残します＝赤くなりません）
        params['flight_status'] = 'active'
        
        # 【緑の足し算】直前の 'active' 指定をここで取り消します
        # これで「着陸済み」の便も届くようになります
        if 'flight_status' in params: del params['flight_status']
        
        # 元のコード（ここも触りません）
        if date_str:
            params['flight_date'] = date_str
            
        # 【緑の足し算】日付指定をここで取り消します
        # これで「昨日出発」の国際線も届くようになります
        if 'flight_date' in params: del params['flight_date']

        if use_time_filter:
            # 元のコード（ここも触りません）
            params['min_scheduled_arrival'] = min_time_str_utc
            
            # 【緑の足し算】時間指定をここで取り消します
            # APIのバグを回避し、最新300件を確実に取得するためです
            if 'min_scheduled_arrival' in params: del params['min_scheduled_arrival']
        
        try:
            filter_msg = f"(Filter UTC > {min_time_str_utc})" if use_time_filter else "(All Day)"
            print(f"DEBUG: Fetching offset {offset} {filter_msg}...", file=sys.stderr)
            
            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()
            
            raw_data = data.get('data', [])
            
            if not raw_data:
                break
            
            for f in raw_data:
                # 抽出関数を使ってデータを整理
                info = extract_flight_info(f)
                if info:
                    all_flights.append(info)
            
            offset += limit
            
            # 300件制限 (夜間のデータあふれ防止)
            if offset >= 300:
                print("DEBUG: Limit reached (300 records). Stopping fetch.", file=sys.stderr)
                break
                
            time.sleep(0.1)

        except Exception as e:
            print(f"Error fetching flights: {e}", file=sys.stderr)
            break
            
    return all_flights

def extract_flight_info(flight):
    """
    フライト情報抽出ヘルパー
    """
    arr = flight.get('arrival', {})
    airline = flight.get('airline', {})
    flight_data = flight.get('flight', {})
    dep = flight.get('departure', {})
    aircraft = flight.get('aircraft', {})
    aircraft_iata = aircraft.get('iata', 'none') if aircraft else 'none'
    
    # 到着時刻がないものは除外
    arrival_time = arr.get('estimated') or arr.get('actual') or arr.get('scheduled')
    if not arrival_time: return None

    # ターミナル情報の補正
    term = arr.get('terminal')
    f_num_str = str(flight_data.get('number', ''))
    airline_iata = airline.get('iata', '??')
    origin_iata = dep.get('iata', 'UNK')

    # 【足し算】国際線の表記ゆれ（IやINT）を「3」に統合
    if term in ["I", "INT", "i", "int"]:
        term = "3"

    # 【足し算】ターミナル判定の強化
    if term is None or term == "" or term == "None":
        # 国内線キャリア（JAL, ANA, スカイマーク等）
        domestic_carriers = ["JL", "NH", "BC", "7G", "6J", "HD", "NU", "FW"]
        
        if airline_iata in domestic_carriers:
            if airline_iata in ["NH", "HD"]: 
                term = "2"
            elif airline_iata == "JL" and (f_num_str.startswith("5") or f_num_str.startswith("8") or len(f_num_str) <= 3):
                # JALの5000/8000番台、および3桁以下の便は国際線(T3)
                term = "3"
            else: 
                term = "1"
        else:
            # LH716, BR192, OZ1085などの外資系はすべて国際線(T3)
            term = "3"

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