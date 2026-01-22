import requests
import json
import time

def fetch_flight_data(api_key):
    """
    AviationStack APIからデータを全件取得し、
    遅延便も含めて正しく抽出する（ページネーション対応版）
    """
    base_url = "http://api.aviationstack.com/v1/flights"
    
    # 取得したいステータス（delayedも重要）
    params = {
        'access_key': api_key,
        'arr_iata': 'HND',
        'flight_status': 'active,scheduled,landed,estimated,delayed',
        'limit': 100,  # 1回の最大取得数
        'offset': 0
    }

    print(f"📡 APIリクエスト開始...")
    
    all_flights = []
    
    # --- ページネーション（ループ処理） ---
    # 最大3ページ（300件）まで取れば十分カバーできます
    for i in range(3):
        params['offset'] = i * 100
        print(f"   -> Page {i+1} 取得中 (Offset {params['offset']})...")
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            raw_data = data.get('data', [])
            if not raw_data:
                break # データが尽きたら終了
            
            # 抽出処理
            for f in raw_data:
                info = extract_flight_info(f)
                if info:
                    all_flights.append(info)
            
            # 取得数が100未満なら、もう次のページはないので終了
            if len(raw_data) < 100:
                break
                
        except Exception as e:
            print(f"❌ API Error (Page {i+1}): {e}")
            break
            
        # API制限への配慮（少し待機）
        time.sleep(0.5)

    print(f"✅ 合計取得数: {len(all_flights)}件")
    return all_flights

def extract_flight_info(flight):
    arr = flight.get('arrival', {})
    airline = flight.get('airline', {})
    dep = flight.get('departure', {})
    
    # ★ここが最重要：実際の到着時刻を優先採用する
    # 1. estimated (最新の見込み) -> 遅延時はこれが未来の時間になる
    # 2. actual (到着済み)
    # 3. scheduled (定刻)
    arrival_time = arr.get('estimated') or arr.get('actual') or arr.get('scheduled')
    
    if not arrival_time:
        return None

    # ターミナル
    term = arr.get('terminal')
    if term is None:
        term = "Intl" # 国際線とみなす

    return {
        "flight_number": f"{airline.get('iata', '??')}{flight.get('flight', {}).get('number', '??')}",
        "airline": airline.get('name', 'Unknown'),
        "origin": dep.get('airport', 'Unknown'),
        "origin_iata": dep.get('iata', 'UNK'),
        "terminal": str(term),
        "arrival_time": arrival_time,
        "status": flight.get('flight_status', 'unknown')
    }