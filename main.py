import time
from datetime import datetime
from api_handler import fetch_flights
from analyzer import analyze_demand

def display_report(demand_results):
    """
    分析結果を現場のドライバーさん向けに分かりやすく表示する
    """
    print("\n" + "="*50)
    print(f" 🚕 KASETACK 羽田需要レーダー ({datetime.now().strftime('%H:%M:%S')} 現在)")
    print("   〜 今から1時間後までに乗り場に現れる予想人数 〜")
    print("="*50)
    
    # 5つの乗り場を順番に表示
    stand_order = [
        "1号 (T1/JAL系)",
        "2号 (T2/ANA系)",
        "3号 (T3/国際)",
        "4号 (T2/国際)",
        "国際 (T3/全体)"
    ]
    
    for stand in stand_order:
        count = demand_results.get(stand, 0)
        
        # 簡易的な「現場判断サイン」のロジック
        if count >= 150:
            status = "🚀 【激アツ】即・実車の可能性大！"
        elif count >= 80:
            status = "🔥 【GO】1時間以内に実車濃厚"
        elif count >= 30:
            status = "👀 【微妙】少し待ち時間が出るかも"
        else:
            status = "⚠️ 【STAY】今は他へ行くのが賢明"
            
        print(f"【{stand}】 {str(count).rjust(4)} 人  >> {status}")

    print("="*50)
    print("※ 実際の着陸時刻と遅延を反映したリアルタイム分析です")

def main():
    print("📡 システム起動中... 羽田の空をスキャンしています。")
    
    while True:
        # 1. APIから最新データを取得
        flights = fetch_flights()
        
        if flights:
            # 2. 新ロジックで需要を分析
            results = analyze_demand(flights)
            
            # 3. 画面に表示
            display_report(results)
        else:
            print("⚠️ データが取得できませんでした。APIキーや通信を確認してください。")

        # 4. 次の更新まで待機（例：5分おきに更新）
        print("\n🔄 5分後に自動更新します... (Ctrl+Cで停止)")
        time.sleep(300)

if __name__ == "__main__":
    main()