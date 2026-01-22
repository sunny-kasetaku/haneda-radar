import requests
import json
import time

def fetch_flight_data(api_key):
    """
    AviationStack APIからデータを取得
    API側のフィルタを使わず、全データを取得してからPythonで処理する（400エラー回避）
    """
    # 念のため http に戻します（有料版でも http は通るため、最も確実な方を選びます）
    base_url = "http://api.aviationstack.com/v1/flights"
    
    # ▼ 修正箇所：flight_status を削除しました。
    # arr_iata=HND (羽田到着) だけを指定する一番シンプルなリクエストにします。
    params = {
        'access_key': api_key,
        'arr_iata': 'HND',
        'limit': 100,
        'offset': 0
    }

    print(f"📡 APIリクエスト開始...")
    
    all_flights = []
    
    # 3ページ分（300件）取得して、遅延便やマイナー便も全部拾います
    for i in range(3):
        params['offset'] = i * 100
        print(f"   -> Page {i+1} 取得中 (Offset {params['offset']})...")
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            raw_data = data.get('data', [])
            if not raw_data:
                break 
            
            for f in raw_data:
                info = extract_flight_info(f)
                if info:
                    all_flights.append(info)
            
            if len(raw_data) < 100:
                break
                
        except Exception as e:
            print(f"❌ API Error (Page {i+1}): {e}")
            # エラーが出ても、そこまでに取れたデータがあれば続行させる
            if len(all_flights) > 0:
                print("⚠️ 部分的なデータ取得で続行します")
                break
            else:
                # 1件も取れなければ終了
                break
            
        time.sleep(0.2)

    print(f"✅ 合計取得数: {len(all_flights)}件")
    return all_flights

def extract_flight_info(flight):
    arr = flight.get('arrival', {})
    airline = flight.get('airline', {})
    dep = flight.get('departure', {})
    
    # statusフィルタを外したので、ここで「キャンセルされた便」などは除外しても良いですが、
    # 遅延便(active)などを漏らさないよう、とりあえず全部通してAnalyzerに任せます。

    # 到着時刻の取得優先度
    arrival_time = arr.get('estimated') or arr.get('actual') or arr.get('scheduled')
    
    if not arrival_time:
        return None

    term = arr.get('terminal')
    if term is None:
        term = "Intl"

    return {
        "flight_number": f"{airline.get('iata', '??')}{flight.get('flight', {}).get('number', '??')}",
        "airline": airline.get('name', 'Unknown'),
        "origin": dep.get('airport', 'Unknown'),
        "origin_iata": dep.get('iata', 'UNK'),
        "terminal": str(term),
        "arrival_time": arrival_time,
        "status": flight.get('flight_status', 'unknown')
    }