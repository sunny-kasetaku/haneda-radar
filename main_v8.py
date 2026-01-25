import os
import random
from datetime import datetime, timedelta
# ▼ ここは api_handler_v2 のままでOKです
from api_handler_v2 import fetch_flight_data  
from analyzer_v2 import analyze_demand
from renderer_new import render_html
from discord_bot import DiscordBot

CONFIG = {
    "AVIATION_STACK_API_KEY": os.environ.get("AVIATION_STACK_API_KEY"),
    "DISCORD_WEBHOOK_URL": os.environ.get("DISCORD_WEBHOOK_URL"),
}

def main():
    # 日本時間 (JST)
    now = datetime.utcnow() + timedelta(hours=9)
    print(f"--- START: {now.strftime('%Y-%m-%d %H:%M:%S')} (JST) ---")

    # 1. パスワード生成 (0-6時は前日ベース)
    if now.hour < 6:
        pass_date = now - timedelta(days=1)
    else:
        pass_date = now
    random.seed(pass_date.strftime('%Y%m%d'))
    daily_pass = f"{random.randint(0, 9999):04d}"
    print(f"PASS: {daily_pass}")

    # 2. データ取得 (超省エネモード)
    api_key = CONFIG.get("AVIATION_STACK_API_KEY")
    
    # (A) 今日の分を取得 (これ1回で active/landed/scheduled 全て入る)
    flights_raw = fetch_flight_data(api_key)
    print(f"LOG: Fetched Today's Data: {len(flights_raw)} records")

    # (B) 日またぎ補完 (深夜0時〜4時の間だけ、昨日のデータも1回だけ取る)
    # ※23時台の「明日」取得は、今日のデータにscheduledが含まれるので不要になりました。
    if 0 <= now.hour < 4:
        target_date = now - timedelta(days=1)
        date_str = target_date.strftime('%Y-%m-%d')
        print(f"LOG: Midnight detected. Fetching YESTERDAY'S data ({date_str})...")
        
        flights_sub = fetch_flight_data(api_key, date_str=date_str)
        flights_raw.extend(flights_sub)
        print(f"LOG: Added Yesterday's Data: +{len(flights_sub)} records")

    # 3. 旅客便フィルター (Cargoやキャンセルを除外)
    flights = []
    for f in flights_raw:
        # キャンセルはAPIで除外できないのでここで弾く
        if f.get('status') == 'cancelled': continue
        
        airline = str(f.get('airline', '')).lower()
        f_num = str(f.get('flight_number', '')).lower()
        
        if 'cargo' in airline or 'cargo' in f_num:
            continue
        
        flights.append(f)

    print(f"LOG: Total Merged {len(flights_raw)} -> Passenger Only {len(flights)}")

    # 4. 分析 & HTML生成
    analysis_result = analyze_demand(flights)
    render_html(analysis_result, daily_pass)
    
    # 5. Discord通知 (朝6時台のみ)
    bot = DiscordBot()
    if now.hour == 6 and 0 <= now.minute < 8:
        bot.send_daily_info(CONFIG.get("DISCORD_WEBHOOK_URL"), daily_pass)

    print("--- END: SUCCESS ---")

if __name__ == "__main__":
    main()
