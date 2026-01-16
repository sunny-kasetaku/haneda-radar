import requests
from datetime import datetime, timedelta

# config.py から設定を読み込む
try:
    from config import CONFIG
    # CONFIG辞書からキーを取得
    ACCESS_KEY = CONFIG.get("AVIATIONSTACK_KEY")
    
    # もし AVIATIONSTACK_KEY という名前でなければ、一般的に使われる他の名前も試す
    if not ACCESS_KEY:
        ACCESS_KEY = CONFIG.get("API_KEY")
except ImportError:
    ACCESS_KEY = None

def get_refined_arrival_time(arrival_data):
    """
    APIの到着データから、最も信頼できる到着時刻を一つ選出する
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
        except:
            return scheduled_str
    return scheduled_str

def fetch_flights(target_airport="HND"):
    """
    APIから羽田のフライト情報を取得
    """
    # キーが取得できていない場合の安全策
    if not ACCESS_KEY:
        print("⚠️ エラー: APIキー(AVIATIONSTACK_KEY)が config.py 内で見つかりません。")
        return []

    url = "http://api.aviationstack.com/v1/flights"
    
    # 💡 パラメータを確実にセット
    params = {
        'access_key': ACCESS_KEY,
        'arr_iata': target_airport,
        'limit': 100,
        'flight_status': 'active'
    }

    try:
        # タイムアウトを設定してフリーズを防ぐ
        response = requests.get(url, params=params, timeout=15)
        
        # エラーがあればここで詳細を表示
        if response.status_code != 200:
            print(f"⚠️ APIエラー発生 (Status: {response.status_code})")
            print(f"URL: {response.url.split('access_key=')[0]}access_key=HIDDEN...")
            return []
            
        raw_data = response.json()

        if 'data' not in raw_data:
            return []

        processed_flights = []
        for flight in raw_data['data']:
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