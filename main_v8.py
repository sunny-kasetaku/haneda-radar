import os
import requests
import json
import random
from datetime import datetime, timedelta
from api_handler_v2 import fetch_flight_data
from analyzer_v2 import analyze_demand
from renderer_new import render_html
from discord_bot import DiscordBot

# 設定
CONFIG = {
    "AVIATION_STACK_API_KEY": os.environ.get("AVIATION_STACK_API_KEY"),
    "DISCORD_WEBHOOK_URL": os.environ.get("DISCORD_WEBHOOK_URL"),
}

def main():
    # 日本時間 (JST)
    start_time = datetime.utcnow() + timedelta(hours=9)
    print("-" * 50)
    print(f"開始時刻: {start_time.strftime('%Y-%m-%d %H:%M:%S')} (JST)")

    # ▼ 日付をシードにして、その日固定のランダムな4桁を生成
    random.seed(start_time.strftime('%Y%m%d'))
    daily_pass = f"{random.randint(0, 9999):04d}"
    
    print(f"【重要】本日のランダムパスワード: {daily_pass}")
    print("-" * 50)

    # 2. データ取得
    print("📡 AviationStackから最新データを取得中...")
    flights_raw = fetch_flight_data(CONFIG.get("AVIATION_STACK_API_KEY"))
    raw_count = len(flights_raw)
    
    # 3. 旅客便のみにフィルタリング
    # typeがpassengerであること、便名にCargo等が含まれないことを確認
    flights = [
        f for f in flights_raw 
        if f.get('type') != 'cargo'
        and 'cargo' not in (f.get('flight_iata') or '').lower()
        and f.get('flight_status') != 'cancelled'
    ]
    passenger_count = len(flights)
    cargo_count = raw_count - passenger_count

    print(f"📊 データ取得結果:")
    print(f"   -> 全取得件数: {raw_count}件")
    print(f"   -> 貨物/不要便の除外: -{cargo_count}件")
    print(f"   -> 分析対象(旅客便): {passenger_count}件")
    
    # 4. 分析
    analysis_result = analyze_demand(flights)
    
    # 5. HTML生成
    render_html(analysis_result, daily_pass)
    
    # 6. 通知 (Discord) - 朝6時台のみ
    bot = DiscordBot()
    if start_time.hour == 6 and 0 <= start_time.minute < 20:
        print("🔔 Discord通知フェーズ: 定時連絡を送信します。")
        bot.send_daily_info(CONFIG.get("DISCORD_WEBHOOK_URL"), daily_pass)
    else:
        print(f"ℹ️  Discord通知フェーズ: 定時外のためスキップ（現在 {start_time.hour}時）")

    print("-" * 50)
    print("終了: 全プロセスが正常に完了しました。")
    print("-" * 50)

if __name__ == "__main__":
    main()
