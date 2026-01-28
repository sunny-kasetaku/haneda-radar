import requests
import time
import sys
from datetime import datetime, timedelta

def fetch_flight_data(api_key, date_str=None):
    """
    【修正版 v8】3連コンボ戦略 ＋ ソート＆重複対策完備
    ・Active/Landed/Yesterdayの3戦略で、シカゴも国内線も全方位で取得。
    ・APIの「sort」を使い、新しい国内線も確実に拾う。
    ・「コードシェア対策」を組み込み、シカゴ便の重複(W)をNH/JL優先で1つにまとめる。
    """
    base_url = "http://api.aviationstack.com/v1/flights"
    
    all_flights = []
    
    # 時間計算
    now_jst = datetime.utcnow() + timedelta(hours=9)
    yesterday_jst = now_jst - timedelta(days=1)
    
    today_str = now_jst.strftime('%Y-%m-%d')
    yesterday_str = yesterday_jst.strftime('%Y-%m-%d')

    print(f"DEBUG: Start API Fetch v8. Strategy: 3-Ren Combo with Sort & Dedup", file=sys.stderr)

    # 【重要】3連コンボ：それぞれの弱点を補う「ソート順」を指定します
    strategies = [
        # 1. Active: 「到着早い順」で、これから着く便を確実に拾う
        {
            'desc': '1. Active',
            'params': {'flight_status': 'active', 'limit': 100, 'sort': 'scheduled_arrival'}
        },
        
        # 2. Landed: 「新しい順」で、さっき着いたばかりの国内線を拾う（これで国内線復活）
        {
            'desc': '2. Landed',
            'params': {'flight_status': 'landed', 'limit': 100, 'sort': 'scheduled_arrival.desc'}
        },
        
        # 3. Yesterday: 「新しい順」で、昨日出発の欧米便を拾う（これでシカゴ確保）
        {
            'desc': '3. Yesterday',
            'params': {'flight_date': yesterday_str, 'limit': 100, 'sort': 'scheduled_arrival.desc'}
        }
    ]

    for strat in strategies:
        params = {
            'access_key': api_key,
            'arr_iata': 'HND'
        }
        params.update(strat['params'])
        
        try:
            print(f"DEBUG: Fetching [{strat['desc']}]...", file=sys.stderr)
            
            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()
            raw_data = data.get('data', [])
            
            if not raw_data:
                continue
            
            for f in raw_data:
                info = extract_flight_info(f)
                if info:
                    # -----------------------------------------------------------
                    # 【コードシェア対策 & 重複排除ロジック】
                    # シカゴ便などで「時間は同じだが便名が違う」ケースを1つにまとめる
                    # -----------------------------------------------------------
                    duplicate_index = -1
                    for i, existing in enumerate(all_flights):
                        # 「到着時間が分単位まで同じ」なら、同じ飛行機とみなす
                        if existing['arrival_time'] == info['arrival_time']:
                            duplicate_index = i
                            break
                    
                    if duplicate_index != -1:
                        # 重複を発見。どっちを残すか決める。
                        existing_flight = all_flights[duplicate_index]
                        
                        # ルール: 「既存が外資」で「新規が日本(NH/JL)」なら、日本に書き換える
                        # (例: UA7911 が先にあっても、後から NH111 が来たら NH111 にする)
                        is_new_japanese = info['flight_number'].startswith(('JL', 'NH'))
                        is_existing_japanese = existing_flight['flight_number'].startswith(('JL', 'NH'))
                        
                        if is_new_japanese and not is_existing_japanese:
                            all_flights[duplicate_index] = info
                        
                        # 逆に「すでにNH」を持っていて「新規がUA」なら、何もしない（NHを守る）
                        
                    else:
                        # 重複がなければ、普通に追加
                        all_flights.append(info)
            
            time.sleep(0.1)

        except Exception as e:
            print(f"Error fetching flights: {e}", file=sys.stderr)
            continue
            
    return all_flights

def extract_flight_info(flight):
    """
    フライト情報抽出ヘルパー
    （サニーさんの元のコードをそのまま維持）
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