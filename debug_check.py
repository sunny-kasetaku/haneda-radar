import os
import requests
import json
from datetime import datetime

# 設定（メインプログラムと同じ環境変数を使います）
API_KEY = os.environ.get("AVIATION_STACK_API_KEY")

def run_diagnosis():
    print("=== 🔍 API生データ診断ツール (ANA & 国際線捜索) ===")
    
    if not API_KEY:
        print("❌ エラー: APIキーが見つかりません。環境変数を設定してください。")
        return

    url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': API_KEY,
        'arr_iata': 'HND',  # 羽田空港到着便
        'limit': 100        # 直近100件を取得
    }

    print("📡 APIにデータを問い合わせ中...")
    try:
        response = requests.get(url, params=params)
        data = response.json()
    except Exception as e:
        print(f"❌ 通信エラー: {e}")
        return

    if 'data' not in data:
        print("❌ データが取得できませんでした。")
        print(f"レスポンス: {data}")
        return

    flights = data['data']
    print(f"✅ 取得成功: 全 {len(flights)} 件のデータを取得しました。\n")

    print("--- 【ANA (NH) / 全日空 便の解析】 ---")
    ana_count = 0
    for f in flights:
        airline = f.get('airline', {}).get('name', 'Unknown')
        flight_num = f.get('flight', {}).get('iata', 'UNK')
        
        # ANA便を探す ("All Nippon" または "ANA")
        if 'All Nippon' in airline or 'ANA' in airline:
            ana_count += 1
            status = f.get('flight_status', 'unknown')
            
            # 生の時刻データを取得
            arrival = f.get('arrival', {})
            scheduled = arrival.get('scheduled', '---')
            estimated = arrival.get('estimated', '---')
            actual = arrival.get('actual', '---')
            terminal = arrival.get('terminal', '---')
            
            print(f"✈️ 便名: {flight_num}")
            print(f"   Status    : {status}")
            print(f"   Terminal  : {terminal}")
            print(f"   Scheduled : {scheduled}") # ここが重要！09:00ならUTC、18:00ならJST
            print(f"   Actual    : {actual}")
            print("-" * 40)

    if ana_count == 0:
        print("⚠️ 警告: 取得した100件の中に ANA便 が1つもありませんでした。")
    else:
        print(f"➡ ANA便は {ana_count} 件見つかりました。")

    print("\n--- 【国際線ターミナル (T3) の解析】 ---")
    t3_count = 0
    for f in flights:
        arrival = f.get('arrival', {})
        terminal = str(arrival.get('terminal', ''))
        
        if '3' in terminal or 'Intl' in terminal:
            t3_count += 1
            flight_num = f.get('flight', {}).get('iata', 'UNK')
            scheduled = arrival.get('scheduled', '---')
            print(f"🌏 便名: {flight_num} (T3) | Scheduled: {scheduled}")
            
    if t3_count == 0:
        print("⚠️ 警告: T3(国際線) が1つもありませんでした。")

    print("\n=== 診断終了 ===")

if __name__ == "__main__":
    run_diagnosis()
