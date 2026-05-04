import requests
from datetime import datetime

# サニーさんのAPIキー
API_KEY = "dd32199bfacf0d3d6f8d538b4511d29b"

def check_today_status(iata_code, airport_name):
    """
    今日の日付を自動取得し、その日のデータを1回だけ取得して表示する
    """
    # 実行時の「今日の日付」を自動で YYYY-MM-DD 形式にする
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': API_KEY,
        'arr_iata': iata_code,
        'flight_date': today_str, # 自動取得した今日の日付を指定
        'limit': 5
    }

    print(f"\n--- {airport_name}({iata_code}) [{today_str}指定] の状況を確認中 ---")
    
    try:
        # APIへの通信（これ1回のみ）
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        flights = data.get('data', [])
        total = data.get('pagination', {}).get('total', 0)
        print(f"結果: 本日の総件数 {total}件中、上位 {len(flights)}件を表示します。")
        
        if len(flights) > 0:
            for i, f in enumerate(flights, 1):
                flight_num = f.get('flight', {}).get('iata', '不明')
                dep_airport = f.get('departure', {}).get('airport', '不明')
                s_arr = f.get('arrival', {}).get('scheduled', 'None')
                
                # 到着時刻と出発地の情報を確認
                status_time = "✅ 時刻あり" if s_arr != 'None' and s_arr is not None else "❌ 時刻なし(None)"
                status_dep = "✅ 出発地あり" if dep_airport != '不明' and dep_airport is not None else "❌ 出発地なし"
                
                print(f"  {i}. 便名: {flight_num}, 出発地: {dep_airport} [{status_dep}], 到着予定: {s_arr} [{status_time}]")
        else:
            print(f"  ⚠️ 本日のデータは「0件」でした。まだ引き出しが空のようです。")
            
    except Exception as e:
        print(f"  エラーが発生しました: {e}")

if __name__ == "__main__":
    print("【API 復旧状況 1点集中検証プログラム】")
    
    # 羽田空港の「今日」を1回だけチェック
    check_today_status('HND', '羽田空港')

    print("\n-------------------------------------------")
    print("「時刻あり」と「出発地あり」が揃っていれば、本番起動OKです。")
