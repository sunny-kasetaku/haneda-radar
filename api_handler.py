import requests
from datetime import datetime, timedelta

# config.py から設定を読み込む（以前の haneda_radar.py の形式に対応）
try:
    from config import CONFIG
    ACCESS_KEY = CONFIG.get("AVIATIONSTACK_KEY")
except (ImportError, KeyError):
    # もしもの時の予備
    ACCESS_KEY = "あなたのAPIキー" 

def get_refined_arrival_time(arrival_data):
    """
    APIの到着データから、最も信頼できる到着時刻を一つ選出する
    優先順位: 1.実着(actual) 2.推定(estimated) 3.遅延込(scheduled+delay) 4.定刻(scheduled)
    """
    if arrival_data.get('actual'):
        return arrival_data['actual']
    
    if arrival_data.get('estimated'):
        return arrival_data['estimated']
    
    scheduled_str = arrival_data.get('scheduled')
    delay = arrival_data.get('delay')
    
    if scheduled_str and delay:
        try:
            base_time = datetime.fromisoformat(scheduled_str.replace('Z', '+00:00'))
            refined_time = base_time + timedelta(minutes=int(delay))
            return refined_time.isoformat()
        except Exception:
            return scheduled_str
            
    return scheduled_str

def fetch_flights(target_airport="HND"):
    """
    APIから羽田のフライト情報を取得
    flight_status='active' を指定することで、未来の予定便(scheduled)に
    データ枠を占領されるのを防ぎ、今まさに羽田に向かっている便を優先的に取得します。
    """
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': ACCESS_KEY,
        'arr_iata': target_airport,
        'limit': 100,
        # 💡 ここが重要：今空にいる便（または着陸直後の便）を狙います
        'flight_status': 'active' 
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        raw_data = response.json()

        if 'data' not in raw_data:
            return []

        processed_flights = []
        for flight in raw_data['data']:
            # 欠航便は除外
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
        print(f"⚠️ API取得エラー: {e}")
        return []