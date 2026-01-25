import os
import random
from datetime import datetime, timedelta
# api_handler_v2 (中身は最新のv3ロジック) を使用
from api_handler_v2 import fetch_flight_data  
from analyzer_v2 import analyze_demand
from renderer_new import render_html
from discord_bot import DiscordBot

CONFIG = {
    "AVIATION_STACK_API_KEY": os.environ.get("AVIATION_STACK_API_KEY"),
    "DISCORD_WEBHOOK_URL": os.environ.get("DISCORD_WEBHOOK_URL"),
}

def main():
    # 1. 現在時刻を「日本時間 (JST)」で確定させる
    now = datetime.utcnow() + timedelta(hours=9)
    today_str = now.strftime('%Y-%m-%d') # 例: "2026-01-26"
    
    print(f"--- START: {now.strftime('%Y-%m-%d %H:%M:%S')} (JST) ---")

    # 2. パスワード生成
    if now.hour < 6:
        pass_date = now - timedelta(days=1)
    else:
        pass_date = now
    random.seed(pass_date.strftime('%Y%m%d'))
    daily_pass = f"{random.randint(0, 9999):04d}"
    print(f"PASS: {daily_pass}")

    # 3. データ取得 (日付指定でUTCズレを防止)
    api_key = CONFIG.get("AVIATION_STACK_API_KEY")
    
    # 【修正点】「今日の日付」を明示的に指定して叩く
    print(f"LOG: Force fetching data for DATE: {today_str} (JST)...")
    flights_raw = fetch_flight_data(api_key, date_str=today_str)
    print(f"LOG: Fetched Today's Data: {len(flights_raw)} records")

    # 日またぎ補完 (深夜0時〜4時の間だけ、昨日のデータも追加で拾う)
    if 0 <= now.hour < 4:
        target_date = now - timedelta(days=1)
        yesterday_str = target_date.strftime('%Y-%m-%d')
        print(f"LOG: Midnight detected. Also fetching YESTERDAY ({yesterday_str})...")
        
        flights_sub = fetch_flight_data(api_key, date_str=yesterday_str)
        flights_raw.extend(flights_sub)
        print(f"LOG: Added Yesterday's Data: +{len(flights_sub)} records")

    # 4. 旅客便フィルター
    flights = []
    for f in flights_raw:
        if f.get('status') == 'cancelled': continue
        
        airline = str(f.get('airline', '')).lower()
        f_num = str(f.get('flight_number', '')).lower()
        if 'cargo' in airline or 'cargo' in f_num: continue
        
        flights.append(f)

    print(f"LOG: Total Merged {len(flights_raw)} -> Passenger Only {len(flights)}")

    # 5. 分析 & HTML生成
    analysis_result = analyze_demand(flights)
    render_html(analysis_result, daily_pass)
    
    # 6. Discord通知 (朝6時台のみ)
    bot = DiscordBot()
    if now.hour == 6 and 0 <= now.minute < 8:
        bot.send_daily_info(CONFIG.get("DISCORD_WEBHOOK_URL"), daily_pass)

    print("--- END: SUCCESS ---")

if __name__ == "__main__":
    main()
