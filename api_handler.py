import requests
from datetime import datetime, timedelta

# --- 💡 config.py の CONFIG 辞書から確実に読み込む ---
try:
    from config import CONFIG
    # CONFIG辞書の中から、考えられるキー名をすべて試す
    ACCESS_KEY = CONFIG.get("AVIATIONSTACK_KEY") or CONFIG.get("API_KEY")
except Exception as e:
    ACCESS_KEY = None

def get_refined_arrival_time(arrival_data):
    """
    最も正確な到着時刻を割り出す
    """
    if arrival_data.get('actual'):
        return arrival_data['actual']
    if arrival_data.get('estimated'):
        return arrival_data['estimated']
    return arrival_data.get('scheduled')

def fetch_flights(target_airport="HND"):
    """
    APIから羽田の最新フライト情報を取得
    """
    # 💡 キーが読み込めていない場合の最終警告
    if not ACCESS_KEY:
        print("⚠️ エラー: config.py の CONFIG 内に 'AVIATIONSTACK_KEY' が見つかりません。")
        return []

    url = "http://api.aviationstack.com/v1/flights"
    
    # 💡 パラメータ：特定のステータスに絞らず、とにかく最新の100件を取る
    params = {
        'access_key': ACCESS_KEY,
        'arr_iata': target_airport,
        'limit': 100
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        
        # 401エラー（キーの間違い）が出た場合に詳細を表示
        if response.status_code == 401:
            print("⚠️ APIキーが無効、または設定ミスです(401)。")
            return []
            
        if response.status_code != 200:
            print(f"⚠️ APIエラー(Status: {response.status_code})")
            return []
            
        raw_data = response.json()
        if 'data' not in raw_data:
            return []

        processed_flights = []
        for flight in raw_data['data']:
            # 欠航便はスキップ
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