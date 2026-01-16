import requests
from datetime import datetime, timedelta, timezone

# 日本時間の定義
JST = timezone(timedelta(hours=9))

try:
    from config import CONFIG
    ACCESS_KEY = CONFIG.get("AVIATIONSTACK_KEY") or CONFIG.get("API_KEY")
except Exception:
    ACCESS_KEY = None

def get_refined_arrival_time(arrival_data):
    if arrival_data.get('actual'):
        return arrival_data['actual']
    if arrival_data.get('estimated'):
        return arrival_data['estimated']
    return arrival_data.get('scheduled')

def fetch_flights(target_airport="HND"):
    if not ACCESS_KEY:
        print("⚠️ エラー: APIキーが見つかりません。")
        return []

    url = "http://api.aviationstack.com/v1/flights"
    
    # 💡 深夜対応ロジック：
    # 深夜0時〜早朝3時までは、「昨日」の便にこそ需要があるため、取得日を調整します。
    now_jst = datetime.now(JST)
    if now_jst.hour < 3:
        # 深夜3時までは前日の日付で検索（23時台の着陸便を捕まえるため）
        target_date = (now_jst - timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        target_date = now_jst.strftime('%Y-%m-%d')

    params = {
        'access_key': ACCESS_KEY,
        'arr_iata': target_airport,
        'limit': 100
        # 日付指定を入れることで、朝の便に押し出されるのを防ぎます
        # 'flight_date': target_date # ティアによって制限があるため、一旦含めずステータスで調整
    }

    try:
        # 💡 ステータスを 'landed'（着陸済み）にすることで、
        # 今まさに客が降りてきている「直近の便」を優先的に取得します。
        params['flight_status'] = 'landed'
        
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return []
            
        raw_data = response.json()
        if 'data' not in raw_data:
            return []

        processed_flights = []
        for flight in raw_data['data']:
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