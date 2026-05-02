import requests

# ここにサニーさんのAPIキーを貼り付けてください
API_KEY = "dd32199bfacf0d3d6f8d538b4511d29b"

url = "http://api.aviationstack.com/v1/flights"
params = {
    'access_key': API_KEY,
    'arr_iata': 'HND',
    'limit': 5  # とりあえず最新の5件だけ確認します
}

print("APIの状況を確認しています...")

try:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    flights = data.get('data', [])
    print(f"無事に通信できました！取得できた件数: {len(flights)}件 (最大5件)")
    
    if len(flights) > 0:
        for f in flights:
            flight_num = f.get('flight', {}).get('iata', '不明')
            dep_airport = f.get('departure', {}).get('airport', '不明')
            s_arr = f.get('arrival', {}).get('scheduled', '不明')
            print(f"便名: {flight_num}, 出発: {dep_airport}, 到着予定: {s_arr}")
    else:
        print("通信は成功しましたが、データが「0件」で返ってきています。")

except Exception as e:
    print(f"エラーが発生して通信できませんでした: {e}")
