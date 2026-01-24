import os
import random
from datetime import datetime, timedelta
from api_handler_v2 import fetch_flight_data
from analyzer_v2 import analyze_demand
from renderer_new import render_html
from discord_bot import DiscordBot

CONFIG = {
    "AVIATION_STACK_API_KEY": os.environ.get("AVIATION_STACK_API_KEY"),
    "DISCORD_WEBHOOK_URL": os.environ.get("DISCORD_WEBHOOK_URL"),
}

def main():
    now = datetime.utcnow() + timedelta(hours=9)
    print(f"--- START: {now.strftime('%Y-%m-%d %H:%M:%S')} (JST) ---")

    # 1. パスワード生成 (日付連動ランダム) - 【維持】
    random.seed(now.strftime('%Y%m%d'))
    daily_pass = f"{random.randint(0, 9999):04d}"
    print(f"PASS: {daily_pass}")

    # 2. データ取得 - 【維持】
    api_key = CONFIG.get("AVIATION_STACK_API_KEY")
    flights_raw = fetch_flight_data(api_key)
    
    # 3. 鉄壁の旅客便フィルター - 【維持】
    flights = []
    for f in flights_raw:
        if f.get('status') == 'cancelled': continue
        
        airline = str(f.get('airline', '')).lower()
        f_num = str(f.get('flight_number', '')).lower()
        
        if 'cargo' in airline or 'cargo' in f_num:
            continue
        
        flights.append(f)

    print(f"LOG: Total {len(flights_raw)} -> Passenger Only {len(flights)}")

    # 4. 分析 & HTML生成 - 【維持】
    analysis_result = analyze_demand(flights)
    render_html(analysis_result, daily_pass)
    
    # 5. Discord通知 (朝6時台のみ)
    bot = DiscordBot()
    
    # 【変更点】ここだけ修正しました
    # < 20 だと、10分間隔(06:00, 06:10)でも15分間隔(06:00, 06:15)でも
    # 2回ヒットして二重投稿になってしまうため、 < 8 (8分間) に狭めました。
    # これで06:00の1回だけ確実に送信されます。
    if now.hour == 6 and 0 <= now.minute < 8:
        bot.send_daily_info(CONFIG.get("DISCORD_WEBHOOK_URL"), daily_pass)

    print("--- END: SUCCESS ---")

if __name__ == "__main__":
    main()
