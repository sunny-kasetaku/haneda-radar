import os
import requests
import json
from datetime import datetime, timedelta

API_KEY = os.environ.get("AVIATION_STACK_API_KEY")

def run_diagnosis():
    print("=== 🔍 API生データ診断ツール v2 (エラー修正＆今日限定版) ===")
    
    if not API_KEY:
        print("❌ エラー: APIキーがありません。")
        return

    url = "http://api.aviationstack.com/v1/flights"
    
    # 【重要】明日のデータ邪魔なので、「active(飛行中)」と「landed(着陸)」に絞って取得する
    # 2回に分けて取得して結合します
    target_statuses = ['active', 'landed']
    all_flights = []

    for status in target_statuses:
        print(f"📡 API問い合わせ中 (Status: {status})...")
        params = {
            'access_key': API_KEY,
            'arr_iata': 'HND',
            'limit': 100,
            'flight_status': status  # ★ここ重要！「予定(scheduled)」を除外して実数だけ取る
        }
        try:
            res = requests.get(url, params=params)
            data = res.json()
            if 'data' in data:
                all_flights.extend(data['data'])
        except Exception as e:
            print(f"❌ 通信エラー ({status}): {e}")

    print(f"\n✅ 取得完了: 合計 {len(all_flights)} 件の【飛行中・着陸済み】データを確保しました。\n")

    print("--- 🔍 ANA (NH) / 全日空 便の捜索 ---")
    ana_count = 0
    
    # JST現在時刻（比較用）
    now_jst = datetime.utcnow() + timedelta(hours=9)
    print(f"🕒 現在の日本時間: {now_jst.strftime('%Y-%m-%d %H:%M')}")

    for f in all_flights:
        # エラー回避：航空会社名がないデータは「Unknown」として扱う
        airline_obj = f.get('airline') or {}
        airline_name = airline_obj.get('name') or "Unknown"
        
        flight_obj = f.get('flight') or {}
        flight_num = flight_obj.get('iata') or "UNK"
        
        # ANA便を探す
        if 'All Nippon' in airline_name or 'ANA' in airline_name:
            ana_count += 1
            status = f.get('flight_status', 'unknown')
            
            arrival = f.get('arrival') or {}
            terminal = arrival.get('terminal', '---')
            
            # 生の時間を取得
            # APIは通常UTCで返してくる
            scheduled_utc = arrival.get('scheduled', '---')
            actual_utc = arrival.get('actual') or arrival.get('estimated', '---')

            print(f"✈️ {flight_num} | Sts: {status} | T: {terminal}")
            print(f"   UTC Time : {scheduled_utc} (Actual: {actual_utc})")
            
            # 時差チェック
            try:
                # 文字列を日付に変換
                dt_utc = datetime.strptime(scheduled_utc[:19], "%Y-%m-%dT%H:%M:%S")
                # +9時間してJSTにする
                dt_jst = dt_utc + timedelta(hours=9)
                print(f"   JST 換算 : {dt_jst.strftime('%m/%d %H:%M')}")
            except:
                pass
                
            print("-" * 40)

    if ana_count == 0:
        print("⚠️ 警告: 'active' または 'landed' の中に ANA便 が1つもありませんでした。")
        print("可能性: APIが ANAのステータスを更新しておらず、全て 'scheduled' のまま放置されている可能性があります。")
    else:
        print(f"➡ ANA便は {ana_count} 件見つかりました。")

    print("\n=== 診断終了 ===")

if __name__ == "__main__":
    run_diagnosis()
