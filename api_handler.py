import requests
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))

try:
    from config import CONFIG
    ACCESS_KEY = CONFIG.get("AVIATIONSTACK_KEY") or CONFIG.get("API_KEY")
except Exception:
    ACCESS_KEY = None

def get_refined_arrival_time(arrival_data):
    if arrival_data.get('actual'): return arrival_data['actual']
    if arrival_data.get('estimated'): return arrival_data['estimated']
    return arrival_data.get('scheduled')

def fetch_flights(target_airport="HND"):
    if not ACCESS_KEY:
        print("⚠️ エラー: APIキーが見つかりません。")
        return []

    url = "http://api.aviationstack.com/v1/flights"
    
    # 💡 戦略変更：日付指定を完全に削除し、
    # 'flight_status': 'landed'（着陸済み）の最新100件だけを要求します。
    # これなら日付を跨いでも「直近に降りた便」が確実に手に入ります。
    params = {
        'access_key': ACCESS_KEY,
        'arr_iata': target_airport,
        'limit': 100,
        'flight_status': 'landed' 
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        
        # 💡 デバッグ用：エラー時に詳細を出す
        if response.status_code != 200:
            print(f"⚠️ APIエラー: ステータスコード {response.status_code}")
            print(f"メッセージ: {response.text[:100]}") # エラー理由のヒントを表示
            return []
            
        raw_data = response.json()
        if 'data' not in raw_data:
            return []

        processed_flights = []
        for flight in raw_data['data']:
            arrival = flight.get('arrival', {})
            arrival_time = get_refined_arrival_time(arrival)
            
            if not arrival_time: continue

            processed_flights.append({
                'flight_iata': flight.get('flight', {}).get('iata'),
                'airline': flight.get('airline', {}).get('name'),
                'arrival_time': arrival_time,
                'terminal': arrival.get('terminal'),
                'status': flight.get('flight_status')
            })

        return processed_flights

    except Exception as e:
        print(f"⚠️ 通信中に例外が発生しました: {e}")
        return []