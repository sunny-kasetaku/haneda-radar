import time
from datetime import datetime, timezone, timedelta
from api_handler import fetch_flights
from analyzer import analyze_demand

# 日本時間の定義
JST = timezone(timedelta(hours=9))

def display_report(demand_results):
    """
    分析結果を現場のドライバーさん向けに分かりやすく表示する
    """
    print("\n" + "="*60)
    print(f" 🚕 KASETACK 羽田需要レーダー ({datetime.now(JST).strftime('%H:%M:%S')} 現在)")
    print("   〜 今から1時間後までに乗り場に現れる予想人数 〜")
    print("="*60)
    
    stand_order = [
        "1号 (T1/JAL系)",
        "2号 (T2/ANA系)",
        "3号 (T3/国際)",
        "4号 (T2/国際)",
        "国際 (T3/全体)"
    ]
    
    for stand in stand_order:
        count = demand_results.get(stand, 0)
        
        if count >= 150:
            status = "🚀 【激アツ】即・実車の可能性大！"
        elif count >= 80:
            status = "🔥 【GO】1時間以内に実車濃厚"
        elif count >= 30:
            status = "👀 【微妙】少し待ち時間が出るかも"
        else:
            status = "⚠️ 【STAY】今は他へ行くのが賢明"
            
        print(f"【{stand}】 {str(count).rjust(4)} 人  >> {status}")

    print("="*60)
    print("※ 実際の着陸時刻と遅延を反映したリアルタイム分析です")

def main():
    print("📡 システム起動中... 羽田の空をスキャンしています。")
    
    while True:
        # 1. APIから最新データを取得
        flights = fetch_flights()
        
        if flights:
            # --- 💡 調査用：取得したデータの先頭数件を表示 ---
            print(f"\n🔍 【データ確認】合計 {len(flights)} 件の便を取得しました。")
            print("直近の到着予定便（一部抜粋）:")
            # 到着時間が「今」に近い順に並び替えて表示（デバッグ用）
            sorted_flights = sorted(flights, key=lambda x: x['arrival_time'])
            
            # リストが長すぎるので、最新の5件だけ表示
            for f in sorted_flights[:8]:
                # 時刻を見やすく成形
                try:
                    t_str = f['arrival_time'].replace('Z', '+00:00')
                    t_jst = datetime.fromisoformat(t_str).astimezone(JST).strftime('%H:%M')
                except:
                    t_jst = f['arrival_time']
                
                print(f"  ✈️ {f['flight_iata'].ljust(7)} | 到着:{t_jst} | T:{str(f['terminal']).ljust(2)} | 航空会社:{f['airline']}")
            print("-" * 60)
            # --- 💡 調査用ここまで ---

            # 2. 新ロジックで需要を分析
            results = analyze_demand(flights)
            
            # 3. 画面に表示
            display_report(results)
        else:
            print("⚠️ データが取得できませんでした。APIキーや通信を確認してください。")

        print("\n🔄 5分後に自動更新します... (Ctrl+Cで停止)")
        time.sleep(300)

if __name__ == "__main__":
    main()