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
    """ APIの到着データから時刻を抽出 """
    return arrival_data.get('actual') or arrival_data.get('estimated') or arrival_data.get('scheduled')

def fetch_flights(target_airport="HND"):
    if not ACCESS_KEY:
        print("⚠️ エラー: APIキーが見つかりません。")
        return []

    url = "http://api.aviationstack.com/v1/flights"
    
    # 💡 策：あえて絞り込みをせず、羽田着の最新100件をありのまま取得
    params = {
        'access_key': ACCESS_KEY,
        'arr_iata': target_airport,
        'limit': 100
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"⚠️ APIエラー: ステータス {response.status_code}")
            return []
            
        raw_data = response.json()
        if 'data' not in raw_data or not raw_data['data']:
            print("⚠️ APIから返されたデータが空です。")
            return []

        processed_flights = []
        for flight in raw_data['data']:
            arrival = flight.get('arrival', {})
            arrival_time = get_refined_arrival_time(arrival)
            
            if not arrival_time: continue

            processed_flights.append({
                'flight_iata': flight.get('flight', {}).get('iata') or "??",
                'airline': flight.get('airline', {}).get('name') or "Unknown",
                'arrival_time': arrival_time,
                'terminal': arrival.get('terminal'),
                'status': flight.get('flight_status')
            })

        return processed_flights

    except Exception as e:
        print(f"⚠️ 通信エラー: {e}")
        return []