# ==========================================
# Project: KASETACK - api_handler_v2.py (Data Fetcher Master)
# ==========================================
import requests
from config import CONFIG

# APIキーの取得
ACCESS_KEY = CONFIG.get("AVIATIONSTACK_KEY") or CONFIG.get("API_KEY")

def fetch_flights_v2(target_airport="HND", pages=3):
    """
    指定されたページ数（1ページ100件）分、繰り返しAPIを叩いてデータを取得する。
    重複を除去し、人数(pax)が空の場合は期待値150人を設定する。
    """
    if not ACCESS_KEY:
        print("⚠️ エラー: APIキーが見つかりません。config.pyを確認してください。")
        return []

    url = "http://api.aviationstack.com/v1/flights"
    all_flights = []
    seen_flight_numbers = set() # 重複チェック用

    for i in range(pages):
        offset = i * 100
        print(f"📡 APIリクエスト中... (Page {i+1}, Offset {offset})")
        
        params = {
            'access_key': ACCESS_KEY,
            'arr_iata': target_airport,
            'limit': 100,
            'offset': offset,
            'flight_status': 'landed' 
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200:
                print(f"❌ APIエラー(Page {i+1}): {response.status_code}")
                continue
                
            raw_data = response.json()
            data_list = raw_data.get('data', [])

            for flight in data_list:
                f_num = flight.get('flight', {}).get('iata')
                
                # 重複の排除（同じ便を二重に数えない）
                if f_num and f_num not in seen_flight_numbers:
                    seen_flight_numbers.add(f_num)
                    
                    arrival = flight.get('arrival', {})
                    # 時刻の取得（実際の着陸時間を最優先）
                    a_time = arrival.get('actual') or arrival.get('estimated') or arrival.get('scheduled') or ""
                    
                    all_flights.append({
                        'flight_iata': f_num or "??",
                        'airline': flight.get('airline', {}).get('name') or "Unknown",
                        'arrival_time': a_time,
                        'terminal': arrival.get('terminal'),
                        'origin': flight.get('departure', {}).get('iata'), # 出発地
                        'pax': flight.get('pax') or 150 # 💡 人数がない場合は期待値150人を注入
                    })
        except Exception as e:
            print(f"⚠️ 通信エラー(Page {i+1}): {e}")
            continue

    return all_flights