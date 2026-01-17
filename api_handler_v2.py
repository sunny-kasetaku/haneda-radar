import requests
from datetime import datetime, timedelta, timezone

# config.py からキーを読み込む
try:
    from config import CONFIG
    ACCESS_KEY = CONFIG.get("AVIATIONSTACK_KEY") or CONFIG.get("API_KEY")
except:
    ACCESS_KEY = None

def fetch_flights_v2(target_airport="HND", pages=3):
    """
    【v2仕様】
    - 指定されたページ数（1ページ100件）分をおかわり取得
    - 取得した全データを「便名＋時刻」で重複排除する
    """
    if not ACCESS_KEY:
        print("⚠️ エラー: APIキーが見つかりません。")
        return []

    url = "http://api.aviationstack.com/v1/flights"
    all_raw_data = []

    # 💡 ページネーション（おかわり）
    for i in range(pages):
        params = {
            'access_key': ACCESS_KEY,
            'arr_iata': target_airport,
            'limit': 100,
            'offset': i * 100  # PL/SQLのOFFSETと同様
        }
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                page_data = response.json().get('data', [])
                if not page_data: break
                all_raw_data.extend(page_data)
            else:
                print(f"❌ APIエラー(Page {i+1}): {response.status_code}")
                break
        except Exception as e:
            print(f"❌ 通信エラー(Page {i+1}): {e}")
            break

    # 💡 重複排除ロジック（PL/SQLのDISTINCT相当）
    seen_ids = set()
    unique_flights = []

    for f in all_raw_data:
        arrival = f.get('arrival', {})
        t_str = arrival.get('actual') or arrival.get('estimated') or arrival.get('scheduled')
        if not t_str: continue
        
        # 便名と時刻を組み合わせてユニークキーを作る
        flight_id = f"{f.get('flight', {}).get('iata')}_{t_str}"
        
        if flight_id not in seen_ids:
            seen_ids.add(flight_id)
            unique_flights.append({
                'flight_iata': f.get('flight', {}).get('iata') or "??",
                'airline': f.get('airline', {}).get('name') or "Unknown",
                'arrival_time': t_str,
                'terminal': arrival.get('terminal'),
                'status': f.get('flight_status')
            })
            
    return unique_flights