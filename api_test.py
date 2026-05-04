import requests
from datetime import datetime

# サニーさんのAPIキー
API_KEY = "dd32199bfacf0d3d6f8d538b4511d29b"

def check_status(target_date=None):
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': API_KEY,
        'arr_iata': 'HND',
        'limit': 5
    }
    
    if target_date:
        params['flight_date'] = target_date
        label = f"【{target_date} 指定】"
    else:
        label = "【日付指定なし（最新データ）】"

    print(f"\n--- {label} の状況を確認中 ---")
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        flights = data.get('data', [])
        total = data.get('pagination', {}).get('total', 0)
        
        print(f"結果: 総件数 {total}件中、上位 {len(flights)}件を確認")
        
        if len(flights) > 0:
            for i, f in enumerate(flights, 1):
                flight_num = f.get('flight', {}).get('iata', '不明')
                dep = f.get('departure', {}).get('airport', '不明')
                s_arr = f.get('arrival', {}).get('scheduled', 'None')
                
                # 時刻が入っているかどうかが復旧の鍵
                status = "✅ 時刻あり" if s_arr != 'None' and s_arr is not None else "❌ 時刻なし(None)"
                print(f"  {i}. {flight_num} ({dep}) -> 到着予定: {s_arr} [{status}]")
        else:
            print("  ⚠️ データが1件もありませんでした。")
            
    except Exception as e:
        print(f"  エラーが発生しました: {e}")

if __name__ == "__main__":
    print("【1:00 最終確認用テストプログラム】")
    
    # 1. まずは日付指定なしで「今、APIが何を出しているか」を確認
    check_status(None)
    
    # 2. 念のため「5/2」の None が治っているかも確認（リハビリ状況の確認）
    check_status("2026-05-02")

    print("\n-------------------------------------------")
    print("「時刻あり」が表示されれば、完全復旧の合図です。")
