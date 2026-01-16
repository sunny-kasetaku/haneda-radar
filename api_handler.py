import requests
from datetime import datetime, timedelta

# もし config.py を作っているならここが活きます
try:
    from config import AVIATIONSTACK_KEY as ACCESS_KEY
except ImportError:
    # config.py がない場合は、ここに直接キーを貼り付けてください
    ACCESS_KEY = "76e04028a66e0e2d2b42d7d9c75462e7"

def get_refined_arrival_time(arrival_data):
    """
    APIの到着データから、最も信頼できる到着時刻を一つ選出する
    優先順位: 1.実着(actual) 2.推定(estimated) 3.遅延込(scheduled+delay) 4.定刻(scheduled)
    """
    # 1. 実際に着陸した時刻（これがあれば確定）
    if arrival_data.get('actual'):
        return arrival_data['actual']
    
    # 2. 最新の推定時刻（管制の予報）
    if arrival_data.get('estimated'):
        return arrival_data['estimated']
    
    # 3. 遅延情報に基づく計算（定刻 + 遅延分）
    scheduled_str = arrival_data.get('scheduled')
    delay = arrival_data.get('delay')
    
    if scheduled_str and delay:
        try:
            # ISO形式(2026-01-17T09:55:00+00:00)を解析
            base_time = datetime.fromisoformat(scheduled_str.replace('Z', '+00:00'))
            refined_time = base_time + timedelta(minutes=int(delay))
            return refined_time.isoformat()
        except Exception:
            return scheduled_str # 計算失敗時は定刻へ
            
    # 4. 何もなければ定刻をそのまま返す
    return scheduled_str

def fetch_flights(target_airport="HND"):
    """
    APIから羽田のフライト情報を取得し、精査して返す
    """
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': ACCESS_KEY,
        'arr_iata': target_airport,
        'limit': 100
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # 通信エラーがあればここで例外を出す
        raw_data = response.json()

        if 'data' not in raw_data:
            return []

        processed_flights = []
        for flight in raw_data['data']:
            # ステータス判定: 欠航(cancelled)以外はすべて拾う
            if flight.get('flight_status') == 'cancelled':
                continue

            arrival = flight.get('arrival', {})
            
            # 💡 最も正確な到着時間を算出
            arrival_time = get_refined_arrival_time(arrival)
            
            if not arrival_time:
                continue

            processed_flights.append({
                'flight_iata': flight.get('flight', {}).get('iata'),
                'airline': flight.get('airline', {}).get('name'),
                'arrival_time': arrival_time,  # 精査された時間
                'terminal': arrival.get('terminal'), # nullの場合もあるがAnalyzerで補完
                'status': flight.get('flight_status')
            })

        return processed_flights

    except Exception as e:
        print(f"⚠️ API取得エラー: {e}")
        return []