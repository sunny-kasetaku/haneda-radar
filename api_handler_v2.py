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
        
        # 国際便の「日またぎ」を拾うため、日付フィルタは無効化します
        # if date_str:
        #     params['flight_date'] = date_str
            
        if use_time_filter:
            # UTC時間を渡すことで、APIが正しく認識できるようにする
            params['min_scheduled_arrival'] = min_time_str_utc
        
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
    
    arrival_time = arr.get('estimated') or arr.get('actual') or arr.get('scheduled')
    if not arrival_time: return None

    term = arr.get('terminal')
    f_num_str = str(flight_data.get('number', ''))
    airline_iata = airline.get('iata', '??')
    origin_iata = dep.get('iata', 'UNK')

    # 1. APIの文字ゆれ修正 (I/INT -> 3)
    if term in ["I", "INT", "i", "int"]:
        term = "3"

    # 2. ターミナルが空(None)の場合の、羽田特化・判定ロジック
    # ※APIが "1" や "2" を返している場合は、それを尊重して何もしません。
    if term is None or term == "":
        # 国内線キャリア（JAL, ANA, スカイマーク, スターフライヤー, ソラシド, AIRDO, JTA, IBEX）
        domestic_carriers = ["JL", "NH", "BC", "7G", "6J", "HD", "NU", "FW"]
        
        if airline_iata in domestic_carriers:
            if airline_iata in ["NH", "HD"]: 
                term = "2" # ANA/AIRDOはT2
            elif airline_iata == "JL" and f_num_str.startswith("5"): 
                term = "3" # JAL 5000番台は国際線(ジャカルタ等)
            else: 
                term = "1" # その他(JAL国内, スカイマーク等)はT1
        else:
            term = "3" # それ以外の外資系（UA, DL, SQ等）はすべてT3

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