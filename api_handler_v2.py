import requests
import json
import time

def fetch_flight_data(api_key):
    """
    AviationStack APIからデータを取得（ページネーション対応）
    """
    # ★ 有料版(Basic)なので https にします（セキュリティ向上）
    base_url = "https://api.aviationstack.com/v1/flights"
    
    # 修正箇所：flight_status から無効な値(estimated, delayed)を削除
    # これで 400 Bad Request が消えます
    params = {
        'access_key': api_key,
        'arr_iata': 'HND',
        'flight_status': 'active,scheduled,landed', 
        'limit': 100,
        'offset': 0
    }

    print(f"📡 APIリクエスト開始...")
    
    all_flights = []
    
    # 最大3ページ（300件）取得
    for i in range(3):
        params['offset'] = i * 100
        print(f"   -> Page {i+1} 取得中 (Offset {params['offset']})...")
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status() # ここでエラーなら例外へ
            data = response.json()
            
            raw_data = data.get('data', [])
            if not raw_data:
                break 
            
            for f in raw_data:
                info = extract_flight_info(f)
                if info:
                    all_flights.append(info)
            
            if len(raw_data) < 100:
                break
                
        except Exception as e:
            # 万が一エラーが出ても、それまでに取れたデータがあればよしとする
            print(f"❌ API Error (Page {i+1}): {e}")
            break
            
        time.sleep(0.2)

    print(f"✅ 合計取得数: {len(all_flights)}件")
    return all_flights

def extract_flight_info(flight):
    arr = flight.get('arrival', {})
    airline = flight.get('airline', {})
    dep = flight.get('departure', {})
    
    # ★ここが「遅延対応」の肝です
    # estimated（見込み時刻）があれば、定刻より優先して採用します
    arrival_time = arr.get('estimated') or arr.get('actual') or arr.get('scheduled')
    
    if not arrival_time:
        return None

    term = arr.get('terminal')
    if term is None:
        term = "Intl"

    return {
        "flight_number": f"{airline.get('iata', '??')}{flight.get('flight', {}).get('number', '??')}",
        "airline": airline.get('name', 'Unknown'),
        "origin": dep.get('airport', 'Unknown'),
        "origin_iata": dep.get('iata', 'UNK'),
        "terminal": str(term),
        "arrival_time": arrival_time,
        "status": flight.get('flight_status', 'unknown')
    }