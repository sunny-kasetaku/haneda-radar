# ==========================================
# Project: KASETACK - api_handler_v2.py (Fixed)
# ==========================================
import requests
import time
from config import CONFIG

# APIキーの取得
ACCESS_KEY = CONFIG.get("AVIATIONSTACK_KEY") or CONFIG.get("API_KEY")

def fetch_flights_v2(target_airport="HND", pages=3):
    """
    指定されたページ数（1ページ100件）分、繰り返しAPIを叩いてデータを取得する。
    有料版(HTTPS)対応済み。
    """
    if not ACCESS_KEY:
        print("⚠️ エラー: APIキーが見つかりません。config.pyを確認してください。")
        return []

    # ★修正1: 有料版なので HTTPS に変更
    url = "https://api.aviationstack.com/v1/flights"
    
    all_flights = []
    seen_flight_numbers = set() # 重複チェック用

    for i in range(pages):
        offset = i * 100
        print(f"📡 APIリクエスト中... (Page {i+1}, Offset {offset})")
        
        params = {
            'access_key': ACCESS_KEY,
            'arr_iata': target_airport,
            'limit': 100,
            'offset': offset
            # ★修正2: 'landed'指定を削除。
            # これを消すことで、到着済みだけでなく「これから来る便(scheduled)」も取得でき、
            # Analyzerで未来の需要予測ができるようになります。
        }

        try:
            # タイムアウトを少し長めに設定
            response = requests.get(url, params=params, timeout=20)
            
            if response.status_code != 200:
                print(f"❌ APIエラー(Page {i+1}): {response.status_code}")
                # エラー詳細を表示
                print(response.text)
                break
                
            raw_data = response.json()
            
            # API側のエラーチェック
            if 'error' in raw_data:
                print(f"❌ API Key Error: {raw_data['error']}")
                break

            data_list = raw_data.get('data', [])
            print(f"   -> 取得数: {len(data_list)}件")

            for flight in data_list:
                f_num = flight.get('flight', {}).get('iata')
                
                # 重複の排除（同じ便を二重に数えない）
                if f_num and f_num not in seen_flight_numbers:
                    seen_flight_numbers.add(f_num)
                    
                    arrival = flight.get('arrival', {})
                    # 時刻の取得（Analyzerが期待するキーを作成）
                    a_time = arrival.get('actual') or arrival.get('estimated') or arrival.get('scheduled') or ""
                    
                    # ★ここが重要！Analyzer用にデータを「翻訳」している部分
                    all_flights.append({
                        'flight_iata': f_num or "??",
                        'airline': flight.get('airline', {}).get('name') or "Unknown",
                        'arrival_time': a_time,
                        'terminal': arrival.get('terminal'),
                        'origin': flight.get('departure', {}).get('iata'), 
                        'pax': flight.get('pax') or 150 
                    })
            
            # 連射防止（優しさ）
            time.sleep(1)

        except Exception as e:
            print(f"⚠️ 通信エラー(Page {i+1}): {e}")
            break

    print(f"✅ 合計取得数: {len(all_flights)}件")
    return all_flights