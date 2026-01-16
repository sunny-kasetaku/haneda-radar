import time
from datetime import datetime, timezone, timedelta
from api_handler import fetch_flights
from analyzer import analyze_demand

JST = timezone(timedelta(hours=9))

def display_report(demand_results):
    print("\n" + "="*65)
    print(f" 🚕 KASETACK 羽田需要レーダー ({datetime.now(JST).strftime('%H:%M:%S')} 現在)")
    print("    〜 今から1時間以内に乗り場に現れる「確実な需要」 〜")
    print("="*65)
    
    stand_order = ["1号 (T1/JAL系)", "2号 (T2/ANA系)", "3号 (T3/国際)", "4号 (T2/国際)", "国際 (T3/全体)"]
    
    for stand in stand_order:
        count = demand_results.get(stand, 0)
        if count >= 150: status = "🚀 【激アツ】即・実車の可能性大！"
        elif count >= 80: status = "🔥 【GO】1時間以内に実車濃厚"
        elif count >= 30: status = "👀 【微妙】少し待ち時間が出るかも"
        else: status = "⚠️ 【STAY】今は他へ行くのが賢明"
        print(f"【{stand}】 {str(count).rjust(4)} 人  >> {status}")
    print("="*65)

def main():
    print("📡 システム起動中... 羽田の空をスキャンしています。")
    
    while True:
        flights = fetch_flights()
        if flights:
            now = datetime.now(JST)
            # 💡 デバッグ表示の改善：今この瞬間に近い便（前後2時間以内）だけを抽出して表示
            print(f"\n🔍 【データ解析】合計 {len(flights)} 件の着陸データを精査中...")
            
            # 現在時刻に近い順にソート
            relevant_flights = []
            for f in flights:
                try:
                    t_jst = datetime.fromisoformat(f['arrival_time'].replace('Z', '+00:00')).astimezone(JST)
                    # 前後2時間以内の便を「今まさに重要な便」としてピックアップ
                    if now - timedelta(hours=2) <= t_jst <= now + timedelta(hours=2):
                        relevant_flights.append((f, t_jst))
                except: continue
            
            print("直近の重要便（乗り場への影響大）:")
            # 到着が新しい順に表示
            relevant_flights.sort(key=lambda x: x[1], reverse=True)
            for f, t in relevant_flights[:10]:
                print(f"  ✈️ {f['flight_iata'].ljust(7)} | 到着:{t.strftime('%H:%M')} | T:{str(f['terminal']).ljust(2)} | {f['airline']}")
            print("-" * 65)

            results = analyze_demand(flights)
            display_report(results)
        else:
            print("⚠️ データを取得できませんでした。")

        print(f"\n🔄 5分後に自動更新します... 次回 { (datetime.now(JST) + timedelta(minutes=5)).strftime('%H:%M') }")
        time.sleep(300)

if __name__ == "__main__":
    main()