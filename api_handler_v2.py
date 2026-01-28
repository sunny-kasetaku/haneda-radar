import requests
import time
import sys
from datetime import datetime, timedelta

def fetch_flight_data(api_key, date_str=None):
    """
    【修正版 v5】「3回別条件」戦略による広範囲取得ロジック
    ・サニーさんのアイデア通り、3回のリクエスト枠を「異なる条件」で使用。
    ・1回目: Active（飛行中）→ 現在の状況確保
    ・2回目: Landed（着陸済み）→ 直近の需要確保
    ・3回目: Yesterday（昨日出発）→ 日付またぎの欧米便確保
    """
    base_url = "http://api.aviationstack.com/v1/flights"
    
    all_flights = []
    
    # 時間計算
    now_jst = datetime.utcnow() + timedelta(hours=9)
    yesterday_jst = now_jst - timedelta(days=1)
    
    # 日付文字列を作成
    today_str = now_jst.strftime('%Y-%m-%d')
    yesterday_str = yesterday_jst.strftime('%Y-%m-%d')

    print(f"DEBUG: Start API Fetch. Strategy: Active -> Landed -> Yesterday", file=sys.stderr)

    # 【重要】3回のチャンスを、それぞれ別の戦略に使います
    strategies = [
        # 戦略1: 今飛んでいる便（日付問わず、リアルタイムな国内・国際）
        {'desc': '1. Active',   'params': {'flight_status': 'active', 'limit': 100}},
        
        # 戦略2: 着陸した便（直近のタクシー需要そのもの）
        {'desc': '2. Landed',   'params': {'flight_status': 'landed', 'limit': 100}},
        
        # 戦略3: 昨日出発した便（日付の壁で消えていた欧米・長距離便を救出）
        {'desc': '3. Yesterday', 'params': {'flight_date': yesterday_str, 'limit': 100}}
    ]

    for strat in strategies:
        params = {
            'access_key': api_key,
            'arr_iata': 'HND'
        }
        # 戦略ごとのパラメータを結合
        params.update(strat['params'])
        
        try:
            print(f"DEBUG: Fetching [{strat['desc']}]...", file=sys.stderr)
            
            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()
            raw_data = data.get('data', [])
            
            if not raw_data:
                print(f"DEBUG: No data for [{strat['desc']}]", file=sys.stderr)
                continue
            
            for f in raw_data:
                # 抽出関数を使ってデータを整理（サニーさんのロジックはそのまま）
                info = extract_flight_info(f)
                if info:
                    # 【重要】重複（W）を防ぐチェック
                    # すでにリストにある便と「便名」かつ「時間」が一致したらリストに入れない
                    is_duplicate = False
                    for existing in all_flights:
                        if (existing['flight_number'] == info['flight_number'] and 
                            existing['arrival_time'] == info['arrival_time']):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        all_flights.append(info)
            
            time.sleep(0.1)

        except Exception as e:
            print(f"Error fetching flights: {e}", file=sys.stderr)
            continue
            
    return all_flights

def extract_flight_info(flight):
    """
    フライト情報抽出ヘルパー
    """
    # ... (ここはサニーさんの元のコードのまま、変更なし) ...
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