import requests
import time
import sys
from datetime import datetime, timedelta

def fetch_flight_data(api_key, date_str=None):
    """
    【v23.6 Midnight-Bridge】API回数12回/run
    ・現在時刻に連動してOffsetを自動計算（スライド方式）。
    ・夜21時以降は「明日出発(Tomorrow)」の100件をブリッジし、0時〜1時の欠落を完全解消。
    ・サニーさんの以前の知見（出発日基準）に基づき、日付の壁を突破するロジック。
    """
    base_url = "http://api.aviationstack.com/v1/flights"
    
    all_flights = []
    
    # 時間計算
    now_jst = datetime.utcnow() + timedelta(hours=9)
    yesterday_jst = now_jst - timedelta(days=1)
    yesterday_str = yesterday_jst.strftime('%Y-%m-%d')
    
    # 🦁 修正: 明日の日付を計算
    tomorrow_jst = now_jst + timedelta(days=1)
    tomorrow_str = tomorrow_jst.strftime('%Y-%m-%d')
    
    # 🦁 修正: 日付指定がない場合は今日とする
    target_date = date_str if date_str else now_jst.strftime('%Y-%m-%d')

    # [2026-02-06] 🦁 追記: APIのUTC基準に合わせるための補正ロジック
    # APIの日付更新はUTC 0時(日本時間9時)のため、JST 0時の切り替わりでOffsetをリセットさせない
    now_utc = datetime.utcnow()
    target_date = now_utc.strftime('%Y-%m-%d') # APIが現在「当日」と認識している日付
    yesterday_str = (now_utc - timedelta(days=1)).strftime('%Y-%m-%d')
    # [2026-02-06] 終

    # 🦁 修正: 全自動スライド・ロジック (CVT方式)
    current_hour = now_jst.hour
    base_offset = 0
    
    if 0 <= current_hour < 21:
        # 【昼間スライドモード】時刻に合わせて網を自動でスライドさせる
        sched_sort = 'scheduled_arrival'
        base_offset = max(0, (current_hour - 2) * 55)
    else:
        # 【深夜逆算モード】21時以降は、24時から遡って拾うのが最も確実
        sched_sort = 'scheduled_arrival.desc'
        base_offset = 0

    # [2026-02-06] 🦁 追記: UTC基準のOffset計算 (JST深夜のデータ消失を防止)
    # UTC基準(朝9時=0時)でOffsetを計算することで、24時間連続したスライドを実現する
    current_hour_utc = now_utc.hour
    
    # [2026-02-06 02:50] 🦁 修正: Offset上限(Cap)とソート順の強制
    # 計算値が900を超えると、リスト末尾にある深夜便(JL78等)をスキップしてしまうため、上限を700に固定する
    # また、深夜帯もスライド方式を維持するため、JST側で設定された .desc を昇順に上書きする
    calc_offset = current_hour_utc * 55
    base_offset = min(700, max(0, calc_offset)) 
    sched_sort = 'scheduled_arrival'
    # [2026-02-06] 終
    
    # 深夜21時〜翌9時の間、Offsetがリセットされるのを防ぐための最終防衛ライン
    if current_hour >= 21 or current_hour < 9:
        # 夜間は「今日(UTC)」の後半を狙い撃つため、Offsetを固定気味に維持
        # Scheduled(400件)で「今日(UTC)」の終わり=JST 09:00までを確実にカバー
        pass 
    # [2026-02-06] 終

    print(f"DEBUG: Start API Fetch v23.8 Safety-Cap. Hour_JST={current_hour}, Offset={base_offset}", file=sys.stderr)

    # 🦁 修正：戦略リストを動的に構築
    strategies = [
        # 1. Active: 今飛んでいる便（絶対削らない）
        {'desc': '1. Active', 'params': {'flight_status': 'active', 'sort': sched_sort, 'flight_date': target_date}, 'max_depth': 500, 'use_offset': False},
        # 2. Landed: 着いたばかりの便（振り返り用）
        {'desc': '2. Landed', 'params': {'flight_status': 'landed', 'sort': 'scheduled_arrival.desc', 'flight_date': target_date}, 'max_depth': 200, 'use_offset': False},
        # 3. Scheduled: これからの便（スライド方式適用）
        {'desc': '3. Scheduled', 'params': {'flight_status': 'scheduled', 'sort': sched_sort, 'flight_date': target_date}, 'max_depth': 400, 'use_offset': True},
    ]

    # 🦁 4番目の枠（100件分）を、サニーさんのロジックで昼夜切り替え
    # [2026-02-06] 🦁 修正：JST深夜0時〜9時の間も「明日(APIにとっての当日)」を拾い続けるよう条件を拡張
    # if current_hour >= 21:
    if current_hour >= 21 or current_hour < 9:
        # 夜間：日付の壁を越えるため「明日出発」の便を拾う
        strategies.append({'desc': '4. Tomorrow', 'params': {'flight_date': tomorrow_str, 'sort': 'scheduled_arrival'}, 'max_depth': 100, 'use_offset': False})
    else:
        # 昼間：昨日分の振り返りを入れる
        strategies.append({'desc': '4. Yesterday', 'params': {'flight_date': yesterday_str, 'sort': 'scheduled_arrival.desc'}, 'max_depth': 100, 'use_offset': False})
    # [2026-02-06] 修正終了

    for strat in strategies:
        if strat.get('use_offset'):
            current_offset = base_offset
        else:
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
                print(f"DEBUG: Fetching [{strat['desc']}] offset={current_offset} date={strat['params'].get('flight_date')}...", file=sys.stderr)
                
                response = requests.get(base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                raw_data = data.get('data', [])
                
                if not raw_data:
                    break
                
                for f in raw_data:
                    info = extract_flight_info(f)
                    if info:
                        same_flight_index = -1
                        for i, existing in enumerate(all_flights):
                            if existing['flight_number'] == info['flight_number']:
                                same_flight_index = i
                                break
                        
                        if same_flight_index != -1:
                            all_flights[same_flight_index] = info
                            continue

                        duplicate_index = -1
                        for i, existing in enumerate(all_flights):
                            if (existing['arrival_time'] == info['arrival_time'] and 
                                existing['terminal'] == info['terminal'] and 
                                existing['origin_iata'] == info['origin_iata']):
                                duplicate_index = i
                                break
                        
                        if duplicate_index != -1:
                            existing_flight = all_flights[duplicate_index]
                            is_new_japanese = info['flight_number'].startswith(('JL', 'NH'))
                            is_existing_japanese = existing_flight['flight_number'].startswith(('JL', 'NH'))
                            
                            if is_new_japanese and not is_existing_japanese:
                                all_flights[duplicate_index] = info
                            continue

                        all_flights.append(info)
                
                got_num = len(raw_data)
                current_offset += got_num
                fetched_count += got_num
                
                if got_num < 100:
                    break
                
                time.sleep(0.5)

            except Exception as e:
                print(f"Error fetching flights: {e}", file=sys.stderr)
                break
            
    return all_flights

# extract_flight_info は変更なし
def extract_flight_info(flight):
    arr = flight.get('arrival', {})
    airline = flight.get('airline', {})
    flight_data = flight.get('flight', {})
    dep = flight.get('departure', {})
    aircraft = flight.get('aircraft', {})
    aircraft_iata = aircraft.get('iata', 'none') if aircraft else 'none'
    
    s_time = arr.get('scheduled')
    e_time = arr.get('estimated')
    a_time = arr.get('actual')
    
    time_candidates = [t for t in [s_time, e_time, a_time] if t]
    if not time_candidates: return None
    
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