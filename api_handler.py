import requests
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))

try:
    from config import CONFIG
    ACCESS_KEY = CONFIG.get("AVIATIONSTACK_KEY") or CONFIG.get("API_KEY")
except Exception:
    ACCESS_KEY = None

def get_refined_arrival_time(arrival_data):
    # 実着(actual)がなければ予定(scheduled)を使用
    return arrival_data.get('actual') or arrival_data.get('estimated') or arrival_data.get('scheduled')

def fetch_flights(target_airport="HND"):
    if not ACCESS_KEY:
        print("⚠️ エラー: APIキーが見つかりません。")
        return []

    url = "http://api.aviationstack.com/v1/flights"
    
    # 💡 改善：特定のステータスに絞らず、幅広く100件取得
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
        if 'data' not in raw_data: return []

        all_flights = []
        now_jst = datetime.now(JST)

        for flight in raw_data['data']:
            arrival = flight.get('arrival', {})
            arrival_time_str = get_refined_arrival_time(arrival)
            if not arrival_time_str: continue

            # 時刻をJSTに変換
            try:
                t_str = arrival_time_str.replace('Z', '+00:00')
                dt_jst = datetime.fromisoformat(t_str).astimezone(JST)
            except: continue

            # 💡 フィルタリング：
            # 「2時間前に着いた便」から「3時間後に着く便」までを有効データとする
            if now_jst - timedelta(hours=2) <= dt_jst <= now_jst + timedelta(hours=3):
                all_flights.append({
                    'flight_iata': flight.get('flight', {}).get('iata') or "??",
                    'airline': flight.get('airline', {}).get('name') or "Unknown",
                    'arrival_time': dt_jst.isoformat(),
                    'terminal': arrival.get('terminal'),
                    'status': flight.get('flight_status')
                })

        # 💡 到着時間が「今」に近い順に並べ替えて返す
        all_flights.sort(key=lambda x: abs((datetime.fromisoformat(x['arrival_time']) - now_jst).total_seconds()))
        
        return all_flights

    except Exception as e:
        print(f"⚠️ 通信エラー: {e}")
        return []