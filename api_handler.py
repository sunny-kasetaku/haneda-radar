import requests
from datetime import datetime, timedelta

try:
    from config import CONFIG
    ACCESS_KEY = CONFIG.get("AVIATIONSTACK_KEY")
except ImportError:
    ACCESS_KEY = None

def get_refined_arrival_time(arrival_data):
    # 到着時間の優先順位：実着 > 推定 > 定刻
    if arrival_data.get('actual'):
        return arrival_data['actual']
    if arrival_data.get('estimated'):
        return arrival_data['estimated']
    return arrival_data.get('scheduled')

def fetch_flights(target_airport="HND"):
    if not ACCESS_KEY:
        print("⚠️ エラー: APIキーが設定されていません。")
        return []

    url = "http://api.aviationstack.com/v1/flights"
    
    # 💡 修正ポイント：特定のステータスに絞らず、羽田着の最新100件を丸ごと取る
    params = {
        'access_key': ACCESS_KEY,
        'arr_iata': target_airport,
        'limit': 100
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return []
            
        raw_data = response.json()
        if 'data' not in raw_data:
            return []

        processed_flights = []
        for flight in raw_data['data']:
            # 欠航以外はすべて受け入れる
            if flight.get('flight_status') == 'cancelled':
                continue

            arrival = flight.get('arrival', {})
            arrival_time = get_refined_arrival_time(arrival)
            
            if not arrival_time:
                continue

            processed_flights.append({
                'flight_iata': flight.get('flight', {}).get('iata'),
                'airline': flight.get('airline', {}).get('name'),
                'arrival_time': arrival_time,
                'terminal': arrival.get('terminal'),
                'status': flight.get('flight_status')
            })

        return processed_flights

    except Exception as e:
        print(f"⚠️ 通信エラー: {e}")
        return []